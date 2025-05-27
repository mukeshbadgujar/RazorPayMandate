import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import get_logger, logger
from app.db.database import get_db
from app.utils.helpers import RequestResponseLogger, format_error_response

# Get logger
app_logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Razorpay eMandate API for recurring payments",
    openapi_url=f"{settings.api_v1_str}/openapi.json" if settings.debug else None,
    docs_url=f"{settings.api_v1_str}/docs" if settings.debug else None,
    redoc_url=f"{settings.api_v1_str}/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to log requests and responses"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Log request/response (in production, you might want to be more selective)
    try:
        # Get database session for logging
        db_gen = get_db()
        db = next(db_gen)
        
        # Create response data for logging
        response_data = {
            "status_code": response.status_code,
            "execution_time": execution_time
        }
        
        # Log the request/response
        request_logger = RequestResponseLogger(db)
        await request_logger.log_request_response(
            request=request,
            response_data=response_data,
            status_code=response.status_code,
            execution_time=execution_time
        )
        
        db.close()
        
    except Exception as e:
        app_logger.error("Failed to log request/response", error=str(e))
    
    # Add execution time to response headers
    response.headers["X-Process-Time"] = str(execution_time)
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    app_logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content=format_error_response("Internal server error")
    )


# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": f"{settings.api_v1_str}/docs" if settings.debug else None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
