import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"pdf_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"PDF Test Biz {suffix}", "slug": f"pdf-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_invoice_and_payment_pdf_generation():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create Buyer Party
    buyer_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"মেসার্স করিম ট্রেডার্স {suffix}", "party_type": "buyer", "phone": "01711000000"},
    )
    buyer_id = buyer_res.json()["id"]

    # 2. Create Sales Invoice
    inv_res = client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": buyer_id,
            "invoice_type": "sales",
            "invoice_number": f"INV-PDF-{suffix}",
            "issue_date": "2026-04-20",
            "due_date": "2026-05-05",
            "subtotal": "50000.00",
            "tax_amount": "3750.00",
            "total_amount": "53750.00",
            "notes": "Premium Printing Paper Procurement",
            "items": [
                {
                    "description": "Offset Printing Paper Reels",
                    "quantity": 10,
                    "unit_price": 5000,
                    "tax_rate": 0.075,
                }
            ],
        },
    )
    inv_id = inv_res.json()["id"]

    # 3. Test GET Invoice PDF
    pdf_res = client.get(f"/api/v1/invoices/{inv_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
    assert len(pdf_res.content) > 1000  # Valid full-size PDF

    # 4. Create Payment (Receipt)
    pay_res = client.post(
        "/api/v1/payments/",
        headers=headers,
        json={
            "party_id": buyer_id,
            "payment_type": "customer_receipt",
            "payment_method": "bkash",
            "payment_date": "2026-04-21",
            "amount": "25000.00",
            "reference_number": "TRX-BKASH-98213",
            "notes": "Partial payment receipt for goods",
        },
    )
    pay_id = pay_res.json()["id"]

    # 5. Test GET Payment Receipt PDF
    pay_pdf_res = client.get(f"/api/v1/payments/{pay_id}/pdf", headers=headers)
    assert pay_pdf_res.status_code == 200
    assert pay_pdf_res.headers["content-type"] == "application/pdf"
    assert pay_pdf_res.content.startswith(b"%PDF")
    assert len(pay_pdf_res.content) > 1000

    # 6. Test 404 for non-existent IDs
    fake_id = str(uuid.uuid4())
    assert client.get(f"/api/v1/invoices/{fake_id}/pdf", headers=headers).status_code == 404
    assert client.get(f"/api/v1/payments/{fake_id}/pdf", headers=headers).status_code == 404
