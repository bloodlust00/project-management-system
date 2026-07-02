import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse

class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user: Optional[UserResponse] = None
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    details: Optional[dict] = None
    created_at: datetime
