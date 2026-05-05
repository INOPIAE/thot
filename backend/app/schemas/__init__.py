"""
Pydantic schemas for request/response validation
"""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
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

    username: str = Field(..., min_length=5, max_length=255)
    email: EmailStr
    tos_agreed: bool = Field(..., description="Required for open registration; skipped in closed registration step 1")
    language: str = Field("en", max_length=2)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        username = v.strip()
        if len(username) < 5:
            raise ValueError("Username must be at least 5 characters")
        return username


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
    orgin_file: Optional[str]
    location_file: Optional[str]
    current_file: Optional[str]
    restriction_file: Optional[str]
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

    orgin_file: Optional[str]
    location_file: Optional[str]
    current_file: Optional[str]
    restriction_file: Optional[str]
    active: bool


# ========================
# Record Metadata Schemas (Lookup Tables)
# ========================

class LoanTypeResponse(BaseModel):
    """Loan type response schema"""

    id: UUID
    loan: str
    subtype: Optional[str] = None
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoanTypeCreate(BaseModel):
    """Create loan type request"""

    loan: str = Field(..., min_length=1, max_length=255)
    subtype: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = Field(None)


class LanguageResponse(BaseModel):
    """Language response schema"""

    id: UUID
    language: str

    model_config = ConfigDict(from_attributes=True)


class LanguageCreate(BaseModel):
    """Create language request"""

    language: str = Field(..., min_length=1, max_length=255)


class AuthorTypeResponse(BaseModel):
    """Author type response schema"""

    id: UUID
    authortype: str

    model_config = ConfigDict(from_attributes=True)


class AuthorTypeCreate(BaseModel):
    """Create author type request"""

    authortype: str = Field(..., min_length=1, max_length=255)


class AuthorResponse(BaseModel):
    """Author response schema"""

    id: UUID
    first_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuthorCreate(BaseModel):
    """Create author request"""

    first_name: Optional[str] = Field(None, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=100)


class AuthorUpdate(BaseModel):
    """Update author request"""

    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=100)


class PublisherResponse(BaseModel):
    """Publisher response schema"""

    id: UUID
    companyname: str
    town: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PublisherCreate(BaseModel):
    """Create publisher request"""

    companyname: str = Field(..., min_length=1, max_length=255)
    town: Optional[str] = Field(None, max_length=255)


class PublisherUpdate(BaseModel):
    """Update publisher request"""

    companyname: Optional[str] = Field(None, min_length=1, max_length=255)
    town: Optional[str] = Field(None, max_length=255)


class PublicationTypeResponse(BaseModel):
    """Publication type response schema"""

    id: UUID
    publicationtype: str

    model_config = ConfigDict(from_attributes=True)


class PublicationTypeCreate(BaseModel):
    """Create publication type request"""

    publicationtype: str = Field(..., min_length=1, max_length=255)


class RecordConditionResponse(BaseModel):
    """Record condition response schema"""

    id: UUID
    condition: str

    model_config = ConfigDict(from_attributes=True)


class RecordConditionCreate(BaseModel):
    """Create record condition request"""

    condition: str = Field(..., min_length=1, max_length=255)


class LetteringResponse(BaseModel):
    """Lettering response schema"""

    id: UUID
    lettering: str

    model_config = ConfigDict(from_attributes=True)


class LetteringCreate(BaseModel):
    """Create lettering request"""

    lettering: str = Field(..., min_length=1, max_length=255)


class KeywordRecordResponse(BaseModel):
    """Keyword record response schema (bibliographic keyword with phonetic codes)"""

    id: UUID
    name: str
    c_search: Optional[str] = None  # Cologne Phonetic
    dblmeta_1: Optional[str] = None  # Double Metaphone primary
    dblmeta_2: Optional[str] = None  # Double Metaphone secondary

    model_config = ConfigDict(from_attributes=True)


class KeywordRecordCreate(BaseModel):
    """Create keyword record request"""

    name: str = Field(..., min_length=1, max_length=255)


# ========================
# Record Author (Junction) Schemas
# ========================

class RecordAuthorCreate(BaseModel):
    """Create record author request"""

    author_id: UUID = Field(..., description="ID of the author")
    authortype_id: Optional[UUID] = Field(None, description="ID of the author type (role)")
    order: Optional[int] = Field(default=0, description="Order of author in list")


