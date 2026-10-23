import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_event import PaymentEvent
from app.schemas.payment import CreatePaymentRequest


def create_payment(
    db: Session, merchant_id: uuid.UUID, data: CreatePaymentRequest
) -> Payment:
    payment = Payment(
        merchant_id=merchant_id,
        amount=data.amount,
        phone_number=data.phone_number,
        reference=data.reference,
        description=data.description,
    )
    db.add(payment)
    db.flush()

    event = PaymentEvent(
        payment_id=payment.id,
        event_type="payment.created",
        data={
            "amount": payment.amount,
            "phone_number": payment.phone_number,
            "reference": payment.reference,
        },
    )
    db.add(event)

    db.commit()
    db.refresh(payment)
    return payment


def get_payment(
    db: Session, merchant_id: uuid.UUID, payment_id: uuid.UUID
) -> Payment | None:
    return db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.merchant_id == merchant_id,
        )
    )