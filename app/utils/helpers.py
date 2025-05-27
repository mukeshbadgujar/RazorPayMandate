import time
import json
from typing import Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.models import APILog
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestResponseLogger:
    """Middleware to log API requests and responses"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_request_response(
        self,
        request: Request,
        response_data: Dict[str, Any],
        status_code: int,
        execution_time: float
    ):
        """Log API request and response"""
        try:
            # Get request data
            request_data = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
            }
            
            # Try to get request body if it exists
            try:
                if hasattr(request, '_body'):
                    body = await request.body()
                    if body:
                        request_data["body"] = body.decode('utf-8')
            except:
                pass
            
            # Create API log entry
            api_log = APILog(
                endpoint=request.url.path,
                method=request.method,
                request_data=json.dumps(request_data),
                response_data=json.dumps(response_data),
                status_code=status_code,
                execution_time=execution_time,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            
            self.db.add(api_log)
            self.db.commit()
            
        except Exception as e:
            logger.error("Failed to log API request/response", error=str(e))


def format_api_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format standardized API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": time.time()
    }
    
    if data is not None:
        response["data"] = data
    
    if errors is not None:
        response["errors"] = errors
    
    return response


def format_success_response(
    message: str = "Operation successful",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format success response"""
    return format_api_response(success=True, message=message, data=data)


def format_error_response(
    message: str = "Operation failed",
    errors: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format error response"""
    return format_api_response(success=False, message=message, errors=errors)


def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Validate Razorpay webhook signature"""
    import hmac
    import hashlib
    
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error("Failed to validate webhook signature", error=str(e))
        return False


def convert_amount_to_paise(amount: float) -> int:
    """Convert amount from rupees to paise"""
    return int(amount * 100)


def convert_amount_from_paise(amount: int) -> float:
    """Convert amount from paise to rupees"""
    return amount / 100
