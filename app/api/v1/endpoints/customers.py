from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, BaseResponse
)
from app.services.database_service import CustomerService
from app.utils.helpers import format_success_response, format_error_response

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create a new customer"""
    try:
        customer_service = CustomerService(db)
        customer = customer_service.create_customer(customer_data)
        
        return format_success_response(
            message="Customer created successfully",
            data={"customer": CustomerResponse.from_orm(customer).dict()}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=format_error_response(str(e))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to create customer")
        )


@router.get("/{customer_id}", response_model=BaseResponse)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
    try:
        customer_service = CustomerService(db)
        customer = customer_service.get_customer(customer_id)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Customer not found")
            )
        
        return format_success_response(
            message="Customer retrieved successfully",
            data={"customer": CustomerResponse.from_orm(customer).dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve customer")
        )


@router.put("/{customer_id}", response_model=BaseResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update customer"""
    try:
        customer_service = CustomerService(db)
        customer = customer_service.update_customer(customer_id, customer_data)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Customer not found")
            )
        
        return format_success_response(
            message="Customer updated successfully",
            data={"customer": CustomerResponse.from_orm(customer).dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to update customer")
        )


@router.get("/", response_model=BaseResponse)
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List customers with pagination"""
    try:
        customer_service = CustomerService(db)
        customers = customer_service.list_customers(skip=skip, limit=limit)
        
        customers_data = [
            CustomerResponse.from_orm(customer).dict() 
            for customer in customers
        ]
        
        return format_success_response(
            message="Customers retrieved successfully",
            data={
                "customers": customers_data,
                "count": len(customers_data),
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve customers")
        )
