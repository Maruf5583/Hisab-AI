from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    businesses,
    parties,
    documents,
    invoices,
    payments,
    ledger,
    reports,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(businesses.router, prefix="/businesses", tags=["Businesses"])
api_router.include_router(parties.router, prefix="/parties", tags=["Parties"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(ledger.router, prefix="/ledger", tags=["General Ledger"])
api_router.include_router(reports.router, prefix="/reports", tags=["Financial Reports"])
