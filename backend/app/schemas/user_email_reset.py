from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserEmailResetRequest(BaseModel):
    email: EmailStr

class UserEmailResetConfirm(BaseModel):
    token: str

class UserEmailResetResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    expires_at: datetime