class RecordAuthorResponse(BaseModel):
    """Record author response with nested author and authortype details"""

    id: UUID
    record_id: UUID
    author_id: UUID
    authortype_id: Optional[UUID] = None
    order: Optional[int] = None
    author: Optional[AuthorResponse] = None
    authortype: Optional[AuthorTypeResponse] = None
    created_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ========================
# Record Schemas (Main Table)
# ========================

class RecordBase(BaseModel):
    """Base record schema with core fields"""

    title: str = Field(..., min_length=1, max_length=255, description="Record title (required)")
    signature: Optional[str] = Field(None, max_length=255, description="Primary signature/call number")
    signature2: Optional[str] = Field(None, max_length=255, description="Secondary signature")
    subtitle: Optional[str] = Field(None, max_length=500, description="Record subtitle")
    description: Optional[str] = Field(None, description="General description")
    comment: Optional[str] = Field(None, description="Internal comment")
    nlf_fdb: bool = Field(False, description="NLF FDB flag")
    pers_count: Optional[int] = Field(None, description="Person count")


class RecordBibliographicFields(BaseModel):
    """Bibliographic fields for records"""

    year: Optional[str] = Field(None, max_length=50, description="Publication year")
    isbn: Optional[str] = Field(None, max_length=50, description="ISBN number")
    number_pages: Optional[str] = Field(None, max_length=50, description="Number of pages")
    edition: Optional[str] = Field(None, max_length=100, description="Edition information")
    reihe: Optional[str] = Field(None, max_length=255, description="Series name (Reihe)")
    volume: Optional[str] = Field(None, max_length=100, description="Volume number")
    jahrgang: Optional[str] = Field(None, max_length=100, description="Year/issue number (Jahrgang)")
    bibl_nr: Optional[str] = Field(None, max_length=100, description="Bibliography number")
    enter_information: Optional[str] = Field(None, description="Information about entry/addition to collection")
    indecies: Optional[str] = Field(None, description="Index information")
    enter_date: Optional[date] = Field(None, description="Date when record was entered (YYYY-MM-DD)")
    sort_out_date: Optional[date] = Field(None, description="Date when record was sorted out (YYYY-MM-DD)")


class RecordMetadataReferences(BaseModel):
    """Foreign key references for record metadata"""

    restriction_id: UUID = Field(..., description="ID of the restriction level")
    workstatus_id: UUID = Field(..., description="ID of the work status")
    record_condition_id: Optional[UUID] = Field(None, description="ID of the record condition")
    loantype_id: Optional[UUID] = Field(None, description="ID of the loan type")
    lettering_id: Optional[UUID] = Field(None, description="ID of the lettering type")
    publicationtype_id: Optional[UUID] = Field(None, description="ID of the publication type")
    publisher_id: Optional[UUID] = Field(None, description="ID of the publisher")


class RecordCreate(RecordBase, RecordBibliographicFields, RecordMetadataReferences):
    """Create record request with all bibliographic fields"""

    pass


class RecordCreateRequest(RecordCreate):
    """Create record request including legacy keyword text fields"""

    keywords_names: Optional[str] = Field(None, description="Comma-separated name keywords")
    keywords_locations: Optional[str] = Field(None, description="Comma-separated location keywords")
    record_authors: Optional[List[RecordAuthorCreate]] = Field(None, description="Record-author assignments")


