from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.notification import Notification
from app.models.role import Role
from app.schemas.notification import NotificationCreate, NotificationOut
from app.models.user import User
from app.utils.auth import get_current_user
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Admin: Create notification
@router.post("/", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    db_notification = Notification(**notification.model_dump(), created_by=current_user.id)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


# User: Get notifications for user roles
def get_user_role_ids(user: User):
    # user.user_roles is a list of UserRole objects
    return [ur.role_id for ur in getattr(user, 'user_roles', []) if ur.active and ur.role and ur.role.active]

@router.get("/", response_model=List[NotificationOut])
def get_notifications_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def enrich_with_role(notifications):
        enriched = []
        for n in notifications:
            notif = n.__dict__.copy()
            notif['role'] = n.role
            enriched.append(NotificationOut.from_orm(n))
            enriched[-1].role = n.role
        return enriched

    if current_user.has_role("admin"):
        notifications = db.query(Notification).filter(
            Notification.active == True
        ).order_by(Notification.created_on.desc()).all()
        return enrich_with_role(notifications)
    else:
        role_ids = get_user_role_ids(current_user)
        notifications = db.query(Notification).filter(
            Notification.roles_id.in_(role_ids),
            Notification.active == True
        ).order_by(Notification.created_on.desc()).all()
        return enrich_with_role(notifications)

# User: Get notifications for start page (last 3 weeks or since last login)
@router.get("/recent", response_model=List[NotificationOut])
def get_recent_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def enrich_with_role(notifications):
        enriched = []
        for n in notifications:
            notif = n.__dict__.copy()
            notif['role'] = n.role
            enriched.append(NotificationOut.from_orm(n))
            enriched[-1].role = n.role
        return enriched

    if current_user.has_role("admin"):
        # Admin sieht alle Notifications der letzten 3 Wochen
        three_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=3)
        notifications = db.query(Notification).filter(
            Notification.created_on >= three_weeks_ago,
            Notification.active == True
        ).order_by(Notification.created_on.desc()).all()
        return enrich_with_role(notifications)
    else:
        role_ids = get_user_role_ids(current_user)
        last_login = getattr(current_user, 'timestamp_last_successful_login', None)
        three_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=3)
        if last_login is None:
            last_login = three_weeks_ago
        if last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=timezone.utc)
        since = max(last_login, three_weeks_ago)
        notifications = db.query(Notification).filter(
            Notification.roles_id.in_(role_ids),
            Notification.created_on >= since,
            Notification.active == True
        ).order_by(Notification.created_on.desc()).all()
        return enrich_with_role(notifications)


# Admin: Get notification by ID
@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification_by_id(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif_out = NotificationOut.from_orm(notif)
    notif_out.role = notif.role
    return notif_out

# Admin: Update notification by ID
@router.put("/{notification_id}", response_model=NotificationOut)
def update_notification(
    notification_id: UUID,
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.title = notification.title
    notif.notification = notification.notification
    notif.roles_id = notification.roles_id
    notif.last_modified_on = datetime.now(timezone.utc)
    notif.last_modified_by = current_user.id
    db.commit()
    db.refresh(notif)
    notif_out = NotificationOut.from_orm(notif)
    notif_out.role = notif.role
    return notif_out
