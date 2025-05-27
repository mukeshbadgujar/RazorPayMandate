from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from app.models.models import Customer, Mandate, Payment, Order, WebhookEvent
from app.schemas.schemas import (
    CustomerCreate, CustomerUpdate, MandateCreate, MandateUpdate,
    PaymentCreate, OrderCreate, WebhookEventCreate
)
from app.services.razorpay_service import get_razorpay_client
from app.core.logging import get_logger
from decimal import Decimal

logger = get_logger(__name__)


class CustomerService:
    """Service for customer operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.razorpay_client = get_razorpay_client()
    
    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Create a new customer"""
        try:
            # Create customer in Razorpay
            razorpay_customer_data = {
                "name": customer_data.name,
                "email": customer_data.email,
                "contact": customer_data.contact,
                "gstin": customer_data.gstin,
                "notes": {}
            }
            
            razorpay_customer = self.razorpay_client.create_customer(razorpay_customer_data)
            
            # Create customer in database
            db_customer = Customer(
                razorpay_customer_id=razorpay_customer.get("id"),
                name=customer_data.name,
                email=customer_data.email,
                contact=customer_data.contact,
                gstin=customer_data.gstin
            )
            
            self.db.add(db_customer)
            self.db.commit()
            self.db.refresh(db_customer)
            
            logger.info("Customer created successfully", customer_id=db_customer.id)
            return db_customer
            
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Customer with this email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create customer", error=str(e))
            raise
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return self.db.query(Customer).filter(Customer.email == email).first()
    
    def update_customer(self, customer_id: int, customer_data: CustomerUpdate) -> Optional[Customer]:
        """Update customer"""
        customer = self.get_customer(customer_id)
        if not customer:
            return None
        
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def list_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """List customers with pagination"""
        return self.db.query(Customer).offset(skip).limit(limit).all()


class MandateService:
    """Service for mandate operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.razorpay_client = get_razorpay_client()
    
    def create_mandate(self, mandate_data: MandateCreate) -> Mandate:
        """Create a new mandate"""
        try:
            # Verify customer exists
            customer = self.db.query(Customer).filter(Customer.id == mandate_data.customer_id).first()
            if not customer:
                raise ValueError("Customer not found")
            
            # Create mandate in database
            db_mandate = Mandate(
                customer_id=mandate_data.customer_id,
                amount=mandate_data.amount,
                currency=mandate_data.currency,
                frequency=mandate_data.frequency,
                start_date=mandate_data.start_date,
                end_date=mandate_data.end_date,
                bank_account=mandate_data.bank_account,
                ifsc_code=mandate_data.ifsc_code,
                account_holder_name=mandate_data.account_holder_name,
                notes=mandate_data.notes
            )
            
            self.db.add(db_mandate)
            self.db.commit()
            self.db.refresh(db_mandate)
            
            logger.info("Mandate created successfully", mandate_id=db_mandate.id)
            return db_mandate
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create mandate", error=str(e))
            raise
    
    def get_mandate(self, mandate_id: int) -> Optional[Mandate]:
        """Get mandate by ID"""
        return self.db.query(Mandate).filter(Mandate.id == mandate_id).first()
    
    def update_mandate(self, mandate_id: int, mandate_data: MandateUpdate) -> Optional[Mandate]:
        """Update mandate"""
        mandate = self.get_mandate(mandate_id)
        if not mandate:
            return None
        
        update_data = mandate_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mandate, field, value)
        
        self.db.commit()
        self.db.refresh(mandate)
        return mandate
    
    def list_customer_mandates(self, customer_id: int) -> List[Mandate]:
        """List mandates for a customer"""
        return self.db.query(Mandate).filter(Mandate.customer_id == customer_id).all()


class PaymentService:
    """Service for payment operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.razorpay_client = get_razorpay_client()
    
    def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order"""
        try:
            # Create order in Razorpay
            razorpay_order_data = {
                "amount": int(order_data.amount * 100),  # Convert to paise
                "currency": order_data.currency,
                "receipt": order_data.receipt,
                "notes": order_data.notes or {}
            }
            
            razorpay_order = self.razorpay_client.create_order(razorpay_order_data)
            
            # Create order in database
            db_order = Order(
                razorpay_order_id=razorpay_order.get("id"),
                customer_id=order_data.customer_id,
                amount=order_data.amount,
                currency=order_data.currency,
                receipt=order_data.receipt,
                status=razorpay_order.get("status"),
                notes=order_data.notes
            )
            
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)
            
            logger.info("Order created successfully", order_id=db_order.id)
            return db_order
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create order", error=str(e))
            raise
    
    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment record"""
        try:
            db_payment = Payment(
                customer_id=payment_data.customer_id,
                mandate_id=payment_data.mandate_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                transaction_type=payment_data.transaction_type,
                description=payment_data.description,
                receipt=payment_data.receipt,
                notes=payment_data.notes
            )
            
            self.db.add(db_payment)
            self.db.commit()
            self.db.refresh(db_payment)
            
            logger.info("Payment created successfully", payment_id=db_payment.id)
            return db_payment
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create payment", error=str(e))
            raise
    
    def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def list_customer_payments(self, customer_id: int) -> List[Payment]:
        """List payments for a customer"""
        return self.db.query(Payment).filter(Payment.customer_id == customer_id).all()


class WebhookService:
    """Service for webhook operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_webhook_event(self, webhook_data: WebhookEventCreate) -> WebhookEvent:
        """Create a new webhook event"""
        try:
            db_webhook = WebhookEvent(
                event_id=webhook_data.event_id,
                event_type=webhook_data.event_type,
                payload=webhook_data.payload
            )
            
            self.db.add(db_webhook)
            self.db.commit()
            self.db.refresh(db_webhook)
            
            logger.info("Webhook event created", event_id=webhook_data.event_id)
            return db_webhook
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create webhook event", error=str(e))
            raise
    
    def mark_webhook_processed(self, webhook_id: int, error: Optional[str] = None) -> bool:
        """Mark webhook as processed"""
        webhook = self.db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        if webhook:
            webhook.processed = True
            webhook.processing_error = error
            self.db.commit()
            return True
        return False
