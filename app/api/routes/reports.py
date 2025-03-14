"""
API routes for reporting system.
"""
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.report import (
    InstallationSummaryReport,
    InstallationTrendReport,
    SLAReport,
    BranchPerformanceReport,
    TargetVsActualReport,
    ReportParams
)
from app.services.report_service import ReportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/installation-summary", response_model=InstallationSummaryReport)
def get_installation_summary(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get installation summary report.
    """
    try:
        report_service = ReportService(db)
        report = report_service.get_installation_summary(
            start_date=start_date,
            end_date=end_date,
            branch_code=branch_code
        )
        return report
    except Exception as e:
        logger.error(f"Error generating installation summary report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/installation-trend", response_model=InstallationTrendReport)
def get_installation_trend(
    *,
    db: Session = Depends(get_db),
    start_date: date,
    end_date: date,
    branch_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get installation trend report.
    """
    try:
        report_service = ReportService(db)
        report = report_service.get_installation_trend(
            start_date=start_date,
            end_date=end_date,
            branch_code=branch_code
        )
        return report
    except Exception as e:
        logger.error(f"Error generating installation trend report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/sla-performance", response_model=SLAReport)
def get_sla_performance(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get SLA performance report.
    """
    try:
        report_service = ReportService(db)
        report = report_service.get_sla_performance(
            start_date=start_date,
            end_date=end_date,
            branch_code=branch_code
        )
        return report
    except Exception as e:
        logger.error(f"Error generating SLA performance report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/branch-performance", response_model=BranchPerformanceReport)
def get_branch_performance(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get branch performance report.
    """
    try:
        report_service = ReportService(db)
        report = report_service.get_branch_performance(
            start_date=start_date,
            end_date=end_date,
            region_id=region_id
        )
        return report
    except Exception as e:
        logger.error(f"Error generating branch performance report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/target-vs-actual", response_model=TargetVsActualReport)
def get_target_vs_actual(
    *,
    db: Session = Depends(get_db),
    year: int,
    branch_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get target vs actual report.
    """
    try:
        report_service = ReportService(db)
        report = report_service.get_target_vs_actual(
            year=year,
            branch_code=branch_code
        )
        return report
    except Exception as e:
        logger.error(f"Error generating target vs actual report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.post("/generate")
def generate_report(
    *,
    db: Session = Depends(get_db),
    params: ReportParams = Body(...),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Generate report based on params.
    """
    try:
        report_service = ReportService(db)
        return report_service.generate_report(params)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        ) 