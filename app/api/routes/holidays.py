"""
API routes for managing holidays.
"""
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import extract

from app.db.session import get_db
from app.models.holiday import Holiday
from app.models.region import Region
from app.schemas.holiday import HolidayCreate, HolidayUpdate, HolidayResponse
from app.api.dependencies import has_role

router = APIRouter()


@router.get("", response_model=List[HolidayResponse])
async def get_holidays(
    year: Optional[int] = None,
    region_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
):
    """
    Retrieve holidays with optional filtering by year and/or region.
    
    Parameters:
    - **year**: Optional filter by year
    - **region_id**: Optional filter by region ID
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    """
    query = db.query(Holiday)
    
    if year:
        query = query.filter(extract('year', Holiday.holiday_date) == year)
        
    if region_id:
        query = query.filter(Holiday.region_id == region_id)
        
    # Order by date
    query = query.order_by(Holiday.holiday_date)
    
    holidays = query.offset(skip).limit(limit).all()
    return holidays


@router.get("/{holiday_id}", response_model=HolidayResponse)
async def get_holiday(
    holiday_id: int,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific holiday by ID.
    
    Parameters:
    - **holiday_id**: ID of the holiday to retrieve
    """
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return holiday


@router.post("", response_model=HolidayResponse)
async def create_holiday(
    holiday: HolidayCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
):
    """
    Create a new holiday.
    
    Parameters:
    - **holiday**: Holiday data
    """
    # Check if region exists if provided
    if holiday.region_id:
        region = db.query(Region).filter(Region.id == holiday.region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
    
    # Check if holiday with same date already exists
    existing = db.query(Holiday).filter(Holiday.holiday_date == holiday.holiday_date).first()
    if existing:
        raise HTTPException(status_code=400, detail="Holiday with this date already exists")
    
    try:
        db_holiday = Holiday(
            holiday_date=holiday.holiday_date,
            description=holiday.description,
            is_national_holiday=holiday.is_national_holiday,
            is_repeating_yearly=holiday.is_repeating_yearly,
            region_id=holiday.region_id,
            updated_by=current_user.id
        )
        db.add(db_holiday)
        db.commit()
        db.refresh(db_holiday)
        return db_holiday
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create holiday")


@router.put("/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: int,
    holiday: HolidayUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
):
    """
    Update a holiday.
    
    Parameters:
    - **holiday_id**: ID of the holiday to update
    - **holiday**: Updated holiday data
    """
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    # Check if region exists if provided
    if holiday.region_id:
        region = db.query(Region).filter(Region.id == holiday.region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
    
    # If we're changing the date, check if it conflicts with an existing holiday
    if holiday.holiday_date and holiday.holiday_date != db_holiday.holiday_date:
        existing = db.query(Holiday).filter(
            Holiday.holiday_date == holiday.holiday_date,
            Holiday.id != holiday_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Holiday with this date already exists")
    
    try:
        # Update fields
        if holiday.holiday_date:
            db_holiday.holiday_date = holiday.holiday_date
        if holiday.description:
            db_holiday.description = holiday.description
        if holiday.is_national_holiday is not None:
            db_holiday.is_national_holiday = holiday.is_national_holiday
        if holiday.is_repeating_yearly is not None:
            db_holiday.is_repeating_yearly = holiday.is_repeating_yearly
        if holiday.region_id is not None:
            db_holiday.region_id = holiday.region_id
        
        db_holiday.updated_by = current_user.id
        db_holiday.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_holiday)
        return db_holiday
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update holiday")


@router.delete("/{holiday_id}", response_model=dict)
async def delete_holiday(
    holiday_id: int,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
):
    """
    Delete a holiday.
    
    Parameters:
    - **holiday_id**: ID of the holiday to delete
    """
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    try:
        db.delete(db_holiday)
        db.commit()
        return {"message": "Holiday deleted successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not delete holiday")
