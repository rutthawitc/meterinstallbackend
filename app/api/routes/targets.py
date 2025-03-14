"""
API routes for managing installation targets.
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
import logging
from datetime import datetime, date

from app.api.dependencies import get_db, has_role
from app.models.target import Target
from app.models.installation_request import InstallationRequest
from app.models.branch import Branch
from app.models.installation_type import InstallationType
from app.models.user import User
from app.schemas.target import (
    Target as TargetSchema,
    TargetCreate,
    TargetUpdate,
    TargetListResponse,
    TargetWithProgress,
    TargetWithProgressListResponse
)

router = APIRouter()

@router.post("/", response_model=TargetSchema)
async def create_target(
    *,
    target_in: TargetCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new target.
    """
    # Check if branch exists
    branch = db.query(Branch).filter(Branch.id == target_in.branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Check if installation_type exists
    installation_type = db.query(InstallationType).filter(InstallationType.id == target_in.installation_type_id).first()
    if not installation_type:
        raise HTTPException(status_code=404, detail="Installation type not found")
    
    # Check if target already exists for the combination
    existing_target = db.query(Target).filter(
        and_(
            Target.year == target_in.year,
            Target.month == target_in.month,
            Target.branch_id == target_in.branch_id,
            Target.installation_type_id == target_in.installation_type_id
        )
    ).first()
    
    if existing_target:
        raise HTTPException(
            status_code=400,
            detail="Target for this combination of year, month, branch and installation type already exists"
        )
    
    # Create new target
    target = Target(
        year=target_in.year,
        month=target_in.month,
        branch_id=target_in.branch_id,
        installation_type_id=target_in.installation_type_id,
        target_count=target_in.target_count,
        target_days=target_in.target_days,
        description=target_in.description,
        created_by=current_user.id,
        created_at=datetime.utcnow().date()
    )
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    # Add related entity names
    target.branch_name = branch.name
    target.installation_type_name = installation_type.name
    target.created_by_name = f"{current_user.firstname} {current_user.lastname}"
    
    return target

@router.get("/", response_model=TargetListResponse)
async def get_targets(
    year: Optional[int] = None,
    month: Optional[int] = None,
    branch_id: Optional[int] = None,
    installation_type_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get targets with optional filters.
    """
    # Build SQL query
    sql_query = """
    SELECT 
        t.id, t.year, t.month, t.branch_id, t.installation_type_id, 
        t.target_count, t.target_days, t.description, t.created_by, 
        t.created_at, t.updated_at,
        b.name as branch_name,
        it.name as installation_type_name,
        CONCAT(u.firstname, ' ', u.lastname) as created_by_name
    FROM 
        targets t
    JOIN 
        branches b ON t.branch_id = b.id
    JOIN 
        installation_types it ON t.installation_type_id = it.id
    JOIN 
        users u ON t.created_by = u.id
    WHERE 1=1
    """
    
    # Initialize parameters
    params = {}
    
    # Add filters
    if year is not None:
        sql_query += " AND t.year = :year"
        params["year"] = year
    
    if month is not None:
        sql_query += " AND t.month = :month"
        params["month"] = month
    
    if branch_id is not None:
        sql_query += " AND t.branch_id = :branch_id"
        params["branch_id"] = branch_id
    
    if installation_type_id is not None:
        sql_query += " AND t.installation_type_id = :installation_type_id"
        params["installation_type_id"] = installation_type_id
    
    # Count total matching records
    count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) AS count_query"
    count_result = db.execute(text(count_query), params).first()
    total = count_result.total if count_result else 0
    
    # Add pagination
    sql_query += " ORDER BY t.year DESC, t.month DESC, b.name ASC"
    sql_query += " OFFSET :skip LIMIT :limit"
    params["skip"] = skip
    params["limit"] = limit
    
    # Execute query
    result = db.execute(text(sql_query), params)
    
    # Process results
    items = []
    for row in result:
        item = {
            "id": row.id,
            "year": row.year,
            "month": row.month,
            "branch_id": row.branch_id,
            "installation_type_id": row.installation_type_id,
            "target_count": row.target_count,
            "target_days": row.target_days,
            "description": row.description,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "branch_name": row.branch_name,
            "installation_type_name": row.installation_type_name,
            "created_by_name": row.created_by_name
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }

@router.get("/with-progress", response_model=TargetWithProgressListResponse)
async def get_targets_with_progress(
    year: Optional[int] = None,
    month: Optional[int] = None,
    branch_id: Optional[int] = None,
    installation_type_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get targets with progress information.
    """
    # Build SQL query for targets
    sql_query = """
    SELECT 
        t.id, t.year, t.month, t.branch_id, t.installation_type_id, 
        t.target_count, t.target_days, t.description, t.created_by, 
        t.created_at, t.updated_at,
        b.name as branch_name,
        it.name as installation_type_name,
        CONCAT(u.firstname, ' ', u.lastname) as created_by_name
    FROM 
        targets t
    JOIN 
        branches b ON t.branch_id = b.id
    JOIN 
        installation_types it ON t.installation_type_id = it.id
    JOIN 
        users u ON t.created_by = u.id
    WHERE 1=1
    """
    
    # Initialize parameters
    params = {}
    
    # Add filters
    if year is not None:
        sql_query += " AND t.year = :year"
        params["year"] = year
    
    if month is not None:
        sql_query += " AND t.month = :month"
        params["month"] = month
    
    if branch_id is not None:
        sql_query += " AND t.branch_id = :branch_id"
        params["branch_id"] = branch_id
    
    if installation_type_id is not None:
        sql_query += " AND t.installation_type_id = :installation_type_id"
        params["installation_type_id"] = installation_type_id
    
    # Count total matching records
    count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) AS count_query"
    count_result = db.execute(text(count_query), params).first()
    total = count_result.total if count_result else 0
    
    # Add pagination
    sql_query += " ORDER BY t.year DESC, t.month DESC, b.name ASC"
    sql_query += " OFFSET :skip LIMIT :limit"
    params["skip"] = skip
    params["limit"] = limit
    
    # Execute query
    result = db.execute(text(sql_query), params)
    
    # Process results and calculate progress
    items = []
    for row in result:
        # Basic target information
        target_info = {
            "id": row.id,
            "year": row.year,
            "month": row.month,
            "branch_id": row.branch_id,
            "installation_type_id": row.installation_type_id,
            "target_count": row.target_count,
            "target_days": row.target_days,
            "description": row.description,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "branch_name": row.branch_name,
            "installation_type_name": row.installation_type_name,
            "created_by_name": row.created_by_name,
            "completed_count": 0,
            "completion_percentage": 0.0,
            "remaining_count": row.target_count,
            "average_days_to_complete": None,
            "on_time_percentage": None
        }
        
        # Calculate completion stats for this target
        completion_query = """
        SELECT 
            COUNT(*) as completed_count,
            AVG(EXTRACT(DAY FROM (completion_date - request_date))) as avg_days
        FROM 
            installation_requests ir
        WHERE 
            ir.branch_id = :branch_id
            AND ir.installation_type_id = :installation_type_id
            AND EXTRACT(YEAR FROM ir.completion_date) = :year
            AND EXTRACT(MONTH FROM ir.completion_date) = :month
            AND ir.completion_date IS NOT NULL
        """
        
        completion_params = {
            "branch_id": row.branch_id,
            "installation_type_id": row.installation_type_id,
            "year": row.year,
            "month": row.month
        }
        
        completion_result = db.execute(text(completion_query), completion_params).first()
        
        if completion_result and completion_result.completed_count:
            completed_count = completion_result.completed_count
            avg_days = completion_result.avg_days
            
            target_info["completed_count"] = completed_count
            target_info["average_days_to_complete"] = round(avg_days, 2) if avg_days else None
            
            # Calculate percentage completed
            if row.target_count > 0:
                target_info["completion_percentage"] = round((completed_count / row.target_count) * 100, 2)
                target_info["remaining_count"] = max(0, row.target_count - completed_count)
            
            # Calculate on-time percentage if target days is set
            if row.target_days:
                on_time_query = """
                SELECT 
                    COUNT(*) as on_time_count
                FROM 
                    installation_requests ir
                WHERE 
                    ir.branch_id = :branch_id
                    AND ir.installation_type_id = :installation_type_id
                    AND EXTRACT(YEAR FROM ir.completion_date) = :year
                    AND EXTRACT(MONTH FROM ir.completion_date) = :month
                    AND ir.completion_date IS NOT NULL
                    AND EXTRACT(DAY FROM (ir.completion_date - ir.request_date)) <= :target_days
                """
                
                on_time_params = {
                    "branch_id": row.branch_id,
                    "installation_type_id": row.installation_type_id,
                    "year": row.year,
                    "month": row.month,
                    "target_days": row.target_days
                }
                
                on_time_result = db.execute(text(on_time_query), on_time_params).first()
                
                if on_time_result and completed_count > 0:
                    on_time_count = on_time_result.on_time_count
                    target_info["on_time_percentage"] = round((on_time_count / completed_count) * 100, 2)
        
        items.append(target_info)
    
    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }

