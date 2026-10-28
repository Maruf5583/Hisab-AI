import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.models.business import Business
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.ledger import LedgerEntry
from app.models.party import Party
from app.models.document import Document
from app.schemas.ledger import (
    AgingReportResponse,
    AgingBucket,
    PartyAgingDetail,
    CashbookReport,
    VatSummaryResponse,
    DashboardSummary,
    LedgerEntryRead,
)
from app.api.deps import get_active_business

router = APIRouter()


@router.get("/receivables-aging", response_model=AgingReportResponse, summary="Aged customer receivables report")
def get_receivables_aging(
    as_of: Optional[date] = Query(None, description="As of date (defaults to today)"),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> AgingReportResponse:
    """Calculate aged breakdown of customer receivables across 0-15, 16-30, 31-60, 60+ day buckets."""
    as_of_date = as_of or date.today()

    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.party))
        .filter(
            Invoice.business_id == business.id,
            Invoice.invoice_type == "sales",
            Invoice.due_amount > Decimal("0.00"),
            Invoice.status.in_(["approved", "partially_paid"]),
            Invoice.issue_date <= as_of_date,
        )
        .all()
    )

    b0_15 = Decimal("0.00")
    b0_15_cnt = 0
    b16_30 = Decimal("0.00")
    b16_30_cnt = 0
    b31_60 = Decimal("0.00")
    b31_60_cnt = 0
    b60_plus = Decimal("0.00")
    b60_plus_cnt = 0
    total_due = Decimal("0.00")

    party_map: Dict[uuid.UUID, Dict] = {}

    for inv in invoices:
        due = inv.due_amount
        total_due += due
        inv_date = inv.due_date or inv.issue_date
        days = (as_of_date - inv_date).days

        p_id = inv.party_id
        if p_id not in party_map:
            party_map[p_id] = {
                "party_id": p_id,
                "party_name": inv.party.name if inv.party else "Unknown",
                "phone": inv.party.phone if inv.party else None,
                "b0_15": Decimal("0.00"),
                "b16_30": Decimal("0.00"),
                "b31_60": Decimal("0.00"),
                "b60_plus": Decimal("0.00"),
                "total": Decimal("0.00"),
            }

        party_map[p_id]["total"] += due

        if days <= 15:
            b0_15 += due
            b0_15_cnt += 1
            party_map[p_id]["b0_15"] += due
        elif days <= 30:
            b16_30 += due
            b16_30_cnt += 1
            party_map[p_id]["b16_30"] += due
        elif days <= 60:
            b31_60 += due
            b31_60_cnt += 1
            party_map[p_id]["b31_60"] += due
        else:
            b60_plus += due
            b60_plus_cnt += 1
            party_map[p_id]["b60_plus"] += due

    party_details = [
        PartyAgingDetail(
            party_id=data["party_id"],
            party_name=data["party_name"],
            phone=data["phone"],
            bucket_0_15=data["b0_15"],
            bucket_16_30=data["b16_30"],
            bucket_31_60=data["b31_60"],
            bucket_60_plus=data["b60_plus"],
            total_due=data["total"],
        )
        for data in party_map.values()
    ]

    return AgingReportResponse(
        report_type="receivables",
        as_of_date=as_of_date,
        total_due=total_due,
        summary_0_15=AgingBucket(amount=b0_15, invoice_count=b0_15_cnt),
        summary_16_30=AgingBucket(amount=b16_30, invoice_count=b16_30_cnt),
        summary_31_60=AgingBucket(amount=b31_60, invoice_count=b31_60_cnt),
        summary_60_plus=AgingBucket(amount=b60_plus, invoice_count=b60_plus_cnt),
        party_details=party_details,
    )


