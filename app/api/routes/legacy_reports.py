"""
API routes for legacy format reports.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.legacy_report import (
    MonthlyInstallationReport,
    InstallationStatusReport,
    SLAComplianceReport,
    DailyInstallationReport,
    TargetProgressReport
)
from app.services.legacy_report_service import LegacyReportService

router = APIRouter()


@router.get("/monthly", response_model=MonthlyInstallationReport)
def get_monthly_installation_report(
    *,
    db: Session = Depends(get_db),
    year: int,
    month: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get monthly installation report in legacy format.
    
    Shows completed installations by branch for a specific month.
    """
    try:
        service = LegacyReportService(db)
        report = service.get_monthly_installation_report(
            year=year,
            month=month
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the full error with traceback
        import traceback
        traceback.print_exc()
        # Return more details about the error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/status", response_model=InstallationStatusReport)
def get_installation_status_report(
    *,
    db: Session = Depends(get_db),
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get installation status report in legacy format.
    
    Shows installation counts by status within date range.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
        
    service = LegacyReportService(db)
    report = service.get_installation_status_report(
        start_date=start_date,
        end_date=end_date
    )
    return report


@router.get("/sla", response_model=SLAComplianceReport)
def get_sla_compliance_report(
    *,
    db: Session = Depends(get_db),
    year: Optional[int] = None,
    month: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get SLA compliance report in legacy format.
    
    Shows SLA compliance by branch for a given period.
    Either provide year/month or start_date/end_date.
    """
    try:
        service = LegacyReportService(db)
        report = service.get_sla_compliance_report(
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the full error with traceback
        import traceback
        traceback.print_exc()
        # Return more details about the error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/daily", response_model=DailyInstallationReport)
def get_daily_installation_report(
    *,
    db: Session = Depends(get_db),
    start_date: date,
    end_date: date,
    branch_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get daily installation report in legacy format.
    
    Shows installation counts by day within a date range.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    try:    
        service = LegacyReportService(db)
        report = service.get_daily_installation_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id
        )
        return report
    except Exception as e:
        # Log the full error with traceback
        import traceback
        traceback.print_exc()
        # Return more details about the error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/target-progress", response_model=TargetProgressReport)
def get_target_progress_report(
    *,
    db: Session = Depends(get_db),
    year: int,
    month: int,
    installation_type_id: int = Query(..., description="Installation type ID (1 for permanent, 2 for temporary)"),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get target progress report in legacy format.
    
    Shows progress toward installation targets by branch.
    """
    try:
        service = LegacyReportService(db)
        report = service.get_target_progress_report(
            year=year,
            month=month,
            installation_type_id=installation_type_id
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/monthly", response_model=Dict[str, Any])
def export_monthly_installation_report(
    *,
    db: Session = Depends(get_db),
    year: int,
    month: int,
    format: str = Query("json", description="Export format (json, csv, excel)"),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Export monthly installation report in various formats.
    
    BETA: Currently returns JSON only with export metadata.
    """
    try:
        service = LegacyReportService(db)
        report = service.get_monthly_installation_report(
            year=year,
            month=month
        )
        
        # In a real implementation, we would convert to the requested format here
        
        return {
            "format": format,
            "filename": f"monthly_installation_report_{year}_{month:02d}.{format}",
            "generated_at": datetime.now(),
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 