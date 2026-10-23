from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.auth import RegisterRequest

class EmailAlreadyRegisteredError(Exception):
    pass

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))

def register_merchant(db: Session, data: RegisterRequest) -> User:
    email = data.email.lower()

    user_exists = get_user_by_email(db, email)
    merchant_exists = db.scalar(select(Merchant).where(Merchant.email == email))
    if user_exists or merchant_exists:
        raise EmailAlreadyRegisteredError

    merchant = Merchant(name=data.merchant_name, email=email)
    db.add(merchant)
    db.flush()

    user = User(
        merchant_id=merchant.id,
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user