@router.get("/payables-aging", response_model=AgingReportResponse, summary="Aged supplier payables report")
def get_payables_aging(
    as_of: Optional[date] = Query(None, description="As of date (defaults to today)"),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> AgingReportResponse:
    """Calculate aged breakdown of supplier payables across 0-15, 16-30, 31-60, 60+ day buckets."""
    as_of_date = as_of or date.today()

    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.party))
        .filter(
            Invoice.business_id == business.id,
            Invoice.invoice_type == "purchase",
            Invoice.due_amount > Decimal("0.00"),
            Invoice.status.in_(["approved", "partially_paid"]),
            Invoice.issue_date <= as_of_date,
        )
        .all()
    )

    b0_15 = Decimal("0.00")
    b0_15_cnt = 0
    b16_30 = Decimal("0.00")
    b16_30_cnt = 0
    b31_60 = Decimal("0.00")
    b31_60_cnt = 0
    b60_plus = Decimal("0.00")
    b60_plus_cnt = 0
    total_due = Decimal("0.00")

    party_map: Dict[uuid.UUID, Dict] = {}

    for inv in invoices:
        due = inv.due_amount
        total_due += due
        inv_date = inv.due_date or inv.issue_date
        days = (as_of_date - inv_date).days

        p_id = inv.party_id
        if p_id not in party_map:
            party_map[p_id] = {
                "party_id": p_id,
                "party_name": inv.party.name if inv.party else "Unknown",
                "phone": inv.party.phone if inv.party else None,
                "b0_15": Decimal("0.00"),
                "b16_30": Decimal("0.00"),
                "b31_60": Decimal("0.00"),
                "b60_plus": Decimal("0.00"),
                "total": Decimal("0.00"),
            }

        party_map[p_id]["total"] += due

        if days <= 15:
            b0_15 += due
            b0_15_cnt += 1
            party_map[p_id]["b0_15"] += due
        elif days <= 30:
            b16_30 += due
            b16_30_cnt += 1
            party_map[p_id]["b16_30"] += due
        elif days <= 60:
            b31_60 += due
            b31_60_cnt += 1
            party_map[p_id]["b31_60"] += due
        else:
            b60_plus += due
            b60_plus_cnt += 1
            party_map[p_id]["b60_plus"] += due

    party_details = [
        PartyAgingDetail(
            party_id=data["party_id"],
            party_name=data["party_name"],
            phone=data["phone"],
            bucket_0_15=data["b0_15"],
            bucket_16_30=data["b16_30"],
            bucket_31_60=data["b31_60"],
            bucket_60_plus=data["b60_plus"],
            total_due=data["total"],
        )
        for data in party_map.values()
    ]

    return AgingReportResponse(
        report_type="payables",
        as_of_date=as_of_date,
        total_due=total_due,
        summary_0_15=AgingBucket(amount=b0_15, invoice_count=b0_15_cnt),
        summary_16_30=AgingBucket(amount=b16_30, invoice_count=b16_30_cnt),
        summary_31_60=AgingBucket(amount=b31_60, invoice_count=b31_60_cnt),
        summary_60_plus=AgingBucket(amount=b60_plus, invoice_count=b60_plus_cnt),
        party_details=party_details,
    )


