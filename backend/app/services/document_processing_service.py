import os
import uuid
import pymupdf
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentPage, DocumentExtraction
from app.services.storage_service import storage_service
from app.document_processing.pdf_text import extract_pdf_native_text
from app.document_processing.providers.factory import get_ocr_provider
from app.document_processing.providers.base import OCRConfigurationError, OCRError
from app.document_processing.extraction.rule_extractor import extract_deterministic_fields
from app.document_processing.extraction.gemini_extractor import extract_with_gemini, is_gemini_configured


class DocumentProcessingService:
    def process_document(self, document_id: uuid.UUID, business_id: uuid.UUID, db: Session) -> Document:
        """Process document: attempt native PDF text extraction first; fall back to OCR for scans/images."""
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.business_id == business_id)
            .first()
        )
        if not doc:
            raise ValueError(f"Document {document_id} not found for business {business_id}")

        doc.status = "processing"
        db.commit()

        try:
            secure_path = storage_service.get_secure_path(business_id, doc.stored_path)
            with open(secure_path, "rb") as f:
                content = f.read()

            ext = os.path.splitext(doc.original_filename)[1].lower().lstrip(".")
            provider = get_ocr_provider()

            # Clean existing pages if re-processing
            db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()

            if ext == "pdf":
                pdf_res = extract_pdf_native_text(content)
                if pdf_res.has_native_text:
                    # Native text extraction succeeded!
                    for p in pdf_res.pages:
                        page_record = DocumentPage(
                            document_id=doc.id,
                            page_number=p.page_number,
                            width=p.width,
                            height=p.height,
                            has_native_text=True,
                            raw_text=p.raw_text,
                            ocr_data={
                                "provider": "native_pdf",
                                "confidence": 1.0,
                                "blocks": [
                                    {"bbox": [b.x0, b.y0, b.x1, b.y1], "text": b.text}
                                    for b in p.blocks
                                ],
                            },
                        )
                        db.add(page_record)
                else:
                    # Scanned PDF: render pages to images and run OCR
                    pdf_doc = pymupdf.open(stream=content, filetype="pdf")
                    for page_idx in range(len(pdf_doc)):
                        pdf_page = pdf_doc[page_idx]
                        rect = pdf_page.rect
                        pix = pdf_page.get_pixmap()
                        page_png = pix.tobytes("png")

                        ocr_res = provider.extract_text_from_pdf_page(page_png)
                        page_record = DocumentPage(
                            document_id=doc.id,
                            page_number=page_idx + 1,
                            width=int(rect.width),
                            height=int(rect.height),
                            has_native_text=False,
                            raw_text=ocr_res.full_text,
                            ocr_data={
                                "provider": ocr_res.provider_name,
                                "confidence": ocr_res.confidence,
                                "blocks": [
                                    {"bbox": list(b.bounding_box), "text": b.text, "confidence": b.confidence}
                                    for b in ocr_res.blocks
                                ],
                            },
                        )
                        db.add(page_record)
                    pdf_doc.close()
            else:
                # Image file: run OCR directly
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(content))
                img_width, img_height = img.size

                ocr_res = provider.extract_text_from_image(content)
                page_record = DocumentPage(
                    document_id=doc.id,
                    page_number=1,
                    width=img_width,
                    height=img_height,
                    has_native_text=False,
                    raw_text=ocr_res.full_text,
                    ocr_data={
                        "provider": ocr_res.provider_name,
                        "confidence": ocr_res.confidence,
                        "blocks": [
                            {"bbox": list(b.bounding_box), "text": b.text, "confidence": b.confidence}
                            for b in ocr_res.blocks
                        ],
                    },
                )
                db.add(page_record)

            # Run deterministic rule extractor on combined page text
            db.flush()
            all_pages = (
                db.query(DocumentPage)
                .filter(DocumentPage.document_id == doc.id)
                .order_by(DocumentPage.page_number.asc())
                .all()
            )
            combined_text = "\n".join(p.raw_text or "" for p in all_pages)
            
            # 1. Attempt Google Gemini Multimodal Vision extraction if configured
            cand = None
            if is_gemini_configured():
                cand = extract_with_gemini(content, doc.mime_type, business_id, db)
            
            # 2. Seamlessly fall back to deterministic rule extractor
            if not cand:
                cand = extract_deterministic_fields(combined_text, business_id, db)

            # Persist candidate fields in DocumentExtraction
            extraction = (
                db.query(DocumentExtraction)
                .filter(DocumentExtraction.document_id == doc.id)
                .first()
            )
            if not extraction:
                extraction = DocumentExtraction(document_id=doc.id)
                db.add(extraction)

            extraction.document_type_candidate = cand["document_type_candidate"]
            extraction.party_name_candidate = cand["party_name_candidate"]
            extraction.matched_party_id = cand["matched_party_id"]
            extraction.document_number_candidate = cand["document_number_candidate"]
            extraction.issue_date_candidate = cand["issue_date_candidate"]
            extraction.due_date_candidate = cand["due_date_candidate"]
            extraction.subtotal_candidate = cand["subtotal_candidate"]
            extraction.tax_amount_candidate = cand["tax_amount_candidate"]
            extraction.total_amount_candidate = cand["total_amount_candidate"]
            extraction.paid_amount_candidate = cand["paid_amount_candidate"]
            extraction.due_amount_candidate = cand["due_amount_candidate"]
            extraction.confidence_score = cand["confidence_score"]
            extraction.warnings = cand["warnings"]
            extraction.extraction_metadata = cand["metadata"]

            if doc.document_type == "unknown" and cand["document_type_candidate"] != "unknown":
                doc.document_type = cand["document_type_candidate"]

            doc.status = "needs_review"
            db.commit()
            db.refresh(doc)
            return doc

        except OCRConfigurationError as e:
            doc.status = "uploaded"
            doc.rejection_reason = f"OCR Configuration Warning: {str(e)}"
            db.commit()
            raise
        except Exception as e:
            doc.status = "uploaded"
            doc.rejection_reason = f"Processing failed: {str(e)}"
            db.commit()
            raise


document_processing_service = DocumentProcessingService()
