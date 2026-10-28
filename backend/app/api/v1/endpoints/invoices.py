import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.invoice import Invoice, InvoiceItem
from app.models.party import Party
from app.models.ledger import LedgerEntry
from app.models.audit import AuditLog
from app.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceItemRead
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_active_business, require_business_role

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[InvoiceRead], summary="List and filter invoices and bills")
def list_invoices(
    invoice_type: Optional[str] = Query(None, description="Filter by type: sales, purchase"),
    invoice_status: Optional[str] = Query(None, alias="status", description="Filter by status: draft, approved, partially_paid, paid, reversed"),
    party_id: Optional[uuid.UUID] = Query(None, description="Filter by party"),
    start_date: Optional[date] = Query(None, description="Filter by issue date from"),
    end_date: Optional[date] = Query(None, description="Filter by issue date to"),
    search: Optional[str] = Query(None, description="Search invoice number or party name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[InvoiceRead]:
    """Retrieve invoices for the active business workspace with filtering and pagination."""
    query = (
        db.query(Invoice)
        .options(joinedload(Invoice.party), joinedload(Invoice.items))
        .filter(Invoice.business_id == business.id)
    )

    if invoice_type:
        query = query.filter(Invoice.invoice_type == invoice_type)
    if invoice_status:
        query = query.filter(Invoice.status == invoice_status)
    if party_id:
        query = query.filter(Invoice.party_id == party_id)
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Invoice.party).filter(
            (Invoice.invoice_number.ilike(search_pattern)) | (Party.name.ilike(search_pattern))
        )

    total = query.count()
    items = (
        query.order_by(Invoice.issue_date.desc(), Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Attach party_name
    result_items = []
    for inv in items:
        inv_data = InvoiceRead.model_validate(inv)
        if inv.party:
            inv_data.party_name = inv.party.name
        result_items.append(inv_data)

    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceRead, summary="Get invoice details")
def get_invoice(
    invoice_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    """Retrieve an invoice by ID with line items and party name."""
    inv = (
        db.query(Invoice)
        .options(joinedload(Invoice.party), joinedload(Invoice.items), joinedload(Invoice.allocations))
        .filter(Invoice.id == invoice_id, Invoice.business_id == business.id)
        .first()
    )
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found in active business workspace",
        )

    res = InvoiceRead.model_validate(inv)
    if inv.party:
        res.party_name = inv.party.name
    return res


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED, summary="Create a new invoice or purchase bill")
def create_invoice(
    invoice_in: InvoiceCreate,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    """Manually create and post a sales invoice or purchase bill with double-entry ledger entries."""
    # 1. Verify party belongs to business
    party = (
        db.query(Party)
        .filter(Party.id == invoice_in.party_id, Party.business_id == business.id)
        .first()
    )
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in active business workspace",
        )

    # 2. Check duplicate invoice number
    duplicate = (
        db.query(Invoice)
        .filter(
            Invoice.business_id == business.id,
            Invoice.invoice_type == invoice_in.invoice_type,
            Invoice.invoice_number == invoice_in.invoice_number,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An invoice with number '{invoice_in.invoice_number}' already exists for this business.",
        )

    now = datetime.now(timezone.utc)
    subtotal = invoice_in.subtotal if invoice_in.subtotal > Decimal("0.00") else (invoice_in.total_amount - invoice_in.tax_amount)
    due_amt = invoice_in.total_amount

    # 3. Create Invoice Record
    inv = Invoice(
        business_id=business.id,
        party_id=party.id,
        invoice_type=invoice_in.invoice_type,
        invoice_number=invoice_in.invoice_number,
        issue_date=invoice_in.issue_date,
        due_date=invoice_in.due_date,
        subtotal=subtotal,
        tax_amount=invoice_in.tax_amount,
        total_amount=invoice_in.total_amount,
        paid_amount=Decimal("0.00"),
        due_amount=due_amt,
        status="approved",
        notes=invoice_in.notes,
        created_by_user_id=current_user.id,
        approved_by_user_id=current_user.id,
        approved_at=now,
        posted_at=now,
    )
    db.add(inv)
    db.flush()

    # 4. Create Items
    if invoice_in.items:
        for itm in invoice_in.items:
            db_item = InvoiceItem(
                invoice_id=inv.id,
                description=itm.description,
                quantity=itm.quantity,
                unit_price=itm.unit_price,
                line_total=itm.line_total,
                tax_rate=itm.tax_rate,
            )
            db.add(db_item)

    # 5. Post Double-Entry Ledger Entries
    if invoice_in.invoice_type == "sales":
        # Debit: Accounts Receivable
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="sales_invoice",
                reference_id=inv.id,
                entry_date=invoice_in.issue_date,
                account_name="accounts_receivable",
                debit=invoice_in.total_amount,
                credit=Decimal("0.00"),
                party_id=party.id,
                description=f"Sales Invoice #{invoice_in.invoice_number} to {party.name}",
            )
        )
        # Credit: Sales Revenue
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="sales_invoice",
                reference_id=inv.id,
                entry_date=invoice_in.issue_date,
                account_name="sales_revenue",
                debit=Decimal("0.00"),
                credit=invoice_in.total_amount,
                party_id=party.id,
                description=f"Sales revenue from Invoice #{invoice_in.invoice_number}",
            )
        )
    else:
        # Purchase Invoice
        # Debit: Purchase Expense
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="purchase_invoice",
                reference_id=inv.id,
                entry_date=invoice_in.issue_date,
                account_name="purchase_expense",
                debit=invoice_in.total_amount,
                credit=Decimal("0.00"),
                party_id=party.id,
                description=f"Purchase bill #{invoice_in.invoice_number} from {party.name}",
            )
        )
        # Credit: Accounts Payable
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="purchase_invoice",
                reference_id=inv.id,
                entry_date=invoice_in.issue_date,
                account_name="accounts_payable",
                debit=Decimal("0.00"),
                credit=invoice_in.total_amount,
                party_id=party.id,
                description=f"Payable liability for Bill #{invoice_in.invoice_number}",
            )
        )

    # 6. Record Audit Log
    db.add(
        AuditLog(
            business_id=business.id,
            user_id=current_user.id,
            action="invoice_created",
            entity_type="invoice",
            entity_id=inv.id,
            changes={"number": inv.invoice_number, "type": inv.invoice_type, "total": str(inv.total_amount)},
        )
    )

    db.commit()
    db.refresh(inv)

    res = InvoiceRead.model_validate(inv)
    res.party_name = party.name
    return res


