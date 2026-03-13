"""
OTP reset service for token-based OTP replacement flows
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging
import secrets
import uuid

from sqlalchemy.orm import Session

from app.models import User, OTPResetToken
from app.services.registration_service import RegistrationService
from app.utils import generate_otp_secret
from config import config

logger = logging.getLogger(__name__)


class OTPResetService:
    """Service for OTP reset token operations"""

    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        """Ensure timestamps are timezone-aware before comparison."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Delete expired OTP reset tokens"""
        try:
            now = datetime.now(timezone.utc)
            expired_tokens = (
                db.query(OTPResetToken)
                .filter(OTPResetToken.expires_at < now)
                .all()
            )

            count = len(expired_tokens)
            for token in expired_tokens:
                db.delete(token)

            db.commit()
            return count
        except Exception as exc:
            db.rollback()
            logger.error(f"Error cleaning up expired OTP reset tokens: {str(exc)}")
            return 0

    @staticmethod
    def invalidate_active_tokens(db: Session, user_id) -> None:
        """Mark existing active OTP reset tokens as used before creating a new one"""
        active_tokens = (
            db.query(OTPResetToken)
            .filter(
                OTPResetToken.userid == user_id,
                OTPResetToken.used.is_(False),
            )
            .all()
        )

        for token in active_tokens:
            token.used = True

    @staticmethod
    def create_reset_token(
        db: Session,
        user: User,
        expiration_hours: int,
    ) -> Tuple[Optional[OTPResetToken], Optional[dict], Optional[str]]:
        """Create a temporary OTP reset token and QR setup payload for a user"""
        try:
            OTPResetService.cleanup_expired_tokens(db)
            OTPResetService.invalidate_active_tokens(db, user.id)

            token_value = secrets.token_urlsafe(32)
            otp_secret = generate_otp_secret()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)

            token_entry = OTPResetToken(
                id=uuid.uuid4(),
                userid=user.id,
                token=token_value,
                otp_token=otp_secret,
                expires_at=expires_at,
                used=False,
            )

            db.add(token_entry)
            db.commit()
            db.refresh(token_entry)

            otp_setup_data = {
                "qr_code": RegistrationService.generate_otp_qr_code(user.username, otp_secret),
                "manual_entry": otp_secret,
            }
            return token_entry, otp_setup_data, None
        except Exception as exc:
            db.rollback()
            logger.error(f"Error creating OTP reset token: {str(exc)}")
            return None, None, "An error occurred while preparing OTP reset"

    @staticmethod
    def get_public_reset_payload(
        db: Session,
        token_value: str,
    ) -> Tuple[Optional[OTPResetToken], Optional[dict], Optional[str]]:
        """Get setup payload for a valid reset token (used by public confirm flow)."""
        token_entry, error = OTPResetService.get_valid_token(db, token_value)
        if error or not token_entry:
            return None, None, error or "Invalid OTP reset request"

        user = db.query(User).filter(User.id == token_entry.userid).first()
        if not user:
            return None, None, "Invalid OTP reset request"

        otp_setup_data = {
            "qr_code": RegistrationService.generate_otp_qr_code(user.username, token_entry.otp_token),
            "manual_entry": token_entry.otp_token,
        }
        return token_entry, otp_setup_data, None

    @staticmethod
    def get_valid_token(
        db: Session,
        token_value: str,
        user_id=None,
    ) -> Tuple[Optional[OTPResetToken], Optional[str]]:
        """Get and validate a non-used, non-expired OTP reset token"""
        try:
            OTPResetService.cleanup_expired_tokens(db)

            query = db.query(OTPResetToken).filter(OTPResetToken.token == token_value)
            if user_id is not None:
                query = query.filter(OTPResetToken.userid == user_id)

            token_entry = query.first()

            if not token_entry:
                return None, "Invalid or expired OTP reset request"

            if token_entry.used:
                return None, "OTP reset request has already been used"

            if OTPResetService._normalize_timestamp(token_entry.expires_at) <= datetime.now(timezone.utc):
                db.delete(token_entry)
                db.commit()
                return None, "Invalid or expired OTP reset request"

            return token_entry, None
        except Exception as exc:
            db.rollback()
            logger.error(f"Error validating OTP reset token: {str(exc)}")
            return None, "An error occurred while validating OTP reset"

    @staticmethod
    def start_user_otp_reset(
        db: Session,
        user_id: str,
    ) -> Tuple[Optional[User], Optional[OTPResetToken], Optional[dict], Optional[str]]:
        """Start OTP reset for the current user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, None, None, "User not found"

        token_entry, otp_setup_data, error = OTPResetService.create_reset_token(
            db=db,
            user=user,
            expiration_hours=config.USER_OTP_RESET_TOKEN_EXPIRE_HOURS,
        )
        if error:
            return None, None, None, error

        return user, token_entry, otp_setup_data, None

    @staticmethod
    def start_support_otp_reset(
        db: Session,
        user_id: str,
    ) -> Tuple[Optional[User], Optional[OTPResetToken], Optional[str]]:
        """Start OTP reset initiated by support/admin (24h expiry by default)."""
        try:
            user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            return None, None, "User not found"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, None, "User not found"

        token_entry, _, error = OTPResetService.create_reset_token(
            db=db,
            user=user,
            expiration_hours=config.SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS,
        )
        if error:
            return None, None, error

        return user, token_entry, None

    @staticmethod
    def confirm_otp_reset_by_token(
        db: Session,
        token_value: str,
        otp_code: str,
        expected_user_id=None,
    ) -> Tuple[bool, Optional[str]]:
        """Confirm OTP reset by token and code, optionally scoped to a specific user."""
        token_entry, error = OTPResetService.get_valid_token(db, token_value)
        if error or not token_entry:
            return False, error or "Invalid OTP reset request"

        if expected_user_id is not None:
            try:
                expected_uuid = uuid.UUID(expected_user_id) if isinstance(expected_user_id, str) else expected_user_id
            except (ValueError, AttributeError):
                return False, "Invalid OTP reset request"

            if token_entry.userid != expected_uuid:
                return False, "Invalid OTP reset request"

        if not RegistrationService.verify_otp_code(token_entry.otp_token, otp_code):
            return False, "The temporary OTP code is invalid"

        user = db.query(User).filter(User.id == token_entry.userid).first()
        if not user:
            return False, "User not found"

        try:
            user.otp_secret = token_entry.otp_token
            user.otp_enabled = True
            user.last_modified_on = datetime.now(timezone.utc)
            user.last_modified_by = user.id
            token_entry.used = True
            db.commit()
            return True, None
        except Exception as exc:
            db.rollback()
            logger.error(f"Error confirming OTP reset: {str(exc)}")
            return False, "An error occurred while updating OTP"

    @staticmethod
    def confirm_user_otp_reset(
        db: Session,
        user: User,
        token_value: str,
        otp_code: str,
    ) -> Tuple[bool, Optional[str]]:
        """Verify the temporary OTP code and replace the user's OTP secret"""
        return OTPResetService.confirm_otp_reset_by_token(
            db=db,
            token_value=token_value,
            otp_code=otp_code,
            expected_user_id=user.id,
        )