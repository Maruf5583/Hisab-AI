import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime
