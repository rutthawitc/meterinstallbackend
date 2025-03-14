"""
Region management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate, Region as RegionSchema

router = APIRouter()


@router.get("/", response_model=List[RegionSchema])
async def get_regions(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in code or name"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve regions.
    """
    query = db.query(Region)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Region.code.ilike(search_term))
            | (Region.name.ilike(search_term))
        )
    
    regions = query.offset(skip).limit(limit).all()
    return regions


@router.post("/", response_model=RegionSchema)
async def create_region(
    region_in: RegionCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new region. Requires admin or manager role.
    """
    # Check if region with this code already exists
    db_region = db.query(Region).filter(Region.code == region_in.code).first()
    if db_region:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region with this code already exists",
        )
    
    # Create new region
    try:
        region = Region(
            code=region_in.code,
            name=region_in.name,
        )
        db.add(region)
        db.commit()
        db.refresh(region)
        return region
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating region",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{region_id}", response_model=RegionSchema)
async def get_region(
    region_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific region by id.
    """
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found",
        )
    return region


@router.put("/{region_id}", response_model=RegionSchema)
async def update_region(
    region_id: int,
    region_in: RegionUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a region. Requires admin or manager role.
    """
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found",
        )
    
    # Check if code is being updated and if the new code already exists
    if region_in.code and region_in.code != region.code:
        db_region = db.query(Region).filter(Region.code == region_in.code).first()
        if db_region:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Region with this code already exists",
            )
    
    # Update region fields
    update_data = region_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(region, field, value)
    
    try:
        db.commit()
        db.refresh(region)
        return region
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating region",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{region_id}", response_model=RegionSchema)
async def delete_region(
    region_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a region. Requires admin role.
    """
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found",
        )
    
    # Check if the region has branches
    if region.branches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete region with associated branches",
        )
    
    try:
        db.delete(region)
        db.commit()
        return region
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) 