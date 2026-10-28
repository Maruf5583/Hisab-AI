import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Boolean, Numeric, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.party import Party


class LedgerEntry(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ledger_entries"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'opening_balance', 'sales_invoice', 'purchase_invoice', 'customer_receipt', 'supplier_payment', 'reversal', 'adjustment'
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 'accounts_receivable', 'accounts_payable', 'cash_in_hand', 'bank', 'sales_revenue', 'purchase_expense'
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    party_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parties.id", ondelete="SET NULL"), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reversal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="ledger_entries")
    party: Mapped[Optional["Party"]] = relationship("Party")
