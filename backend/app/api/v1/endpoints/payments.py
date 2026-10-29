import uuid
import csv
import io
from decimal import Decimal
from datetime import datetime, timezone, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.payment import Payment, PaymentAllocation
from app.models.invoice import Invoice
from app.models.party import Party
from app.models.ledger import LedgerEntry
from app.models.audit import AuditLog
from app.schemas.payment import (
    PaymentCreate,
    PaymentRead,
    PaymentAllocateBatchRequest,
    PaymentAllocationRead,
)
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_active_business, require_business_role
from app.services.pdf_service import pdf_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[PaymentRead], summary="List and filter payments and receipts")
def list_payments(
    payment_type: Optional[str] = Query(None, description="Filter by type: customer_receipt, supplier_payment"),
    payment_method: Optional[str] = Query(None, description="Filter by method: cash, bank, bkash, nagad, other"),
    party_id: Optional[uuid.UUID] = Query(None, description="Filter by party"),
    start_date: Optional[date] = Query(None, description="Filter by date from"),
    end_date: Optional[date] = Query(None, description="Filter by date to"),
    search: Optional[str] = Query(None, description="Search reference number or party name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PaymentRead]:
    """Retrieve payments and customer receipts for the active business workspace."""
    query = (
        db.query(Payment)
        .options(joinedload(Payment.party), joinedload(Payment.allocations))
        .filter(Payment.business_id == business.id)
    )

    if payment_type:
        query = query.filter(Payment.payment_type == payment_type)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    if party_id:
        query = query.filter(Payment.party_id == party_id)
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Payment.party).filter(
            (Payment.reference_number.ilike(search_pattern)) | (Party.name.ilike(search_pattern))
        )

    total = query.count()
    items = (
        query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result_items = []
    for p in items:
        p_data = PaymentRead.model_validate(p)
        if p.party:
            p_data.party_name = p.party.name
        result_items.append(p_data)

    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/export", summary="Export payments as CSV spreadsheet")
def export_payments_csv(
    payment_type: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Response:
    """Stream complete filtered payments dataset as CSV spreadsheet."""
    query = (
        db.query(Payment)
        .options(joinedload(Payment.party))
        .filter(Payment.business_id == business.id)
    )
    if payment_type:
        query = query.filter(Payment.payment_type == payment_type)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)

    payments = query.order_by(Payment.payment_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Voucher ID",
        "Payment Date",
        "Party Name",
        "Payment Type",
        "Payment Method",
        "Reference Number",
        "Amount (BDT)",
        "Allocated Amount (BDT)",
        "Unapplied Amount (BDT)",
        "Status",
    ])

    for p in payments:
        party_name = p.party.name if p.party else ""
        writer.writerow([
            str(p.id)[:8].upper(),
            str(p.payment_date),
            party_name,
            p.payment_type,
            p.payment_method,
            p.reference_number or "",
            str(p.amount),
            str(p.allocated_amount),
            str(p.unapplied_amount),
            p.status,
        ])

    csv_data = output.getvalue()
    filename = f"payments_export_{date.today()}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{payment_id}", response_model=PaymentRead, summary="Get payment details with allocations")
