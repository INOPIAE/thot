from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.user import User
from app.models.user_email_reset import UserEmailReset
from app.schemas.user_email_reset import UserEmailResetRequest, UserEmailResetConfirm, UserEmailResetResponse
from app.utils.email_service import email_service
from app.utils import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import config

router = APIRouter(prefix="/user-email-reset", tags=["user-email-reset"])
security = HTTPBearer()

async def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/request", response_model=UserEmailResetResponse)
async def request_email_reset(
    request: UserEmailResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Remove old requests for this user
    db.query(UserEmailReset).filter(UserEmailReset.user_id == current_user.id).delete()
    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    email_reset = UserEmailReset(
        id=uuid4(),
        user_id=current_user.id,
        email=request.email,
        token=token,
        expires_at=expires_at,
    )
    db.add(email_reset)
    db.commit()
    db.refresh(email_reset)
    # Send confirmation email (background)
    language = getattr(current_user, "current_language", "en")
    background_tasks.add_task(email_service.send_email_reset_confirmation, request.email, token, current_user.username, language)
    return UserEmailResetResponse(
        id=email_reset.id,
        user_id=email_reset.user_id,
        email=email_reset.email,
        expires_at=email_reset.expires_at,
    )

@router.post("/confirm", response_model=UserEmailResetResponse)
async def confirm_email_reset(
    request: UserEmailResetConfirm,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email_reset = db.query(UserEmailReset).filter(UserEmailReset.token == request.token).first()
    if not email_reset or email_reset.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == email_reset.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_email = user.email
    user.email = email_reset.email
    db.delete(email_reset)
    db.commit()
    # Send info email to old address
    language = getattr(user, "current_language", "en")
    background_tasks.add_task(email_service.send_email_reset_info, old_email, user.username, language)
    return UserEmailResetResponse(
        id=user.id,
        user_id=user.id,
        email=user.email,
        expires_at=datetime.now(timezone.utc),
    )
