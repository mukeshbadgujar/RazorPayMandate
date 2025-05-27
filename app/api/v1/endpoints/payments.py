from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.schemas import (
    PaymentCreate, PaymentResponse, OrderCreate, OrderResponse, 
    EMandateAuthorizationRequest, EMandateRecurringPaymentRequest, BaseResponse
)
from app.services.database_service import PaymentService, MandateService
from app.tasks.emandate_tasks import process_emandate_authorization, process_recurring_payment
from app.utils.helpers import format_success_response, format_error_response

router = APIRouter()


@router.post("/orders", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order"""
    try:
        payment_service = PaymentService(db)
        order = payment_service.create_order(order_data)
        
        return format_success_response(
            message="Order created successfully",
            data={"order": OrderResponse.from_orm(order).dict()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to create order")
        )


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """Create a new payment"""
    try:
        payment_service = PaymentService(db)
        payment = payment_service.create_payment(payment_data)
        
        return format_success_response(
            message="Payment created successfully",
            data={"payment": PaymentResponse.from_orm(payment).dict()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to create payment")
        )


@router.get("/{payment_id}", response_model=BaseResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Get payment by ID"""
    try:
        payment_service = PaymentService(db)
        payment = payment_service.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Payment not found")
            )
        
        return format_success_response(
            message="Payment retrieved successfully",
            data={"payment": PaymentResponse.from_orm(payment).dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve payment")
        )


@router.get("/customer/{customer_id}", response_model=BaseResponse)
async def list_customer_payments(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """List payments for a customer"""
    try:
        payment_service = PaymentService(db)
        payments = payment_service.list_customer_payments(customer_id)
        
        payments_data = [
            PaymentResponse.from_orm(payment).dict() 
            for payment in payments
        ]
        
        return format_success_response(
            message="Customer payments retrieved successfully",
            data={
                "payments": payments_data,
                "customer_id": customer_id,
                "count": len(payments_data)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve customer payments")
        )
