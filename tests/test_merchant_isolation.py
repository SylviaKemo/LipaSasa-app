from app.models.payment import Payment

PAYMENT = {
    "amount": 500,
    "phone_number": "0712345678",
    "reference": "ORDER-1043",
}


def create_payment(client, headers, key="key-1", body=PAYMENT):
    response = client.post(
        "/api/v1/payments",
        json=body,
        headers={**headers, "Idempotency-Key": key},
    )
    assert response.status_code == 201
    return response.json()


def test_merchant_can_read_own_payment(client, auth_headers):
    mama_mboga = auth_headers()
    payment = create_payment(client, mama_mboga)

    response = client.get(f"/api/v1/payments/{payment['id']}", headers=mama_mboga)

    assert response.status_code == 200
    assert response.json()["id"] == payment["id"]


def test_merchant_cannot_read_another_merchants_payment(client, auth_headers):
    mama_mboga = auth_headers()
    school = auth_headers(email="school@example.com", merchant_name="Sunrise School")
    payment = create_payment(client, mama_mboga)

    response = client.get(f"/api/v1/payments/{payment['id']}", headers=school)

    assert response.status_code == 404


def test_same_idempotency_key_is_separate_per_merchant(client, auth_headers):
    mama_mboga = auth_headers()
    school = auth_headers(email="school@example.com", merchant_name="Sunrise School")

    first = create_payment(client, mama_mboga, key="order-2001")
    second = create_payment(client, school, key="order-2001")

    assert first["id"] != second["id"]


def test_merchant_id_in_body_is_ignored(client, auth_headers, db):
    mama_mboga = auth_headers()
    school = auth_headers(email="school@example.com", merchant_name="Sunrise School")
    school_merchant_id = client.get("/api/v1/auth/me", headers=school).json()["merchant_id"]
    mama_mboga_merchant_id = client.get("/api/v1/auth/me", headers=mama_mboga).json()["merchant_id"]

    payment = create_payment(
        client,
        mama_mboga,
        body={**PAYMENT, "merchant_id": school_merchant_id},
    )

    saved = db.get(Payment, payment["id"])
    assert str(saved.merchant_id) == mama_mboga_merchant_id


def test_unknown_payment_id_returns_404(client, auth_headers):
    response = client.get(
        "/api/v1/payments/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(),
    )
    assert response.status_code == 404