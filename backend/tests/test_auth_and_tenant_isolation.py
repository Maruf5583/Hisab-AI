import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.business import Business, BusinessMembership

client = TestClient(app)


def test_auth_registration_and_login_flow():
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"test_{unique_suffix}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "রাকিব হাসান (Rakib Hasan)",
            "phone": "01700112233",
        },
    )
    assert reg_response.status_code == 201, reg_response.text
    user_data = reg_response.json()
    assert user_data["email"] == email
    assert user_data["full_name"] == "রাকিব হাসান (Rakib Hasan)"
    assert "password" not in user_data
    assert "hashed_password" not in user_data

    # 2. Reject duplicate email
    dup_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Duplicate User",
        },
    )
    assert dup_response.status_code == 409

    # 3. Login with wrong password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 4. Login with correct password
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 5. Get current user profile
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email

    # 6. Unauthenticated request rejected
    no_token_response = client.get("/api/v1/auth/me")
    assert no_token_response.status_code == 401


def test_cross_tenant_isolation_and_role_permissions():
    """Verify that tenant isolation strictly denies cross-business access."""
    # Create User A & User B
    s_a = uuid.uuid4().hex[:8]
    s_b = uuid.uuid4().hex[:8]

    # User A
    user_a_email = f"user_a_{s_a}@example.com"
    reg_a = client.post("/api/v1/auth/register", json={"email": user_a_email, "password": "PasswordA123!", "full_name": "User A"})
    assert reg_a.status_code == 201, reg_a.text
    token_a = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": "PasswordA123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    user_b_email = f"user_b_{s_b}@example.com"
    reg_b = client.post("/api/v1/auth/register", json={"email": user_b_email, "password": "PasswordB123!", "full_name": "User B"})
    assert reg_b.status_code == 201, reg_b.text
    token_b = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": "PasswordB123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Business A
    biz_a_res = client.post(
        "/api/v1/businesses/",
        json={
            "name": f"Business Alpha {s_a}",
            "slug": f"biz-alpha-{s_a}",
            "currency": "BDT",
        },
        headers=headers_a,
    )
    assert biz_a_res.status_code == 201
    biz_a_id = biz_a_res.json()["id"]

    # User B creates Business B
    biz_b_res = client.post(
        "/api/v1/businesses/",
        json={
            "name": f"Business Beta {s_b}",
            "slug": f"biz-beta-{s_b}",
            "currency": "BDT",
        },
        headers=headers_b,
    )
    assert biz_b_res.status_code == 201
    biz_b_id = biz_b_res.json()["id"]

    # --- CROSS-TENANT DENIAL TESTS ---
    # 1. User B attempts to access Business A
    cross_get = client.get(f"/api/v1/businesses/{biz_a_id}", headers=headers_b)
    assert cross_get.status_code == 403, "User B must not view Business A"
    assert "not a member" in cross_get.json()["detail"].lower()

    # 2. User B attempts to update Business A
    cross_put = client.put(
        f"/api/v1/businesses/{biz_a_id}",
        json={"name": "Hacked Business Name"},
        headers=headers_b,
    )
    assert cross_put.status_code == 403, "User B must not modify Business A"

    # 3. User B attempts to list Business A members
    cross_members = client.get(f"/api/v1/businesses/{biz_a_id}/members", headers=headers_b)
    assert cross_members.status_code == 403, "User B must not view Business A members"

    # --- ROLE-BASED ACCESS CONTROL TESTS ---
    # User A (Owner) invites User B to Business A as a 'viewer'
    invite_res = client.post(
        f"/api/v1/businesses/{biz_a_id}/members",
        json={"email": user_b_email, "role": "viewer"},
        headers=headers_a,
    )
    assert invite_res.status_code == 201
    assert invite_res.json()["role"] == "viewer"

    # Now User B CAN view Business A
    allowed_get = client.get(f"/api/v1/businesses/{biz_a_id}", headers=headers_b)
    assert allowed_get.status_code == 200
    assert allowed_get.json()["id"] == biz_a_id

    # BUT User B (as viewer) CANNOT update Business A (requires owner/accountant)
    viewer_put = client.put(
        f"/api/v1/businesses/{biz_a_id}",
        json={"name": "Viewer Try Update"},
        headers=headers_b,
    )
    assert viewer_put.status_code == 403
    assert "requires one of the following roles" in viewer_put.json()["detail"].lower()

    # AND User B (as viewer) CANNOT add other members (requires owner)
    viewer_invite = client.post(
        f"/api/v1/businesses/{biz_a_id}/members",
        json={"email": "someone@example.com", "role": "viewer"},
        headers=headers_b,
    )
    assert viewer_invite.status_code == 403
