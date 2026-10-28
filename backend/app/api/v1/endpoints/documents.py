import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.document import Document, DocumentPage, DocumentExtraction
from app.schemas.document import (
    DocumentRead,
    DocumentPageRead,
    DocumentExtractionRead,
    DocumentExtractionUpdate,
    DocumentApprovalRequest,
    DocumentPostingResponse,
    DocumentRejectionRequest,
)
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_active_business, require_business_role
from app.services.storage_service import storage_service
from app.services.document_processing_service import document_processing_service
from app.services.posting_service import posting_service

router = APIRouter()


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED, summary="Upload a new document (PDF, PNG, JPG, WebP)")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("unknown"),
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """Upload a business document, compute SHA256, validate page count, and save privately."""
    # 1. Validate file extension
    ext = storage_service.validate_file(file)

    # 2. Read bytes and compute hash
    content = await file.read()
    file_hash, size_bytes, page_count = storage_service.compute_hash_and_inspect(content, ext)

    # 3. Check duplicate within active business workspace
    duplicate = (
        db.query(Document)
        .filter(
            Document.business_id == business.id,
            Document.file_hash_sha256 == file_hash,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document: this file was already uploaded as '{duplicate.original_filename}' (Document ID: {duplicate.id})",
        )

    # 4. Save file to private storage
    stored_path, _ = storage_service.save_file(business.id, content, ext)

    # 5. Persist Document record
    doc_type_val = document_type if document_type in ["sales_invoice", "purchase_invoice", "payment_receipt", "voucher"] else "unknown"
    doc = Document(
        business_id=business.id,
        uploaded_by_user_id=current_user.id,
        original_filename=file.filename or f"uploaded_document.{ext}",
        stored_path=stored_path,
        file_hash_sha256=file_hash,
        mime_type=file.content_type or f"application/{ext}",
        file_size_bytes=size_bytes,
        page_count=page_count,
        document_type=doc_type_val,
        status="uploaded",
    )
    db.add(doc)
    db.flush()

    # Create initial DocumentExtraction container
    extraction = DocumentExtraction(
        document_id=doc.id,
        document_type_candidate=doc_type_val if doc_type_val != "unknown" else None,
        is_human_corrected=False,
    )
    db.add(extraction)
    db.commit()
    db.refresh(doc)

    return doc


@router.get("/", response_model=PaginatedResponse[DocumentRead], summary="List and filter documents in inbox")
def list_documents(
    doc_status: Optional[str] = Query(None, alias="status", description="Filter by status: uploaded, processing, needs_review, approved, rejected, posted"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DocumentRead]:
    """Retrieve documents for the active business inbox with optional status/type filtering."""
    query = (
        db.query(Document)
        .options(joinedload(Document.extraction))
        .filter(Document.business_id == business.id)
    )

    if doc_status:
        query = query.filter(Document.status == doc_status)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{document_id}", response_model=DocumentRead, summary="Get document details")
def get_document(
    document_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Document:
    """Retrieve document metadata, pages, and extraction details."""
    doc = (
        db.query(Document)
        .options(joinedload(Document.pages), joinedload(Document.extraction))
        .filter(Document.id == document_id, Document.business_id == business.id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this business workspace",
        )
    return doc


@router.get("/{document_id}/download", summary="Download or view private document file")
def download_document(
    document_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Securely stream/download the private document file. Authorized only to members of this business."""
    doc = db.query(Document).filter(Document.id == document_id, Document.business_id == business.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this business workspace",
        )

    secure_filepath = storage_service.get_secure_path(business.id, doc.stored_path)
    return FileResponse(
        path=secure_filepath,
        media_type=doc.mime_type,
        filename=doc.original_filename,
    )


@router.post("/{document_id}/reject", response_model=DocumentRead, summary="Reject a document")
def reject_document(
    document_id: uuid.UUID,
    rejection: DocumentRejectionRequest,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Document:
    """Reject a document with an explicit reason."""
    doc = db.query(Document).filter(Document.id == document_id, Document.business_id == business.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this business workspace",
        )

    if doc.status == "posted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject an already posted document. Create an accounting reversal instead.",
        )

    doc.status = "rejected"
    doc.rejection_reason = rejection.reason.strip()
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{document_id}/process", response_model=DocumentRead, summary="Trigger document text/OCR extraction")
def process_document(
    document_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> Document:
    """Extract embedded PDF text or run configured OCR provider on scanned pages/images."""
    try:
        doc = document_processing_service.process_document(document_id, business.id, db)
        return doc
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{document_id}/pages", response_model=List[DocumentPageRead], summary="Get extracted pages with text and blocks")
def get_document_pages(
    document_id: uuid.UUID,
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> List[DocumentPage]:
    """Retrieve all extracted pages, OCR text, and block coordinates for a document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.business_id == business.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this business workspace",
        )

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == doc.id)
        .order_by(DocumentPage.page_number.asc())
        .all()
    )
    return pages


@router.put("/{document_id}/extraction", response_model=DocumentExtractionRead, summary="Human correction of extracted candidate fields")
def update_document_extraction(
    document_id: uuid.UUID,
    update_in: DocumentExtractionUpdate,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentExtraction:
    """Manually correct or confirm candidate extraction values for review."""
    doc = db.query(Document).filter(Document.id == document_id, Document.business_id == business.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this business workspace",
        )

    extraction = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == doc.id).first()
    if not extraction:
        extraction = DocumentExtraction(document_id=doc.id)
        db.add(extraction)

    update_dict = update_in.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(extraction, field, val)

    extraction.is_human_corrected = True
    extraction.corrected_by_user_id = current_user.id
    db.commit()
    db.refresh(extraction)
    return extraction


@router.post(
    "/{document_id}/post",
    response_model=DocumentPostingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Approve document and post transactions to accounting ledger",
)
def post_document(
    document_id: uuid.UUID,
    approval: DocumentApprovalRequest,
    business: Business = Depends(get_active_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentPostingResponse:
    """Approve document and atomically record invoices, payments, and double-entry ledger entries."""
    return posting_service.post_document(
        document_id=document_id,
        business_id=business.id,
        user_id=current_user.id,
        approval=approval,
        db=db,
    )



