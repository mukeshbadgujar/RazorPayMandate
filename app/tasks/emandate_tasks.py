from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.database_service import PaymentService, MandateService
from app.services.razorpay_service import get_razorpay_client
from app.core.logging import get_logger
from app.models.models import PaymentStatus, MandateStatus
from typing import Dict, Any
import json

logger = get_logger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_emandate_authorization(self, customer_id: int, mandate_id: int, order_data: Dict[str, Any]):
    """Process eMandate authorization transaction"""
    db = get_db_session()
    try:
        logger.info("Processing eMandate authorization", 
                   customer_id=customer_id, mandate_id=mandate_id)
        
        mandate_service = MandateService(db)
        payment_service = PaymentService(db)
        razorpay_client = get_razorpay_client()
        
        # Get mandate
        mandate = mandate_service.get_mandate(mandate_id)
        if not mandate:
            raise ValueError("Mandate not found")
        
        # Create order for authorization
        order = payment_service.create_order(order_data)
        
        # Update mandate status
        mandate.status = MandateStatus.AUTHORIZED
        mandate.razorpay_mandate_id = f"mandate_mock_{mandate_id}"
        db.commit()
        
        logger.info("eMandate authorization processed successfully",
                   mandate_id=mandate_id, order_id=order.id)
        
        return {
            "status": "success",
            "mandate_id": mandate_id,
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id
        }
        
    except Exception as e:
        logger.error("Failed to process eMandate authorization", 
                    error=str(e), mandate_id=mandate_id)
        
        # Retry the task
        raise self.retry(exc=e)
    
    finally:
        db.close()


@celery_app.task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_recurring_payment(self, mandate_id: int, payment_data: Dict[str, Any]):
    """Process recurring payment using eMandate"""
    db = get_db_session()
    try:
        logger.info("Processing recurring payment", mandate_id=mandate_id)
        
        mandate_service = MandateService(db)
        payment_service = PaymentService(db)
        razorpay_client = get_razorpay_client()
        
        # Get mandate
        mandate = mandate_service.get_mandate(mandate_id)
        if not mandate:
            raise ValueError("Mandate not found")
        
        if mandate.status != MandateStatus.CONFIRMED:
            raise ValueError("Mandate is not confirmed")
        
        # Create order for recurring payment
        order_data = {
            "amount": payment_data["amount"],
            "currency": payment_data.get("currency", "INR"),
            "receipt": payment_data.get("receipt"),
            "notes": payment_data.get("notes"),
            "customer_id": mandate.customer_id
        }
        
        order = payment_service.create_order(order_data)
        
        # Create payment record
        payment = payment_service.create_payment({
            "customer_id": mandate.customer_id,
            "mandate_id": mandate_id,
            "amount": payment_data["amount"],
            "currency": payment_data.get("currency", "INR"),
            "description": payment_data.get("description"),
            "receipt": payment_data.get("receipt"),
            "notes": payment_data.get("notes"),
            "transaction_type": "recurring_payment"
        })
        
        # Simulate payment processing (in real scenario, this would be handled by Razorpay)
        payment.razorpay_payment_id = f"pay_mock_{payment.id}"
        payment.razorpay_order_id = order.razorpay_order_id
        payment.status = PaymentStatus.CAPTURED
        db.commit()
        
        logger.info("Recurring payment processed successfully",
                   payment_id=payment.id, mandate_id=mandate_id)
        
        return {
            "status": "success",
            "payment_id": payment.id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "amount": float(payment.amount)
        }
        
    except Exception as e:
        logger.error("Failed to process recurring payment", 
                    error=str(e), mandate_id=mandate_id)
        
        # Retry the task
        raise self.retry(exc=e)
    
    finally:
        db.close()


@celery_app.task(bind=True)
def validate_mandate_status(self, mandate_id: int):
    """Validate and update mandate status"""
    db = get_db_session()
    try:
        logger.info("Validating mandate status", mandate_id=mandate_id)
        
        mandate_service = MandateService(db)
        razorpay_client = get_razorpay_client()
        
        mandate = mandate_service.get_mandate(mandate_id)
        if not mandate:
            raise ValueError("Mandate not found")
        
        # In real scenario, fetch mandate status from Razorpay
        # For mock, we'll simulate status validation
        if mandate.razorpay_mandate_id:
            mandate.status = MandateStatus.CONFIRMED
            db.commit()
            
        logger.info("Mandate status validated", mandate_id=mandate_id, status=mandate.status)
        
        return {
            "mandate_id": mandate_id,
            "status": mandate.status.value
        }
        
    except Exception as e:
        logger.error("Failed to validate mandate status", 
                    error=str(e), mandate_id=mandate_id)
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_expired_orders(self):
    """Clean up expired orders"""
    db = get_db_session()
    try:
        logger.info("Starting cleanup of expired orders")
        
        # Implementation for cleaning up expired orders
        # This would typically involve checking order status and updating accordingly
        
        logger.info("Completed cleanup of expired orders")
        
        return {"status": "completed"}
        
    except Exception as e:
        logger.error("Failed to cleanup expired orders", error=str(e))
        raise
    
    finally:
        db.close()
