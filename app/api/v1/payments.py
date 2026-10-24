import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import CreatePaymentRequest, PaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: CreatePaymentRequest,
    response: Response,                                             
    idempotency_key: str = Header(min_length=1, max_length=255),  
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:                                                             
        payment, created = payment_service.create_payment(
            db, current_user.merchant_id, data, idempotency_key
        )
    except payment_service.IdempotencyKeyReusedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Idempotency-Key was already used with different payment details",
        )

    if not created:                                                 
        response.status_code = status.HTTP_200_OK

    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = payment_service.get_payment(db, current_user.merchant_id, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment