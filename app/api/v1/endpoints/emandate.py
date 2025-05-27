from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import (
    EMandateAuthorizationRequest, EMandateRecurringPaymentRequest, BaseResponse, OrderCreate
)
from app.services.database_service import MandateService, CustomerService
from app.tasks.emandate_tasks import (
    process_emandate_authorization, process_recurring_payment, validate_mandate_status
)
from app.utils.helpers import format_success_response, format_error_response
from app.models.models import MandateStatus
from decimal import Decimal

router = APIRouter()


@router.post("/authorize", response_model=BaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def authorize_emandate(
    request_data: EMandateAuthorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Authorize eMandate for recurring payments"""
    try:
        customer_service = CustomerService(db)
        mandate_service = MandateService(db)
        
        # Verify customer exists
        customer = customer_service.get_customer(request_data.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Customer not found")
            )
        
        # Create mandate
        mandate_data = {
            "customer_id": request_data.customer_id,
            "amount": request_data.amount,
            "frequency": request_data.frequency,
            "start_date": request_data.start_date,
            "end_date": request_data.end_date,
            "notes": str(request_data.notes) if request_data.notes else None
        }
        
        mandate = mandate_service.create_mandate(mandate_data)
        
        # Create order for authorization transaction
        order_data = OrderCreate(
            amount=request_data.amount,
            currency="INR",
            receipt=f"emandate_auth_{mandate.id}",
            notes=request_data.notes,
            customer_id=request_data.customer_id
        )
        
        # Process authorization asynchronously
        task = process_emandate_authorization.delay(
            customer_id=request_data.customer_id,
            mandate_id=mandate.id,
            order_data=order_data.dict()
        )
        
        return format_success_response(
            message="eMandate authorization initiated successfully",
            data={
                "mandate_id": mandate.id,
                "task_id": task.id,
                "status": "processing",
                "customer_id": request_data.customer_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to initiate eMandate authorization")
        )


@router.post("/recurring-payment", response_model=BaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_recurring_payment(
    request_data: EMandateRecurringPaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a recurring payment using eMandate"""
    try:
        mandate_service = MandateService(db)
        
        # Verify mandate exists and is active
        mandate = mandate_service.get_mandate(request_data.mandate_id)
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Mandate not found")
            )
        
        if mandate.status not in [MandateStatus.AUTHORIZED, MandateStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=format_error_response("Mandate is not active for payments")
            )
        
        # Validate amount doesn't exceed mandate limit
        if request_data.amount > mandate.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=format_error_response("Payment amount exceeds mandate limit")
            )
        
        # Process recurring payment asynchronously
        payment_data = {
            "amount": request_data.amount,
            "description": request_data.description,
            "receipt": request_data.receipt,
            "notes": request_data.notes
        }
        
        task = process_recurring_payment.delay(
            mandate_id=request_data.mandate_id,
            payment_data=payment_data
        )
        
        return format_success_response(
            message="Recurring payment initiated successfully",
            data={
                "mandate_id": request_data.mandate_id,
                "task_id": task.id,
                "status": "processing",
                "amount": float(request_data.amount)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to initiate recurring payment")
        )


@router.post("/validate-mandate/{mandate_id}", response_model=BaseResponse)
async def validate_mandate(
    mandate_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Validate and update mandate status"""
    try:
        mandate_service = MandateService(db)
        
        # Verify mandate exists
        mandate = mandate_service.get_mandate(mandate_id)
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Mandate not found")
            )
        
        # Validate mandate status asynchronously
        task = validate_mandate_status.delay(mandate_id)
        
        return format_success_response(
            message="Mandate validation initiated",
            data={
                "mandate_id": mandate_id,
                "task_id": task.id,
                "current_status": mandate.status.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to validate mandate")
        )


@router.get("/mandate-status/{mandate_id}", response_model=BaseResponse)
async def get_mandate_status(
    mandate_id: int,
    db: Session = Depends(get_db)
):
    """Get current mandate status"""
    try:
        mandate_service = MandateService(db)
        mandate = mandate_service.get_mandate(mandate_id)
        
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Mandate not found")
            )
        
        return format_success_response(
            message="Mandate status retrieved successfully",
            data={
                "mandate_id": mandate_id,
                "status": mandate.status.value,
                "razorpay_mandate_id": mandate.razorpay_mandate_id,
                "amount": float(mandate.amount),
                "currency": mandate.currency,
                "frequency": mandate.frequency
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve mandate status")
        )
