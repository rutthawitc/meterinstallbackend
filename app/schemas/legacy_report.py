"""
Legacy report schemas module.
Contains Pydantic models for reports in legacy format.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class MonthlyInstallationItem(BaseModel):
    """Monthly installation item for legacy report."""
    branch_code: str
    branch_name: str
    permanent_count: int
    temporary_count: int
    total_count: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "branch_code": {"description": "Branch code"},
                "branch_name": {"description": "Branch name"},
                "permanent_count": {"description": "Permanent installation count"},
                "temporary_count": {"description": "Temporary installation count"},
                "total_count": {"description": "Total installation count"}
            }
        }
    }


class MonthlyInstallationReport(BaseModel):
    """Monthly installation report in legacy format."""
    year: int
    month: int
    total_permanent: int
    total_temporary: int
    grand_total: int
    data: List[MonthlyInstallationItem]
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "year": {"description": "Year"},
                "month": {"description": "Month"},
                "total_permanent": {"description": "Total permanent installations"},
                "total_temporary": {"description": "Total temporary installations"},
                "grand_total": {"description": "Grand total of installations"},
                "data": {"description": "Installation data by branch"}
            }
        }
    }


class InstallationStatusCountItem(BaseModel):
    """Installation status count item for legacy report."""
    status_name: str
    permanent_count: int
    temporary_count: int
    total_count: int
    percentage: float
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "status_name": {"description": "Status name"},
                "permanent_count": {"description": "Permanent installation count"},
                "temporary_count": {"description": "Temporary installation count"},
                "total_count": {"description": "Total count"},
                "percentage": {"description": "Percentage of total"}
            }
        }
    }


class InstallationStatusReport(BaseModel):
    """Installation status report in legacy format."""
    start_date: date
    end_date: date
    total_requests: int
    statuses: List[InstallationStatusCountItem]
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "start_date": {"description": "Start date"},
                "end_date": {"description": "End date"},
                "total_requests": {"description": "Total installation requests"},
                "statuses": {"description": "Status counts"}
            }
        }
    }


class BranchSLAItem(BaseModel):
    """Branch SLA item for legacy report."""
    branch_code: str
    branch_name: str
    total_completed: int
    completed_within_sla: int
    completed_exceeded_sla: int
    sla_percentage: float
    avg_completion_days: float
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "branch_code": {"description": "Branch code"},
                "branch_name": {"description": "Branch name"},
                "total_completed": {"description": "Total completed installations"},
                "completed_within_sla": {"description": "Installations completed within SLA"},
                "completed_exceeded_sla": {"description": "Installations exceeded SLA"},
                "sla_percentage": {"description": "SLA percentage"},
                "avg_completion_days": {"description": "Average completion days"}
            }
        }
    }


class SLAComplianceReport(BaseModel):
    """SLA compliance report in legacy format."""
    year: Optional[int] = None
    month: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_completed: int
    total_within_sla: int
    total_exceeded_sla: int
    overall_sla_percentage: float
    branches: List[BranchSLAItem]
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "year": {"description": "Year"},
                "month": {"description": "Month"},
                "start_date": {"description": "Start date"},
                "end_date": {"description": "End date"},
                "total_completed": {"description": "Total completed installations"},
                "total_within_sla": {"description": "Total installations within SLA"},
                "total_exceeded_sla": {"description": "Total installations exceeded SLA"},
                "overall_sla_percentage": {"description": "Overall SLA percentage"},
                "branches": {"description": "SLA data by branch"}
            }
        }
    }


class DailyInstallationCountItem(BaseModel):
    """Daily installation count item for legacy report."""
    date: date
    permanent_count: int
    temporary_count: int
    total_count: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "date": {"description": "Date"},
                "permanent_count": {"description": "Permanent installation count"},
                "temporary_count": {"description": "Temporary installation count"},
                "total_count": {"description": "Total count"}
            }
        }
    }


class DailyInstallationReport(BaseModel):
    """Daily installation report in legacy format."""
    start_date: date
    end_date: date
    branch_code: Optional[str] = None
    branch_name: Optional[str] = None
    total_permanent: int
    total_temporary: int
    grand_total: int
    daily_data: List[DailyInstallationCountItem]
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "start_date": {"description": "Start date"},
                "end_date": {"description": "End date"},
                "branch_code": {"description": "Branch code"},
                "branch_name": {"description": "Branch name"},
                "total_permanent": {"description": "Total permanent installations"},
                "total_temporary": {"description": "Total temporary installations"},
                "grand_total": {"description": "Grand total of installations"},
                "daily_data": {"description": "Daily installation data"}
            }
        }
    }


class TargetProgressItem(BaseModel):
    """Target progress item for legacy report."""
    branch_code: str
    branch_name: str
    target: int
    achieved: int
    remaining: int
    progress_percentage: float
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "branch_code": {"description": "Branch code"},
                "branch_name": {"description": "Branch name"},
                "target": {"description": "Target count"},
                "achieved": {"description": "Achieved count"},
                "remaining": {"description": "Remaining count"},
                "progress_percentage": {"description": "Progress percentage"}
            }
        }
    }


class TargetProgressReport(BaseModel):
    """Target progress report in legacy format."""
    year: int
    month: int
    installation_type: str
    total_target: int
    total_achieved: int
    total_remaining: int
    overall_progress: float
    branches: List[TargetProgressItem]
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "year": {"description": "Year"},
                "month": {"description": "Month"},
                "installation_type": {"description": "Installation type"},
                "total_target": {"description": "Total target"},
                "total_achieved": {"description": "Total achieved"},
                "total_remaining": {"description": "Total remaining"},
                "overall_progress": {"description": "Overall progress percentage"},
                "branches": {"description": "Progress data by branch"}
            }
        }
    } 