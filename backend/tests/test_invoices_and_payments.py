import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"inv_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Invoice Test Biz {suffix}", "slug": f"inv-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_create_and_list_invoices():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create a buyer party
    p_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"গ্রাহক হাসান ট্রেডার্স {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    assert p_res.status_code == 201
    party_id = p_res.json()["id"]

    # 2. Create a sales invoice
    inv_data = {
        "party_id": party_id,
        "invoice_type": "sales",
        "invoice_number": f"INV-TEST-{suffix}",
        "issue_date": "2026-04-20",
        "due_date": "2026-05-04",
        "subtotal": "30000.00",
        "tax_amount": "2250.00",
        "total_amount": "32250.00",
        "notes": "Test sales invoice notes",
        "items": [
            {"description": "Item 1 A4 Paper", "quantity": 10, "unit_price": 2000, "line_total": 20000, "tax_rate": 7.5},
            {"description": "Item 2 Binders", "quantity": 50, "unit_price": 200, "line_total": 10000, "tax_rate": 7.5},
        ],
    }
    create_res = client.post("/api/v1/invoices/", headers=headers, json=inv_data)
    assert create_res.status_code == 201
    inv = create_res.json()
    assert inv["invoice_number"] == f"INV-TEST-{suffix}"
    assert inv["party_name"] == f"গ্রাহক হাসান ট্রেডার্স {suffix}"
    assert inv["total_amount"] == "32250.00"
    assert inv["due_amount"] == "32250.00"
    assert inv["status"] == "approved"
    assert len(inv["items"]) == 2

    # 3. List invoices with filtering
    list_res = client.get("/api/v1/invoices/?invoice_type=sales", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 1
    assert items[0]["invoice_number"] == f"INV-TEST-{suffix}"

    # Search filter
    search_res = client.get(f"/api/v1/invoices/?search=INV-TEST-{suffix}", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()["items"]) == 1


def test_payment_recording_and_invoice_allocation():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create a buyer party
    p_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"সততা এন্টারপ্রাইজ {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    party_id = p_res.json()["id"]

    # 2. Create Invoice of 50,000 BDT
    inv_res = client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": party_id,
            "invoice_type": "sales",
            "invoice_number": f"INV-ALLOC-{suffix}",
            "issue_date": "2026-04-20",
            "subtotal": "50000.00",
            "tax_amount": "0.00",
            "total_amount": "50000.00",
        },
    )
    assert inv_res.status_code == 201
    invoice_id = inv_res.json()["id"]

    # 3. Record Customer Receipt of 30,000 BDT via bKash
    pay_res = client.post(
        "/api/v1/payments/",
        headers=headers,
        json={
            "party_id": party_id,
            "payment_type": "customer_receipt",
            "payment_method": "bkash",
            "payment_date": "2026-04-21",
            "amount": "30000.00",
            "reference_number": f"BK-TRX-{suffix}",
            "notes": "Advance customer payment received",
        },
    )
    assert pay_res.status_code == 201
    pay = pay_res.json()
    payment_id = pay["id"]
    assert pay["amount"] == "30000.00"
    assert pay["unapplied_amount"] == "30000.00"
    assert pay["allocated_amount"] == "0.00"

    # 4. Allocate 30,000 to the invoice
    alloc_res = client.post(
        f"/api/v1/payments/{payment_id}/allocate",
        headers=headers,
        json={
            "allocations": [
                {"invoice_id": invoice_id, "allocated_amount": "30000.00"}
            ]
        },
    )
    assert alloc_res.status_code == 200
    updated_pay = alloc_res.json()
    assert updated_pay["unapplied_amount"] == "0.00"
    assert updated_pay["allocated_amount"] == "30000.00"

    # 5. Verify Invoice state: paid_amount = 30000, due_amount = 20000, status = partially_paid
    inv_check = client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert inv_check.status_code == 200
    inv_data = inv_check.json()
    assert inv_data["paid_amount"] == "30000.00"
    assert inv_data["due_amount"] == "20000.00"
    assert inv_data["status"] == "partially_paid"


def test_over_allocation_prevention():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    p_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"করিম স্টোর {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    party_id = p_res.json()["id"]

    inv_res = client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={"party_id": party_id, "invoice_type": "sales", "invoice_number": f"INV-OVER-{suffix}", "issue_date": "2026-04-20", "total_amount": "5000.00"},
    )
    invoice_id = inv_res.json()["id"]

    pay_res = client.post(
        "/api/v1/payments/",
        headers=headers,
        json={"party_id": party_id, "payment_type": "customer_receipt", "payment_date": "2026-04-21", "amount": "10000.00"},
    )
    payment_id = pay_res.json()["id"]

    # Attempting to allocate 6,000 BDT to an invoice whose due is only 5,000 must fail with 400
    res = client.post(
        f"/api/v1/payments/{payment_id}/allocate",
        headers=headers,
        json={"allocations": [{"invoice_id": invoice_id, "allocated_amount": "6000.00"}]},
    )
    assert res.status_code == 400
    assert "exceeds" in res.json()["detail"]


def test_invoice_reversal():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    p_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"রিভার্সাল টেস্ট পার্টি {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    party_id = p_res.json()["id"]

    inv_res = client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={"party_id": party_id, "invoice_type": "sales", "invoice_number": f"INV-REV-{suffix}", "issue_date": "2026-04-20", "total_amount": "12000.00"},
    )
    invoice_id = inv_res.json()["id"]

    # Reverse invoice
    rev_res = client.post(f"/api/v1/invoices/{invoice_id}/reverse", headers=headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "reversed"

    # Reversing again should fail with 409
    dup_rev = client.post(f"/api/v1/invoices/{invoice_id}/reverse", headers=headers)
    assert dup_rev.status_code == 409
