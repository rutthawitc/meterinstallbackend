"""
Report service for generating various report data.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func, case, distinct, extract, and_, or_, text
from sqlalchemy.orm import Session

from app.models.installation_request import InstallationRequest
from app.models.installation_type import InstallationType
from app.models.installation_status import InstallationStatus
from app.models.branch import Branch
from app.models.target import Target
from app.schemas.report import (
    InstallationSummaryReport, InstallationStatItem,
    InstallationTrendReport, DailyInstallationStat,
    SLAReport, SLAStatItem,
    BranchPerformanceReport, BranchPerformanceItem,
    TargetVsActualReport, TargetVsActualItem,
    ReportParams
)

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating reports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_installation_summary(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        branch_code: Optional[str] = None
    ) -> InstallationSummaryReport:
        """
        Generate installation summary report.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            branch_code: Optional branch code filter
            
        Returns:
            Installation summary report
        """
        try:
            # Base query
            query = self.db.query(InstallationRequest)
            
            # Apply filters
            if start_date:
                query = query.filter(InstallationRequest.created_at >= start_date)
            if end_date:
                next_day = end_date + timedelta(days=1)
                query = query.filter(InstallationRequest.created_at < next_day)
            if branch_code:
                query = query.filter(InstallationRequest.branch_code == branch_code)
                
            # Get total count
            total_requests = query.count()
            
            if total_requests == 0:
                # Return empty report if no data
                return InstallationSummaryReport(
                    total_requests=0,
                    completed=0,
                    in_progress=0,
                    pending=0,
                    cancelled=0,
                    completion_rate=0.0,
                    by_type=[],
                    by_branch=[],
                    by_status=[]
                )
            
            # Create filter conditions for subsequent queries
            filter_conditions = []
            if start_date:
                filter_conditions.append(InstallationRequest.created_at >= start_date)
            if end_date:
                next_day = end_date + timedelta(days=1)
                filter_conditions.append(InstallationRequest.created_at < next_day)
            if branch_code:
                filter_conditions.append(InstallationRequest.branch_code == branch_code)
            
            # Get status counts
            status_counts = self.db.query(
                InstallationRequest.status_id,
                InstallationStatus.name,
                func.count(InstallationRequest.id).label('count')
            ).join(
                InstallationStatus,
                InstallationRequest.status_id == InstallationStatus.id
            ).group_by(
                InstallationRequest.status_id,
                InstallationStatus.name
            )
            
            # Apply the same filters as the base query
            if filter_conditions:
                status_counts = status_counts.filter(*filter_conditions)
                
            status_counts = status_counts.all()
            
            # Convert to dictionary for easier access
            status_map = {
                status.lower(): count for status_id, status, count in status_counts
            }
            
            # Calculate counts
            completed = status_map.get('completed', 0)
            in_progress = status_map.get('in progress', 0)
            pending = status_map.get('pending', 0) + status_map.get('new', 0)
            cancelled = status_map.get('cancelled', 0)
            
            # Calculate completion rate
            completion_rate = (completed / total_requests * 100) if total_requests > 0 else 0
            
            # Get statistics by type
            type_stats = self.db.query(
                InstallationType.name,
                func.count(InstallationRequest.id).label('count')
            ).join(
                InstallationRequest,
                InstallationRequest.installation_type_id == InstallationType.id
            ).group_by(
                InstallationType.name
            )
            
            # Apply filters
            if filter_conditions:
                type_stats = type_stats.filter(*filter_conditions)
                
            type_stats = type_stats.all()
            
            by_type = [
                InstallationStatItem(
                    name=name,
                    value=count,
                    percentage=(count / total_requests * 100) if total_requests > 0 else 0
                )
                for name, count in type_stats
            ]
            
            # Get statistics by branch
            branch_stats = self.db.query(
                Branch.name,
                func.count(InstallationRequest.id).label('count')
            ).join(
                InstallationRequest,
                InstallationRequest.branch_code == Branch.ba_code
            ).group_by(
                Branch.name
            )
            
            # Apply filters
            if filter_conditions:
                branch_stats = branch_stats.filter(*filter_conditions)
                
            branch_stats = branch_stats.all()
            
            by_branch = [
                InstallationStatItem(
                    name=name or "Unknown Branch",
                    value=count,
                    percentage=(count / total_requests * 100) if total_requests > 0 else 0
                )
                for name, count in branch_stats
            ]
            
            # Get statistics by status
            by_status = [
                InstallationStatItem(
                    name=status or "Unknown Status",
                    value=count,
                    percentage=(count / total_requests * 100) if total_requests > 0 else 0
                )
                for status_id, status, count in status_counts
            ]
            
            return InstallationSummaryReport(
                total_requests=total_requests,
                completed=completed,
                in_progress=in_progress,
                pending=pending,
                cancelled=cancelled,
                completion_rate=completion_rate,
                by_type=by_type,
                by_branch=by_branch,
                by_status=by_status
            )
        except Exception as e:
            logger.error(f"Error in get_installation_summary: {str(e)}", exc_info=True)
            raise
    
    def get_installation_trend(
        self,
        start_date: date,
        end_date: date,
        branch_code: Optional[str] = None,
        installation_type_id: Optional[int] = None
    ) -> InstallationTrendReport:
        """
        Generate installation trend report.
        
        Args:
            start_date: Start date for trend
            end_date: End date for trend
            branch_code: Optional branch code filter
            installation_type_id: Optional installation type ID filter
            
        Returns:
            Installation trend report
        """
        try:
            # Ensure start_date <= end_date
            if start_date > end_date:
                start_date, end_date = end_date, start_date
                
            # Get daily counts
            query = self.db.query(
                func.date(InstallationRequest.created_at).label('date'),
                func.count(InstallationRequest.id).label('total'),
                func.sum(
                    case(
                        (InstallationRequest.installation_type_id == 1, 1),
                        else_=0
                    )
                ).label('permanent'),
                func.sum(
                    case(
                        (InstallationRequest.installation_type_id == 2, 1),
                        else_=0
                    )
                ).label('temporary_count')
            ).filter(
                InstallationRequest.created_at >= start_date,
                InstallationRequest.created_at < end_date + timedelta(days=1)
            )
            
            if branch_code:
                query = query.filter(InstallationRequest.branch_code == branch_code)
                
            if installation_type_id:
                query = query.filter(InstallationRequest.installation_type_id == installation_type_id)
                
            daily_data = query.group_by(
                func.date(InstallationRequest.created_at)
            ).order_by(
                func.date(InstallationRequest.created_at)
            ).all()
            
            # Create daily stats objects
            daily_stats = [
                DailyInstallationStat(
                    date=day_data.date,
                    total=day_data.total,
                    permanent=day_data.permanent,
                    temporary=day_data.temporary_count
                )
                for day_data in daily_data
            ]
            
            # Calculate totals and averages
            if not daily_stats:
                return InstallationTrendReport(
                    daily_stats=[],
                    total_in_period=0,
                    avg_daily=0.0,
                    max_daily=0,
                    min_daily=0
                )
                
            total_in_period = sum(stat.total for stat in daily_stats)
            
            # Calculate days in period considering there might be days with no installations
            days_in_period = (end_date - start_date).days + 1
            avg_daily = total_in_period / days_in_period if days_in_period > 0 else 0
            
            max_daily = max(stat.total for stat in daily_stats) if daily_stats else 0
            min_daily = min(stat.total for stat in daily_stats) if daily_stats else 0
            
            return InstallationTrendReport(
                daily_stats=daily_stats,
                total_in_period=total_in_period,
                avg_daily=avg_daily,
                max_daily=max_daily,
                min_daily=min_daily
            )
        except Exception as e:
            logger.error(f"Error in get_installation_trend: {str(e)}", exc_info=True)
            raise
    
    def get_sla_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        branch_code: Optional[str] = None,
        installation_type_id: Optional[int] = None
    ) -> SLAReport:
        """
        Generate SLA performance report.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            branch_code: Optional branch code filter
            installation_type_id: Optional installation type ID filter
            
        Returns:
            SLA performance report
        """
        try:
            # Get SLA config from database
            from app.models.sla_config import SLAConfig
            
            sla_configs = self.db.query(SLAConfig).filter(SLAConfig.is_active == True).all()
            
            # If no config found, use default
            default_sla_days = 22  # Default based on database values
            if sla_configs:
                # Sort by fee_threshold for easier lookup later
                sla_configs = sorted(sla_configs, key=lambda x: x.fee_threshold or float('inf'))
            
            # Get completed requests with SLA data
            # Use completion_date instead of updated_at since we're pulling data from Oracle
            query = self.db.query(
                InstallationRequest,
                Branch.name.label('branch_name'),
                InstallationType.name.label('type_name'),
                case(
                    (InstallationRequest.completion_date != None, 
                     (func.extract('epoch', InstallationRequest.completion_date) - 
                      func.extract('epoch', InstallationRequest.created_at)) / 86400),  # Convert seconds to days
                    else_=None
                ),
                InstallationRequest.installation_fee
            ).join(
                Branch, InstallationRequest.branch_code == Branch.ba_code
            ).join(
                InstallationType, InstallationRequest.installation_type_id == InstallationType.id
            ).filter(
                InstallationRequest.status_id == 4  # Completed status ID
            )
            
            if start_date:
                query = query.filter(InstallationRequest.created_at >= start_date)
            if end_date:
                next_day = end_date + timedelta(days=1)
                query = query.filter(InstallationRequest.created_at < next_day)
            if branch_code:
                query = query.filter(InstallationRequest.branch_code == branch_code)
            if installation_type_id:
                query = query.filter(InstallationRequest.installation_type_id == installation_type_id)
                
            results = query.all()
            
            if not results:
                return SLAReport(
                    overall_performance=0.0,
                    total_requests=0,
                    within_sla=0,
                    exceeded_sla=0,
                    avg_completion_days=0.0,
                    by_branch=[],
                    by_type=[]
                )
            
            # Process results
            total_requests = len(results)
            
            # Filter out items where days_taken is None
            valid_results = [r for r in results if r[3] is not None]
            if not valid_results:
                # Log warning about missing completion dates
                logger.warning(f"No completion dates found for {total_requests} completed requests. SLA report will be empty.")
                return SLAReport(
                    overall_performance=0.0,
                    total_requests=total_requests,
                    within_sla=0,
                    exceeded_sla=0,
                    avg_completion_days=0.0,
                    by_branch=[],
                    by_type=[]
                )
            
            # Function to determine SLA days based on fee
            def get_sla_days(fee):
                if not fee or not sla_configs:
                    return default_sla_days
                
                # Find appropriate SLA config based on fee
                for config in sla_configs:
                    if config.fee_threshold is None or fee <= config.fee_threshold:
                        return config.days
                
                # If no matching config, use the highest threshold or default
                return sla_configs[-1].days if sla_configs else default_sla_days
            
            # Calculate SLA performance
            within_sla = 0
            exceeded_sla = 0
            
            # Group by branch
            branch_data = {}
            # Group by installation type
            type_data = {}
            
            for r in valid_results:
                branch_name = r[1]
                type_name = r[2]
                days_taken = r[3]
                fee = r[4]
                
                # Get SLA days for this request
                sla_days = get_sla_days(fee)
                
                # Check if within SLA
                within = days_taken <= sla_days
                
                if within:
                    within_sla += 1
                else:
                    exceeded_sla += 1
                
                # Add to branch data
                if branch_name not in branch_data:
                    branch_data[branch_name] = {
                        'total': 0,
                        'within_sla': 0,
                        'exceeded_sla': 0,
                        'total_days': 0
                    }
                    
                branch_data[branch_name]['total'] += 1
                branch_data[branch_name]['within_sla'] += 1 if within else 0
                branch_data[branch_name]['exceeded_sla'] += 0 if within else 1
                branch_data[branch_name]['total_days'] += days_taken
                
                # Add to type data
                if type_name not in type_data:
                    type_data[type_name] = {
                        'total': 0,
                        'within_sla': 0,
                        'exceeded_sla': 0,
                        'total_days': 0
                    }
                    
                type_data[type_name]['total'] += 1
                type_data[type_name]['within_sla'] += 1 if within else 0
                type_data[type_name]['exceeded_sla'] += 0 if within else 1
                type_data[type_name]['total_days'] += days_taken
            
            # Calculate overall performance
            overall_performance = (within_sla / len(valid_results) * 100) if len(valid_results) > 0 else 0
            avg_completion_days = sum(r[3] for r in valid_results) / len(valid_results) if len(valid_results) > 0 else 0
            
            by_branch = [
                SLAStatItem(
                    name=branch_name,
                    total=data['total'],
                    within_sla=data['within_sla'],
                    exceeded_sla=data['exceeded_sla'],
                    sla_performance=(data['within_sla'] / data['total'] * 100) if data['total'] > 0 else 0,
                    avg_days=(data['total_days'] / data['total']) if data['total'] > 0 else 0
                )
                for branch_name, data in branch_data.items()
            ]
            
            by_type = [
                SLAStatItem(
                    name=type_name,
                    total=data['total'],
                    within_sla=data['within_sla'],
                    exceeded_sla=data['exceeded_sla'],
                    sla_performance=(data['within_sla'] / data['total'] * 100) if data['total'] > 0 else 0,
                    avg_days=(data['total_days'] / data['total']) if data['total'] > 0 else 0
                )
                for type_name, data in type_data.items()
            ]
            
            return SLAReport(
                overall_performance=overall_performance,
                total_requests=total_requests,
                within_sla=within_sla,
                exceeded_sla=exceeded_sla,
                avg_completion_days=avg_completion_days,
                by_branch=by_branch,
                by_type=by_type
            )
        except Exception as e:
            logger.error(f"Error in get_sla_performance: {str(e)}", exc_info=True)
            raise
    
    def get_branch_performance(
        self,
        year: int,
        month: Optional[int] = None
    ) -> BranchPerformanceReport:
        """
        Generate branch performance report.
        
        Args:
            year: Year for report
            month: Optional month for report
            
        Returns:
            Branch performance report
        """
        try:
            # Get SLA config from database
            from app.models.sla_config import SLAConfig
            
            sla_configs = self.db.query(SLAConfig).filter(SLAConfig.is_active == True).all()
            
            # If no config found, use default
            default_sla_days = 22  # Default based on database values
            if sla_configs:
                # Sort by fee_threshold for easier lookup later
                sla_configs = sorted(sla_configs, key=lambda x: x.fee_threshold or float('inf'))
                
            # Function to determine SLA days based on fee
            def get_sla_days(fee):
                if not fee or not sla_configs:
                    return default_sla_days
                
                # Find appropriate SLA config based on fee
                for config in sla_configs:
                    if config.fee_threshold is None or fee <= config.fee_threshold:
                        return config.days
                
                # If no matching config, use the highest threshold or default
                return sla_configs[-1].days if sla_configs else default_sla_days
            
            # Get date range for filter
            if month:
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            else:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
            
            # Get all branches
            branches = self.db.query(Branch).all()
            
            if not branches:
                return BranchPerformanceReport(
                    branches=[],
                    top_performing=[],
                    needs_improvement=[]
                )
            
            # Get branch performance data
            branch_items = []
            
            for branch in branches:
                # Get installation requests for branch
                query = self.db.query(InstallationRequest).filter(
                    InstallationRequest.branch_code == branch.ba_code,
                    InstallationRequest.created_at >= start_date,
                    InstallationRequest.created_at <= end_date + timedelta(days=1)
                )
                
                total_requests = query.count()
                
                if total_requests == 0:
                    # Skip branches with no data
                    continue
                    
                completed = query.filter(InstallationRequest.status_id == 4).count()  # Completed status ID
                in_progress = query.filter(InstallationRequest.status_id == 2).count()  # In Progress status ID
                pending = query.filter(InstallationRequest.status_id.in_([1, 3])).count()  # New, Pending status IDs
                
                completion_rate = (completed / total_requests * 100) if total_requests > 0 else 0
                
                # Get SLA performance using PostgreSQL functions
                # Use completion_date instead of updated_at since we're pulling data from Oracle
                sla_query = self.db.query(
                    InstallationRequest.id,
                    case(
                        (InstallationRequest.completion_date != None, 
                         (func.extract('epoch', InstallationRequest.completion_date) - 
                          func.extract('epoch', InstallationRequest.created_at)) / 86400),  # Convert seconds to days
                        else_=None
                    ),
                    InstallationRequest.installation_fee
                ).filter(
                    InstallationRequest.branch_code == branch.ba_code,
                    InstallationRequest.status_id == 4,  # Completed status ID
                    InstallationRequest.created_at >= start_date,
                    InstallationRequest.created_at <= end_date + timedelta(days=1)
                )
                
                sla_results = sla_query.all()
                
                if sla_results:
                    # Filter out items where days_taken is None
                    valid_results = [r for r in sla_results if r[1] is not None]
                    
                    if valid_results:
                        within_sla = 0
                        total_days = 0
                        
                        for result in valid_results:
                            days_taken = result[1]
                            fee = result[2]
                            sla_days = get_sla_days(fee)
                            
                            if days_taken <= sla_days:
                                within_sla += 1
                            
                            total_days += days_taken
                        
                        sla_performance = (within_sla / len(valid_results) * 100) if len(valid_results) > 0 else 0
                        avg_completion_days = total_days / len(valid_results) if len(valid_results) > 0 else 0
                    else:
                        # Log warning about missing completion dates
                        logger.warning(f"No valid completion dates for branch {branch.name} ({branch.ba_code}). SLA performance will be 0.")
                        sla_performance = 0
                        avg_completion_days = 0
                else:
                    sla_performance = 0
                    avg_completion_days = 0
                
                # Create branch performance item
                branch_item = BranchPerformanceItem(
                    branch_code=branch.ba_code,
                    branch_name=branch.name,
                    original_branch_code=branch.branch_code,
                    total_requests=total_requests,
                    completed=completed,
                    in_progress=in_progress,
                    pending=pending,
                    completion_rate=completion_rate,
                    sla_performance=sla_performance,
                    avg_completion_days=avg_completion_days
                )
                
                branch_items.append(branch_item)
            
            if not branch_items:
                return BranchPerformanceReport(
                    branches=[],
                    top_performing=[],
                    needs_improvement=[]
                )
            
            # Sort by performance for top and bottom lists
            top_performing = sorted(branch_items, key=lambda x: (x.completion_rate, x.sla_performance), reverse=True)[:5]
            needs_improvement = sorted(branch_items, key=lambda x: (x.completion_rate, x.sla_performance))[:5]
            
            return BranchPerformanceReport(
                branches=branch_items,
                top_performing=top_performing,
                needs_improvement=needs_improvement
            )
        except Exception as e:
            logger.error(f"Error in get_branch_performance: {str(e)}", exc_info=True)
            raise
    
    def get_target_vs_actual(
        self,
        year: int,
        month: Optional[int] = None,
        branch_code: Optional[str] = None
    ) -> TargetVsActualReport:
        """
        Generate target vs actual performance report.
        
        Args:
            year: Year for report
            month: Optional month for report
            branch_code: Optional branch code filter (ba_code)
            
        Returns:
            Target vs actual performance report
        """
        try:
            # Get targets
            query = self.db.query(Target)
            
            if year:
                query = query.filter(Target.year == year)
            if month:
                query = query.filter(Target.month == month)
            if branch_code:
                # Directly filter by branch_code which is ba_code in the branches table
                query = query.filter(Target.branch_code == branch_code)
                
            targets = query.all()
            
            if not targets:
                return TargetVsActualReport(
                    overall_achievement=0.0,
                    total_target=0,
                    total_actual=0,
                    total_remaining=0,
                    by_month=[],
                    by_branch=[],
                    by_type=[]
                )
            
            # Get total target count
            total_target = sum(target.target_count for target in targets)
            
            # Get actual counts
            actual_counts = {}
            remaining_counts = {}
            
            for target in targets:
                # Determine date range
                if target.month:
                    start_date = date(target.year, target.month, 1)
                    if target.month == 12:
                        end_date = date(target.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = date(target.year, target.month + 1, 1) - timedelta(days=1)
                else:
                    start_date = date(target.year, 1, 1)
                    end_date = date(target.year, 12, 31)
                
                # Get completed installations
                actual_count = self.db.query(InstallationRequest).filter(
                    InstallationRequest.branch_code == target.branch_code,
                    InstallationRequest.installation_type_id == target.installation_type_id,
                    InstallationRequest.status_id == 4,  # Completed status ID
                    InstallationRequest.created_at >= start_date,
                    InstallationRequest.created_at <= end_date + timedelta(days=1)
                ).count()
                
                # Store counts
                key = f"{target.year}-{target.month}-{target.branch_code}-{target.installation_type_id}"
                actual_counts[key] = actual_count
                remaining_counts[key] = max(0, target.target_count - actual_count)
            
            # Calculate total actual and remaining
            total_actual = sum(actual_counts.values())
            total_remaining = sum(remaining_counts.values())
            
            # Calculate overall achievement
            overall_achievement = (total_actual / total_target * 100) if total_target > 0 else 0
            
            # Group by month
            month_data = {}
            for target in targets:
                month_key = f"{target.year}-{target.month if target.month else 'all'}"
                month_name = f"{target.month}/{target.year}" if target.month else f"Year {target.year}"
                
                if month_key not in month_data:
                    month_data[month_key] = {
                        'name': month_name,
                        'target': 0,
                        'actual': 0
                    }
                
                target_key = f"{target.year}-{target.month}-{target.branch_code}-{target.installation_type_id}"
                month_data[month_key]['target'] += target.target_count
                month_data[month_key]['actual'] += actual_counts.get(target_key, 0)
            
            by_month = [
                TargetVsActualItem(
                    name=data['name'],
                    target=data['target'],
                    actual=data['actual'],
                    percentage=(data['actual'] / data['target'] * 100) if data['target'] > 0 else 0,
                    remaining=max(0, data['target'] - data['actual'])
                )
                for month_key, data in month_data.items()
            ]
            
            # Group by branch
            branch_data = {}
            for target in targets:
                # Access branch data through relationship
                branch = target.branch
                if not branch:
                    continue
                    
                branch_key = target.branch_code
                
                if branch_key not in branch_data:
                    branch_data[branch_key] = {
                        'name': branch.name,
                        'target': 0,
                        'actual': 0
                    }
                
                target_key = f"{target.year}-{target.month}-{target.branch_code}-{target.installation_type_id}"
                branch_data[branch_key]['target'] += target.target_count
                branch_data[branch_key]['actual'] += actual_counts.get(target_key, 0)
            
            by_branch = [
                TargetVsActualItem(
                    name=data['name'],
                    target=data['target'],
                    actual=data['actual'],
                    percentage=(data['actual'] / data['target'] * 100) if data['target'] > 0 else 0,
                    remaining=max(0, data['target'] - data['actual'])
                )
                for branch_key, data in branch_data.items()
            ]
            
            # Group by installation type
            type_data = {}
            for target in targets:
                installation_type = self.db.query(InstallationType).filter(
                    InstallationType.id == target.installation_type_id
                ).first()
                
                if not installation_type:
                    continue
                    
                type_key = str(target.installation_type_id)
                
                if type_key not in type_data:
                    type_data[type_key] = {
                        'name': installation_type.name,
                        'target': 0,
                        'actual': 0
                    }
                
                target_key = f"{target.year}-{target.month}-{target.branch_code}-{target.installation_type_id}"
                type_data[type_key]['target'] += target.target_count
                type_data[type_key]['actual'] += actual_counts.get(target_key, 0)
            
            by_type = [
                TargetVsActualItem(
                    name=data['name'],
                    target=data['target'],
                    actual=data['actual'],
                    percentage=(data['actual'] / data['target'] * 100) if data['target'] > 0 else 0,
                    remaining=max(0, data['target'] - data['actual'])
                )
                for type_key, data in type_data.items()
            ]
            
            return TargetVsActualReport(
                overall_achievement=overall_achievement,
                total_target=total_target,
                total_actual=total_actual,
                total_remaining=total_remaining,
                by_month=by_month,
                by_branch=by_branch,
                by_type=by_type
            )
        except Exception as e:
            logger.error(f"Error in get_target_vs_actual: {str(e)}", exc_info=True)
            raise

    def generate_report(self, params: ReportParams) -> Dict[str, Any]:
        """
        Generate reports based on provided parameters
        
        Args:
            params: Report parameters
            
        Returns:
            Dictionary with generated reports
        """
        try:
            # Set default dates if not provided
            if not params.start_date or not params.end_date:
                year = params.year or datetime.now().year
                month = params.month or datetime.now().month
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            else:
                start_date = params.start_date
                end_date = params.end_date
            
            # Generate reports
            installation_summary = self.get_installation_summary(
                start_date=start_date,
                end_date=end_date,
                branch_code=params.branch_code
            )
            
            # Add additional reports as needed
            
            return {
                "installation_summary": installation_summary,
                # Add more reports as they're implemented
            }
        except Exception as e:
            logger.error(f"Error in generate_report: {str(e)}", exc_info=True)
            raise 