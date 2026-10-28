from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    currency: str = Field("BDT", min_length=3, max_length=10)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class BusinessCreate(BusinessBase):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class BusinessRead(BusinessBase):
    id: UUID
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessMembershipRead(BaseModel):
    id: UUID
    business_id: UUID
    user_id: UUID
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessMemberCreate(BaseModel):
    email: str
    role: str = Field(..., pattern=r"^(owner|accountant|reviewer|viewer)$")


class BusinessMemberWithUserRead(BaseModel):
    id: UUID
    business_id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

