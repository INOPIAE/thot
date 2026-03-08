"""
User service for business logic
"""

from datetime import datetime, timedelta
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
            created_on=datetime.utcnow(),
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

        # Check grace period
        if user.unsuccessful_logins >= 3:
            if user.timestamp_last_successful_login:
                grace_period_minutes = (
                    config.GRACE_PERIOD_MINUTES_5_ATTEMPTS
                    if user.unsuccessful_logins >= 5
                    else config.GRACE_PERIOD_MINUTES_3_ATTEMPTS
                )
                grace_until = user.timestamp_last_successful_login + timedelta(
                    minutes=grace_period_minutes
                )
                if datetime.utcnow() < grace_until:
                    return None, "Login temporarily locked. Please try again later"

        # Verify password
        if not verify_password(password, user.hashed_password):
            user.unsuccessful_logins += 1
            # Update timestamp on first unsuccessful attempt
            if user.unsuccessful_logins == 1:
                user.timestamp_last_successful_login = datetime.utcnow()
            db.commit()
            return None, "Invalid username or password"

        # Successful login
        user.unsuccessful_logins = 0
        user.timestamp_last_successful_login = datetime.utcnow()
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

        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id

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
        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id
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
        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id
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
        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id
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
        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id
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
        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = user_id
        db.commit()
        return True

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        filter_username: Optional[str] = None,
        filter_email: Optional[str] = None,
    ) -> Tuple[List[User], int]:
        """List users with optional filters and pagination"""
        query = db.query(User)

        if filter_username:
            query = query.filter(User.username.ilike(f"%{filter_username}%"))
        if filter_email:
            query = query.filter(User.email.ilike(f"%{filter_email}%"))

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

        user.last_modified_on = datetime.utcnow()
        user.last_modified_by = admin_id
        db.commit()
        db.refresh(user)
        return user
