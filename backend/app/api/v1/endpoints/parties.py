import uuid
from decimal import Decimal
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.models.party import Party
from app.models.ledger import LedgerEntry
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.party import PartyCreate, PartyRead, PartyUpdate, PartyBalanceRead
from app.schemas.ledger import LedgerEntryRead
from app.schemas.common import PaginatedResponse
from app.api.deps import get_active_business, require_business_role

router = APIRouter()


@router.post("/", response_model=PartyRead, status_code=status.HTTP_201_CREATED, summary="Create a new customer or supplier party")
def create_party(
    party_in: PartyCreate,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Party:
    """Create a new party (customer, supplier, or both) under the active business workspace."""
    # Check duplicate party name in same business
    existing = (
        db.query(Party)
        .filter(
            Party.business_id == business.id,
            func.lower(Party.name) == party_in.name.strip().lower(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Party with name '{party_in.name}' already exists in this workspace",
        )

    party = Party(
        business_id=business.id,
        name=party_in.name.strip(),
        party_type=party_in.party_type,
        phone=party_in.phone.strip() if party_in.phone else None,
        email=party_in.email.strip().lower() if party_in.email else None,
        address=party_in.address,
        tax_id=party_in.tax_id,
        opening_balance=party_in.opening_balance,
        opening_balance_type=party_in.opening_balance_type,
        is_active=True,
    )
    db.add(party)
    db.flush()

    # Record opening balance in double-entry general ledger if non-zero
    if party.opening_balance > Decimal("0.00"):
        account = "accounts_receivable" if party.opening_balance_type == "receivable" else "accounts_payable"
        debit_val = party.opening_balance if party.opening_balance_type == "receivable" else Decimal("0.00")
        credit_val = Decimal("0.00") if party.opening_balance_type == "receivable" else party.opening_balance

        entry = LedgerEntry(
            business_id=business.id,
            transaction_type="opening_balance",
            reference_id=party.id,
            entry_date=date.today(),
            account_name=account,
            debit=debit_val,
            credit=credit_val,
            party_id=party.id,
            description=f"Opening balance for {party.name} ({party.opening_balance_type})",
            is_reversal=False,
        )
        db.add(entry)

    db.commit()
    db.refresh(party)
    return party


@router.get("/", response_model=PaginatedResponse[PartyRead], summary="List and filter parties")
def list_parties(
    party_type: Optional[str] = Query(None, description="Filter by party type: buyer, supplier, both"),
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PartyRead]:
    """Retrieve parties for the active business workspace with optional filtering and pagination."""
    query = db.query(Party).filter(Party.business_id == business.id)

    if party_type:
        query = query.filter(Party.party_type == party_type)
    if is_active is not None:
        query = query.filter(Party.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Party.name.ilike(pattern),
                Party.phone.ilike(pattern),
                Party.email.ilike(pattern),
            )
        )

    total = query.count()
    items = query.order_by(Party.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{party_id}", response_model=PartyRead, summary="Get party details")
def get_party(
    party_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Party:
    """Retrieve details for a single party. Scoped to the active business."""
    party = db.query(Party).filter(Party.id == party_id, Party.business_id == business.id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in this business workspace",
        )
    return party


@router.put("/{party_id}", response_model=PartyRead, summary="Update party details")
def update_party(
    party_id: uuid.UUID,
    party_in: PartyUpdate,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Party:
    """Update party details. Scoped to active business."""
    party = db.query(Party).filter(Party.id == party_id, Party.business_id == business.id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in this business workspace",
        )

    update_data = party_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"]:
        # Verify name uniqueness if changed
        new_name = update_data["name"].strip()
        existing = (
            db.query(Party)
            .filter(
                Party.business_id == business.id,
                func.lower(Party.name) == new_name.lower(),
                Party.id != party.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another party with name '{new_name}' already exists",
            )
        update_data["name"] = new_name

    for field, val in update_data.items():
        setattr(party, field, val)

    db.commit()
    db.refresh(party)
    return party


@router.get("/{party_id}/balance", response_model=PartyBalanceRead, summary="Get reconciled party balance")
def get_party_balance(
    party_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PartyBalanceRead:
    """Compute real-time reconciled balance for a customer or supplier party."""
    party = db.query(Party).filter(Party.id == party_id, Party.business_id == business.id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in this business workspace",
        )

    # Invoices total (posted/approved only)
    invoices_total = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0.00))
        .filter(
            Invoice.business_id == business.id,
            Invoice.party_id == party.id,
            Invoice.status.in_(["approved", "partially_paid", "paid"]),
        )
        .scalar()
    )
    total_invoiced = Decimal(str(invoices_total))

    # Payments total (posted/approved only)
    payments_total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.00))
        .filter(
            Payment.business_id == business.id,
            Payment.party_id == party.id,
            Payment.status.in_(["approved", "posted"]),
        )
        .scalar()
    )
    total_paid = Decimal(str(payments_total))

    # Reconciled Balance formula based on party type / opening balance type
    opening = party.opening_balance
    if party.party_type == "buyer" or party.opening_balance_type == "receivable":
        current_balance = opening + total_invoiced - total_paid
        if current_balance > Decimal("0.00"):
            balance_type = "receivable"
        elif current_balance < Decimal("0.00"):
            balance_type = "payable"  # Overpayment/advance
        else:
            balance_type = "zero"
    else:  # supplier / payable
        current_balance = opening + total_invoiced - total_paid
        if current_balance > Decimal("0.00"):
            balance_type = "payable"
        elif current_balance < Decimal("0.00"):
            balance_type = "receivable"  # Advance payment
        else:
            balance_type = "zero"

    return PartyBalanceRead(
        party_id=party.id,
        party_name=party.name,
        party_type=party.party_type,
        opening_balance=party.opening_balance,
        opening_balance_type=party.opening_balance_type,
        total_invoiced=total_invoiced,
        total_paid=total_paid,
        current_balance=abs(current_balance),
        balance_type=balance_type,
    )


@router.get("/{party_id}/ledger", response_model=List[LedgerEntryRead], summary="Get ledger entries for party")
def get_party_ledger(
    party_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> List[LedgerEntry]:
    """Retrieve full chronological transaction ledger history for this party."""
    party = db.query(Party).filter(Party.id == party_id, Party.business_id == business.id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found in this business workspace",
        )

    entries = (
        db.query(LedgerEntry)
        .filter(
            LedgerEntry.business_id == business.id,
            LedgerEntry.party_id == party.id,
        )
        .order_by(LedgerEntry.entry_date.asc(), LedgerEntry.created_at.asc())
        .all()
    )
    return entries
