import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"rep_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Report Test Biz {suffix}", "slug": f"rep-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_ledger_listing_and_trial_balance_equilibrium():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create Buyer and Supplier
    buyer_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"ক্রেতা রহিম {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    buyer_id = buyer_res.json()["id"]

    # 2. Post Sales Invoice (50,000 BDT)
    client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": buyer_id,
            "invoice_type": "sales",
            "invoice_number": f"INV-LED-{suffix}",
            "issue_date": "2026-04-10",
            "total_amount": "50000.00",
        },
    )

    # 3. Post Receipt (20,000 BDT)
    client.post(
        "/api/v1/payments/",
        headers=headers,
        json={
            "party_id": buyer_id,
            "payment_type": "customer_receipt",
            "payment_method": "cash",
            "payment_date": "2026-04-12",
            "amount": "20000.00",
        },
    )

    # 4. Query Ledger
    ledger_res = client.get("/api/v1/ledger/", headers=headers)
    assert ledger_res.status_code == 200
    entries = ledger_res.json()["items"]
    assert len(entries) >= 4  # 2 for invoice (AR, Sales), 2 for receipt (Cash, AR)

    # 5. Query Trial Balance
    tb_res = client.get("/api/v1/ledger/trial-balance", headers=headers)
    assert tb_res.status_code == 200
    tb = tb_res.json()

    assert tb["is_balanced"] is True
    assert Decimal(str(tb["grand_total_debit"])) == Decimal(str(tb["grand_total_credit"]))
    assert Decimal(str(tb["difference"])) == Decimal("0.00")
    assert len(tb["accounts"]) >= 3


def test_aging_reports_and_cashbook():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Create Buyer Party
    b_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"আলম ট্রেডার্স {suffix}", "party_type": "buyer", "opening_balance": "0.00", "opening_balance_type": "receivable"},
    )
    buyer_id = b_res.json()["id"]

    # 2. Create Supplier Party
    s_res = client.post(
        "/api/v1/parties/",
        headers=headers,
        json={"name": f"সাপ্লায়ার করিম মিলস {suffix}", "party_type": "supplier", "opening_balance": "0.00", "opening_balance_type": "payable"},
    )
    supplier_id = s_res.json()["id"]

    # 3. Create Overdue Sales Invoice (15,000 BDT)
    client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": buyer_id,
            "invoice_type": "sales",
            "invoice_number": f"INV-AGE-{suffix}",
            "issue_date": "2026-04-01",
            "due_date": "2026-04-10",
            "total_amount": "15000.00",
        },
    )

    # 4. Create Purchase Bill (25,000 BDT)
    client.post(
        "/api/v1/invoices/",
        headers=headers,
        json={
            "party_id": supplier_id,
            "invoice_type": "purchase",
            "invoice_number": f"BILL-AGE-{suffix}",
            "issue_date": "2026-04-05",
            "due_date": "2026-04-15",
            "total_amount": "25000.00",
        },
    )

    # 5. Test Receivables Aging Report
    rec_res = client.get("/api/v1/reports/receivables-aging", headers=headers)
    assert rec_res.status_code == 200
    rec_aging = rec_res.json()
    assert rec_aging["report_type"] == "receivables"
    assert Decimal(str(rec_aging["total_due"])) >= Decimal("15000.00")
    assert len(rec_aging["party_details"]) >= 1

    # 6. Test Payables Aging Report
    pay_res = client.get("/api/v1/reports/payables-aging", headers=headers)
    assert pay_res.status_code == 200
    pay_aging = pay_res.json()
    assert pay_aging["report_type"] == "payables"
    assert Decimal(str(pay_aging["total_due"])) >= Decimal("25000.00")

    # 7. Test Cashbook Report
    cb_res = client.get("/api/v1/reports/cashbook", headers=headers)
    assert cb_res.status_code == 200
    cashbook = cb_res.json()
    assert "opening_cash" in cashbook
    assert "total_inflow" in cashbook
    assert "closing_cash" in cashbook

    # 8. Test Dashboard Summary
    dash_res = client.get("/api/v1/reports/dashboard-summary", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert Decimal(str(dash["total_receivable"])) >= Decimal("15000.00")
    assert Decimal(str(dash["total_payable"])) >= Decimal("25000.00")
