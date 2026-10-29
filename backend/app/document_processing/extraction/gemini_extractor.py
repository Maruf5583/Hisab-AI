import os
import json
import base64
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
import httpx
import pymupdf
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.party import Party
from app.document_processing.normalization import (
    normalize_bengali_digits,
    parse_monetary_amount,
    parse_flexible_date,
)
from app.document_processing.extraction.party_matcher import match_party_name

logger = logging.getLogger(__name__)


def is_gemini_configured() -> bool:
    """Return True if GEMINI_API_KEY is configured."""
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())


def extract_with_gemini(
    content: bytes,
    mime_type: str,
    business_id: uuid.UUID,
    db: Session,
) -> Optional[Dict[str, Any]]:
    """Extract accounting fields from document using Google Gemini Multimodal Vision API.
    
    Returns structured dictionary matching DocumentExtraction schema, or None if Gemini
    is not configured or encounters an error (enabling transparent rule-based fallback).
    """
    if not is_gemini_configured():
        logger.info("Gemini API key is not configured; skipping Gemini extraction.")
        return None

    try:
        # Prepare image bytes for Gemini
        img_bytes = content
        gemini_mime = mime_type

        if mime_type == "application/pdf" or mime_type.endswith("/pdf"):
            try:
                pdf_doc = pymupdf.open(stream=content, filetype="pdf")
                if len(pdf_doc) > 0:
                    page = pdf_doc[0]
                    # Render high-resolution pixmap (150 DPI)
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("jpeg")
                    gemini_mime = "image/jpeg"
                pdf_doc.close()
            except Exception as e:
                logger.warning(f"Failed to render PDF to image for Gemini: {e}")
                gemini_mime = "application/pdf"

        # Encode image to base64
        b64_data = base64.b64encode(img_bytes).decode("utf-8")

        # Gather known parties for this business to assist AI recognition
        parties = db.query(Party).filter(Party.business_id == business_id).all()
        known_parties = [{"id": str(p.id), "name": p.name, "type": p.party_type} for p in parties]
        known_parties_json = json.dumps(known_parties, ensure_ascii=False)

        prompt = f"""You are the expert accounting AI document processor for HisabAI (Hisab Management System).
Analyze this invoice, bill, cash memo, receipt, or expense voucher.
The document may be in Bengali, English, or mixed bilingual, printed or handwritten.

Known registered parties for this business:
{known_parties_json}

Extract the accounting fields with extreme precision and return ONLY a JSON object:
1. document_type: "sales_invoice" (বিক্রয় চালান/ক্যাশ মেমো), "purchase_invoice" (ক্রয় চালান/বিল), "payment_receipt" (টাকা জমার রশিদ/মানি রিসিট), or "voucher" (খরচ ভাউচার).
2. document_number: invoice/chalan/memo/voucher number string or null.
3. issue_date: "YYYY-MM-DD" or null. Convert Bengali digits (০-৯) and Bengali month names if present.
4. due_date: "YYYY-MM-DD" or null.
5. party_name: Name of the customer, supplier, or store. If it matches one of the known parties, use that name.
6. matched_party_id: UUID string of the matched known party if identified, otherwise null.
7. subtotal: Total amount before tax as decimal string (e.g. "12500.00").
8. tax_amount: Total VAT/Tax as decimal string (e.g. "0.00").
9. total_amount: Grand total invoice amount as decimal string (e.g. "12500.00").
10. paid_amount: Advance or paid amount on this document (e.g. "0.00").
11. due_amount: Remaining due amount (e.g. "12500.00").
12. line_items: Array of objects with description, quantity, unit_price, line_total.
13. confidence_score: Confidence estimate as number between 0.0 and 1.0.
14. warnings: Array of strings if any text is ambiguous or handwritten text is partially faded.
"""

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY.strip()}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": gemini_mime,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, json=payload)
            if resp.status_code != 200:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None

            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                logger.warning("Gemini returned empty candidates.")
                return None

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text_content:
                return None

            data = json.loads(text_content)

        # Normalize and validate extracted fields
        doc_type = data.get("document_type") or "unknown"
        if doc_type not in ["sales_invoice", "purchase_invoice", "payment_receipt", "voucher"]:
            doc_type = "unknown"

        raw_party_name = data.get("party_name")
        matched_party_id = None
        if data.get("matched_party_id"):
            try:
                matched_party_id = uuid.UUID(data["matched_party_id"])
            except Exception:
                matched_party_id = None

        if not matched_party_id and raw_party_name:
            match = match_party_name(raw_party_name, business_id, db)
            if match:
                matched_party_id = match.party_id
                raw_party_name = match.party_name

        # Parse amounts
        subtotal = parse_monetary_amount(str(data.get("subtotal") or "0.00")) or Decimal("0.00")
        tax_amount = parse_monetary_amount(str(data.get("tax_amount") or "0.00")) or Decimal("0.00")
        total_amount = parse_monetary_amount(str(data.get("total_amount") or "0.00")) or Decimal("0.00")
        paid_amount = parse_monetary_amount(str(data.get("paid_amount") or "0.00")) or Decimal("0.00")
        due_amount = parse_monetary_amount(str(data.get("due_amount") or "0.00")) or (total_amount - paid_amount)

        # Parse dates
        issue_date = None
        if data.get("issue_date"):
            issue_date = parse_flexible_date(str(data["issue_date"]))

        due_date = None
        if data.get("due_date"):
            due_date = parse_flexible_date(str(data["due_date"]))

        confidence = Decimal(str(data.get("confidence_score", "0.9500")))
        if confidence > Decimal("1.0000"):
            confidence = Decimal("1.0000")

        warnings = data.get("warnings") or []
        if not isinstance(warnings, list):
            warnings = [str(warnings)]

        line_items = data.get("line_items") or []

        return {
            "document_type_candidate": doc_type,
            "party_name_candidate": raw_party_name,
            "matched_party_id": matched_party_id,
            "document_number_candidate": data.get("document_number"),
            "issue_date_candidate": issue_date,
            "due_date_candidate": due_date,
            "subtotal_candidate": subtotal,
            "tax_amount_candidate": tax_amount,
            "total_amount_candidate": total_amount,
            "paid_amount_candidate": paid_amount,
            "due_amount_candidate": due_amount,
            "confidence_score": confidence,
            "warnings": warnings,
            "metadata": {
                "engine": "google_gemini",
                "model": settings.GEMINI_MODEL,
                "line_items": line_items,
            },
        }

    except Exception as e:
        logger.warning(f"Error during Gemini document extraction: {e}")
        return None