def get_payment(
    payment_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaymentRead:
    """Retrieve a payment transaction by ID with its allocations."""
    p = (
        db.query(Payment)
        .options(joinedload(Payment.party), joinedload(Payment.allocations))
        .filter(Payment.id == payment_id, Payment.business_id == business.id)
        .first()
    )
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found in active business workspace",
        )

    res = PaymentRead.model_validate(p)
    if p.party:
        res.party_name = p.party.name
    return res


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED, summary="Record a new customer receipt or supplier payment")
def create_payment(
    payment_in: PaymentCreate,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRead:
    """Record customer receipt or supplier payment and post double-entry ledger entries."""
    party = (
        db.query(Party)
        .filter(Party.id == payment_in.party_id, Party.business_id == business.id)
        .first()
    )
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in active business workspace",
        )

    now = datetime.now(timezone.utc)
    payment = Payment(
        business_id=business.id,
        party_id=party.id,
        payment_type=payment_in.payment_type,
        payment_method=payment_in.payment_method,
        payment_date=payment_in.payment_date,
        amount=payment_in.amount,
        allocated_amount=Decimal("0.00"),
        unapplied_amount=payment_in.amount,
        reference_number=payment_in.reference_number,
        notes=payment_in.notes,
        status="posted",
        created_by_user_id=current_user.id,
        approved_by_user_id=current_user.id,
        posted_at=now,
    )
    db.add(payment)
    db.flush()

    # Determine asset account based on method
    asset_account = "bank" if payment_in.payment_method in ["bank", "bkash", "nagad"] else "cash_in_hand"

    # Post Double-Entry Ledger Entries
    if payment_in.payment_type == "customer_receipt":
        # Debit: Cash or Bank (Asset increase)
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="customer_receipt",
                reference_id=payment.id,
                entry_date=payment_in.payment_date,
                account_name=asset_account,
                debit=payment_in.amount,
                credit=Decimal("0.00"),
                party_id=party.id,
                description=f"Payment received from {party.name} via {payment_in.payment_method}",
            )
        )
        # Credit: Accounts Receivable (Asset decrease)
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="customer_receipt",
                reference_id=payment.id,
                entry_date=payment_in.payment_date,
                account_name="accounts_receivable",
                debit=Decimal("0.00"),
                credit=payment_in.amount,
                party_id=party.id,
                description=f"Receivable reduction for receipt from {party.name}",
            )
        )
    else:
        # Supplier Payment (Money out)
        # Debit: Accounts Payable (Liability decrease)
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="supplier_payment",
                reference_id=payment.id,
                entry_date=payment_in.payment_date,
                account_name="accounts_payable",
                debit=payment_in.amount,
                credit=Decimal("0.00"),
                party_id=party.id,
                description=f"Payment to {party.name} via {payment_in.payment_method}",
            )
        )
        # Credit: Cash or Bank (Asset decrease)
        db.add(
            LedgerEntry(
                business_id=business.id,
                transaction_type="supplier_payment",
                reference_id=payment.id,
                entry_date=payment_in.payment_date,
                account_name=asset_account,
                debit=Decimal("0.00"),
                credit=payment_in.amount,
                party_id=party.id,
                description=f"Disbursement to {party.name}",
            )
        )

    # Record Audit Log
    db.add(
        AuditLog(
            business_id=business.id,
            user_id=current_user.id,
            action="payment_recorded",
            entity_type="payment",
            entity_id=payment.id,
            changes={"amount": str(payment.amount), "method": payment.payment_method, "type": payment.payment_type},
        )
    )

    db.commit()
    db.refresh(payment)

    res = PaymentRead.model_validate(payment)
    res.party_name = party.name
    return res


@router.post("/{payment_id}/allocate", response_model=PaymentRead, summary="Allocate payment to one or more invoices")
def allocate_payment(
    payment_id: uuid.UUID,
    alloc_req: PaymentAllocateBatchRequest,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRead:
    """Safely allocate unapplied payment amount to specific outstanding invoices."""
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.party), joinedload(Payment.allocations))
        .filter(Payment.id == payment_id, Payment.business_id == business.id)
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found in active business workspace",
        )

    total_to_allocate = sum(a.allocated_amount for a in alloc_req.allocations)
    if total_to_allocate > payment.unapplied_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Requested allocation amount ({total_to_allocate}) exceeds "
                f"available unapplied payment balance ({payment.unapplied_amount})."
            ),
        )

    today = date.today()

    for item in alloc_req.allocations:
        inv = (
            db.query(Invoice)
            .filter(Invoice.id == item.invoice_id, Invoice.business_id == business.id)
            .first()
        )
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice ID {item.invoice_id} not found in this business workspace",
            )

        if inv.party_id != payment.party_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice #{inv.invoice_number} belongs to a different party than this payment.",
            )

        if item.allocated_amount > inv.due_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Allocated amount ({item.allocated_amount}) exceeds "
                    f"invoice #{inv.invoice_number} remaining due ({inv.due_amount})."
                ),
            )

        # Create PaymentAllocation record
        allocation = PaymentAllocation(
            business_id=business.id,
            payment_id=payment.id,
            invoice_id=inv.id,
            allocated_amount=item.allocated_amount,
            allocation_date=today,
        )
        db.add(allocation)

        # Update Invoice paid & due amount
        inv.paid_amount += item.allocated_amount
        inv.due_amount -= item.allocated_amount
        if inv.due_amount == Decimal("0.00"):
            inv.status = "paid"
        else:
            inv.status = "partially_paid"
        db.add(inv)

        # Update Payment allocated & unapplied amount
        payment.allocated_amount += item.allocated_amount
        payment.unapplied_amount -= item.allocated_amount

    db.add(payment)

    db.add(
        AuditLog(
            business_id=business.id,
            user_id=current_user.id,
            action="payment_allocated",
            entity_type="payment",
            entity_id=payment.id,
            changes={"total_allocated": str(total_to_allocate)},
        )
    )

    db.commit()
    db.refresh(payment)

    res = PaymentRead.model_validate(payment)
    if payment.party:
        res.party_name = payment.party.name
    return res


@router.get("/{payment_id}/pdf", summary="Generate and stream official money receipt / voucher PDF")
def download_payment_pdf(
    payment_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Response:
    """Generate and download official branded money receipt PDF."""
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.party), joinedload(Payment.allocations))
        .filter(Payment.id == payment_id, Payment.business_id == business.id)
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment voucher not found in active business workspace",
        )

    pdf_bytes = pdf_service.generate_payment_receipt_pdf(payment, business, payment.party)
    filename = f"Receipt-{str(payment.id)[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )

