import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"audit_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Audit Test Biz {suffix}", "slug": f"audit-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_audit_logs_listing_and_filtering():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create a party
    party_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"Audit Party {suffix}", "party_type": "buyer"},
    )
    party_id = party_res.json()["id"]

    # 2. Create invoice (generates invoice_created audit log)
    inv_res = client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": party_id,
            "invoice_type": "sales",
            "invoice_number": f"INV-AUDIT-{suffix}",
            "issue_date": "2026-04-10",
            "total_amount": "20000.00",
        },
    )
    inv_id = inv_res.json()["id"]

    # 3. Reverse invoice (generates invoice_reversed audit log)
    client.post(f"/api/v1/invoices/{inv_id}/reverse", headers=headers)

    # 4. Check audit logs
    logs_res = client.get("/api/v1/audit-logs/", headers=headers)
    assert logs_res.status_code == 200
    data = logs_res.json()
    assert data["total"] >= 1
    assert any(log["action"] == "invoice_reversed" for log in data["items"])

    # 5. Filter by entity_type=invoice
    filtered_res = client.get("/api/v1/audit-logs/?entity_type=invoice", headers=headers)
    assert filtered_res.status_code == 200
    assert all(log["entity_type"] == "invoice" for log in filtered_res.json()["items"])


def test_invoices_and_payments_csv_exports():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create party
    p_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"Export Customer {suffix}", "party_type": "buyer"},
    )
    p_id = p_res.json()["id"]

    # 2. Create Invoice
    client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": p_id,
            "invoice_type": "sales",
            "invoice_number": f"EXP-INV-{suffix}",
            "issue_date": "2026-04-15",
            "total_amount": "75000.00",
        },
    )

    # 3. Create Payment
    client.post(
        "/api/v1/payments/",
        headers=headers,
        json={
            "party_id": p_id,
            "payment_type": "customer_receipt",
            "payment_method": "bank",
            "payment_date": "2026-04-16",
            "amount": "30000.00",
            "reference_number": f"REF-EXP-{suffix}",
        },
    )

    # 4. Test Invoices CSV Export
    inv_csv_res = client.get("/api/v1/invoices/export", headers=headers)
    assert inv_csv_res.status_code == 200
    assert "text/csv" in inv_csv_res.headers["content-type"]
    assert "invoices_export_" in inv_csv_res.headers["content-disposition"]
    csv_text = inv_csv_res.text
    assert "Invoice Number,Invoice Type,Party Name" in csv_text
    assert f"EXP-INV-{suffix}" in csv_text

    # 5. Test Payments CSV Export
    pay_csv_res = client.get("/api/v1/payments/export", headers=headers)
    assert pay_csv_res.status_code == 200
    assert "text/csv" in pay_csv_res.headers["content-type"]
    assert "payments_export_" in pay_csv_res.headers["content-disposition"]
    pay_csv_text = pay_csv_res.text
    assert "Voucher ID,Payment Date,Party Name" in pay_csv_text
    assert f"REF-EXP-{suffix}" in pay_csv_text
