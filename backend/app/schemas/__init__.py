"""
Pydantic schemas for request/response validation
"""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ========================
# User Schemas
# ========================

class UserBase(BaseModel):
    """Base user schema"""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    current_language: str = Field("en", max_length=2)
    corporate_number: Optional[str] = Field(None, max_length=255)


class UserRegisterRequest(BaseModel):
    """User registration request"""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    tos_agreed: bool = Field(..., description="Required for open registration; skipped in closed registration step 1")
    language: str = Field("en", max_length=2)


class UserCompleteRegistration(BaseModel):
    """Complete user registration with password"""

    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=10, max_length=60)
    password_confirm: str = Field(..., min_length=10, max_length=60)
    corporate_number: Optional[str] = Field(None, max_length=255)
    enable_otp: bool = Field(False)
    tos_agreed: bool = Field(False, description="ToS agreement required for admin-created registrations")
    current_language: str = Field("en", max_length=2)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets requirements:
        - 10-60 characters
        - Contains uppercase and lowercase
        - Contains digit or special character
        """
        if len(v) < 10 or len(v) > 60:
            raise ValueError("Password must be between 10 and 60 characters")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(not c.isalnum() for c in v)
        
        if not (has_upper and has_lower):
            raise ValueError("Password must contain both uppercase and lowercase letters")
        
        if not (has_digit or has_special):
            raise ValueError("Password must contain at least one digit or special character")
        
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserLoginRequest(BaseModel):
    """User login request"""

    username: str
    password: str
    otp_code: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""

    id: UUID
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    current_language: str
    corporate_number: Optional[str]
    corporate_approved: bool
    otp_enabled: bool
    active: bool
    created_on: datetime
    roles: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    """User login response"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegistrationInitiatedResponse(BaseModel):
    """Response after initiating registration"""

    message: str
    email: str


class RegistrationCompleteResponse(BaseModel):
    """Response after completing registration"""

    message: str
    user: UserResponse
    otp_setup: Optional[dict] = None


class UserDetailResponse(UserResponse):
    """Detailed user response with permissions"""

    permissions: List[str] = []


class UserUpdateRequest(BaseModel):
    """Update user profile"""

    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    current_language: Optional[str] = Field(None, max_length=2)


class PasswordChangeRequest(BaseModel):
    """Change password request"""

    current_password: str
    new_password: str = Field(..., min_length=10, max_length=60)
    new_password_confirm: str = Field(..., min_length=10, max_length=60)

    @field_validator("new_password_confirm")
    @classmethod
    def validate_passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordResetRequest(BaseModel):
    """Request password reset"""

    username: str = Field(..., min_length=3, max_length=255)


class PasswordResetConfirmRequest(BaseModel):
    """Confirm password reset"""

    new_password: str = Field(..., min_length=10, max_length=60)
    new_password_confirm: str = Field(..., min_length=10, max_length=60)

    @field_validator("new_password_confirm")
    @classmethod
    def validate_passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class EmailChangeRequest(BaseModel):
    """Request email change"""

    new_email: EmailStr


class EmailChangeConfirmRequest(BaseModel):
    """Confirm email change with verification code"""

    verification_code: str = Field(..., min_length=6, max_length=6)


class OTPEnableRequest(BaseModel):
    """Request to enable OTP"""

    otp_code: str = Field(..., min_length=6, max_length=6)


class OTPResetConfirmRequest(BaseModel):
    """Confirm OTP reset with temporary token"""

    token: str = Field(..., min_length=20, max_length=255)
    otp_code: str = Field(..., min_length=6, max_length=6)


# ========================
# Role Schemas
# ========================

class RoleBase(BaseModel):
    """Base role schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class RoleResponse(RoleBase):
    """Role response schema"""

    id: UUID
    active: bool
    created_on: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignRequest(BaseModel):
    """Request to assign a role to a user"""

    role_id: UUID = Field(..., description="ID of the role to assign")


class UserRoleResponse(BaseModel):
    """User role assignment response"""

    user_role_id: UUID
    role_id: UUID
    role_name: str
    role_description: Optional[str]
    assigned_on: datetime
    assigned_by: Optional[UUID]
    active: bool
    removed_on: Optional[datetime] = None
    removed_by: Optional[UUID] = None


# ========================
# Permission Schemas
# ========================

class PermissionBase(BaseModel):
    """Base permission schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class PermissionResponse(PermissionBase):
    """Permission response schema"""

    id: UUID
    active: bool
    created_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ========================
# User Management (Support/Admin)
# ========================

class UserListResponse(BaseModel):
    """User list item for support/admin"""

    id: UUID
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    corporate_number: Optional[str]
    corporate_approved: bool
    otp_enabled: bool
    active: bool


class UserDetailSupportResponse(UserListResponse):
    """Detailed user response for support/admin"""

    created_on: datetime
    last_modified_on: Optional[datetime]
    unsuccessful_logins: int
    timestamp_last_successful_login: Optional[datetime]


class UserUpdateSupportRequest(BaseModel):
    """Update user as support/admin"""

    corporate_number: Optional[str] = Field(None, max_length=255)
    corporate_approved: Optional[bool] = None
    active: Optional[bool] = None


# ========================
# Page Schemas
# ========================

class PageBase(BaseModel):
    """Base page schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    page: Optional[str] = Field(None, description="Page text content")
    comment: Optional[str] = Field(None)
    record_id: UUID
    restriction_id: UUID


class PageCreate(BaseModel):
    """Create page request (file uploaded separately)"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    page: Optional[str] = Field(None, description="Page text content")
    comment: Optional[str] = Field(None)
    record_id: UUID
    restriction_id: UUID


class PageUpdate(BaseModel):
    """Update page request"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    page: Optional[str] = Field(None, description="Page text content")
    comment: Optional[str] = Field(None)
    restriction_id: Optional[UUID] = None


class PageResponse(PageBase):
    """Page response schema"""

    id: UUID
    location_file: Optional[str]
    location_thumbnail: Optional[str]
    location_file_watermark: Optional[str]
    workstatus_id: Optional[UUID]
    active: bool
    created_on: datetime
    created_by: Optional[UUID]
    last_modified_on: Optional[datetime]
    last_modified_by: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class PageListResponse(BaseModel):
    """Page list item for overview"""

    id: UUID
    name: str
    description: Optional[str]
    page: Optional[str]
    comment: Optional[str]
    restriction_id: UUID
    created_on: datetime


class PageListDetailResponse(PageListResponse):
    """Detailed page list response"""

    location_file: Optional[str]
    active: bool


# ========================
# Generic Schemas
# ========================

class PaginatedResponse(BaseModel):
    """Generic paginated response"""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[dict]


class ErrorResponse(BaseModel):
    """Error response"""

    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response"""

    message: str
    data: Optional[dict] = None


# Export all schemas
__all__ = [
    "UserRegisterRequest",
    "UserCompleteRegistration",
    "UserLoginRequest",
    "UserLoginResponse",
    "UserResponse",
    "UserDetailResponse",
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "EmailChangeRequest",
    "EmailChangeConfirmRequest",
    "OTPEnableRequest",
    "OTPResetConfirmRequest",
    "RoleBase",
    "RoleResponse",
    "UserRoleAssignRequest",
    "UserRoleResponse",
    "PermissionBase",
    "PermissionResponse",
    "UserListResponse",
    "UserDetailSupportResponse",
    "UserUpdateSupportRequest",
    "PageBase",
    "PageCreate",
    "PageUpdate",
    "PageResponse",
    "PageListResponse",
    "PageListDetailResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
