import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

class CreatePaymentRequest(BaseModel):
        amount: int = Field(gt=0, le=250_000)
        phone_number: str
        reference: str = Field(min_length=1, max_length=100)
        description: str | None = Field(default=None, max_length=255)

        @field_validator("phone_number")
        @classmethod
        def normalise_phone_number(cls, value: str) -> str:
                 phone = re.sub(r"[\s\-]", "", value)

                 if phone.startswith("+"):
                         phone = phone[1:]
                 if phone.startswith("0"):
                         phone = "254" + phone[1:]

                 if not re.fullmatch(r"254[17]\d{8}", phone):
                     raise ValueError("Enter a valid Kenyan mobile number, e.g. 0712345678")
                 return phone


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: int
    currency: str
    phone_number: str
    reference: str
    description: str | None
    status: str
    created_at: datetime