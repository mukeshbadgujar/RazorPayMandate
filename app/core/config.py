from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./razorpay_mandate.db"
    database_host: str = "localhost"
    database_port: int = 3306
    database_name: str = "razorpay_mandate_db"
    database_user: str = "root"
    database_password: str = "password"
    test_database_url: str = "sqlite:///./test_razorpay_mandate.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Razorpay
    razorpay_key_id: str = "rzp_test_your_key_id"
    razorpay_key_secret: str = "your_key_secret"
    razorpay_webhook_secret: str = "your_webhook_secret"
    razorpay_base_url: str = "https://api.razorpay.com/v1"
    
    # Application
    app_name: str = "Razorpay eMandate API"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # API
    api_v1_str: str = "/api/v1"
    max_connections_count: int = 10
    min_connections_count: int = 10
    
    # Environment
    environment: str = "development"
    
    # CORS
    allowed_hosts: str = "localhost,127.0.0.1"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Mock configuration
    use_mock_razorpay: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields


settings = Settings()
