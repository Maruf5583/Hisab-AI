import io
import uuid
from decimal import Decimal
import pytest
import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.invoice import Invoice
from app.models.ledger import LedgerEntry
from app.models.party import Party

client = TestClient(app)


def create_synthetic_pdf(text: str = "চালান নং ১২৩৪৫\nমেসার্স সততা এন্টারপ্রাইজ") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def setup_user_and_business(suffix: str):
    email = f"post_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"Post User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Posting Test Business {suffix}", "slug": f"posting-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_post_sales_invoice_and_ledger_equilibrium():
    suffix = uuid.uuid4().hex[:8]
    headers, biz_id = setup_user_and_business(suffix)

    # 1. Create a customer party via API
    party_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={
            "name": f"কাস্টমার করিম স্টোর {suffix}",
            "party_type": "buyer",
            "phone": "01711223344",
            "opening_balance": "0.00",
            "opening_balance_type": "receivable",
        },
    )
    assert party_res.status_code == 201
    party_id = party_res.json()["id"]

    # 2. Upload a test sales document
    file_bytes = create_synthetic_pdf(f"Sales Invoice #{suffix}")
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("sales_inv_101.pdf", io.BytesIO(file_bytes), "application/pdf")},
        data={"document_type": "sales_invoice"},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 3. Post document
    post_payload = {
        "document_type": "sales_invoice",
        "party_id": party_id,
        "document_number": f"INV-{suffix}",
        "issue_date": "2026-04-20",
        "due_date": "2026-05-04",
        "subtotal": "50000.00",
        "tax_amount": "3750.00",
        "total_amount": "53750.00",
        "paid_amount": "20000.00",
        "notes": "Delivered in full to showroom",
    }
    post_res = client.post(
        f"/api/v1/documents/{doc_id}/post",
        headers=headers,
        json=post_payload,
    )
    assert post_res.status_code == 201, post_res.text
    data = post_res.json()

    assert data["success"] is True
    assert data["document_status"] == "posted"
    assert data["invoice_id"] is not None
    assert data["payment_id"] is not None
    assert Decimal(str(data["total_posted_debit"])) == Decimal(str(data["total_posted_credit"]))
    assert Decimal(str(data["total_posted_debit"])) == Decimal("73750.00")  # 53750 (inv) + 20000 (payment)

    # 4. Verify in Database
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
        assert doc.status == "posted"

        inv = db.query(Invoice).filter(Invoice.id == uuid.UUID(data["invoice_id"])).first()
        assert inv.invoice_number == f"INV-{suffix}"
        assert inv.total_amount == Decimal("53750.00")
        assert inv.paid_amount == Decimal("20000.00")
        assert inv.due_amount == Decimal("33750.00")
        assert inv.status == "partially_paid"

        entries = db.query(LedgerEntry).filter(LedgerEntry.business_id == uuid.UUID(biz_id)).all()
        inv_entries = [e for e in entries if str(e.reference_id) in [data["invoice_id"], data["payment_id"]]]
        assert len(inv_entries) == 4

        total_debit = sum(e.debit for e in inv_entries)
        total_credit = sum(e.credit for e in inv_entries)
        assert total_debit == total_credit
    finally:
        db.close()


def test_idempotent_duplicate_posting_prevention():
    suffix = uuid.uuid4().hex[:8]
    headers, biz_id = setup_user_and_business(suffix)

    party_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={
            "name": f"মেসার্স সততা হার্ডওয়্যার {suffix}",
            "party_type": "buyer",
            "phone": "01811998877",
            "opening_balance": "0.00",
            "opening_balance_type": "receivable",
        },
    )
    party_id = party_res.json()["id"]

    file_bytes = create_synthetic_pdf(f"Duplicate check {suffix}")
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("dup_check.pdf", io.BytesIO(file_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    post_payload = {
        "document_type": "sales_invoice",
        "party_id": party_id,
        "document_number": f"INV-DUP-{suffix}",
        "issue_date": "2026-04-21",
        "subtotal": "10000.00",
        "tax_amount": "0.00",
        "total_amount": "10000.00",
        "paid_amount": "0.00",
    }

    # First post succeeds
    res1 = client.post(f"/api/v1/documents/{doc_id}/post", headers=headers, json=post_payload)
    assert res1.status_code == 201

    # Second post MUST be rejected with HTTP 409 Conflict
    res2 = client.post(f"/api/v1/documents/{doc_id}/post", headers=headers, json=post_payload)
    assert res2.status_code == 409
    assert "already been approved and posted" in res2.json()["detail"]


def test_mathematical_inconsistency_rejection():
    suffix = uuid.uuid4().hex[:8]
    headers, biz_id = setup_user_and_business(suffix)

    party_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={
            "name": f"রহিম ব্রাদার্স {suffix}",
            "party_type": "buyer",
            "opening_balance": "0.00",
            "opening_balance_type": "receivable",
        },
    )
    party_id = party_res.json()["id"]

    file_bytes = create_synthetic_pdf(f"Math check {suffix}")
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("math_test.pdf", io.BytesIO(file_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # Subtotal (100) + Tax (20) != Total (150) -> must be rejected
    bad_payload = {
        "document_type": "sales_invoice",
        "party_id": party_id,
        "document_number": f"INV-ERR-{suffix}",
        "issue_date": "2026-04-21",
        "subtotal": "100.00",
        "tax_amount": "20.00",
        "total_amount": "150.00",
        "paid_amount": "0.00",
    }
    res = client.post(f"/api/v1/documents/{doc_id}/post", headers=headers, json=bad_payload)
    assert res.status_code == 422
    assert "Mathematical inconsistency" in res.json()["detail"]
