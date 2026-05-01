"""
Authentication routes for user registration, login, and password management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import User
from app.schemas import (
    UserRegisterRequest,
    UserCompleteRegistration,
    UserLoginRequest,
    UserLoginResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailChangeRequest,
    EmailChangeConfirmRequest,
    OTPEnableRequest,
)
from app.services import UserService, RegistrationService, PasswordResetService
from app.services.otp_reset_service import OTPResetService
from app.middleware.csrf import CSRFMiddleware
from app.utils import (
    create_access_token,
    decode_access_token,
    get_current_user,
    verify_otp,
)
from app.utils.email_service import email_service
from config import config

logger = logging.getLogger(__name__)
optional_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/register", response_model=dict)
async def register_user(
    request: UserRegisterRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
):
    """
    Register a new user - Step 1
    User must agree to Terms of Service
    Sends confirmation email with token link
    """
    closed_registration_effective = RegistrationService.is_closed_registration_effective(db)
    is_admin_registration = False

    if closed_registration_effective:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is currently limited to support and admin users",
            )

        user_id = decode_access_token(credentials.credentials)
        current_user = UserService.get_user_by_id(db, user_id) if user_id else None
        if not current_user or not current_user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user_roles = set(current_user.get_roles())
        if not ("admin" in user_roles or "support" in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is currently limited to support and admin users",
            )

        is_admin_registration = True
    else:
        # Open registration requires ToS agreement in step 1.
        if not request.tos_agreed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must agree to the Terms of Service"
            )

    # Initiate registration and cleanup expired entries
    registration, error = RegistrationService.initiate_registration(
        db=db,
        username=request.username,
        email=request.email,
        admin=is_admin_registration,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Send registration confirmation email
    confirmation_link = f"{config.FRONTEND_URL}/auth/register/confirm/{registration.token}"
    email_sent = email_service.send_registration_confirmation_email(
        to_email=registration.email,
        username=registration.username,
        confirmation_link=confirmation_link,
        expiration_hours=config.REGISTRATION_TOKEN_EXPIRE_HOURS,
        language=request.language,
    )
    
    if not email_sent:
        logger.warning(f"Email sending failed for registration {registration.id}, but registration was created")

    return {
        "message": f"Registration initiated. Please check your email ({registration.email}) for confirmation link. The link will expire in {config.REGISTRATION_TOKEN_EXPIRE_HOURS} hours.",
        "username": registration.username,
        "email": registration.email,
        "expires_in_hours": config.REGISTRATION_TOKEN_EXPIRE_HOURS,
        "admin": registration.admin,
        "closed_registration": closed_registration_effective,
    }


from fastapi import Response

@router.get("/register/confirm/{token}")
async def get_registration_confirmation(
    token: str,
    db: Session = Depends(get_db),
    response: Response = None,
):
    """
    Get registration details to confirm before completing registration
    Used by frontend to show the registration form
    """
    # Cleanup expired registrations and get token
    registration, error = RegistrationService.get_registration_by_token(db, token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Set CSRF cookie for registration confirmation POST
    from app.middleware.csrf import CSRFMiddleware
    csrf_token = CSRFMiddleware.generate_csrf_token()
    if response is not None:
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,  # Must be readable by frontend JS
            secure=False,    # Set True in production with HTTPS
            samesite="Lax",
            max_age=60*60*24,
        )

    return {
        "token": token,
        "username": registration.username,
        "email": registration.email,
        "expires_at": registration.expires_at.isoformat(),
        "admin": registration.admin,
    }


@router.post("/register/confirm/{token}")
async def confirm_registration(
    token: str,
    request: UserCompleteRegistration,
    db: Session = Depends(get_db),
):
    """
    Complete user registration with password - Step 2
    """
    try:
        # Complete registration and create user
        user, otp_setup_data, error = RegistrationService.complete_registration(
            db=db,
            token=token,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password,
            corporate_number=request.corporate_number,
            enable_otp=request.enable_otp,
            tos_agreed=request.tos_agreed,
            current_language=request.current_language,
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Prepare response
        response_data = {
            "message": "Registration completed successfully",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "roles": user.get_roles(),
            }
        }

        # Add OTP setup data if enabled
        if request.enable_otp and otp_setup_data:
            response_data["otp_setup"] = {
                "qr_code": otp_setup_data.get("qr_code"),
                "manual_entry": otp_setup_data.get("manual_entry"),
            }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while completing registration"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Login user with username/email and password
    Optional OTP for two-factor authentication
    """
    # Authenticate user
    user, error = UserService.authenticate_user(
        db=db,
        username=request.username,
        password=request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Die Anmeldung ist fehlgeschlagen"
        )

    # Set CSRF token cookie
    csrf_token = CSRFMiddleware.generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by frontend JS
        secure=config.COOKIE_SECURE,
        samesite="Lax",
        max_age=60*60*24,
        # domain entfernt, damit Cookie für localhost funktioniert
    )

    # Require OTP either when user has OTP enabled or when privileged role is assigned.
    requires_role_based_otp = user.has_role("support") or user.has_role("admin")
    otp_required = user.otp_enabled or requires_role_based_otp

    if otp_required:
        if not request.otp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Die Anmeldung ist fehlgeschlagen"
            )

        if not user.otp_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Die Anmeldung ist fehlgeschlagen"
            )

        # Verify OTP
        if not verify_otp(user.otp_secret, request.otp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Die Anmeldung ist fehlgeschlagen"
            )

    # Create access token
    access_token = create_access_token(str(user.id))

    # Prepare user response
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        current_language=user.current_language,
        corporate_number=user.corporate_number,
        corporate_approved=user.corporate_approved,
        otp_enabled=user.otp_enabled,
        active=user.active,
        created_on=user.created_on,
        roles=user.get_roles(),
    )

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/refresh")
async def refresh_access_token(current_user: User = Depends(get_current_user)):
    """
    Refresh the access token for an authenticated active user.
    """
    access_token = create_access_token(str(current_user.id))
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset via email
    """
    user, token_entry, error = PasswordResetService.start_user_password_reset(
        db=db,
        username=request.username,
    )

    # Always return success for security
    if user and token_entry and not error:
        reset_link = f"{config.FRONTEND_URL}/auth/password-reset/confirm/{token_entry.token}"
        email_service.send_password_reset_email(
            to_email=user.email,
            username=user.username,
            reset_link=reset_link,
            expiration_hours=config.USER_PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
            language=user.current_language,
            initiated_by_support=False,
        )

    return {
        "message": f"If the username exists, you will receive password reset instructions by email. The link is valid for {config.USER_PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s)."
    }


@router.get("/password-reset/confirm/{token}")
async def validate_password_reset_token(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Validate password reset token before showing reset form
    """
    token_entry, error = PasswordResetService.get_valid_token(db, token)
    if error or not token_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Invalid reset token",
        )

    return {
        "message": "Password reset token is valid",
        "expires_at": token_entry.expires_at.isoformat(),
    }


