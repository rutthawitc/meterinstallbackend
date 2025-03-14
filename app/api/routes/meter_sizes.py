"""
Meter Size management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.models.meter_size import MeterSize
from app.schemas.meter_size import (
    MeterSizeCreate, 
    MeterSizeUpdate, 
    MeterSize as MeterSizeSchema
)

router = APIRouter()


@router.get("/", response_model=List[MeterSizeSchema])
async def get_meter_sizes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in code or name"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve meter sizes.
    """
    query = db.query(MeterSize)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (MeterSize.code.ilike(search_term))
            | (MeterSize.name.ilike(search_term))
        )
    
    meter_sizes = query.offset(skip).limit(limit).all()
    return meter_sizes


@router.post("/", response_model=MeterSizeSchema)
async def create_meter_size(
    meter_size_in: MeterSizeCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new meter size. Requires admin or manager role.
    """
    # Check if meter size with this code already exists
    db_meter_size = db.query(MeterSize).filter(MeterSize.code == meter_size_in.code).first()
    if db_meter_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meter size with this code already exists",
        )
    
    # Create new meter size
    try:
        meter_size = MeterSize(
            code=meter_size_in.code,
            name=meter_size_in.name,
            description=meter_size_in.description,
        )
        db.add(meter_size)
        db.commit()
        db.refresh(meter_size)
        return meter_size
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating meter size",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{meter_size_id}", response_model=MeterSizeSchema)
async def get_meter_size(
    meter_size_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific meter size by id.
    """
    meter_size = db.query(MeterSize).filter(MeterSize.id == meter_size_id).first()
    if not meter_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter size not found",
        )
    return meter_size


@router.put("/{meter_size_id}", response_model=MeterSizeSchema)
async def update_meter_size(
    meter_size_id: int,
    meter_size_in: MeterSizeUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a meter size. Requires admin or manager role.
    """
    meter_size = db.query(MeterSize).filter(MeterSize.id == meter_size_id).first()
    if not meter_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter size not found",
        )
    
    # Check if code is being updated and if the new code already exists
    if meter_size_in.code and meter_size_in.code != meter_size.code:
        db_meter_size = db.query(MeterSize).filter(MeterSize.code == meter_size_in.code).first()
        if db_meter_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meter size with this code already exists",
            )
    
    # Update meter size fields
    update_data = meter_size_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meter_size, field, value)
    
    try:
        db.commit()
        db.refresh(meter_size)
        return meter_size
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating meter size",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{meter_size_id}", response_model=MeterSizeSchema)
async def delete_meter_size(
    meter_size_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a meter size. Requires admin role.
    """
    meter_size = db.query(MeterSize).filter(MeterSize.id == meter_size_id).first()
    if not meter_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter size not found",
        )
    
    # Check if the meter size is used in requests
    if meter_size.installation_requests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete meter size that is in use",
        )
    
    try:
        db.delete(meter_size)
        db.commit()
        return meter_size
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) 