import uuid
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.business import Business
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import PaginatedResponse
from app.api.deps import get_active_business

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AuditLogRead], summary="List business audit trail logs")
def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity: invoice, document, payment, ledger"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    start_date: Optional[date] = Query(None, description="Filter logs from date"),
    end_date: Optional[date] = Query(None, description="Filter logs to date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    business: Business = Depends(get_active_business),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AuditLogRead]:
    """Retrieve immutable audit trail records for current business workspace."""
    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(AuditLog.business_id == business.id)
    )

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))

    total = query.count()
    items_raw = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for log in items_raw:
        item = AuditLogRead.model_validate(log)
        if log.user:
            item.user_email = log.user.email
            item.user_full_name = log.user.full_name
        items.append(item)

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[AuditLogRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
