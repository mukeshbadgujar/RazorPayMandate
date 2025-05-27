from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MandateStatusEnum(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CONFIRMED = "confirmed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatusEnum(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class TransactionTypeEnum(str, Enum):
    AUTHORIZATION = "authorization"
    RECURRING_PAYMENT = "recurring_payment"
    REFUND = "refund"


# Base Response Schema
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[Any, Any]] = None
    errors: Optional[Dict[str, Any]] = None


# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    contact: Optional[str] = None
    gstin: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact: Optional[str] = None
    gstin: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    razorpay_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Mandate Schemas
class MandateBase(BaseModel):
    amount: Decimal
    currency: str = "INR"
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    notes: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class MandateCreate(MandateBase):
    customer_id: int


class MandateUpdate(BaseModel):
    amount: Optional[Decimal] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[MandateStatusEnum] = None
    notes: Optional[str] = None


class MandateResponse(MandateBase):
    id: int
    razorpay_mandate_id: Optional[str] = None
    customer_id: int
    status: MandateStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentBase(BaseModel):
    amount: Decimal
    currency: str = "INR"
    description: Optional[str] = None
    receipt: Optional[str] = None
    notes: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class PaymentCreate(PaymentBase):
    customer_id: int
    mandate_id: Optional[int] = None
    transaction_type: TransactionTypeEnum = TransactionTypeEnum.RECURRING_PAYMENT


class PaymentResponse(PaymentBase):
    id: int
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    customer_id: int
    mandate_id: Optional[int] = None
    status: PaymentStatusEnum
    transaction_type: TransactionTypeEnum
    fee: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Order Schemas
class OrderCreate(BaseModel):
    amount: Decimal
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[str] = None
    customer_id: Optional[int] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class OrderResponse(BaseModel):
    id: int
    razorpay_order_id: Optional[str] = None
    customer_id: Optional[int] = None
    amount: Decimal
    currency: str
    receipt: Optional[str] = None
    status: Optional[str] = None
    attempts: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Webhook Schemas
class WebhookEventCreate(BaseModel):
    event_id: str
    event_type: str
    payload: str


class WebhookEventResponse(BaseModel):
    id: int
    event_id: str
    event_type: str
    processed: bool
    processing_error: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# eMandate specific schemas
class EMandateAuthorizationRequest(BaseModel):
    customer_id: int
    amount: Decimal
    frequency: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None


class EMandateRecurringPaymentRequest(BaseModel):
    mandate_id: int
    amount: Decimal
    description: Optional[str] = None
    receipt: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None


class RazorpayWebhookPayload(BaseModel):
    event: str
    account_id: str
    entity: Dict[str, Any]
    contains: list
    created_at: int
