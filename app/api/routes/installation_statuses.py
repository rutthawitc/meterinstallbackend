"""
Installation Status management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.models.installation_status import InstallationStatus
from app.schemas.installation_status import (
    InstallationStatusCreate, 
    InstallationStatusUpdate, 
    InstallationStatus as InstallationStatusSchema
)

router = APIRouter()


@router.get("/", response_model=List[InstallationStatusSchema])
async def get_installation_statuses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in code or name"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve installation statuses.
    """
    query = db.query(InstallationStatus)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (InstallationStatus.code.ilike(search_term))
            | (InstallationStatus.name.ilike(search_term))
        )
    
    statuses = query.offset(skip).limit(limit).all()
    return statuses


@router.post("/", response_model=InstallationStatusSchema)
async def create_installation_status(
    status_in: InstallationStatusCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new installation status. Requires admin or manager role.
    """
    # Check if installation status with this code already exists
    db_status = db.query(InstallationStatus).filter(InstallationStatus.code == status_in.code).first()
    if db_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installation status with this code already exists",
        )
    
    # Create new installation status
    try:
        installation_status = InstallationStatus(
            code=status_in.code,
            name=status_in.name,
            description=status_in.description,
        )
        db.add(installation_status)
        db.commit()
        db.refresh(installation_status)
        return installation_status
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating installation status",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{status_id}", response_model=InstallationStatusSchema)
async def get_installation_status(
    status_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific installation status by id.
    """
    installation_status = db.query(InstallationStatus).filter(InstallationStatus.id == status_id).first()
    if not installation_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation status not found",
        )
    return installation_status


@router.put("/{status_id}", response_model=InstallationStatusSchema)
async def update_installation_status(
    status_id: int,
    status_in: InstallationStatusUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update an installation status. Requires admin or manager role.
    """
    installation_status = db.query(InstallationStatus).filter(InstallationStatus.id == status_id).first()
    if not installation_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation status not found",
        )
    
    # Check if code is being updated and if the new code already exists
    if status_in.code and status_in.code != installation_status.code:
        db_status = db.query(InstallationStatus).filter(InstallationStatus.code == status_in.code).first()
        if db_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Installation status with this code already exists",
            )
    
    # Update installation status fields
    update_data = status_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(installation_status, field, value)
    
    try:
        db.commit()
        db.refresh(installation_status)
        return installation_status
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating installation status",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{status_id}", response_model=InstallationStatusSchema)
async def delete_installation_status(
    status_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete an installation status. Requires admin role.
    """
    installation_status = db.query(InstallationStatus).filter(InstallationStatus.id == status_id).first()
    if not installation_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation status not found",
        )
    
    # Check if the status is used in requests or logs
    if installation_status.installation_requests or installation_status.installation_logs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete installation status that is in use",
        )
    
    try:
        db.delete(installation_status)
        db.commit()
        return installation_status
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) 