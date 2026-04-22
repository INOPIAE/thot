"""
Authentication utilities
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import pyotp
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, selectinload

from config import config
from app.database import get_db

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    now_utc = datetime.now(timezone.utc)
    expire = now_utc + expires_delta
    payload = {"sub": user_id, "exp": expire, "iat": now_utc}

    encoded_jwt = jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_email_token() -> tuple[str, str]:
    """Generate a secure email verification token"""
    token = secrets.token_urlsafe(32)
    return token, token


def generate_otp_secret() -> str:
    """Generate a secret for OTP (One-Time Password)"""
    return pyotp.random_base32()


def verify_otp(secret: str, token: str) -> bool:
    """Verify an OTP token"""
    totp = pyotp.TOTP(secret)
    # Accept one adjacent TOTP step to avoid false negatives around time-boundary rollover.
    return totp.verify(token, valid_window=1)


def get_otp_qr_code(secret: str, username: str, issuer: str = "NLF Database") -> str:
    """Get OTP provisioning URI for QR code generation"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_short_code(length: int = 6) -> str:
    """Generate a short numeric code for email verification"""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def validate_password_requirements(password: str) -> tuple[bool, str]:
    """
    Validate password against requirements
    Returns: (is_valid, error_message)
    """
    if len(password) < config.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters long"

    if len(password) > config.PASSWORD_MAX_LENGTH:
        return False, f"Password must be at most {config.PASSWORD_MAX_LENGTH} characters long"

    if config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if config.PASSWORD_REQUIRE_DIGIT_OR_SPECIAL:
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        if not (has_digit or has_special):
            return False, "Password must contain at least one digit or special character"

    return True, ""


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get current user from JWT token
    FastAPI dependency for routes that require authentication
    """
    # Import here to avoid circular imports
    from app.services.user_service import UserService
    
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.models.user import User
    from app.models.user_role import UserRole

    token = credentials.credentials
    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(User)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission),
        )
        .filter(User.id == user_id)
        .first()
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def is_password_reset_needed(password: str) -> bool:
    """Check if password matches common weak patterns"""
    weak_passwords = ["password", "12345678", "qwerty", "123456", "passw0rd"]
    return password.lower() in weak_passwords

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

async def optional_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Returns user if logged in.
    If PUBLIC_USE is True → user can be None (aber auch User).
    """
    token = request.headers.get("authorization")
    current_user = None
    if token and token.lower().startswith("bearer "):
        try:
            current_user = await get_current_user(
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=token.split()[1]), db
            )
        except Exception:
            current_user = None

    if config.PUBLIC_USE:
        return current_user  # darf auch None sein

    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return current_user
