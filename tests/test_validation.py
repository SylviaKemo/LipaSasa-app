import pytest

VALID_PAYMENT = {
    "amount": 500,
    "phone_number": "0712345678",
    "reference": "ORDER-1",
}


def test_register_rejects_bad_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "merchant_name": "Mama Mboga's Shop",
            "full_name": "Sly",
            "email": "not-an-email",
            "password": "sukuma123",
        },
    )
    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "merchant_name": "Mama Mboga's Shop",
            "full_name": "Sly",
            "email": "sly@example.com",
            "password": "123",
        },
    )
    assert response.status_code == 422


def test_login_rejects_wrong_password(client, auth_headers):
    auth_headers()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "sly@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_create_payment_requires_token(client):
    response = client.post(
        "/api/v1/payments",
        json=VALID_PAYMENT,
        headers={"Idempotency-Key": "key-1"},
    )
    assert response.status_code == 401


def test_create_payment_rejects_fake_token(client):
    response = client.post(
        "/api/v1/payments",
        json=VALID_PAYMENT,
        headers={"Authorization": "Bearer abc123", "Idempotency-Key": "key-1"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("amount", [0, -50, 250_001])
def test_create_payment_rejects_bad_amount(client, auth_headers, amount):
    headers = auth_headers()
    headers["Idempotency-Key"] = "key-1"
    response = client.post(
        "/api/v1/payments",
        json={**VALID_PAYMENT, "amount": amount},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.parametrize("phone", ["12345", "0812345678", "abcdefghij", ""])
def test_create_payment_rejects_bad_phone(client, auth_headers, phone):
    headers = auth_headers()
    headers["Idempotency-Key"] = "key-1"
    response = client.post(
        "/api/v1/payments",
        json={**VALID_PAYMENT, "phone_number": phone},
        headers=headers,
    )
    assert response.status_code == 422


def test_create_payment_requires_idempotency_key(client, auth_headers):
    response = client.post(
        "/api/v1/payments",
        json=VALID_PAYMENT,
        headers=auth_headers(),
    )
    assert response.status_code == 422


def test_create_payment_normalises_phone(client, auth_headers):
    headers = auth_headers()
    headers["Idempotency-Key"] = "key-1"
    response = client.post(
        "/api/v1/payments",
        json={**VALID_PAYMENT, "phone_number": "+254 712-345-678"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["phone_number"] == "254712345678"
    assert response.json()["status"] == "pending"