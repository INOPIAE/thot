"""
User service for business logic
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging

from app.models import User, Role, UserRole, Permission
from app.utils import (
    hash_password,
    verify_password,
    validate_password_requirements,
    generate_otp_secret,
)
from config import config

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related operations"""

    @staticmethod
    def _normalize_to_utc(value: Optional[datetime]) -> Optional[datetime]:
        """Normalize datetimes to timezone-aware UTC for safe comparisons."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        current_language: str = "en",
        is_first_user: bool = False,
    ) -> User:
        """
        Create a new user
        First user gets admin role, others get user role
        """
        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            current_language=current_language,
            created_on=datetime.now(timezone.utc),
        )

        db.add(user)
        db.flush()

        # Assign role
        if is_first_user:
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role:
                user_role = UserRole(user_id=user.id, role_id=admin_role.id)
                db.add(user_role)
        else:
            user_role = db.query(Role).filter(Role.name == "user").first()
            if user_role:
                user_role_entry = UserRole(user_id=user.id, role_id=user_role.id)
                db.add(user_role_entry)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            return None
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def authenticate_user(
        db: Session, username: str, password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user by username and password
        Returns: (user, error_message)
        """
        user = UserService.get_user_by_username(db, username)

        if not user:
            return None, "Invalid username or password"

        if not user.active:
            return None, "User account is locked"

        # Check grace period based on configured attempt thresholds.
        if user.timestamp_last_successful_login:
            last_login_utc = UserService._normalize_to_utc(
                user.timestamp_last_successful_login
            )
            grace_period_minutes = config.get_grace_period_minutes_for_attempts(
                user.unsuccessful_logins
            )
            if grace_period_minutes > 0 and last_login_utc is not None:
                grace_until = last_login_utc + timedelta(
                    minutes=grace_period_minutes
                )
                if datetime.now(timezone.utc) < grace_until:
                                                                                     
                    return None, "Login temporarily locked. Please try again later"

        # Verify password
        if not verify_password(password, user.hashed_password):
            user.unsuccessful_logins += 1
            # Update timestamp on first unsuccessful attempt
            if user.unsuccessful_logins == 1:
                user.timestamp_last_successful_login = datetime.now(timezone.utc)
            grace_period_minutes = config.get_grace_period_minutes_for_attempts(
                user.unsuccessful_logins
            )
            db.commit()
            if grace_period_minutes > 0:
                return None, "Login temporarily locked. Please try again later"
            return None, "Invalid username or password"

        # Successful login
        user.unsuccessful_logins = 0
        user.timestamp_last_successful_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user, ""

    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        current_language: Optional[str] = None,
    ) -> User:
        """Update user profile information"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if current_language is not None:
            user.current_language = current_language

        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(
        db: Session, user_id: str, current_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False, "User not found"

        if not verify_password(current_password, user.hashed_password):
            return False, "Current password is incorrect"

        is_valid, error_msg = validate_password_requirements(new_password)
        if not is_valid:
            return False, error_msg

        user.hashed_password = hash_password(new_password)
        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        return True, "Password changed successfully"

    @staticmethod
    def reset_password(db: Session, user_id: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password (without current password verification)"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False, "User not found"

        is_valid, error_msg = validate_password_requirements(new_password)
        if not is_valid:
            return False, error_msg

        user.hashed_password = hash_password(new_password)
        user.unsuccessful_logins = 0
        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        return True, "Password reset successfully"

    @staticmethod
    def update_email(db: Session, user_id: str, new_email: str) -> Tuple[bool, str]:
        """Update user email"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False, "User not found"

        # Check if email already exists
        existing_user = UserService.get_user_by_email(db, new_email)
        if existing_user and existing_user.id != user.id:
            return False, "Email already in use"

        user.email = new_email
        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        return True, "Email updated successfully"

    @staticmethod
    def enable_otp(db: Session, user_id: str) -> str:
        """Enable OTP for user and return secret"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        secret = generate_otp_secret()
        user.otp_secret = secret
        user.otp_enabled = True
        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        return secret

    @staticmethod
    def disable_otp(db: Session, user_id: str) -> bool:
        """Disable OTP for user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.otp_secret = None
        user.otp_enabled = False
        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        return True


    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        filter_username: Optional[str] = None,
        filter_email: Optional[str] = None,
        active_only: bool = True,
    ) -> Tuple[List[User], int]:
        """List users with optional filters and pagination
        If active_only is True, only users with active=True are returned.
        """
        query = db.query(User)

        if filter_username:
            query = query.filter(User.username.ilike(f"%{filter_username}%"))
        if filter_email:
            query = query.filter(User.email.ilike(f"%{filter_email}%"))
        if active_only:
            query = query.filter(User.active == True)

        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    @staticmethod
    def update_user_as_support(
        db: Session,
        user_id: str,
        admin_id: str,
        corporate_number: Optional[str] = None,
        corporate_approved: Optional[bool] = None,
        active: Optional[bool] = None,
    ) -> User:
        """Update user account as support/admin"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        if corporate_number is not None:
            user.corporate_number = corporate_number
        if corporate_approved is not None:
            user.corporate_approved = corporate_approved
        if active is not None:
            user.active = active

        user.last_modified_on = datetime.now(timezone.utc)
        try:
            user.last_modified_by = uuid.UUID(admin_id) if isinstance(admin_id, str) else admin_id
        except (ValueError, AttributeError):
            user.last_modified_by = None
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_roles(db: Session, user_id: str, include_inactive: bool = False) -> List[dict]:
        """
        Get all roles assigned to a user
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive (deleted) role assignments
        Returns:
            List of dicts with role info and assignment metadata
        """
        try:
            user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            return []
        
        query = db.query(UserRole).filter(UserRole.user_id == user_id_uuid)
        
        if not include_inactive:
            query = query.filter(UserRole.active == True)
        
        user_roles = query.all()
        
        result = []
        for ur in user_roles:
            result.append({
                "user_role_id": ur.id,
                "role_id": ur.role.id,
                "role_name": ur.role.name,
                "role_description": ur.role.description,
                "assigned_on": ur.created_on,
                "assigned_by": ur.created_by,
                "active": ur.active,
                "removed_on": ur.last_modified_on if not ur.active else None,
                "removed_by": ur.last_modified_by if not ur.active else None,
            })
        
        return result

    @staticmethod
    def assign_role_to_user(
        db: Session,
        user_id: str,
        role_id: str,
        assigned_by: str,
    ) -> Tuple[Optional[UserRole], Optional[str]]:
        """
        Assign a role to a user
        Creates a new UserRole entry with active=True
        Args:
            user_id: User ID to assign role to
            role_id: Role ID to assign
            assigned_by: Admin/Support user ID performing the assignment
        Returns:
            (UserRole, error_message)
        """
        # Convert string UUIDs to UUID objects
        try:
            user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            role_id_uuid = uuid.UUID(role_id) if isinstance(role_id, str) else role_id
            assigned_by_uuid = uuid.UUID(assigned_by) if isinstance(assigned_by, str) else assigned_by
        except (ValueError, AttributeError):
            return None, "Invalid UUID format"
        
        # Check if user exists
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None, "User not found"
        
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id_uuid).first()
        if not role:
            return None, "Role not found"
        
        if not role.active:
            return None, "Role is not active"

        # OTP-Prüfung für support/admin (außer erster User)
        if role.name in ("support", "admin"):
            # Erster User: hat nur eine Zeile in users
            user_count = db.query(User).count()
            if user_count > 1 and not user.otp_enabled:
                return None, "User must have OTP enabled to be assigned support/admin role"
        
        # Check if there's already an active assignment
        existing_active = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id_uuid,
                UserRole.role_id == role_id_uuid,
                UserRole.active == True
            )
        ).first()
        
        if existing_active:
            return None, "User already has this role assigned"

        # Prevent reactivation via new row creation if role was removed before.
        existing_inactive = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id_uuid,
                UserRole.role_id == role_id_uuid,
                UserRole.active == False
            )
        ).first()
        if existing_inactive:
            return None, "Role assignment was previously removed and cannot be reactivated"
        
        # Create new role assignment
        user_role = UserRole(
            id=uuid.uuid4(),
            user_id=user_id_uuid,
            role_id=role_id_uuid,
            created_by=assigned_by_uuid,
            created_on=datetime.now(timezone.utc),
            active=True,
        )
        
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        
        return user_role, None

    @staticmethod
    def remove_role_from_user(
        db: Session,
        user_id: str,
        role_id: str,
        removed_by: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove a role from a user (soft delete - sets active=False)
        Once removed, the entry cannot be reactivated
        Args:
            user_id: User ID
            role_id: Role ID to remove
            removed_by: Admin/Support user ID performing the removal
        Returns:
            (success, error_message)
        """
        # Convert string UUIDs to UUID objects
        try:
            user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            role_id_uuid = uuid.UUID(role_id) if isinstance(role_id, str) else role_id
            removed_by_uuid = uuid.UUID(removed_by) if isinstance(removed_by, str) else removed_by
        except (ValueError, AttributeError):
            return False, "Invalid UUID format"
        
        # Find active role assignment
        user_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id_uuid,
                UserRole.role_id == role_id_uuid,
                UserRole.active == True
            )
        ).first()
        
        if not user_role:
            return False, "User does not have this active role assignment"
        
        # Soft delete - set active to False and record who removed it
        user_role.active = False
        user_role.last_modified_by = removed_by_uuid
        user_role.last_modified_on = datetime.now(timezone.utc)
        
        db.commit()
        
        return True, None
