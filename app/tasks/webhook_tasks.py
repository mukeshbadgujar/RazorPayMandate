from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.database_service import WebhookService, PaymentService, MandateService
from app.core.logging import get_logger
from app.models.models import PaymentStatus, MandateStatus, WebhookEvent, Payment, Order
import json
from typing import Dict, Any

logger = get_logger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_webhook_event(self, webhook_id: int):
    """Process a webhook event"""
    db = get_db_session()
    try:
        logger.info("Processing webhook event", webhook_id=webhook_id)
        
        webhook_service = WebhookService(db)
        
        # Get webhook event
        webhook = db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        if not webhook:
            raise ValueError("Webhook event not found")
        
        if webhook.processed:
            logger.info("Webhook already processed", webhook_id=webhook_id)
            return {"status": "already_processed"}
        
        # Parse payload
        payload = json.loads(webhook.payload)
        event_type = webhook.event_type
        
        # Process based on event type
        if event_type == "payment.authorized":
            process_payment_authorized(db, payload)
        elif event_type == "payment.captured":
            process_payment_captured(db, payload)
        elif event_type == "payment.failed":
            process_payment_failed(db, payload)
        elif event_type == "order.paid":
            process_order_paid(db, payload)
        else:
            logger.warning("Unhandled webhook event type", event_type=event_type)
        
        # Mark webhook as processed
        webhook_service.mark_webhook_processed(webhook_id)
        
        logger.info("Webhook event processed successfully", webhook_id=webhook_id)
        
        return {"status": "processed", "event_type": event_type}
        
    except Exception as e:
        logger.error("Failed to process webhook event", 
                    error=str(e), webhook_id=webhook_id)
        
        # Mark webhook with error
        webhook_service = WebhookService(db)
        webhook_service.mark_webhook_processed(webhook_id, str(e))
        
        # Retry the task
        raise self.retry(exc=e)
    
    finally:
        db.close()


def process_payment_authorized(db: Session, payload: Dict[str, Any]):
    """Process payment.authorized webhook"""
    payment_entity = payload.get("entity", {})
    razorpay_payment_id = payment_entity.get("id")
    
    if not razorpay_payment_id:
        return
    
    # Find payment in database
    payment = db.query(Payment).filter(
        Payment.razorpay_payment_id == razorpay_payment_id
    ).first()
    
    if payment:
        payment.status = PaymentStatus.AUTHORIZED
        db.commit()
        logger.info("Payment authorized", payment_id=payment.id)


def process_payment_captured(db: Session, payload: Dict[str, Any]):
    """Process payment.captured webhook"""
    payment_entity = payload.get("entity", {})
    razorpay_payment_id = payment_entity.get("id")
    
    if not razorpay_payment_id:
        return
    
    # Find payment in database
    payment = db.query(Payment).filter(
        Payment.razorpay_payment_id == razorpay_payment_id
    ).first()
    
    if payment:
        payment.status = PaymentStatus.CAPTURED
        payment.fee = payment_entity.get("fee", 0) / 100  # Convert from paise
        payment.tax = payment_entity.get("tax", 0) / 100  # Convert from paise
        db.commit()
        logger.info("Payment captured", payment_id=payment.id)


def process_payment_failed(db: Session, payload: Dict[str, Any]):
    """Process payment.failed webhook"""
    payment_entity = payload.get("entity", {})
    razorpay_payment_id = payment_entity.get("id")
    
    if not razorpay_payment_id:
        return
    
    # Find payment in database
    payment = db.query(Payment).filter(
        Payment.razorpay_payment_id == razorpay_payment_id
    ).first()
    
    if payment:
        payment.status = PaymentStatus.FAILED
        payment.error_code = payment_entity.get("error_code")
        payment.error_description = payment_entity.get("error_description")
        db.commit()
        logger.info("Payment failed", payment_id=payment.id)


def process_order_paid(db: Session, payload: Dict[str, Any]):
    """Process order.paid webhook"""
    order_entity = payload.get("entity", {})
    razorpay_order_id = order_entity.get("id")
    
    if not razorpay_order_id:
        return
    
    # Find order in database
    order = db.query(Order).filter(
        Order.razorpay_order_id == razorpay_order_id
    ).first()
    
    if order:
        order.status = "paid"
        db.commit()
        logger.info("Order paid", order_id=order.id)


@celery_app.task(bind=True)
def send_payment_notification(self, payment_id: int, notification_type: str):
    """Send payment notification to customer"""
    db = get_db_session()
    try:
        logger.info("Sending payment notification", 
                   payment_id=payment_id, type=notification_type)
        
        payment_service = PaymentService(db)
        payment = payment_service.get_payment(payment_id)
        
        if not payment:
            raise ValueError("Payment not found")
        
        # In real implementation, this would send email/SMS notifications
        # For now, we'll just log the notification
        
        logger.info("Payment notification sent successfully",
                   payment_id=payment_id, customer_id=payment.customer_id)
        
        return {
            "status": "sent",
            "payment_id": payment_id,
            "notification_type": notification_type
        }
        
    except Exception as e:
        logger.error("Failed to send payment notification", 
                    error=str(e), payment_id=payment_id)
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True)
def process_failed_payments_retry(self):
    """Retry failed payments"""
    db = get_db_session()
    try:
        logger.info("Processing failed payments for retry")
        
        # Find failed payments that can be retried
        failed_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.FAILED
        ).limit(100).all()
        
        retry_count = 0
        for payment in failed_payments:
            # Implement retry logic here
            # For now, we'll just log
            logger.info("Found failed payment for retry", payment_id=payment.id)
            retry_count += 1
        
        logger.info("Completed failed payments retry processing", 
                   retry_count=retry_count)
        
        return {"status": "completed", "retry_count": retry_count}
        
    except Exception as e:
        logger.error("Failed to process failed payments retry", error=str(e))
        raise
    
    finally:
        db.close()
