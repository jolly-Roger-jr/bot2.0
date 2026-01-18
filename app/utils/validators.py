# app/utils/validators.py
from pydantic import BaseModel, validator


class OrderData(BaseModel):
    address: str
    phone: str

    @validator('address')
    def validate_address(cls, v):
        if len(v) < 10:
            raise ValueError('Адрес слишком короткий')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError('Телефон должен содержать цифры')
        return v