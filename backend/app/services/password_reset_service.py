"""
Password reset service for token-based password reset flows
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging
import secrets
import uuid

from sqlalchemy.orm import Session

from app.models import User, PasswordResetToken
from config import config

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for password reset token operations"""

    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        """Ensure timestamps are timezone-aware before comparison."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Delete expired password reset tokens"""
        try:
            now = datetime.now(timezone.utc)
            expired_tokens = (
                db.query(PasswordResetToken)
                .filter(PasswordResetToken.expires_at < now)
                .all()
            )

            count = len(expired_tokens)
            for token in expired_tokens:
                db.delete(token)

            db.commit()
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up expired password reset tokens: {str(e)}")
            return 0

    @staticmethod
    def create_reset_token(
        db: Session,
        user: User,
        expiration_hours: int,
    ) -> Tuple[Optional[PasswordResetToken], Optional[str]]:
        """Create a password reset token for a user"""
        try:
            PasswordResetService.cleanup_expired_tokens(db)

            token_value = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)

            reset_token = PasswordResetToken(
                id=uuid.uuid4(),
                userid=user.id,
                token=token_value,
                expires_at=expires_at,
                used=False,
            )

            db.add(reset_token)
            db.commit()
            db.refresh(reset_token)
            return reset_token, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating password reset token: {str(e)}")
            return None, "An error occurred while creating reset token"

    @staticmethod
    def get_valid_token(db: Session, token_value: str) -> Tuple[Optional[PasswordResetToken], Optional[str]]:
        """Get and validate a non-used, non-expired token, and ensure user has at least one valid token"""
        try:
            PasswordResetService.cleanup_expired_tokens(db)

            token_entry = (
                db.query(PasswordResetToken)
                .filter(PasswordResetToken.token == token_value)
                .first()
            )

            if not token_entry:
                return None, "Invalid or expired password reset link"

            if token_entry.used:
                return None, "Password reset token has already been used"

            if PasswordResetService._normalize_timestamp(token_entry.expires_at) <= datetime.now(timezone.utc):
                db.delete(token_entry)
                db.commit()
                return None, "Invalid or expired password reset link"

            user_valid_tokens = (
                db.query(PasswordResetToken)
                .filter(
                    PasswordResetToken.userid == token_entry.userid,
                    PasswordResetToken.used.is_(False),
                    PasswordResetToken.expires_at > datetime.now(timezone.utc),
                )
                .count()
            )

            if user_valid_tokens < 1:
                return None, "No valid password reset available. Please request a new one"

            return token_entry, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error validating password reset token: {str(e)}")
            return None, "An error occurred while validating reset token"

    @staticmethod
    def mark_token_used(db: Session, token_entry: PasswordResetToken) -> Tuple[bool, Optional[str]]:
        """Mark a password reset token as used"""
        try:
            token_entry.used = True
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking password reset token as used: {str(e)}")
            return False, "An error occurred while finalizing password reset"

    @staticmethod
    def start_user_password_reset(
        db: Session,
        username: str,
    ) -> Tuple[Optional[User], Optional[PasswordResetToken], Optional[str]]:
        """Start password reset requested by user (1h expiry)"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None, None, None

        token_entry, error = PasswordResetService.create_reset_token(
            db=db,
            user=user,
            expiration_hours=config.USER_PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
        )
        if error:
            return None, None, error

        return user, token_entry, None

    @staticmethod
    def start_support_password_reset(
        db: Session,
        user_id: str,
    ) -> Tuple[Optional[User], Optional[PasswordResetToken], Optional[str]]:
        """Start password reset initiated by support/admin (24h expiry)"""
        try:
            user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            return None, None, "User not found"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, None, "User not found"

        token_entry, error = PasswordResetService.create_reset_token(
            db=db,
            user=user,
            expiration_hours=config.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
        )
        if error:
            return None, None, error

        return user, token_entry, None