import uuid
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.invoice import Invoice
    from app.models.payment import Payment


class Party(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parties"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    party_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'buyer', 'supplier', 'both'
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    opening_balance_type: Mapped[str] = mapped_column(String(20), default="receivable", nullable=False)  # 'receivable', 'payable'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="parties")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="party")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="party")