@router.get("/cashbook", response_model=CashbookReport, summary="Cash & Bank register and period summary")
def get_cashbook(
    start_date: Optional[date] = Query(None, description="Start date (defaults to 1st of month)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> CashbookReport:
    """Generate chronological cashbook report with opening cash, inflows, outflows, and closing cash."""
    today = date.today()
    s_date = start_date or date(today.year, today.month, 1)
    e_date = end_date or today

    cash_accounts = ["cash_in_hand", "bank"]

    # 1. Compute opening cash prior to start_date
    prior_rows = (
        db.query(
            func.coalesce(func.sum(LedgerEntry.debit), Decimal("0.00")).label("debits"),
            func.coalesce(func.sum(LedgerEntry.credit), Decimal("0.00")).label("credits"),
        )
        .filter(
            LedgerEntry.business_id == business.id,
            LedgerEntry.account_name.in_(cash_accounts),
            LedgerEntry.entry_date < s_date,
        )
        .first()
    )
    opening_cash = (
        Decimal(str(prior_rows.debits)) - Decimal(str(prior_rows.credits))
        if prior_rows
        else Decimal("0.00")
    )

    # 2. Entries during period
    entries = (
        db.query(LedgerEntry)
        .options(joinedload(LedgerEntry.party))
        .filter(
            LedgerEntry.business_id == business.id,
            LedgerEntry.account_name.in_(cash_accounts),
            LedgerEntry.entry_date >= s_date,
            LedgerEntry.entry_date <= e_date,
        )
        .order_by(LedgerEntry.entry_date.asc(), LedgerEntry.created_at.asc())
        .all()
    )

    total_inflow = Decimal("0.00")
    total_outflow = Decimal("0.00")
    entry_reads: List[LedgerEntryRead] = []

    for entry in entries:
        deb = Decimal(str(entry.debit))
        cred = Decimal(str(entry.credit))
        total_inflow += deb
        total_outflow += cred

        e_read = LedgerEntryRead.model_validate(entry)
        if entry.party:
            e_read.party_name = entry.party.name
        entry_reads.append(e_read)

    closing_cash = opening_cash + total_inflow - total_outflow

    return CashbookReport(
        start_date=s_date,
        end_date=e_date,
        opening_cash=opening_cash,
        total_inflow=total_inflow,
        total_outflow=total_outflow,
        closing_cash=closing_cash,
        entries=entry_reads,
    )


@router.get("/vat-summary", response_model=VatSummaryResponse, summary="Input vs Output VAT statement")
def get_vat_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> VatSummaryResponse:
    """Calculate total Output VAT from sales invoices vs Input VAT from purchase bills."""
    s_query = db.query(func.coalesce(func.sum(Invoice.tax_amount), Decimal("0.00"))).filter(
        Invoice.business_id == business.id,
        Invoice.invoice_type == "sales",
        Invoice.status.in_(["approved", "partially_paid", "paid"]),
    )
    p_query = db.query(func.coalesce(func.sum(Invoice.tax_amount), Decimal("0.00"))).filter(
        Invoice.business_id == business.id,
        Invoice.invoice_type == "purchase",
        Invoice.status.in_(["approved", "partially_paid", "paid"]),
    )

    if start_date:
        s_query = s_query.filter(Invoice.issue_date >= start_date)
        p_query = p_query.filter(Invoice.issue_date >= start_date)
    if end_date:
        s_query = s_query.filter(Invoice.issue_date <= end_date)
        p_query = p_query.filter(Invoice.issue_date <= end_date)

    output_vat = Decimal(str(s_query.scalar()))
    input_vat = Decimal(str(p_query.scalar()))

    return VatSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        output_vat_collected=output_vat,
        input_vat_paid=input_vat,
        net_vat_payable=output_vat - input_vat,
    )


@router.get("/dashboard-summary", response_model=DashboardSummary, summary="Dashboard KPI metrics")
def get_dashboard_summary(
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    """Consolidated KPI counters for Executive Dashboard."""
    # Receivables
    rec = db.query(func.coalesce(func.sum(Invoice.due_amount), Decimal("0.00"))).filter(
        Invoice.business_id == business.id,
        Invoice.invoice_type == "sales",
        Invoice.status.in_(["approved", "partially_paid"]),
    ).scalar()

    # Payables
    pay = db.query(func.coalesce(func.sum(Invoice.due_amount), Decimal("0.00"))).filter(
        Invoice.business_id == business.id,
        Invoice.invoice_type == "purchase",
        Invoice.status.in_(["approved", "partially_paid"]),
    ).scalar()

    # Cash in hand
    cash_debits = db.query(func.coalesce(func.sum(LedgerEntry.debit), Decimal("0.00"))).filter(
        LedgerEntry.business_id == business.id, LedgerEntry.account_name == "cash_in_hand"
    ).scalar()
    cash_credits = db.query(func.coalesce(func.sum(LedgerEntry.credit), Decimal("0.00"))).filter(
        LedgerEntry.business_id == business.id, LedgerEntry.account_name == "cash_in_hand"
    ).scalar()
    cash_bal = Decimal(str(cash_debits)) - Decimal(str(cash_credits))

    # Bank balance
    bank_debits = db.query(func.coalesce(func.sum(LedgerEntry.debit), Decimal("0.00"))).filter(
        LedgerEntry.business_id == business.id, LedgerEntry.account_name == "bank"
    ).scalar()
    bank_credits = db.query(func.coalesce(func.sum(LedgerEntry.credit), Decimal("0.00"))).filter(
        LedgerEntry.business_id == business.id, LedgerEntry.account_name == "bank"
    ).scalar()
    bank_bal = Decimal(str(bank_debits)) - Decimal(str(bank_credits))

    # Pending docs count
    pending_docs = db.query(Document).filter(
        Document.business_id == business.id,
        Document.status.in_(["uploaded", "processing", "needs_review"]),
    ).count()

    return DashboardSummary(
        total_receivable=Decimal(str(rec)),
        total_payable=Decimal(str(pay)),
        cash_in_hand=cash_bal,
        bank_balance=bank_bal,
        pending_documents_count=pending_docs,
    )
