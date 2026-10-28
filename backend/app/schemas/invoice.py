from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(default=Decimal("1.0000"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    id: UUID
    invoice_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    party_id: UUID
    invoice_type: Literal["sales", "purchase"]
    invoice_number: str = Field(..., min_length=1, max_length=100)
    issue_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    document_id: Optional[UUID] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceRead(InvoiceBase):
    id: UUID
    business_id: UUID
    document_id: Optional[UUID] = None
    paid_amount: Decimal
    due_amount: Decimal
    status: str
    approved_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: Optional[List[InvoiceItemRead]] = None

    model_config = ConfigDict(from_attributes=True)
