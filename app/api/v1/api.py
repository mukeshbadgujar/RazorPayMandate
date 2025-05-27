from fastapi import APIRouter
from app.api.v1.endpoints import customers, mandates, payments, emandate, webhooks

api_router = APIRouter()

api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["customers"]
)

api_router.include_router(
    mandates.router,
    prefix="/mandates",
    tags=["mandates"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["payments"]
)

api_router.include_router(
    emandate.router,
    prefix="/emandate",
    tags=["emandate"]
)

api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["webhooks"]
)
