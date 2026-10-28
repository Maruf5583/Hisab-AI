import uuid
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, Boolean, Text, Integer, BigInteger, Numeric, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.user import User
    from app.models.party import Party


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)  # 'sales_invoice', 'purchase_invoice', 'payment_receipt', 'voucher', 'unknown'
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)  # 'uploaded', 'processing', 'needs_review', 'approved', 'rejected', 'posted'
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    business: Mapped["Business"] = relationship("Business", back_populates="documents")
    uploader: Mapped[Optional["User"]] = relationship("User")
    pages: Mapped[List["DocumentPage"]] = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    extraction: Mapped[Optional["DocumentExtraction"]] = relationship("DocumentExtraction", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentPage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_page"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_native_text: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="pages")


class DocumentExtraction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_extractions"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    document_type_candidate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    party_name_candidate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matched_party_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parties.id", ondelete="SET NULL"), nullable=True)
    document_number_candidate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issue_date_candidate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date_candidate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    subtotal_candidate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    tax_amount_candidate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    total_amount_candidate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    paid_amount_candidate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    due_amount_candidate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    is_human_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corrected_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="extraction")
    matched_party: Mapped[Optional["Party"]] = relationship("Party")
    corrected_by: Mapped[Optional["User"]] = relationship("User")
