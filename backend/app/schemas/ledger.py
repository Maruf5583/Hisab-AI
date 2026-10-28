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
    description: Optional[str] = None
    is_reversal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
