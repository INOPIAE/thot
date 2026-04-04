"""
User routes for profile and user management
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.schemas import (
    UserResponse,
    UserDetailResponse,
    UserUpdateRequest,
    PasswordChangeRequest,
    OTPResetConfirmRequest,
    UserListResponse,
    UserDetailSupportResponse,
    UserUpdateSupportRequest,
    UserRoleAssignRequest,
    UserRoleResponse,
)
from app.services import UserService, OTPResetService
from app.services.password_reset_service import PasswordResetService
from app.utils import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.email_service import email_service
from config import config


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

security = HTTPBearer()


async def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from JWT token
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


@router.get("/profile", response_model=UserDetailResponse)
async def get_user_profile(
    current_user = Depends(get_current_user),
):
    """
    Get current user profile
    """
    return UserDetailResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        current_language=current_user.current_language,
        corporate_number=current_user.corporate_number,
        corporate_approved=current_user.corporate_approved,
        otp_enabled=current_user.otp_enabled,
        active=current_user.active,
        created_on=current_user.created_on,
        roles=current_user.get_roles(),
        permissions=current_user.get_permissions(),
    )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update current user profile
    """
    user = UserService.update_user_profile(
        db=db,
        user_id=str(current_user.id),
        first_name=request.first_name,
        last_name=request.last_name,
        current_language=request.current_language,
    )

    return UserResponse(
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


@router.post("/password-change")
async def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Change user password
    """
    success, message = UserService.change_password(
        db=db,
        user_id=str(current_user.id),
        current_password=request.current_password,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"message": message}


@router.get("", response_model=dict)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    filter_username: str = None,
    filter_email: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    List users with filters (support/admin only)
    """
    # Check if user has support/admin role
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access user management",
        )

    users, total = UserService.list_users(
        db=db,
        skip=skip,
        limit=limit,
        filter_username=filter_username,
        filter_email=filter_email,
    )

    user_responses = [
        UserListResponse(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            corporate_number=u.corporate_number,
            corporate_approved=u.corporate_approved,
            otp_enabled=u.otp_enabled,
            active=u.active,
        )
        for u in users
    ]

    return {
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit,
        "items": user_responses,
    }


@router.get("/statistics", response_model=dict)
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get user statistics (support/admin only)
    Returns total, active, and inactive user counts
    """
    # Check if user has support/admin role
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access user statistics",
        )

    total = db.query(func.count(User.id)).scalar()
    active = db.query(func.count(User.id)).filter(User.active == True).scalar()
    inactive = db.query(func.count(User.id)).filter(User.active == False).scalar()

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
    }


@router.get("/pending-approval", response_model=dict)
async def get_pending_approval_users(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get count of users pending corporate approval (support/admin only)
    Returns count of users with active=True and corporate_approved=False
    """
    # Check if user has support/admin role
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access user information",
        )

    pending_count = db.query(func.count(User.id)).filter(
        User.active == True,
        User.corporate_approved == False
    ).scalar()

    return {
        "pending_approval_count": pending_count,
    }


