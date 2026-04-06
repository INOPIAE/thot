"""
User model
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Boolean, UUID, Text
from sqlalchemy.orm import relationship

from app.database import Base
from .base import BaseModel


class User(BaseModel):
    """
    User model for authentication and user management
    """

    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    unsuccessful_logins = Column(Integer, default=0, nullable=False)
    timestamp_last_successful_login = Column(DateTime(timezone=True), nullable=True)
    current_language = Column(String(2), default="en", nullable=False)
    corporate_number = Column(String(255), nullable=True)
    corporate_approved = Column(Boolean, default=False, nullable=False)
    otp_secret = Column(String(255), nullable=True)
    otp_enabled = Column(Boolean, default=False, nullable=False)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    email_resets = relationship("UserEmailReset", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.active

    def is_locked(self) -> bool:
        """Check if user account is locked due to unsuccessful login attempts"""
        return not self.active

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(
            ur.role.name == role_name
            for ur in self.user_roles
            if ur.active and ur.role.active
        )

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through their roles"""
        for user_role in self.user_roles:
            if not user_role.active or not user_role.role.active:
                continue
            for role_perm in user_role.role.role_permissions:
                if role_perm.permission.name == permission_name and role_perm.permission.active:
                    return True
        return False

    def get_roles(self) -> list[str]:
        """Get list of role names for the user"""
        return [ur.role.name for ur in self.user_roles if ur.active and ur.role.active]

    def get_permissions(self) -> list[str]:
        """Get list of all permissions for the user"""
        permissions = set()
        for user_role in self.user_roles:
            if not user_role.active or not user_role.role.active:
                continue
            for role_perm in user_role.role.role_permissions:
                if role_perm.permission.active:
                    permissions.add(role_perm.permission.name)
        return list(permissions)
