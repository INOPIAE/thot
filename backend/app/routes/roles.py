"""
Role routes for role management (admin only)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.role import Role
from app.utils import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)

security = HTTPBearer()


async def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from JWT token
    """
    from app.services.user_service import UserService
    
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


# Pydantic schemas
class RoleResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class RoleCreateRequest(BaseModel):
    name: str
    description: str | None = None


class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    List all roles (admin only)
    """
    # Check if user has admin role
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    roles = db.query(Role).all()
    
    return [
        RoleResponse(
            id=str(r.id),
            name=r.name,
            description=r.description,
            active=r.active,
        )
        for r in roles
    ]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get role by ID (admin only)
    """
    # Check if user has admin role
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    try:
        role_uuid = uuid.UUID(role_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format",
        )

    role = db.query(Role).filter(Role.id == role_uuid).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        active=role.active,
    )


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new role (admin only)
    """
    # Check if user has admin role
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    # Check if role name already exists
    existing_role = db.query(Role).filter(Role.name == request.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )

    # Create new role
    role = Role(
        name=request.name,
        description=request.description,
        created_by=current_user.id,
        last_modified_by=current_user.id,
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        active=role.active,
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update an existing role (admin only)
    """
    # Check if user has admin role
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    try:
        role_uuid = uuid.UUID(role_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format",
        )

    role = db.query(Role).filter(Role.id == role_uuid).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if new name conflicts with another role
    if request.name and request.name != role.name:
        existing_role = db.query(Role).filter(Role.name == request.name).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )
        role.name = request.name

    if request.description is not None:
        role.description = request.description

    if request.active is not None:
        role.active = request.active

    role.last_modified_by = current_user.id

    db.commit()
    db.refresh(role)

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        active=role.active,
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Delete a role (soft delete - admin only)
    """
    # Check if user has admin role
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    try:
        role_uuid = uuid.UUID(role_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format",
        )

    role = db.query(Role).filter(Role.id == role_uuid).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if role is a system role (admin, support, user)
    if role.name in ["admin", "support", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles"
        )

    # Soft delete
    role.active = False
    role.last_modified_by = current_user.id

    db.commit()

    return None
