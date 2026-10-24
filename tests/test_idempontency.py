from sqlalchemy import func, select

from app.models.payment import Payment
from app.models.payment_event import PaymentEvent

PAYMENT = {
    "amount": 700,
    "phone_number": "0712345678",
    "reference": "ORDER-2001",
}


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_retry_returns_same_payment(client, auth_headers, db):
    headers = auth_headers()
    headers["Idempotency-Key"] = "order-2001"

    first = client.post("/api/v1/payments", json=PAYMENT, headers=headers)
    second = client.post("/api/v1/payments", json=PAYMENT, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    assert count(db, Payment) == 1
    assert count(db, PaymentEvent) == 1


def test_same_key_with_different_details_is_rejected(client, auth_headers, db):
    headers = auth_headers()
    headers["Idempotency-Key"] = "order-2001"

    client.post("/api/v1/payments", json=PAYMENT, headers=headers)
    response = client.post(
        "/api/v1/payments",
        json={**PAYMENT, "amount": 7000},
        headers=headers,
    )

    assert response.status_code == 409
    assert count(db, Payment) == 1


def test_different_keys_create_different_payments(client, auth_headers, db):
    headers = auth_headers()

    first = client.post(
        "/api/v1/payments",
        json=PAYMENT,
        headers={**headers, "Idempotency-Key": "key-1"},
    )
    second = client.post(
        "/api/v1/payments",
        json=PAYMENT,
        headers={**headers, "Idempotency-Key": "key-2"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert count(db, Payment) == 2


def test_register_same_email_twice_is_rejected(client, auth_headers):
    auth_headers()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "merchant_name": "Another Shop",
            "full_name": "Someone Else",
            "email": "SLY@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 409