@router.post("/password-reset/confirm/{token}")
async def confirm_password_reset(
    token: str,
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with new password
    """
    token_entry, error = PasswordResetService.get_valid_token(db, token)
    if error or not token_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Invalid reset token",
        )

    success, message = UserService.reset_password(
        db=db,
        user_id=str(token_entry.userid),
        new_password=request.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    marked, mark_error = PasswordResetService.mark_token_used(db, token_entry)
    if not marked:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=mark_error or "Could not finalize password reset",
        )

    return {
        "message": "Password reset successfully"
    }


@router.get("/otp-reset/confirm/{token}")
async def validate_otp_reset_token(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Validate OTP reset token and return temporary setup details
    """
    token_entry, otp_setup_data, error = OTPResetService.get_public_reset_payload(db, token)
    if error or not token_entry or not otp_setup_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Invalid OTP reset token",
        )

    return {
        "message": "OTP reset token is valid",
        "expires_at": token_entry.expires_at.isoformat(),
        "otp_setup": otp_setup_data,
    }


@router.post("/otp-reset/confirm/{token}")
async def confirm_otp_reset_token(
    token: str,
    request: OTPEnableRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm OTP reset with token and one OTP code
    """
    success, error = OTPResetService.confirm_otp_reset_by_token(
        db=db,
        token_value=token,
        otp_code=request.otp_code,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not confirm OTP reset",
        )

    return {
        "message": "OTP updated successfully"
    }


# TODO: Implement remaining endpoints:
# - /logout - Logout user
# - /users/otp/enable - Enable OTP
# - /users/otp/disable - Disable OTP