@router.get("/{user_id}", response_model=UserDetailSupportResponse)
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get user detail (support/admin only)
    """
    # Check if user has support/admin role
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserDetailSupportResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        corporate_number=user.corporate_number,
        corporate_approved=user.corporate_approved,
        otp_enabled=user.otp_enabled,
        active=user.active,
        created_on=user.created_on,
        last_modified_on=user.last_modified_on,
        unsuccessful_logins=user.unsuccessful_logins,
        timestamp_last_successful_login=user.timestamp_last_successful_login,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateSupportRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update user as support/admin
    """
    # Check if user has support/admin role
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user = UserService.update_user_as_support(
        db=db,
        user_id=user_id,
        admin_id=str(current_user.id),
        corporate_number=request.corporate_number,
        corporate_approved=request.corporate_approved,
        active=request.active,
    )

    return UserResponse(
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


@router.post("/otp/reset")
async def start_otp_reset(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Start OTP reset for current user and return temporary setup data
    """
    user, token_entry, otp_setup_data, error = OTPResetService.start_user_otp_reset(
        db=db,
        user_id=current_user.id,
    )
    if error or not user or not token_entry or not otp_setup_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not start OTP reset",
        )

    return {
        "message": "OTP reset initiated. Configure your authenticator app with the temporary setup data and confirm the generated code.",
        "token": token_entry.token,
        "otp_setup": otp_setup_data,
        "expires_in_hours": config.USER_OTP_RESET_TOKEN_EXPIRE_HOURS,
    }


@router.post("/otp/reset/confirm")
async def confirm_otp_reset(
    request: OTPResetConfirmRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Confirm OTP reset by validating the temporary OTP code
    """
    success, error = OTPResetService.confirm_user_otp_reset(
        db=db,
        user=current_user,
        token_value=request.token,
        otp_code=request.otp_code,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not confirm OTP reset",
        )

    return {
        "message": "OTP updated successfully",
    }


# TODO: Implement remaining endpoints:
# - PUT /{user_id}/activate - Activate user
# - PUT /{user_id}/deactivate - Deactivate user


# --- DELETE ACCOUNT ENDPOINT (SELF) ---
@router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_own_account(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Delete Account (set active=False)
    ---
    EN: Allows the user to delete their own account (sets active=False, soft delete).
    DE: Ermöglicht dem Benutzer, seinen eigenen Account zu löschen (setzt active=False, Soft-Delete).
    """
    user = UserService.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already deleted/inactive"
        )
    user.active = False
    user.last_modified_on = datetime.now(timezone.utc)
    user.last_modified_by = user.id
    db.commit()
    return {"message": "Account deleted successfully (soft delete)", "detail": {"en": "Your account has been deleted (deactivated).", "de": "Ihr Account wurde gelöscht (deaktiviert)."}}


@router.put("/{user_id}/password-reset")
async def support_reset_user_password(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Start password reset process for a user (support/admin only)
    """
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user, token_entry, error = PasswordResetService.start_support_password_reset(
        db=db,
        user_id=user_id,
    )
    if error or not user or not token_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not start password reset",
        )

    reset_link = f"{config.FRONTEND_URL}/auth/password-reset/confirm/{token_entry.token}"
    email_service.send_password_reset_email(
        to_email=user.email,
        username=user.username,
        reset_link=reset_link,
        expiration_hours=config.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
        language=user.current_language,
        initiated_by_support=True,
    )

    return {
        "message": "Password reset email has been sent",
        "expires_in_hours": config.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
    }


@router.put("/{user_id}/otp-reset")
async def support_reset_user_otp(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Start OTP reset process for a user (support/admin only)
    """
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user, token_entry, error = OTPResetService.start_support_otp_reset(
        db=db,
        user_id=user_id,
    )
    if error or not user or not token_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not start OTP reset",
        )

    reset_link = f"{config.FRONTEND_URL}/auth/otp-reset/confirm/{token_entry.token}"
    email_service.send_otp_reset_email(
        to_email=user.email,
        username=user.username,
        reset_link=reset_link,
        expiration_hours=config.SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS,
        language=user.current_language,
        initiated_by_support=True,
    )

    return {
        "message": "OTP reset email has been sent",
        "expires_in_hours": config.SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS,
    }


# ========================
# User Role Management
# ========================

@router.get("/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: str,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all roles assigned to a user (support/admin only)
    """
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    # Verify user exists
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    roles = UserService.get_user_roles(db, user_id, include_inactive=include_inactive)
    
    return [UserRoleResponse(**role) for role in roles]


@router.post("/{user_id}/roles", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: str,
    request: UserRoleAssignRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Assign a role to a user (support/admin only)
    Creates a new active role assignment
    """
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user_role, error = UserService.assign_role_to_user(
        db=db,
        user_id=user_id,
        role_id=str(request.role_id),
        assigned_by=str(current_user.id),
    )

    if error or not user_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Failed to assign role"
        )

    # Get full role information for response
    roles = UserService.get_user_roles(db, user_id, include_inactive=False)
    assigned_role = next((r for r in roles if str(r["user_role_id"]) == str(user_role.id)), None)
    
    if not assigned_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role assigned but could not retrieve details"
        )

    return UserRoleResponse(**assigned_role)


@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Remove a role from a user (support/admin only)
    Soft deletes the role assignment (sets active=False)
    Deleted role assignments cannot be reactivated
    """
    if not (current_user.has_role("support") or current_user.has_role("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    success, error = UserService.remove_role_from_user(
        db=db,
        user_id=user_id,
        role_id=role_id,
        removed_by=str(current_user.id),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Failed to remove role"
        )

    return {
        "message": "Role removed successfully",
        "user_id": user_id,
        "role_id": role_id,
    }