@router.get("/{target_id}", response_model=TargetSchema)
async def get_target(
    target_id: int,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get target by ID.
    """
    # Build SQL query
    sql_query = """
    SELECT 
        t.id, t.year, t.month, t.branch_id, t.installation_type_id, 
        t.target_count, t.target_days, t.description, t.created_by, 
        t.created_at, t.updated_at,
        b.name as branch_name,
        it.name as installation_type_name,
        CONCAT(u.firstname, ' ', u.lastname) as created_by_name
    FROM 
        targets t
    JOIN 
        branches b ON t.branch_id = b.id
    JOIN 
        installation_types it ON t.installation_type_id = it.id
    JOIN 
        users u ON t.created_by = u.id
    WHERE 
        t.id = :target_id
    """
    
    # Execute query
    result = db.execute(text(sql_query), {"target_id": target_id}).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # Process result
    target = {
        "id": result.id,
        "year": result.year,
        "month": result.month,
        "branch_id": result.branch_id,
        "installation_type_id": result.installation_type_id,
        "target_count": result.target_count,
        "target_days": result.target_days,
        "description": result.description,
        "created_by": result.created_by,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "branch_name": result.branch_name,
        "installation_type_name": result.installation_type_name,
        "created_by_name": result.created_by_name
    }
    
    return target

@router.get("/{target_id}/progress", response_model=TargetWithProgress)
async def get_target_progress(
    target_id: int,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get target with progress information by ID.
    """
    # Get target with basic information
    target_result = await get_target(target_id, current_user, db)
    
    # Calculate completion stats for this target
    completion_query = """
    SELECT 
        COUNT(*) as completed_count,
        AVG(EXTRACT(DAY FROM (completion_date - request_date))) as avg_days
    FROM 
        installation_requests ir
    WHERE 
        ir.branch_id = :branch_id
        AND ir.installation_type_id = :installation_type_id
        AND EXTRACT(YEAR FROM ir.completion_date) = :year
        AND EXTRACT(MONTH FROM ir.completion_date) = :month
        AND ir.completion_date IS NOT NULL
    """
    
    completion_params = {
        "branch_id": target_result["branch_id"],
        "installation_type_id": target_result["installation_type_id"],
        "year": target_result["year"],
        "month": target_result["month"]
    }
    
    completion_result = db.execute(text(completion_query), completion_params).first()
    
    # Initialize progress information
    target_progress = {
        **target_result,
        "completed_count": 0,
        "completion_percentage": 0.0,
        "remaining_count": target_result["target_count"],
        "average_days_to_complete": None,
        "on_time_percentage": None
    }
    
    if completion_result and completion_result.completed_count:
        completed_count = completion_result.completed_count
        avg_days = completion_result.avg_days
        
        target_progress["completed_count"] = completed_count
        target_progress["average_days_to_complete"] = round(avg_days, 2) if avg_days else None
        
        # Calculate percentage completed
        if target_result["target_count"] > 0:
            target_progress["completion_percentage"] = round((completed_count / target_result["target_count"]) * 100, 2)
            target_progress["remaining_count"] = max(0, target_result["target_count"] - completed_count)
        
        # Calculate on-time percentage if target days is set
        if target_result["target_days"]:
            on_time_query = """
            SELECT 
                COUNT(*) as on_time_count
            FROM 
                installation_requests ir
            WHERE 
                ir.branch_id = :branch_id
                AND ir.installation_type_id = :installation_type_id
                AND EXTRACT(YEAR FROM ir.completion_date) = :year
                AND EXTRACT(MONTH FROM ir.completion_date) = :month
                AND ir.completion_date IS NOT NULL
                AND EXTRACT(DAY FROM (ir.completion_date - ir.request_date)) <= :target_days
            """
            
            on_time_params = {
                "branch_id": target_result["branch_id"],
                "installation_type_id": target_result["installation_type_id"],
                "year": target_result["year"],
                "month": target_result["month"],
                "target_days": target_result["target_days"]
            }
            
            on_time_result = db.execute(text(on_time_query), on_time_params).first()
            
            if on_time_result and completed_count > 0:
                on_time_count = on_time_result.on_time_count
                target_progress["on_time_percentage"] = round((on_time_count / completed_count) * 100, 2)
    
    return target_progress

@router.put("/{target_id}", response_model=TargetSchema)
async def update_target(
    target_id: int,
    target_in: TargetUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update target.
    """
    # Get existing target
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    update_data = target_in.model_dump(exclude_unset=True)
    
    # Check if changing year, month, branch or installation_type
    changing_key = False
    if any(key in update_data for key in ['year', 'month', 'branch_id', 'installation_type_id']):
        changing_key = True
        
        # Get updated key values or use existing ones
        new_year = update_data.get('year', target.year)
        new_month = update_data.get('month', target.month)
        new_branch_id = update_data.get('branch_id', target.branch_id)
        new_installation_type_id = update_data.get('installation_type_id', target.installation_type_id)
        
        # Check if branch exists if changing
        if 'branch_id' in update_data:
            branch = db.query(Branch).filter(Branch.id == new_branch_id).first()
            if not branch:
                raise HTTPException(status_code=404, detail="Branch not found")
        
        # Check if installation_type exists if changing
        if 'installation_type_id' in update_data:
            installation_type = db.query(InstallationType).filter(InstallationType.id == new_installation_type_id).first()
            if not installation_type:
                raise HTTPException(status_code=404, detail="Installation type not found")
        
        # Check for duplicate
        existing_target = db.query(Target).filter(
            and_(
                Target.year == new_year,
                Target.month == new_month,
                Target.branch_id == new_branch_id,
                Target.installation_type_id == new_installation_type_id,
                Target.id != target_id
            )
        ).first()
        
        if existing_target:
            raise HTTPException(
                status_code=400,
                detail="Target for this combination of year, month, branch and installation type already exists"
            )
    
    # Update target fields
    for field, value in update_data.items():
        setattr(target, field, value)
    
    # Update the updated_at timestamp
    target.updated_at = datetime.utcnow().date()
    
    db.commit()
    db.refresh(target)
    
    # Get branch, installation_type and created_by names
    branch = db.query(Branch).filter(Branch.id == target.branch_id).first()
    installation_type = db.query(InstallationType).filter(InstallationType.id == target.installation_type_id).first()
    user = db.query(User).filter(User.id == target.created_by).first()
    
    # Add related entity names
    target.branch_name = branch.name if branch else None
    target.installation_type_name = installation_type.name if installation_type else None
    target.created_by_name = f"{user.firstname} {user.lastname}" if user else None
    
    return target

@router.delete("/{target_id}", response_model=dict)
async def delete_target(
    target_id: int,
    current_user = Depends(has_role(["admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete target. Only admin can delete targets.
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    db.delete(target)
    db.commit()
    
    return {"message": "Target deleted successfully"} 