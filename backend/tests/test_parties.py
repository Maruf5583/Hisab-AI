import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"party_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Party Test Business {suffix}", "slug": f"party-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def test_create_party_with_bengali_and_opening_ledger():
    suffix = uuid.uuid4().hex[:8]
    headers, biz_id = setup_user_and_business(suffix)

    # 1. Create Buyer Party with Bengali Name and Opening Receivable
    party_data = {
        "name": "মেসার্স সততা এন্টারপ্রাইজ",
        "party_type": "buyer",
        "phone": "01712345678",
        "email": f"satata_{suffix}@example.com",
        "address": "কারওয়ান বাজার, ঢাকা",
        "opening_balance": "25000.75",
        "opening_balance_type": "receivable",
    }
    response = client.post("/api/v1/parties/", json=party_data, headers=headers)
    assert response.status_code == 201, response.text
    party = response.json()
    party_id = party["id"]
    assert party["name"] == "মেসার্স সততা এন্টারপ্রাইজ"
    assert party["opening_balance"] == "25000.75"
    assert party["opening_balance_type"] == "receivable"

    # 2. Reject duplicate party name
    dup_res = client.post("/api/v1/parties/", json=party_data, headers=headers)
    assert dup_res.status_code == 409

    # 3. Create Supplier Party with Opening Payable
    sup_data = {
        "name": "বিসমিল্লাহ পেপার সাপ্লায়ার্স",
        "party_type": "supplier",
        "phone": "01812345678",
        "opening_balance": "40000.00",
        "opening_balance_type": "payable",
    }
    sup_res = client.post("/api/v1/parties/", json=sup_data, headers=headers)
    assert sup_res.status_code == 201
    sup_id = sup_res.json()["id"]

    # 4. Check Reconciled Balance Endpoint
    bal_res = client.get(f"/api/v1/parties/{party_id}/balance", headers=headers)
    assert bal_res.status_code == 200
    bal_data = bal_res.json()
    assert bal_data["party_id"] == party_id
    assert bal_data["party_name"] == "মেসার্স সততা এন্টারপ্রাইজ"
    assert bal_data["opening_balance"] == "25000.75"
    assert bal_data["current_balance"] == "25000.75"
    assert bal_data["balance_type"] == "receivable"

    # 5. Check Ledger Entries Endpoint (Opening Balance must be recorded)
    ledger_res = client.get(f"/api/v1/parties/{party_id}/ledger", headers=headers)
    assert ledger_res.status_code == 200
    ledger_entries = ledger_res.json()
    assert len(ledger_entries) == 1
    entry = ledger_entries[0]
    assert entry["transaction_type"] == "opening_balance"
    assert entry["account_name"] == "accounts_receivable"
    assert entry["debit"] == "25000.75"
    assert entry["credit"] == "0.00"

    # Check Supplier Ledger Entry
    sup_ledger_res = client.get(f"/api/v1/parties/{sup_id}/ledger", headers=headers)
    assert sup_ledger_res.status_code == 200
    sup_entry = sup_ledger_res.json()[0]
    assert sup_entry["account_name"] == "accounts_payable"
    assert sup_entry["credit"] == "40000.00"
    assert sup_entry["debit"] == "0.00"


def test_party_listing_and_filtering():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # Add 2 buyers and 1 supplier
    client.post("/api/v1/parties/", json={"name": f"গ্রাহক এক {suffix}", "party_type": "buyer", "phone": "01711111111"}, headers=headers)
    client.post("/api/v1/parties/", json={"name": f"গ্রাহক দুই {suffix}", "party_type": "buyer", "phone": "01722222222"}, headers=headers)
    client.post("/api/v1/parties/", json={"name": f"সরবরাহকারী {suffix}", "party_type": "supplier", "phone": "01833333333"}, headers=headers)

    # 1. List all
    all_res = client.get("/api/v1/parties/", headers=headers)
    assert all_res.status_code == 200
    assert all_res.json()["total"] == 3

    # 2. Filter by party_type=buyer
    buyer_res = client.get("/api/v1/parties/?party_type=buyer", headers=headers)
    assert buyer_res.status_code == 200
    assert buyer_res.json()["total"] == 2

    # 3. Filter by party_type=supplier
    sup_res = client.get("/api/v1/parties/?party_type=supplier", headers=headers)
    assert sup_res.status_code == 200
    assert sup_res.json()["total"] == 1

    # 4. Search by Bengali text
    search_res = client.get(f"/api/v1/parties/?search=দুই", headers=headers)
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert "দুই" in search_res.json()["items"][0]["name"]


def test_party_cross_tenant_isolation():
    """Verify that Party data is strictly isolated between business workspaces."""
    s1 = uuid.uuid4().hex[:8]
    s2 = uuid.uuid4().hex[:8]

    headers_1, biz_1 = setup_user_and_business(s1)
    headers_2, biz_2 = setup_user_and_business(s2)

    # Create party in Business 1
    p1_res = client.post(
        "/api/v1/parties/",
        json={"name": f"Business 1 Party {s1}", "party_type": "buyer"},
        headers=headers_1,
    )
    p1_id = p1_res.json()["id"]

    # 1. User 2 cannot GET Business 1's party
    cross_get = client.get(f"/api/v1/parties/{p1_id}", headers=headers_2)
    assert cross_get.status_code == 404, "Cross-tenant access must return 404"

    # 2. User 2 cannot PUT Business 1's party
    cross_put = client.put(f"/api/v1/parties/{p1_id}", json={"name": "Hacked Party"}, headers=headers_2)
    assert cross_put.status_code == 404

    # 3. User 2 cannot query Business 1's party balance
    cross_bal = client.get(f"/api/v1/parties/{p1_id}/balance", headers=headers_2)
    assert cross_bal.status_code == 404

    # 4. Business 2 party list does NOT contain Business 1's party
    list_res = client.get("/api/v1/parties/", headers=headers_2)
    party_ids = [p["id"] for p in list_res.json()["items"]]
    assert p1_id not in party_ids