class RecordUpdate(BaseModel):
    """Update record request - all fields optional"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    signature: Optional[str] = Field(None, max_length=255)
    signature2: Optional[str] = Field(None, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    comment: Optional[str] = None
    year: Optional[str] = Field(None, max_length=50)
    isbn: Optional[str] = Field(None, max_length=50)
    number_pages: Optional[str] = Field(None, max_length=50)
    edition: Optional[str] = Field(None, max_length=100)
    reihe: Optional[str] = Field(None, max_length=255)
    volume: Optional[str] = Field(None, max_length=100)
    jahrgang: Optional[str] = Field(None, max_length=100)
    bibl_nr: Optional[str] = Field(None, max_length=100)
    enter_information: Optional[str] = None
    indecies: Optional[str] = None
    enter_date: Optional[date] = None
    sort_out_date: Optional[date] = None
    restriction_id: Optional[UUID] = None
    workstatus_id: Optional[UUID] = None
    record_condition_id: Optional[UUID] = None
    loantype_id: Optional[UUID] = None
    lettering_id: Optional[UUID] = None
    publicationtype_id: Optional[UUID] = None
    publisher_id: Optional[UUID] = None
    nlf_fdb: Optional[bool] = None
    pers_count: Optional[int] = None


class RecordUpdateRequest(RecordUpdate):
    """Update record request including legacy keyword text fields"""

    keywords_names: Optional[str] = None
    keywords_locations: Optional[str] = None
    record_authors: Optional[List[RecordAuthorCreate]] = None


class RecordResponse(RecordBase, RecordBibliographicFields):
    """Record response schema with basic metadata"""

    id: UUID
    restriction_id: UUID
    workstatus_id: UUID
    record_condition_id: Optional[UUID] = None
    loantype_id: Optional[UUID] = None
    lettering_id: Optional[UUID] = None
    publicationtype_id: Optional[UUID] = None
    publisher_id: Optional[UUID] = None
    nlf_fdb: bool
    pers_count: Optional[int] = None
    active: bool
    created_on: datetime
    created_by: Optional[UUID] = None
    last_modified_on: Optional[datetime] = None
    last_modified_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class RecordDetailResponse(RecordResponse):
    """Detailed record response with all relationships"""

    # Metadata objects (eager loaded)
    record_condition: Optional[RecordConditionResponse] = None
    loantype: Optional[LoanTypeResponse] = None
    lettering: Optional[LetteringResponse] = None
    publicationtype: Optional[PublicationTypeResponse] = None
    publisher: Optional[PublisherResponse] = None

    # Associations
    keywords_records: List[KeywordRecordResponse] = []
    languages: List[LanguageResponse] = []
    record_authors: List[RecordAuthorResponse] = []
    keywords_names: str = ""
    keywords_locations: str = ""


class RecordListItemResponse(BaseModel):
    """Record list item used in paginated list endpoint"""

    id: UUID
    title: str
    description: Optional[str] = None
    signature: Optional[str] = None
    comment: Optional[str] = None
    loantype: Optional[str] = None  # Name des Loantype (loan)
    loantype_subtype: Optional[str] = None  # Subtype, nur für admin/user_bibl
    restriction_id: UUID
    restriction: Optional[str] = None
    workstatus_id: UUID
    workstatus: Optional[str] = None
    keywords_names: str = ""
    keywords_locations: str = ""
    authors: str = ""
    publisher: str = ""
    created_on: Optional[datetime] = None
    created_by: Optional[UUID] = None
    entered_on: Optional[datetime] = None
    page_count: int = 0
    nlf_fdb: bool = False
    pers_count: Optional[int] = None


class RecordListResponse(BaseModel):
    """Paginated record list response"""

    items: List[RecordListItemResponse]
    total: int
    skip: int
    limit: int


class RecordReducedResponse(BaseModel):
    """Reduced record response used for selectors"""

    id: UUID
    name: str
    signature: Optional[str] = None


class RecordListDefaultItemResponse(BaseModel):
    """Record list item used in paginated list endpoint"""

    id: UUID
    title: str
    description: Optional[str] = None
    signature: Optional[str] = None
    comment: Optional[str] = None
    loantype: Optional[str] = None  # Name des Loantype (loan)
    keywords_names: str = ""
    keywords_locations: str = ""
    authors: str = ""
    publisher: str = ""
    page_count: int = 0
    nlf_fdb: bool = False
    pers_count: Optional[int] = None


class RecordListDefaultResponse(BaseModel):
    """Paginated record list response"""

    items: List[RecordListDefaultItemResponse]
    total: int
    skip: int
    limit: int


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
    # Record Metadata Schemas
    "LoanTypeResponse",
    "LoanTypeCreate",
    "LanguageResponse",
    "LanguageCreate",
    "AuthorTypeResponse",
    "AuthorTypeCreate",
    "AuthorResponse",
    "AuthorCreate",
    "AuthorUpdate",
    "PublisherResponse",
    "PublisherCreate",
    "PublisherUpdate",
    "PublicationTypeResponse",
    "PublicationTypeCreate",
    "RecordConditionResponse",
    "RecordConditionCreate",
    "LetteringResponse",
    "LetteringCreate",
    "KeywordRecordResponse",
    "KeywordRecordCreate",
    "RecordAuthorResponse",
    "RecordAuthorCreate",
    # Record Schemas
    "RecordBase",
    "RecordBibliographicFields",
    "RecordMetadataReferences",
    "RecordCreate",
    "RecordCreateRequest",
    "RecordUpdate",
    "RecordUpdateRequest",
    "RecordResponse",
    "RecordDetailResponse",
    "RecordListItemResponse",
    "RecordListResponse",
    "RecordReducedResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
