import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.party import Party
from app.document_processing.normalization import (
    normalize_bengali_digits,
    to_bengali_digits,
    parse_monetary_amount,
    parse_flexible_date,
)
from app.document_processing.extraction.party_matcher import match_party_name
from app.document_processing.extraction.rule_extractor import extract_deterministic_fields

client = TestClient(app)


def test_bengali_digit_normalization():
    assert normalize_bengali_digits("১২৩৪৫৬৭৮৯০") == "1234567890"
    assert to_bengali_digits("1234567890") == "১২৩৪৫৬৭৮৯০"
    assert normalize_bengali_digits("চালান নং ১২৩") == "চালান নং 123"


def test_monetary_amount_parsing():
    assert parse_monetary_amount("১৫,৫০০.০০") == Decimal("15500.00")
    assert parse_monetary_amount("৳ ১,২০,০০০/-") == Decimal("120000.00")
    assert parse_monetary_amount("12,500.50 Tk") == Decimal("12500.50")
    assert parse_monetary_amount("৫০ টাকা") == Decimal("50.00")
    assert parse_monetary_amount("Total: $450.25") == Decimal("450.25")
    assert parse_monetary_amount("invalid string") is None


def test_flexible_date_parsing():
    assert parse_flexible_date("২৮/১০/২০২৬") == date(2026, 10, 28)
    assert parse_flexible_date("28-10-2026") == date(2026, 10, 28)
    assert parse_flexible_date("2026-10-28") == date(2026, 10, 28)
    assert parse_flexible_date("তারিখ: ১৫/০৩/২০২৫") == date(2025, 3, 15)
    assert parse_flexible_date("no date here") is None


def test_fuzzy_party_matching():
    with SessionLocal() as db:
        suffix = uuid.uuid4().hex[:8]
        # Create a business
        from app.models.business import Business
        biz = Business(name=f"Fuzzy Biz {suffix}", slug=f"fuzzy-biz-{suffix}")
        db.add(biz)
        db.flush()

        # Create party
        party = Party(
            business_id=biz.id,
            name="মেসার্স রহিম ট্রেডার্স",
            party_type="buyer",
        )
        db.add(party)
        db.commit()

        # Match close variation
        matched_id, name, score = match_party_name("রহিম ট্রেডার্স", biz.id, db)
        assert matched_id == party.id
        assert score >= 75.0

        # Non-matching candidate
        unmatched_id, _, score_low = match_party_name("সম্পূর্ণ ভিন্ন কোম্পানি", biz.id, db)
        assert unmatched_id is None
        assert score_low < 75.0

        # Cleanup
        db.delete(biz)
        db.commit()


def test_deterministic_extraction_rules():
    raw_text = """
    মেসার্স আল-মদিনা এন্টারপ্রাইজ
    বিক্রয় চালান
    চালান নং: INV-2026-88
    তারিখ: ২৮/১০/২০২৬
    ক্রেতার নাম: মেসার্স রহিম ট্রেডার্স
    উপমোট: ১২,০০০.০০
    ভ্যাট: ১,০০০.০০
    সর্বমোট টাকা: ১৩,০০০.০০
    নগদ পরিশোধ: ৮,০০০.০০
    বাকি টাকা: ৫,০০০.০০
    """
    with SessionLocal() as db:
        dummy_biz_id = uuid.uuid4()
        res = extract_deterministic_fields(raw_text, dummy_biz_id, db)

        assert res["document_type_candidate"] == "sales_invoice"
        assert res["document_number_candidate"] == "INV-2026-88"
        assert res["issue_date_candidate"] == date(2026, 10, 28)
        assert res["subtotal_candidate"] == Decimal("12000.00")
        assert res["tax_amount_candidate"] == Decimal("1000.00")
        assert res["total_amount_candidate"] == Decimal("13000.00")
        assert res["paid_amount_candidate"] == Decimal("8000.00")
        assert res["due_amount_candidate"] == Decimal("5000.00")
        assert res["confidence_score"] == Decimal("1.00")


def test_end_to_end_extraction_and_human_correction():
    suffix = uuid.uuid4().hex[:8]
    # Register & setup business
    email = f"extract_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Extraction Biz {suffix}", "slug": f"ext-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id

    # Create synthetic image and upload
    from PIL import Image
    import io
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("voucher.png", buf.getvalue(), "image/png")},
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    # Trigger processing (runs MockOCRProvider which outputs simulated Bengali receipt text)
    proc_res = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_res.status_code == 200
    doc_data = proc_res.json()
    assert doc_data["status"] == "needs_review"

    # Inspect DocumentExtraction
    doc_detail = client.get(f"/api/v1/documents/{doc_id}", headers=headers).json()
    ext = doc_detail["extraction"]
    assert ext is not None
    assert ext["total_amount_candidate"] == "15500.00"
    assert ext["paid_amount_candidate"] == "5500.00"
    assert ext["due_amount_candidate"] == "10000.00"
    assert ext["is_human_corrected"] is False

    # Human Correction via PUT /extraction
    correction_payload = {
        "document_type_candidate": "sales_invoice",
        "document_number_candidate": "INV-CORRECTED-99",
        "total_amount_candidate": "16000.00",
        "paid_amount_candidate": "6000.00",
        "due_amount_candidate": "10000.00",
    }
    put_res = client.put(f"/api/v1/documents/{doc_id}/extraction", json=correction_payload, headers=headers)
    assert put_res.status_code == 200
    updated_ext = put_res.json()
    assert updated_ext["document_number_candidate"] == "INV-CORRECTED-99"
    assert updated_ext["total_amount_candidate"] == "16000.00"
    assert updated_ext["is_human_corrected"] is True
