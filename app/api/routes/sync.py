"""
API routes for data synchronization with Oracle.
"""
from typing import Any, List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies import get_current_superuser, get_current_active_user, has_role
from app.db.session import get_db
from app.models.sync_log import SyncLog
from app.services.sync_service import SyncService
from app.schemas.sync import SyncLogResponse, SyncLogDetail, SyncRequest

router = APIRouter()


@router.post("/holidays", response_model=SyncLogResponse)
async def sync_holidays(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync holidays from Oracle database.
    
    Parameters:
    - **is_full_sync**: Whether to do a full sync or a delta sync
    - **year**: Optional year to sync holidays for (YYYY)
    """
    sync_service = SyncService(db)
    
    # If run_async is True, run in background
    if request.run_async:
        background_tasks.add_task(
            sync_service.sync_holidays,
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year
        )
        return {
            "message": "Holiday sync started in background",
            "status": "running",
            "is_async": True
        }
    else:
        # Run synchronously
        result = sync_service.sync_holidays(
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year
        )
        
        return {
            "id": result.id,
            "sync_type": result.sync_type,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "records_failed": result.records_failed,
            "is_async": False
        }


@router.post("/installation-requests", response_model=SyncLogResponse)
async def sync_installation_requests(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync installation requests from Oracle database.
    
    Parameters:
    - **is_full_sync**: Whether to do a full sync or a delta sync
    - **start_date**: Optional start date for delta sync (YYYY-MM-DD)
    - **end_date**: Optional end date for delta sync (YYYY-MM-DD)
    - **branch_code**: Optional branch code to filter by
    """
    sync_service = SyncService(db)
    
    # Parse dates if provided
    start_date = datetime.fromisoformat(request.start_date) if request.start_date else None
    end_date = datetime.fromisoformat(request.end_date) if request.end_date else None
    
    # If run_async is True, run in background
    if request.run_async:
        background_tasks.add_task(
            sync_service.sync_installation_requests,
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            start_date=start_date,
            end_date=end_date,
            branch_code=request.branch_code
        )
        return {
            "message": "Installation requests sync started in background",
            "status": "running",
            "is_async": True
        }
    else:
        # Run synchronously
        result = sync_service.sync_installation_requests(
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            start_date=start_date,
            end_date=end_date,
            branch_code=request.branch_code
        )
        
        return {
            "id": result.id,
            "sync_type": result.sync_type,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "records_failed": result.records_failed,
            "is_async": False
        }


@router.post("/temporary-installations", response_model=SyncLogResponse)
async def sync_temporary_installations(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync temporary installation data from Oracle database.
    
    Parameters:
    - **is_full_sync**: Whether to do a full sync or a delta sync
    - **year**: Optional year to filter by (YYYY)
    - **month**: Optional month to filter by (MM) - if provided with year, creates a YYYYMM filter
    """
    sync_service = SyncService(db)
    
    # Create year_month parameter if year and/or month provided
    year_month = None
    if request.year:
        if hasattr(request, 'month') and request.month:
            # Both year and month provided
            year_month = f"{request.year}{request.month:02d}"
        else:
            # Only year provided, use January
            year_month = f"{request.year}01"
    
    # If run_async is True, run in background
    if request.run_async:
        background_tasks.add_task(
            sync_service.sync_temporary_installations,
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year_month=year_month
        )
        return {
            "message": "Temporary installations sync started in background",
            "status": "running",
            "is_async": True
        }
    else:
        # Run synchronously
        result = sync_service.sync_temporary_installations(
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year_month=year_month
        )
        
        return {
            "id": result.id,
            "sync_type": result.sync_type,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "records_failed": result.records_failed,
            "is_async": False
        }


@router.post("/customer-type-changes", response_model=SyncLogResponse)
async def sync_customer_type_changes(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync customer type changes from Oracle database.
    
    Parameters:
    - **is_full_sync**: Whether to do a full sync or a delta sync
    - **year**: Optional year to filter by (Gregorian calendar, will be converted to Thai Buddhist calendar)
    - **month**: Optional month to filter by (MM)
    """
    sync_service = SyncService(db)
    
    # If run_async is True, run in background
    if request.run_async:
        background_tasks.add_task(
            sync_service.sync_customer_type_changes,
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year,
            month=request.month
        )
        return {
            "message": "Customer type changes sync started in background",
            "status": "running",
            "is_async": True
        }
    else:
        # Run synchronously
        result = sync_service.sync_customer_type_changes(
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year,
            month=request.month
        )
        
        return {
            "id": result.id,
            "sync_type": result.sync_type,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "records_failed": result.records_failed,
            "is_async": False
        }


@router.post("/new-customers", response_model=SyncLogResponse)
async def sync_new_customers(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync new water customers from Oracle database.
    
    Parameters:
    - **is_full_sync**: Whether to do a full sync or a delta sync
    - **year**: Optional year to filter by (Gregorian calendar, will be converted to Thai Buddhist calendar)
    - **month**: Optional month to filter by (MM)
    """
    sync_service = SyncService(db)
    
    # If run_async is True, run in background
    if request.run_async:
        background_tasks.add_task(
            sync_service.sync_new_customers,
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year,
            month=request.month
        )
        return {
            "message": "New customers sync started in background",
            "status": "running",
            "is_async": True
        }
    else:
        # Run synchronously
        result = sync_service.sync_new_customers(
            user_id=current_user.id,
            is_full_sync=request.is_full_sync,
            year=request.year,
            month=request.month
        )
        
        return {
            "id": result.id,
            "sync_type": result.sync_type,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "records_failed": result.records_failed,
            "is_async": False
        }


@router.get("/logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    sync_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get recent sync logs.
    
    Parameters:
    - **sync_type**: Optional type of sync logs to retrieve (e.g., "holiday", "installation_request")
    - **limit**: Maximum number of logs to retrieve (default: 10, max: 100)
    """
    sync_service = SyncService(db)
    logs = sync_service.get_sync_logs(sync_type=sync_type, limit=limit)
    
    return logs


@router.get("/logs/{log_id}", response_model=SyncLogDetail)
async def get_sync_log(
    log_id: int,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific sync log by ID.
    
    Parameters:
    - **log_id**: ID of the sync log to retrieve
    """
    sync_service = SyncService(db)
    log = sync_service.get_sync_log(log_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync log not found",
        )
    
    return log 