from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
from datetime import datetime


class MandateStatus(enum.Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CONFIRMED = "confirmed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(enum.Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class TransactionType(enum.Enum):
    AUTHORIZATION = "authorization"
    RECURRING_PAYMENT = "recurring_payment"
    REFUND = "refund"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_customer_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    contact = Column(String(20))
    gstin = Column(String(15))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mandates = relationship("Mandate", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_mandate_id = Column(String(255), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Max amount per transaction
    currency = Column(String(3), default="INR")
    status = Column(SQLEnum(MandateStatus), default=MandateStatus.CREATED)
    frequency = Column(String(50))  # monthly, quarterly, yearly, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    bank_account = Column(String(255))
    ifsc_code = Column(String(11))
    account_holder_name = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="mandates")
    payments = relationship("Payment", back_populates="mandate")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_payment_id = Column(String(255), unique=True, index=True)
    razorpay_order_id = Column(String(255), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    mandate_id = Column(Integer, ForeignKey("mandates.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.CREATED)
    transaction_type = Column(SQLEnum(TransactionType), default=TransactionType.RECURRING_PAYMENT)
    description = Column(Text)
    receipt = Column(String(255))
    notes = Column(Text)
    fee = Column(Numeric(10, 2))
    tax = Column(Numeric(10, 2))
    error_code = Column(String(100))
    error_description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    mandate = relationship("Mandate", back_populates="payments")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_order_id = Column(String(255), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    receipt = Column(String(255))
    status = Column(String(50))
    attempts = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), unique=True, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text)
    processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime)


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255))
    method = Column(String(10))
    request_data = Column(Text)
    response_data = Column(Text)
    status_code = Column(Integer)
    execution_time = Column(Numeric(10, 4))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
