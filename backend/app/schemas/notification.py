from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class RoleOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    model_config = {
        "from_attributes": True
    }

class NotificationBase(BaseModel):
    title: str
    notification: str
    roles_id: UUID

class NotificationCreate(NotificationBase):
    pass

class NotificationOut(NotificationBase):
    id: UUID
    created_on: datetime
    created_by: Optional[UUID]
    last_modified_on: Optional[datetime]
    last_modified_by: Optional[UUID]
    active: bool
    role: Optional[RoleOut]

    model_config = {
        "from_attributes": True
    }
