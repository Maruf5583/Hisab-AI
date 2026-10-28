import uuid
from decimal import Decimal
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.models.business import Business
from app.models.ledger import LedgerEntry
from app.models.party import Party
from app.schemas.ledger import (
    LedgerEntryRead,
    TrialBalanceAccountSummary,
    TrialBalanceResponse,
)
from app.schemas.common import PaginatedResponse
from app.api.deps import get_active_business

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[LedgerEntryRead], summary="List double-entry general ledger entries")
def list_ledger_entries(
    account_name: Optional[str] = Query(None, description="Filter by account: accounts_receivable, accounts_payable, cash_in_hand, bank, sales_revenue, purchase_expense"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    party_id: Optional[uuid.UUID] = Query(None, description="Filter by party"),
    start_date: Optional[date] = Query(None, description="From entry date"),
    end_date: Optional[date] = Query(None, description="To entry date"),
    search: Optional[str] = Query(None, description="Search description or account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LedgerEntryRead]:
    """Retrieve immutable general ledger records for the active business."""
    query = (
        db.query(LedgerEntry)
        .options(joinedload(LedgerEntry.party))
        .filter(LedgerEntry.business_id == business.id)
    )

    if account_name:
        query = query.filter(LedgerEntry.account_name == account_name)
    if transaction_type:
        query = query.filter(LedgerEntry.transaction_type == transaction_type)
    if party_id:
        query = query.filter(LedgerEntry.party_id == party_id)
    if start_date:
        query = query.filter(LedgerEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.entry_date <= end_date)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (LedgerEntry.description.ilike(search_pattern)) | (LedgerEntry.account_name.ilike(search_pattern))
        )

    total = query.count()
    items = (
        query.order_by(LedgerEntry.entry_date.desc(), LedgerEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result_items = []
    for entry in items:
        e_data = LedgerEntryRead.model_validate(entry)
        if entry.party:
            e_data.party_name = entry.party.name
        result_items.append(e_data)

    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/trial-balance", response_model=TrialBalanceResponse, summary="Get active trial balance equilibrium")
def get_trial_balance(
    as_of: Optional[date] = Query(None, description="As of entry date (defaults to today)"),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> TrialBalanceResponse:
    """Calculate debit and credit totals per account and verify trial balance equality."""
    as_of_date = as_of or date.today()

    rows = (
        db.query(
            LedgerEntry.account_name,
            func.coalesce(func.sum(LedgerEntry.debit), Decimal("0.00")).label("total_debit"),
            func.coalesce(func.sum(LedgerEntry.credit), Decimal("0.00")).label("total_credit"),
        )
        .filter(
            LedgerEntry.business_id == business.id,
            LedgerEntry.entry_date <= as_of_date,
        )
        .group_by(LedgerEntry.account_name)
        .all()
    )

    accounts_summary: List[TrialBalanceAccountSummary] = []
    grand_debit = Decimal("0.00")
    grand_credit = Decimal("0.00")

    for acc_name, deb, cred in rows:
        deb_dec = Decimal(str(deb))
        cred_dec = Decimal(str(cred))
        accounts_summary.append(
            TrialBalanceAccountSummary(
                account_name=acc_name,
                total_debit=deb_dec,
                total_credit=cred_dec,
                net_balance=deb_dec - cred_dec,
            )
        )
        grand_debit += deb_dec
        grand_credit += cred_dec

    diff = abs(grand_debit - grand_credit)
    is_balanced = diff < Decimal("0.01")

    return TrialBalanceResponse(
        as_of_date=as_of_date,
        accounts=accounts_summary,
        grand_total_debit=grand_debit,
        grand_total_credit=grand_credit,
        is_balanced=is_balanced,
        difference=diff,
    )
