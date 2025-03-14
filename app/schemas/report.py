"""
Report schemas module.
Contains all the Pydantic models for reporting system.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """Time range for report filtering."""
    start_date: date = Field(..., description="Start date for the report")
    end_date: date = Field(..., description="End date for the report")


class InstallationStatItem(BaseModel):
    """Installation statistics item."""
    name: str = Field(..., description="Name of the item (e.g., branch name, status)")
    value: int = Field(..., description="Value count")
    percentage: float = Field(..., description="Percentage of total")


class InstallationSummaryReport(BaseModel):
    """Installation summary report."""
    total_requests: int = Field(..., description="Total installation requests")
    completed: int = Field(..., description="Completed installations")
    in_progress: int = Field(..., description="In-progress installations")
    pending: int = Field(..., description="Pending installations")
    cancelled: int = Field(..., description="Cancelled installations")
    completion_rate: float = Field(..., description="Completion rate percentage")
    
    by_type: List[InstallationStatItem] = Field(
        ..., description="Installation statistics by type"
    )
    by_branch: List[InstallationStatItem] = Field(
        ..., description="Installation statistics by branch"
    )
    by_status: List[InstallationStatItem] = Field(
        ..., description="Installation statistics by status"
    )


class DailyInstallationStat(BaseModel):
    """Daily installation statistics."""
    date: date
    total: int
    permanent: int
    temporary_count: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "date": {"description": "Date"},
                "total": {"description": "Total installations"},
                "permanent": {"description": "Permanent installations"},
                "temporary_count": {"description": "Temporary installations"}
            }
        }
    }


class InstallationTrendReport(BaseModel):
    """Installation trend report."""
    daily_stats: List[DailyInstallationStat] = Field(
        ..., description="Daily installation statistics"
    )
    total_in_period: int = Field(..., description="Total installations in period")
    avg_daily: float = Field(..., description="Average daily installations")
    max_daily: int = Field(..., description="Maximum daily installations")
    min_daily: int = Field(..., description="Minimum daily installations")


class SLAStatItem(BaseModel):
    """SLA statistics item."""
    name: str = Field(..., description="Name of the item (e.g., branch name)")
    total: int = Field(..., description="Total requests")
    within_sla: int = Field(..., description="Requests completed within SLA")
    exceeded_sla: int = Field(..., description="Requests exceeded SLA")
    sla_performance: float = Field(..., description="SLA performance percentage")
    avg_days: float = Field(..., description="Average days to complete")


class SLAReport(BaseModel):
    """SLA performance report."""
    overall_performance: float = Field(..., description="Overall SLA performance percentage")
    total_requests: int = Field(..., description="Total requests")
    within_sla: int = Field(..., description="Requests completed within SLA")
    exceeded_sla: int = Field(..., description="Requests exceeded SLA")
    avg_completion_days: float = Field(..., description="Average days to complete")
    
    by_branch: List[SLAStatItem] = Field(
        ..., description="SLA statistics by branch"
    )
    by_type: List[SLAStatItem] = Field(
        ..., description="SLA statistics by installation type"
    )


class BranchPerformanceItem(BaseModel):
    """Branch performance item."""
    branch_code: str = Field(..., description="Branch code (BA code)")
    branch_name: str = Field(..., description="Branch name")
    original_branch_code: str = Field(..., description="Original branch code")
    total_requests: int = Field(..., description="Total installation requests")
    completed: int = Field(..., description="Completed installations")
    in_progress: int = Field(..., description="In-progress installations")
    pending: int = Field(..., description="Pending installations")
    completion_rate: float = Field(..., description="Completion rate percentage")
    sla_performance: float = Field(..., description="SLA performance percentage")
    avg_completion_days: float = Field(..., description="Average days to complete")


class BranchPerformanceReport(BaseModel):
    """Branch performance report."""
    branches: List[BranchPerformanceItem] = Field(
        ..., description="Branch performance items"
    )
    top_performing: List[BranchPerformanceItem] = Field(
        ..., description="Top performing branches"
    )
    needs_improvement: List[BranchPerformanceItem] = Field(
        ..., description="Branches needing improvement"
    )


class TargetVsActualItem(BaseModel):
    """Target vs actual item."""
    name: str = Field(..., description="Name (month/branch/type)")
    target: int = Field(..., description="Target count")
    actual: int = Field(..., description="Actual count")
    percentage: float = Field(..., description="Achievement percentage")
    remaining: int = Field(..., description="Remaining count")


class TargetVsActualReport(BaseModel):
    """Target vs actual performance report."""
    overall_achievement: float = Field(..., description="Overall achievement percentage")
    total_target: int = Field(..., description="Total target")
    total_actual: int = Field(..., description="Total actual")
    total_remaining: int = Field(..., description="Total remaining")
    
    by_month: List[TargetVsActualItem] = Field(
        ..., description="Target vs actual by month"
    )
    by_branch: List[TargetVsActualItem] = Field(
        ..., description="Target vs actual by branch"
    )
    by_type: List[TargetVsActualItem] = Field(
        ..., description="Target vs actual by installation type"
    )


class ReportParams(BaseModel):
    """Common report parameters."""
    start_date: Optional[date] = Field(None, description="Start date for the report")
    end_date: Optional[date] = Field(None, description="End date for the report")
    branch_code: Optional[str] = Field(None, description="Filter by branch code (BA code)")
    installation_type_id: Optional[int] = Field(None, description="Filter by installation type ID")
    status_id: Optional[int] = Field(None, description="Filter by status ID")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month") 