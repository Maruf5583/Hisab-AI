from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field


class PaymentAllocationCreate(BaseModel):
    invoice_id: UUID
    allocated_amount: Decimal = Field(..., gt=0)


class PaymentAllocationRead(BaseModel):
    id: UUID
    payment_id: UUID
    invoice_id: UUID
    allocated_amount: Decimal
    allocation_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    party_id: UUID
    payment_type: Literal["customer_receipt", "supplier_payment"]
    payment_method: Literal["cash", "bank", "bkash", "nagad", "other"] = "cash"
    payment_date: date
    amount: Decimal = Field(..., gt=0)
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    document_id: Optional[UUID] = None
    allocations: Optional[List[PaymentAllocationCreate]] = None


class PaymentRead(PaymentBase):
    id: UUID
    business_id: UUID
    document_id: Optional[UUID] = None
    allocated_amount: Decimal
    unapplied_amount: Decimal
    status: str
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    allocations: Optional[List[PaymentAllocationRead]] = None

    model_config = ConfigDict(from_attributes=True)
