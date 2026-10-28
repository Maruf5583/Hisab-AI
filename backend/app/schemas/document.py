from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class DocumentPageRead(BaseModel):
    id: UUID
    page_number: int
    width: Optional[int] = None
    height: Optional[int] = None
    has_native_text: bool
    raw_text: Optional[str] = None
    ocr_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentExtractionBase(BaseModel):
    document_type_candidate: Optional[str] = None
    party_name_candidate: Optional[str] = None
    matched_party_id: Optional[UUID] = None
    document_number_candidate: Optional[str] = None
    issue_date_candidate: Optional[date] = None
    due_date_candidate: Optional[date] = None
    subtotal_candidate: Optional[Decimal] = None
    tax_amount_candidate: Optional[Decimal] = None
    total_amount_candidate: Optional[Decimal] = None
    paid_amount_candidate: Optional[Decimal] = None
    due_amount_candidate: Optional[Decimal] = None


class DocumentExtractionUpdate(DocumentExtractionBase):
    pass


class DocumentExtractionRead(DocumentExtractionBase):
    id: UUID
    document_id: UUID
    confidence_score: Optional[Decimal] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[Any]] = None
    is_human_corrected: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    business_id: UUID
    uploaded_by_user_id: Optional[UUID] = None
    original_filename: str
    file_hash_sha256: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    document_type: str
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    pages: Optional[List[DocumentPageRead]] = None
    extraction: Optional[DocumentExtractionRead] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentApprovalRequest(BaseModel):
    document_type: Literal["sales_invoice", "purchase_invoice", "payment_receipt", "voucher"]
    party_id: UUID
    document_number: str = Field(..., min_length=1, max_length=100)
    issue_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., gt=0)
    paid_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class DocumentPostingResponse(BaseModel):
    success: bool = True
    document_id: UUID
    document_status: str
    invoice_id: Optional[UUID] = None
    payment_id: Optional[UUID] = None
    ledger_entry_ids: List[UUID] = []
    total_posted_debit: Decimal
    total_posted_credit: Decimal
    message: str


class DocumentRejectionRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)
