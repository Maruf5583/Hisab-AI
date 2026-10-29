import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.document_processing.extraction.gemini_extractor import (
    is_gemini_configured,
    extract_with_gemini,
)
from app.core.database import SessionLocal
from app.models.business import Business
from app.models.party import Party

client = TestClient(app)


def test_gemini_configuration_detection():
    # 1. When key is empty, should report not configured
    with patch.object(settings, "GEMINI_API_KEY", ""):
        assert is_gemini_configured() is False
        db = SessionLocal()
        try:
            res = extract_with_gemini(b"dummy_content", "image/jpeg", uuid.uuid4(), db)
            assert res is None
        finally:
            db.close()

    # 2. When key is set
    with patch.object(settings, "GEMINI_API_KEY", "dummy_test_api_key_12345"):
        assert is_gemini_configured() is True


def test_gemini_extraction_success_parsing():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]
    try:
        # Create test business and party
        biz = Business(
            name=f"Gemini Test Biz {suffix}",
            slug=f"gem-biz-{suffix}",
            currency="BDT",
        )
        db.add(biz)
        db.flush()

        party = Party(
            business_id=biz.id,
            name=f"মেসার্স রহিম ট্রেডার্স {suffix}",
            party_type="supplier",
        )
        db.add(party)
        db.commit()

        mock_gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "document_type": "purchase_invoice",
                                        "document_number": f"MEMO-{suffix}",
                                        "issue_date": "2026-04-25",
                                        "due_date": "2026-05-10",
                                        "party_name": party.name,
                                        "matched_party_id": str(party.id),
                                        "subtotal": "45000.00",
                                        "tax_amount": "3000.00",
                                        "total_amount": "48000.00",
                                        "paid_amount": "10000.00",
                                        "due_amount": "38000.00",
                                        "confidence_score": 0.98,
                                        "warnings": ["Handwritten signature verified"],
                                        "line_items": [
                                            {
                                                "description": "Offset Printing Paper",
                                                "quantity": 10,
                                                "unit_price": 4500,
                                                "line_total": 45000,
                                            }
                                        ],
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = mock_gemini_response

        with patch.object(settings, "GEMINI_API_KEY", "test_gemini_key_xyz"):
            with patch("httpx.Client.post", return_value=mock_http_resp):
                extracted = extract_with_gemini(
                    b"dummy_image_bytes",
                    "image/jpeg",
                    biz.id,
                    db,
                )

                assert extracted is not None
                assert extracted["document_type_candidate"] == "purchase_invoice"
                assert extracted["document_number_candidate"] == f"MEMO-{suffix}"
                assert str(extracted["issue_date_candidate"]) == "2026-04-25"
                assert extracted["party_name_candidate"] == party.name
                assert extracted["matched_party_id"] == party.id
                assert extracted["total_amount_candidate"] == Decimal("48000.00")
                assert extracted["due_amount_candidate"] == Decimal("38000.00")
                assert extracted["metadata"]["engine"] == "google_gemini"
                assert len(extracted["metadata"]["line_items"]) == 1

    finally:
        db.close()


def test_gemini_http_error_graceful_fallback():
    db = SessionLocal()
    try:
        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 403
        mock_http_resp.text = "Forbidden - Invalid API Key"

        with patch.object(settings, "GEMINI_API_KEY", "invalid_key"):
            with patch("httpx.Client.post", return_value=mock_http_resp):
                # When Gemini fails or has invalid key, returns None without crashing
                extracted = extract_with_gemini(
                    b"dummy_bytes",
                    "image/jpeg",
                    uuid.uuid4(),
                    db,
                )
                assert extracted is None

    finally:
        db.close()
