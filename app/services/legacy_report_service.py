"""
Legacy report service for generating reports in legacy format.
"""
import logging
import calendar
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy import func, case, distinct, extract, and_, or_, text
from sqlalchemy.orm import Session

from app.models.installation_request import InstallationRequest
from app.models.installation_type import InstallationType
from app.models.installation_status import InstallationStatus
from app.models.branch import Branch
from app.models.target import Target
from app.schemas.legacy_report import (
    MonthlyInstallationReport, MonthlyInstallationItem,
    InstallationStatusReport, InstallationStatusCountItem,
    SLAComplianceReport, BranchSLAItem,
    DailyInstallationReport, DailyInstallationCountItem,
    TargetProgressReport, TargetProgressItem
)

logger = logging.getLogger(__name__)


class LegacyReportService:
    """Service for generating reports in legacy format."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_monthly_installation_report(
        self,
        year: int,
        month: int
    ) -> MonthlyInstallationReport:
        """
        Generate monthly installation report in legacy format.
        
        Args:
            year: Year for the report
            month: Month for the report (1-12)
            
        Returns:
            Monthly installation report
        """
        # Validate month
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
            
        # Get date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        # Get completed installations for the month by branch
        query = self.db.query(
            Branch.branch_code,
            Branch.name.label('branch_name'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 1, 1),
                else_=0
            )).label('permanent_count'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 2, 1),
                else_=0
            )).label('temporary_count'),
            func.count(InstallationRequest.id).label('total_count')
        ).join(
            InstallationRequest,
            InstallationRequest.branch_code == Branch.ba_code
        ).filter(
            InstallationRequest.status_id == 4,  # Completed status
            InstallationRequest.created_at >= start_date,
            InstallationRequest.created_at <= end_date
        ).group_by(
            Branch.branch_code,
            Branch.name
        ).order_by(
            Branch.branch_code
        ).all()
        
        # Create report items
        items = [
            MonthlyInstallationItem(
                branch_code=item.branch_code,
                branch_name=item.branch_name,
                permanent_count=item.permanent_count,
                temporary_count=item.temporary_count,
                total_count=item.total_count
            )
            for item in query
        ]
        
        # Calculate totals
        total_permanent = sum(item.permanent_count for item in items)
        total_temporary = sum(item.temporary_count for item in items)
        grand_total = total_permanent + total_temporary
        
        return MonthlyInstallationReport(
            year=year,
            month=month,
            total_permanent=total_permanent,
            total_temporary=total_temporary,
            grand_total=grand_total,
            data=items
        )
    
    def get_installation_status_report(
        self,
        start_date: date,
        end_date: date
    ) -> InstallationStatusReport:
        """
        Generate installation status report in legacy format.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Installation status report
        """
        # Get total requests in the period
        total_requests = self.db.query(InstallationRequest).filter(
            InstallationRequest.created_at >= start_date,
            InstallationRequest.created_at <= end_date
        ).count()
        
        # Get status counts with installation types
        query = self.db.query(
            InstallationStatus.name.label('status_name'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 1, 1),
                else_=0
            )).label('permanent_count'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 2, 1),
                else_=0
            )).label('temporary_count'),
            func.count(InstallationRequest.id).label('total_count')
        ).join(
            InstallationStatus,
            InstallationRequest.status_id == InstallationStatus.id
        ).filter(
            InstallationRequest.created_at >= start_date,
            InstallationRequest.created_at <= end_date
        )
        
        query = query.group_by(
            InstallationStatus.name
        ).order_by(
            InstallationStatus.name
        ).all()
        
        # Create status items
        status_items = [
            InstallationStatusCountItem(
                status_name=item.status_name,
                permanent_count=item.permanent_count,
                temporary_count=item.temporary_count,
                total_count=item.total_count,
                percentage=(item.total_count / total_requests * 100) if total_requests > 0 else 0
            )
            for item in query
        ]
        
        return InstallationStatusReport(
            start_date=start_date,
            end_date=end_date,
            total_requests=total_requests,
            statuses=status_items
        )
    
    def get_sla_compliance_report(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> SLAComplianceReport:
        """
        Generate SLA compliance report in legacy format.
        
        Args:
            year: Year for the report (if month is provided)
            month: Month for the report (1-12)
            start_date: Start date (if year/month not provided)
            end_date: End date (if year/month not provided)
            
        Returns:
            SLA compliance report
        """
        # Determine date range
        if year and month:
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
                
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        elif not start_date or not end_date:
            raise ValueError("Either year/month or start_date/end_date must be provided")
        
        # Get SLA config from database
        from app.models.sla_config import SLAConfig
        
        sla_configs = self.db.query(SLAConfig).filter(SLAConfig.is_active == True).all()
        
        # If no config found, use default
        default_sla_days = 22  # Default based on database values
            
        # Get completed installations with SLA information by branch
        query = self.db.query(
            Branch.branch_code,
            Branch.name.label('branch_name'),
            func.count(InstallationRequest.id).label('total_completed'),
            func.sum(case(
                (InstallationRequest.updated_at - InstallationRequest.created_at <= timedelta(days=default_sla_days), 1),
                else_=0
            )).label('completed_within_sla'),
            func.avg(func.extract('epoch', InstallationRequest.updated_at - InstallationRequest.created_at) / 86400).label('avg_completion_days')
        ).join(
            InstallationRequest,
            InstallationRequest.branch_code == Branch.ba_code
        ).filter(
            InstallationRequest.status_id == 4,  # Completed status
            InstallationRequest.created_at >= start_date,
            InstallationRequest.created_at <= end_date
        ).group_by(
            Branch.branch_code,
            Branch.name
        ).order_by(
            Branch.branch_code
        ).all()
        
        # Create branch items
        branch_items = []
        total_completed = 0
        total_within_sla = 0
        
        for item in query:
            total_completed += item.total_completed
            total_within_sla += item.completed_within_sla
            completed_exceeded_sla = item.total_completed - item.completed_within_sla
            
            branch_items.append(
                BranchSLAItem(
                    branch_code=item.branch_code,
                    branch_name=item.branch_name,
                    total_completed=item.total_completed,
                    completed_within_sla=item.completed_within_sla,
                    completed_exceeded_sla=completed_exceeded_sla,
                    sla_percentage=(item.completed_within_sla / item.total_completed * 100) 
                                if item.total_completed > 0 else 0,
                    avg_completion_days=item.avg_completion_days or 0
                )
            )
        
        # Calculate totals
        total_exceeded_sla = total_completed - total_within_sla
        overall_sla_percentage = (total_within_sla / total_completed * 100) if total_completed > 0 else 0
        
        return SLAComplianceReport(
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date,
            total_completed=total_completed,
            total_within_sla=total_within_sla,
            total_exceeded_sla=total_exceeded_sla,
            overall_sla_percentage=overall_sla_percentage,
            branches=branch_items
        )
    
    def get_daily_installation_report(
        self,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None
    ) -> DailyInstallationReport:
        """
        Generate daily installation report in legacy format.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            branch_id: Optional branch ID filter
            
        Returns:
            Daily installation report
        """
        # Get branch info if provided
        branch_code = None
        branch_name = None
        
        if branch_id:
            branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
            if branch:
                branch_code = branch.ba_code
                branch_name = branch.name
            
        # Get daily installation counts
        query = self.db.query(
            func.date(InstallationRequest.created_at).label('date'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 1, 1),
                else_=0
            )).label('permanent_count'),
            func.sum(case(
                (InstallationRequest.installation_type_id == 2, 1),
                else_=0
            )).label('temporary_count'),
            func.count(InstallationRequest.id).label('total_count')
        )
        
        # Apply filters
        query = query.filter(
            InstallationRequest.created_at >= start_date,
            InstallationRequest.created_at <= end_date
        )
        
        if branch_id and branch_code:
            query = query.filter(InstallationRequest.branch_code == branch_code)
            
        # Finalize query
        query = query.group_by(
            func.date(InstallationRequest.created_at)
        ).order_by(
            func.date(InstallationRequest.created_at)
        )
        
        # Execute query
        results = query.all()
        
        # Create daily items
        daily_items = [
            DailyInstallationCountItem(
                date=item.date,
                permanent_count=item.permanent_count,
                temporary_count=item.temporary_count,
                total_count=item.total_count
            )
            for item in results
        ]
        
        # Calculate totals
        total_permanent = sum(item.permanent_count for item in daily_items)
        total_temporary = sum(item.temporary_count for item in daily_items)
        grand_total = total_permanent + total_temporary
        
        return DailyInstallationReport(
            start_date=start_date,
            end_date=end_date,
            branch_code=branch_code,
            branch_name=branch_name,
            total_permanent=total_permanent,
            total_temporary=total_temporary,
            grand_total=grand_total,
            daily_data=daily_items
        )
    
    def get_target_progress_report(
        self,
        year: int,
        month: int,
        installation_type_id: int
    ) -> TargetProgressReport:
        """
        Generate target progress report in legacy format.
        
        Args:
            year: Year for the report
            month: Month for the report (1-12)
            installation_type_id: Installation type ID (1 for permanent, 2 for temporary)
            
        Returns:
            Target progress report
        """
        # Validate month
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
            
        # Get installation type name
        installation_type = self.db.query(InstallationType).filter(
            InstallationType.id == installation_type_id
        ).first()
        
        if not installation_type:
            raise ValueError(f"Invalid installation type ID: {installation_type_id}")
            
        # Get date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        # Get targets for the month and installation type
        targets = self.db.query(
            Target
        ).filter(
            Target.year == year,
            Target.month == month,
            Target.installation_type_id == installation_type_id
        ).all()
        
        if not targets:
            return TargetProgressReport(
                year=year,
                month=month,
                installation_type=installation_type.name,
                total_target=0,
                total_achieved=0,
                total_remaining=0,
                overall_progress=0,
                branches=[]
            )
            
        # Create progress items
        progress_items = []
        total_target = 0
        total_achieved = 0
        
        for target in targets:
            branch = self.db.query(Branch).filter(Branch.ba_code == target.branch_code).first()
            if not branch:
                continue
                
            # Get achievement count (completed installations)
            achieved = self.db.query(InstallationRequest).filter(
                InstallationRequest.branch_code == target.branch_code,
                InstallationRequest.installation_type_id == installation_type_id,
                InstallationRequest.status_id == 4,  # Completed status
                InstallationRequest.created_at >= start_date,
                InstallationRequest.created_at <= end_date
            ).count()
            
            remaining = max(0, target.target_count - achieved)
            progress_percentage = (achieved / target.target_count * 100) if target.target_count > 0 else 0
            
            total_target += target.target_count
            total_achieved += achieved
            
            progress_items.append(
                TargetProgressItem(
                    branch_code=branch.branch_code,
                    branch_name=branch.name,
                    target=target.target_count,
                    achieved=achieved,
                    remaining=remaining,
                    progress_percentage=progress_percentage
                )
            )
            
        # Calculate totals
        total_remaining = max(0, total_target - total_achieved)
        overall_progress = (total_achieved / total_target * 100) if total_target > 0 else 0
        
        return TargetProgressReport(
            year=year,
            month=month,
            installation_type=installation_type.name,
            total_target=total_target,
            total_achieved=total_achieved,
            total_remaining=total_remaining,
            overall_progress=overall_progress,
            branches=sorted(progress_items, key=lambda x: x.branch_code)
        ) 