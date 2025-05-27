#!/usr/bin/env python3

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.core.celery_app import celery_app
    
    # Start Celery worker
    celery_app.start()
