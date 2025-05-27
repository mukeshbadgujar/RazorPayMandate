from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import json
from app.db.database import get_db
from app.schemas.schemas import RazorpayWebhookPayload, WebhookEventCreate, BaseResponse
from app.services.database_service import WebhookService
from app.tasks.webhook_tasks import process_webhook_event
from app.utils.helpers import format_success_response, format_error_response, validate_webhook_signature
from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import WebhookEvent

logger = get_logger(__name__)
router = APIRouter()


@router.post("/razorpay", response_model=BaseResponse)
async def handle_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Razorpay webhook events"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")
        
        # Validate webhook signature
        if not validate_webhook_signature(body.decode(), signature, settings.razorpay_webhook_secret):
            logger.warning("Invalid webhook signature", signature=signature)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=format_error_response("Invalid webhook signature")
            )
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode())
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=format_error_response("Invalid JSON payload")
            )
        
        # Validate payload structure
        required_fields = ["event", "account_id", "entity"]
        if not all(field in payload for field in required_fields):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=format_error_response("Missing required webhook fields")
            )
        
        # Create webhook event record
        webhook_service = WebhookService(db)
        event_id = payload.get("entity", {}).get("id", f"unknown_{payload.get('created_at', '')}")
        
        webhook_data = WebhookEventCreate(
            event_id=event_id,
            event_type=payload.get("event"),
            payload=body.decode()
        )
        
        webhook_event = webhook_service.create_webhook_event(webhook_data)
        
        # Process webhook asynchronously
        task = process_webhook_event.delay(webhook_event.id)
        
        logger.info("Webhook received and queued for processing",
                   event_id=event_id, event_type=payload.get("event"), task_id=task.id)
        
        return format_success_response(
            message="Webhook received and queued for processing",
            data={
                "event_id": event_id,
                "event_type": payload.get("event"),
                "task_id": task.id,
                "webhook_id": webhook_event.id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to process webhook")
        )


@router.get("/events/{event_id}", response_model=BaseResponse)
async def get_webhook_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get webhook event by event ID"""
    try:
        webhook = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Webhook event not found")
            )
        
        return format_success_response(
            message="Webhook event retrieved successfully",
            data={
                "event_id": webhook.event_id,
                "event_type": webhook.event_type,
                "processed": webhook.processed,
                "processing_error": webhook.processing_error,
                "created_at": webhook.created_at.isoformat(),
                "processed_at": webhook.processed_at.isoformat() if webhook.processed_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve webhook event")
        )


@router.get("/events", response_model=BaseResponse)
async def list_webhook_events(
    skip: int = 0,
    limit: int = 100,
    event_type: str = None,
    processed: bool = None,
    db: Session = Depends(get_db)
):
    """List webhook events with filtering"""
    try:
        query = db.query(WebhookEvent)
        
        if event_type:
            query = query.filter(WebhookEvent.event_type == event_type)
        
        if processed is not None:
            query = query.filter(WebhookEvent.processed == processed)
        
        webhooks = query.offset(skip).limit(limit).all()
        
        webhooks_data = [
            {
                "id": webhook.id,
                "event_id": webhook.event_id,
                "event_type": webhook.event_type,
                "processed": webhook.processed,
                "processing_error": webhook.processing_error,
                "created_at": webhook.created_at.isoformat(),
                "processed_at": webhook.processed_at.isoformat() if webhook.processed_at else None
            }
            for webhook in webhooks
        ]
        
        return format_success_response(
            message="Webhook events retrieved successfully",
            data={
                "webhooks": webhooks_data,
                "count": len(webhooks_data),
                "skip": skip,
                "limit": limit,
                "filters": {
                    "event_type": event_type,
                    "processed": processed
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve webhook events")
        )
