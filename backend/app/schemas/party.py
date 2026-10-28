from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class PartyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    party_type: Literal["buyer", "supplier", "both"]
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None


class PartyCreate(PartyBase):
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    opening_balance_type: Literal["receivable", "payable"] = "receivable"


class PartyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    party_type: Optional[Literal["buyer", "supplier", "both"]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: Optional[bool] = None


class PartyRead(PartyBase):
    id: UUID
    business_id: UUID
    opening_balance: Decimal
    opening_balance_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PartyBalanceRead(BaseModel):
    party_id: UUID
    party_name: str
    party_type: str
    opening_balance: Decimal
    opening_balance_type: str
    total_invoiced: Decimal
    total_paid: Decimal
    current_balance: Decimal
    balance_type: Literal["receivable", "payable", "zero"]
