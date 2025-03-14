"""
Installation Type management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.models.installation_type import InstallationType
from app.schemas.installation_type import (
    InstallationTypeCreate, 
    InstallationTypeUpdate, 
    InstallationType as InstallationTypeSchema
)

router = APIRouter()


@router.get("/", response_model=List[InstallationTypeSchema])
async def get_installation_types(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in code or name"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve installation types.
    """
    query = db.query(InstallationType)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (InstallationType.code.ilike(search_term))
            | (InstallationType.name.ilike(search_term))
        )
    
    types = query.offset(skip).limit(limit).all()
    return types


@router.post("/", response_model=InstallationTypeSchema)
async def create_installation_type(
    type_in: InstallationTypeCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new installation type. Requires admin or manager role.
    """
    # Check if installation type with this code already exists
    db_type = db.query(InstallationType).filter(InstallationType.code == type_in.code).first()
    if db_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installation type with this code already exists",
        )
    
    # Create new installation type
    try:
        installation_type = InstallationType(
            code=type_in.code,
            name=type_in.name,
            description=type_in.description,
        )
        db.add(installation_type)
        db.commit()
        db.refresh(installation_type)
        return installation_type
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating installation type",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{type_id}", response_model=InstallationTypeSchema)
async def get_installation_type(
    type_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific installation type by id.
    """
    installation_type = db.query(InstallationType).filter(InstallationType.id == type_id).first()
    if not installation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation type not found",
        )
    return installation_type


@router.put("/{type_id}", response_model=InstallationTypeSchema)
async def update_installation_type(
    type_id: int,
    type_in: InstallationTypeUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update an installation type. Requires admin or manager role.
    """
    installation_type = db.query(InstallationType).filter(InstallationType.id == type_id).first()
    if not installation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation type not found",
        )
    
    # Check if code is being updated and if the new code already exists
    if type_in.code and type_in.code != installation_type.code:
        db_type = db.query(InstallationType).filter(InstallationType.code == type_in.code).first()
        if db_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Installation type with this code already exists",
            )
    
    # Update installation type fields
    update_data = type_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(installation_type, field, value)
    
    try:
        db.commit()
        db.refresh(installation_type)
        return installation_type
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating installation type",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{type_id}", response_model=InstallationTypeSchema)
async def delete_installation_type(
    type_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete an installation type. Requires admin role.
    """
    installation_type = db.query(InstallationType).filter(InstallationType.id == type_id).first()
    if not installation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation type not found",
        )
    
    # Check if the type is used in requests
    if installation_type.installation_requests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete installation type that is in use",
        )
    
    try:
        db.delete(installation_type)
        db.commit()
        return installation_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) 