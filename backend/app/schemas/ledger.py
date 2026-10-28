from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class LedgerEntryRead(BaseModel):
    id: UUID
    business_id: UUID
    transaction_type: str
    reference_id: UUID
    entry_date: date
    account_name: str
    debit: Decimal
    credit: Decimal
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None
    description: Optional[str] = None
    is_reversal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrialBalanceAccountSummary(BaseModel):
    account_name: str
    total_debit: Decimal
    total_credit: Decimal
    net_balance: Decimal


class TrialBalanceResponse(BaseModel):
    as_of_date: date
    accounts: List[TrialBalanceAccountSummary]
    grand_total_debit: Decimal
    grand_total_credit: Decimal
    is_balanced: bool
    difference: Decimal


class AgingBucket(BaseModel):
    amount: Decimal
    invoice_count: int


class PartyAgingDetail(BaseModel):
    party_id: UUID
    party_name: str
    phone: Optional[str] = None
    bucket_0_15: Decimal
    bucket_16_30: Decimal
    bucket_31_60: Decimal
    bucket_60_plus: Decimal
    total_due: Decimal


class AgingReportResponse(BaseModel):
    report_type: str  # 'receivables' or 'payables'
    as_of_date: date
    total_due: Decimal
    summary_0_15: AgingBucket
    summary_16_30: AgingBucket
    summary_31_60: AgingBucket
    summary_60_plus: AgingBucket
    party_details: List[PartyAgingDetail]


class VatSummaryResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    output_vat_collected: Decimal
    input_vat_paid: Decimal
    net_vat_payable: Decimal


class ReceivablesReportItem(BaseModel):
    party_id: UUID
    party_name: str
    phone: Optional[str] = None
    opening_receivable: Decimal
    total_sales: Decimal
    total_received: Decimal
    current_receivable: Decimal


class PayablesReportItem(BaseModel):
    party_id: UUID
    party_name: str
    phone: Optional[str] = None
    opening_payable: Decimal
    total_purchases: Decimal
    total_paid: Decimal
    current_payable: Decimal


class CashbookReport(BaseModel):
    start_date: date
    end_date: date
    opening_cash: Decimal
    total_inflow: Decimal
    total_outflow: Decimal
    closing_cash: Decimal
    entries: List[LedgerEntryRead]


class DashboardSummary(BaseModel):
    total_receivable: Decimal
    total_payable: Decimal
    cash_in_hand: Decimal
    bank_balance: Decimal
    pending_documents_count: int