@router.post("/{invoice_id}/reverse", response_model=InvoiceRead, summary="Reverse a posted invoice with double-entry journal reversal")
def reverse_invoice(
    invoice_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    """Safely reverse an invoice by creating offsetting double-entry reversal lines."""
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.business_id == business.id)
        .first()
    )
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found in active business workspace",
        )

    if inv.status == "reversed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice is already reversed",
        )

    if inv.paid_amount > Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reverse an invoice with payments applied. Remove payment allocations first.",
        )

    today = date.today()

    # Reversing ledger entries
    if inv.invoice_type == "sales":
        # Credit Accounts Receivable
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="reversal",
                reference_id=inv.id,
                entry_date=today,
                account_name="accounts_receivable",
                debit=Decimal("0.00"),
                credit=inv.total_amount,
                party_id=inv.party_id,
                description=f"Reversal of Sales Invoice #{inv.invoice_number}",
                is_reversal=True,
            )
        )
        # Debit Sales Revenue
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="reversal",
                reference_id=inv.id,
                entry_date=today,
                account_name="sales_revenue",
                debit=inv.total_amount,
                credit=Decimal("0.00"),
                party_id=inv.party_id,
                description=f"Reversal of Sales Revenue from #{inv.invoice_number}",
                is_reversal=True,
            )
        )
    else:
        # Purchase reversal
        # Debit Accounts Payable
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="reversal",
                reference_id=inv.id,
                entry_date=today,
                account_name="accounts_payable",
                debit=inv.total_amount,
                credit=Decimal("0.00"),
                party_id=inv.party_id,
                description=f"Reversal of Purchase Bill #{inv.invoice_number}",
                is_reversal=True,
            )
        )
        # Credit Purchase Expense
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="reversal",
                reference_id=inv.id,
                entry_date=today,
                account_name="purchase_expense",
                debit=Decimal("0.00"),
                credit=inv.total_amount,
                party_id=inv.party_id,
                description=f"Reversal of Purchase Expense from #{inv.invoice_number}",
                is_reversal=True,
            )
        )

    inv.status = "reversed"
    db.add(inv)

    db.add(
        AuditLog(
            business_id=business.id,
            user_id=current_user.id,
            action="invoice_reversed",
            entity_type="invoice",
            entity_id=inv.id,
            changes={"status": "reversed", "amount": str(inv.total_amount)},
        )
    )

    db.commit()
    db.refresh(inv)
    return InvoiceRead.model_validate(inv)
