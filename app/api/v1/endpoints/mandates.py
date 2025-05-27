from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.schemas import (
    MandateCreate, MandateUpdate, MandateResponse, BaseResponse
)
from app.services.database_service import MandateService
from app.utils.helpers import format_success_response, format_error_response

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_mandate(
    mandate_data: MandateCreate,
    db: Session = Depends(get_db)
):
    """Create a new mandate"""
    try:
        mandate_service = MandateService(db)
        mandate = mandate_service.create_mandate(mandate_data)
        
        return format_success_response(
            message="Mandate created successfully",
            data={"mandate": MandateResponse.from_orm(mandate).dict()}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=format_error_response(str(e))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to create mandate")
        )


@router.get("/{mandate_id}", response_model=BaseResponse)
async def get_mandate(
    mandate_id: int,
    db: Session = Depends(get_db)
):
    """Get mandate by ID"""
    try:
        mandate_service = MandateService(db)
        mandate = mandate_service.get_mandate(mandate_id)
        
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Mandate not found")
            )
        
        return format_success_response(
            message="Mandate retrieved successfully",
            data={"mandate": MandateResponse.from_orm(mandate).dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve mandate")
        )


@router.put("/{mandate_id}", response_model=BaseResponse)
async def update_mandate(
    mandate_id: int,
    mandate_data: MandateUpdate,
    db: Session = Depends(get_db)
):
    """Update mandate"""
    try:
        mandate_service = MandateService(db)
        mandate = mandate_service.update_mandate(mandate_id, mandate_data)
        
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=format_error_response("Mandate not found")
            )
        
        return format_success_response(
            message="Mandate updated successfully",
            data={"mandate": MandateResponse.from_orm(mandate).dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to update mandate")
        )


@router.get("/customer/{customer_id}", response_model=BaseResponse)
async def list_customer_mandates(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """List mandates for a customer"""
    try:
        mandate_service = MandateService(db)
        mandates = mandate_service.list_customer_mandates(customer_id)
        
        mandates_data = [
            MandateResponse.from_orm(mandate).dict() 
            for mandate in mandates
        ]
        
        return format_success_response(
            message="Customer mandates retrieved successfully",
            data={
                "mandates": mandates_data,
                "customer_id": customer_id,
                "count": len(mandates_data)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response("Failed to retrieve customer mandates")
        )
