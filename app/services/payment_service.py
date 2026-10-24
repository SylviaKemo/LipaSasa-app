import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_event import PaymentEvent
from app.schemas.payment import CreatePaymentRequest

class IdempotencyKeyReusedError(Exception):
    pass

def get_payment_by_idempotency_key(
    db: Session, merchant_id: uuid.UUID, idempotency_key: str
) -> Payment | None:
    return db.scalar(
        select(Payment).where(
            Payment.merchant_id == merchant_id,
            Payment.idempotency_key == idempotency_key,
        )
    )


def _is_same_request(payment: Payment, data: CreatePaymentRequest) -> bool:
    return (
        payment.amount == data.amount
        and payment.phone_number == data.phone_number
        and payment.reference == data.reference
        and payment.description == data.description
    )


def _replay(payment: Payment, data: CreatePaymentRequest) -> tuple[Payment, bool]:
    if not _is_same_request(payment, data):
        raise IdempotencyKeyReusedError()
    return payment, False

def create_payment(
    db: Session, merchant_id: uuid.UUID, data: CreatePaymentRequest,  idempotency_key: str,  
)  -> tuple[Payment, bool]:   

    existing = get_payment_by_idempotency_key(db, merchant_id, idempotency_key)
    if existing is not None:
        return _replay(existing, data)
    
    payment = Payment(
        merchant_id=merchant_id,
        amount=data.amount,
        phone_number=data.phone_number,
        reference=data.reference,
        description=data.description,
        idempotency_key=idempotency_key,
    )
    db.add(payment)


    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = get_payment_by_idempotency_key(db, merchant_id, idempotency_key)
        if existing is None:
            raise
        return _replay(existing, data)

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
    return payment, True    


def get_payment(
    db: Session, merchant_id: uuid.UUID, payment_id: uuid.UUID
) -> Payment | None:
    return db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.merchant_id == merchant_id,
        )
    )