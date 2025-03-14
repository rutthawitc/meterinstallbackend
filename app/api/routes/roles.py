"""
API routes for role management.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.crud import roles as role_crud
from app.models.role import Role
from app.schemas.role import Role as RoleSchema
from app.schemas.role import RoleCreate, RoleUpdate, RoleWithUsers

router = APIRouter()


@router.get("/", response_model=List[RoleSchema])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in name or description"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve all roles.
    """
    roles = role_crud.get_roles(db, skip=skip, limit=limit, search=search)
    return roles


@router.post("/", response_model=RoleSchema)
async def create_role(
    role_in: RoleCreate,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new role.
    """
    # Check if a role with this name already exists
    role = role_crud.get_role_by_name(db, name=role_in.name)
    if role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_in.name}' already exists",
        )
    
    role = role_crud.create_role(db, obj_in=role_in)
    return role


@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get role by ID.
    """
    role = role_crud.get_role(db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.put("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a role.
    """
    role = role_crud.get_role(db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # If name is being updated, check it's not a duplicate
    if role_in.name and role_in.name != role.name:
        existing_role = role_crud.get_role_by_name(db, name=role_in.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_in.name}' already exists",
            )
    
    role = role_crud.update_role(db, db_obj=role, obj_in=role_in)
    return role


@router.delete("/{role_id}", response_model=RoleSchema)
async def delete_role(
    role_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a role.
    """
    role = role_crud.get_role(db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Check if this is a default role
    if role.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a default role",
        )
    
    # Check if the role has any users
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a role that is assigned to users",
        )
    
    role = role_crud.delete_role(db, id=role_id)
    return role


@router.get("/{role_id}/users", response_model=RoleWithUsers)
async def get_role_with_users(
    role_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(has_role(["admin", "manager"])),
) -> Any:
    """
    Get role with its users.
    """
    role = role_crud.get_role(db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return role 