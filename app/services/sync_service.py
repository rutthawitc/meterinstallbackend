"""
Service for syncing data from Oracle database.
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.oracle import oracle_db
from app.models.sync_log import SyncLog
from app.models.installation_request import InstallationRequest
from app.models.customer import Customer
from app.models.holiday import Holiday
from app.models.user import User
from app.models.branch import Branch
from app.models.installation_status import InstallationStatus
from app.models.installation_type import InstallationType
from app.models.meter_size import MeterSize
from app.models.region import Region

# Configure logging
logger = logging.getLogger(__name__)


class SyncService:
    """
    Service for syncing data from Oracle database.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the sync service.
        
        Args:
            db: Database session.
        """
        self.db = db
        self.sync_log = None
    
    def _start_sync_log(self, sync_type: str, user_id: Optional[int] = None, is_full_sync: bool = True, query_params: Optional[Dict[str, Any]] = None) -> SyncLog:
        """
        Start a new sync log entry.
        
        Args:
            sync_type: Type of sync (e.g., "installation_request", "holiday").
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            query_params: Parameters used for the sync query.
            
        Returns:
            The created SyncLog object.
        """
        sync_log = SyncLog(
            sync_type=sync_type,
            start_time=datetime.utcnow(),
            status="running",
            is_full_sync=is_full_sync,
            user_id=user_id,
            query_params=json.dumps(query_params) if query_params else None
        )
        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)
        self.sync_log = sync_log
        logger.info(f"Started {sync_type} sync, log ID: {sync_log.id}")
        return sync_log
    
    def _update_sync_log(self, records_processed: int = 0, records_created: int = 0, 
                        records_updated: int = 0, records_skipped: int = 0, 
                        records_failed: int = 0, reset_counters: bool = False) -> None:
        """
        Update the current sync log entry.
        
        Args:
            records_processed: Number of records processed.
            records_created: Number of records created.
            records_updated: Number of records updated.
            records_skipped: Number of records skipped.
            records_failed: Number of records with errors.
            reset_counters: Whether to reset counters before updating (for final updates).
        """
        if not self.sync_log:
            logger.warning("No active sync log to update")
            return
        
        # Reset counters if requested (for final updates to avoid double counting)
        if reset_counters:
            self.sync_log.records_processed = 0
            self.sync_log.records_created = 0
            self.sync_log.records_updated = 0
            self.sync_log.records_skipped = 0
            self.sync_log.records_failed = 0
            
        # Update with new values
        self.sync_log.records_processed += records_processed
        self.sync_log.records_created += records_created
        self.sync_log.records_updated += records_updated
        self.sync_log.records_skipped += records_skipped
        self.sync_log.records_failed += records_failed
        self.db.commit()
        self.db.refresh(self.sync_log)
        
        # Log details for debugging
        logger.debug(f"Updated sync log: processed={self.sync_log.records_processed}, "
                    f"created={self.sync_log.records_created}, updated={self.sync_log.records_updated}, "
                    f"skipped={self.sync_log.records_skipped}, failed={self.sync_log.records_failed}")
    
    def _end_sync_log(self, status: str = "success", error_message: Optional[str] = None, 
                     sync_details: Optional[Dict[str, Any]] = None) -> SyncLog:
        """
        End the current sync log entry.
        
        Args:
            status: Status of the sync ("success" or "failed").
            error_message: Error message if the sync failed.
            sync_details: Additional details about the sync.
            
        Returns:
            The updated SyncLog object.
        """
        if not self.sync_log:
            logger.warning("No active sync log to end")
            return None
            
        self.sync_log.end_time = datetime.utcnow()
        
        # Determine actual status based on statistics
        total_processed = self.sync_log.records_processed
        total_failed = self.sync_log.records_failed
        
        # Override status if significant failure rate
        if total_processed > 0:
            # If all records failed or failure rate is over 90%, mark as failed
            if total_failed == total_processed or (total_failed / total_processed) > 0.9:
                status = "failed"
                if not error_message:
                    error_message = f"Sync failed: {total_failed} of {total_processed} records failed"
            # If failure rate is between 10% and 90%, mark as partial success
            elif (total_failed / total_processed) > 0.1:
                status = "partial"
                if not error_message:
                    error_message = f"Partial sync: {total_failed} of {total_processed} records failed"
                    
        self.sync_log.status = status
        if error_message:
            self.sync_log.error_message = error_message
        if sync_details:
            self.sync_log.sync_details = json.dumps(sync_details)
            
        self.db.commit()
        self.db.refresh(self.sync_log)
        
        duration = (self.sync_log.end_time - self.sync_log.start_time).total_seconds()
        logger.info(f"Ended {self.sync_log.sync_type} sync, log ID: {self.sync_log.id}, status: {status}, duration: {duration:.2f} seconds")
        logger.info(f"Sync statistics: processed={self.sync_log.records_processed}, created={self.sync_log.records_created}, updated={self.sync_log.records_updated}, skipped={self.sync_log.records_skipped}, failed={self.sync_log.records_failed}")
        
        result = self.sync_log
        self.sync_log = None
        return result
    
    def sync_holidays(self, user_id: Optional[int] = None, is_full_sync: bool = True, 
                     year: Optional[int] = None) -> SyncLog:
        """
        Sync holidays from Oracle database.
        
        Args:
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            year: Specific year to sync holidays for.
            
        Returns:
            The SyncLog object with the sync results.
        """
        query_params = {"year": year} if year else {}
        self._start_sync_log("holiday", user_id, is_full_sync, query_params)
        
        try:
            # Build the query - using the same query structure as the old system
            query = """
                SELECT TO_CHAR(HOLIDAY_DATE, 'YYYY-MM-DD') AS HOLIDAY_DATE,
                    DESC_TH AS DESCRIPTION, 
                    UPDATE_BY AS LASTUPDATE,
                    1 AS IS_NATIONAL_HOLIDAY,  -- Default to True for national holidays
                    CASE 
                        WHEN REGEXP_LIKE(DESC_TH, '(วันขึ้นปีใหม่|วันสงกรานต์|วันแรงงาน|วันวิสาขบูชา|วันเฉลิมพระชนมพรรษา|วันจักรี|วันรัฐธรรมนูญ|วันปิยมหาราช)') THEN 1
                        ELSE 0
                    END AS IS_REPEATING_YEARLY
                FROM PWACIS.TB_MS_HOLIDAY
                WHERE NVL(DESC_EN, ' ') NOT IN ('Sunday', 'Saturday')
            """
            
            if year:
                query += " AND EXTRACT(YEAR FROM HOLIDAY_DATE) = :year"
                
            query += " ORDER BY HOLIDAY_DATE"
            
            # Execute the query
            with oracle_db as db:
                logger.info(f"Executing Oracle query: {query}")
                holidays = db.execute_query(query, {"year": year} if year else None)
            
            processed = 0
            created = 0
            updated = 0
            skipped = 0
            failed = 0
            
            logger.info(f"Found {len(holidays)} holidays to process")
            
            for holiday in holidays:
                try:
                    processed += 1
                    holiday_date_str = holiday.get("holiday_date")
                    
                    try:
                        # Convert string date to Python date object
                        holiday_date = datetime.strptime(holiday_date_str, "%Y-%m-%d").date()
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error converting date {holiday_date_str}: {str(e)}")
                        failed += 1
                        continue
                    
                    # Check if the holiday already exists
                    existing_holiday = self.db.query(Holiday).filter(Holiday.holiday_date == holiday_date).first()
                    
                    # Get region if specified (not used in this case since old system doesn't have regions for holidays)
                    region_id = None
                    
                    description = holiday.get("description", "")
                    is_national = bool(holiday.get("is_national_holiday", True))
                    is_repeating = bool(holiday.get("is_repeating_yearly", False))
                    original_id = holiday_date_str  # Use date as original_id since there's no ID in the original table
                    
                    if existing_holiday:
                        # Update existing holiday
                        existing_holiday.description = description
                        existing_holiday.is_national_holiday = is_national
                        existing_holiday.is_repeating_yearly = is_repeating
                        existing_holiday.region_id = region_id
                        existing_holiday.original_id = original_id
                        existing_holiday.updated_by = user_id
                        existing_holiday.updated_at = datetime.utcnow()
                        
                        self.db.commit()
                        updated += 1
                        logger.debug(f"Updated holiday: {holiday_date}")
                    else:
                        # Create new holiday
                        new_holiday = Holiday(
                            holiday_date=holiday_date,
                            description=description,
                            is_national_holiday=is_national,
                            is_repeating_yearly=is_repeating,
                            region_id=region_id,
                            original_id=original_id,
                            updated_by=user_id
                        )
                        
                        self.db.add(new_holiday)
                        self.db.commit()
                        created += 1
                        logger.debug(f"Created holiday: {holiday_date}")
                        
                except Exception as e:
                    logger.error(f"Error processing holiday {holiday.get('holiday_date')}: {str(e)}")
                    failed += 1
                    self.db.rollback()
                
                # Update sync log periodically
                if processed % 10 == 0:
                    self._update_sync_log(
                        records_processed=processed, 
                        records_created=created,
                        records_updated=updated,
                        records_skipped=skipped,
                        records_failed=failed
                    )
            
            # Final update
            self._update_sync_log(
                records_processed=processed, 
                records_created=created,
                records_updated=updated,
                records_skipped=skipped,
                records_failed=failed
            )
            
            logger.info(f"Holiday sync completed: {created} created, {updated} updated, {failed} failed")
            return self._end_sync_log("success")
            
        except Exception as e:
            logger.error(f"Error syncing holidays: {str(e)}")
            return self._end_sync_log("failed", str(e))
    
    def sync_installation_requests(self, user_id: Optional[int] = None, is_full_sync: bool = True,
                                 start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                                 branch_code: Optional[str] = None) -> SyncLog:
        """
        Sync installation requests from Oracle database.
        
        Args:
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            start_date: Start date for filtering requests.
            end_date: End date for filtering requests.
            branch_code: Branch code for filtering requests.
            
        Returns:
            The SyncLog object with the sync results.
        """
        query_params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "branch_code": branch_code
        }
        
        self._start_sync_log("installation_request", user_id, is_full_sync, query_params)
        
        try:
            # Build the query - using the query structure from the old system
            query = """
                SELECT 
                    CUS.ID as CUSTOMER_ID,
                    CUS.INSTALL_CUS_TITLE as TITLE,
                    CUS.INSTALL_CUS_NAME as FIRSTNAME,
                    CUS.INSTALL_CUS_SURNAME as LASTNAME,
                    CUS.CARD_ID as ID_CARD,
                    CAI.ADDRESS_NO as ADDRESS,
                    CAI.MOBILE,
                    RH.ID as REQUEST_ID,
                    RH.REQ_NO as REQUEST_NO,
                    RH.CREATED_DATE,
                    RH.UPDATED_DATE,
                    RH.ORG_OWNER_ID,
                    ORG.BA_CODE as BRANCH_CODE,
                    RH.REQ_DATE as REQUEST_DATE,
                    RH.RQFINISHDATE as ESTIMATED_DATE,
                    RH.APP_DATE as APPROVED_DATE,
                    BILL.PAID_DATE as PAYMENT_DATE,
                    REXP.INSTALL_DATE as INSTALLATION_DATE,
                    RH.UPDATED_DATE as COMPLETION_DATE,
                    REXP.ADD_PRICE as INSTALLATION_FEE,
                    BILL.BILL_NO,
                    RH.REMARK as REMARKS,
                    RH.INSTALL_TYPE as INSTALLATION_TYPE_CODE,
                    RH.DOC_STS as STATUS_CODE,
                    RID.METER_SIZE as METER_SIZE_CODE
                FROM PWACIS.TB_TR_REQ_HEAD_INF RH
                LEFT JOIN PWACIS.TB_TR_CUSTOMER_INF CUS ON RH.CUS_ID = CUS.ID
                LEFT JOIN PWACIS.TB_TR_CUSADDR_INF CAI ON RH.CUS_ID = CAI.ID AND CAI.ADDR_TYPE = '1'
                LEFT JOIN PWACIS.TB_TR_REQ_INSTALL_DETAIL RID ON RH.ID = RID.REQ_ID
                LEFT JOIN PWACIS.TB_TR_INSTALL_TRN REXP ON RID.INSTALL_ID = REXP.ID
                LEFT JOIN PWACIS.TB_TR_BILL BILL ON RH.CUS_ID = BILL.CUST_ID AND BILL.BILL_DETAIL = 2 AND BILL.IS_DELETED = 'F'
                LEFT JOIN PWACIS.TB_LT_ORGANIZATION ORG ON RH.ORG_OWNER_ID = ORG.ID
                WHERE RH.INSTALL_TYPE = '1' 
                  AND RH.IS_DELETED = 'F' 
                  AND RH.IS_APPROVED = 'T'
                  AND RH.DOC_STS = '11' 
                  AND (RH.ORG_OWNER_ID IN (1060, 1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 
                                           1070, 1071, 1072, 1073, 1074, 1075, 1076, 1077, 1133, 1134, 
                                           1135, 1245))
            """
            
            params = {}
            
            if start_date:
                query += " AND RH.REQ_DATE >= :start_date"
                params["start_date"] = start_date
                
            if end_date:
                query += " AND RH.REQ_DATE <= :end_date"
                params["end_date"] = end_date
                
            if branch_code:
                query += " AND ORG.BA_CODE = :branch_code"
                params["branch_code"] = branch_code
            
            # Add order by
            query += " ORDER BY RH.REQ_DATE DESC"
                
            # Execute the query in batches
            with oracle_db as db:
                logger.info(f"Executing Oracle query: {query}")
                batches = db.fetch_batch(query, params, batch_size=100)
                
                total_processed = 0
                total_created = 0
                total_updated = 0
                total_skipped = 0
                total_failed = 0
                
                for batch in batches:
                    processed = 0
                    created = 0
                    updated = 0
                    skipped = 0
                    failed = 0
                    
                    logger.info(f"Processing batch of {len(batch)} installation requests")
                    
                    for request in batch:
                        try:
                            processed += 1
                            
                            # Process customer first
                            customer_id = request.get("customer_id")
                            customer = None
                            
                            if customer_id:
                                # Check if customer exists
                                customer = self.db.query(Customer).filter(Customer.original_id == str(customer_id)).first()
                                
                                if not customer:
                                    # Get branch - use ba_code from Oracle database (3-4 digits)
                                    ba_code = str(request.get("branch_code")) if request.get("branch_code") is not None else None
                                    branch = None
                                    if ba_code:
                                        # Search by ba_code (3-4 digit code)
                                        branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                        
                                        if not branch:
                                            logger.warning(f"Branch not found for ba_code: {ba_code}")
                                            
                                            # Try to find the region for this branch (assuming branch code starts with region code)
                                            region_code = ba_code[:1] if len(ba_code) > 0 else None
                                            region = None
                                            if region_code:
                                                region = self.db.query(Region).filter(Region.code == region_code).first()
                                        
                                            # Create a default branch if not exists
                                            branch = Branch(
                                                branch_code=None,  # We don't have the 7-digit branch_code yet
                                                name=f"Branch {ba_code}",
                                                region_id=region.id if region else None,
                                                ba_code=ba_code,
                                                oracle_org_id=request.get("org_owner_id") 
                                            )
                                            self.db.add(branch)
                                            self.db.commit()
                                            self.db.refresh(branch)
                                            logger.info(f"Created new branch with ba_code: {ba_code}")
                                    
                                    # Create customer
                                    # การจัดการค่า NULL สำหรับฟิลด์ที่ต้องการ NOT NULL
                                    title = request.get("title") or ""
                                    firstname = request.get("firstname") or ""
                                    # สำหรับสถานที่ ใช้ชื่อเป็นนามสกุลถ้าไม่มีนามสกุล
                                    lastname = request.get("lastname")
                                    if lastname is None or (isinstance(lastname, str) and lastname.strip() == ""):
                                        # ถ้าไม่มีนามสกุล ใช้ชื่อเป็นนามสกุล หรือถ้าไม่มีทั้งชื่อและนามสกุล ใช้ค่าว่าง
                                        lastname = firstname or "-"
                                    
                                    customer = Customer(
                                        original_id=str(customer_id),
                                        title=title,
                                        firstname=firstname,
                                        lastname=lastname,
                                        id_card=request.get("id_card"),
                                        address=request.get("address"),
                                        mobile=request.get("mobile"),
                                        branch_code=ba_code if branch else None
                                    )
                                    
                                    self.db.add(customer)
                                    self.db.commit()
                                    self.db.refresh(customer)
                                    logger.debug(f"Created new customer: ID {customer.id}, Original ID {customer_id}")
                            
                            # Process installation request
                            request_no = request.get('request_no')
                            
                            # เช็คว่ามี request_no หรือไม่
                            if not request_no:
                                # ถ้าไม่มี request_no ให้ใช้ request_id แทน
                                request_id = request.get('request_id')
                                if request_id:
                                    request_no = f'REQ-{request_id}'
                                    logger.warning(f'Generated request_no from request_id: {request_no}')
                                else:
                                    logger.warning(f'Skipping request without request_no and request_id: {request}')
                                    skipped += 1
                                    continue
                            
                            # Standardize request_no (strip spaces, uppercase)
                            request_no = str(request_no).strip().upper()
                                
                            # Check if installation request exists
                            try:
                                existing_request = self.db.query(InstallationRequest).filter(
                                    func.upper(InstallationRequest.request_no) == request_no
                                ).first()
                            except Exception as e:
                                logger.error(f"Error querying existing request {request_no}: {str(e)}")
                                # Fallback to simpler query if func.upper causes issues
                                existing_request = self.db.query(InstallationRequest).filter(
                                    InstallationRequest.request_no == request_no
                                ).first()
                            
                            # Get branch - use ba_code from Oracle database which is 3-4 digits
                            ba_code = str(request.get('branch_code')) if request.get('branch_code') is not None else None
                            branch = None
                            if ba_code:
                                # Search by ba_code (3-4 digit code)
                                branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                
                                if not branch:
                                    logger.warning(f'Branch not found for ba_code: {ba_code}')
                                    
                                    # Try to find the region for this branch (assuming branch code starts with region code)
                                    region_code = ba_code[:1] if len(ba_code) > 0 else None
                                    region = None
                                    if region_code:
                                        region = self.db.query(Region).filter(Region.code == region_code).first()
                                    
                                    # Create a default branch if not exists
                                    branch = Branch(
                                        branch_code=None,  # We don't have the 7-digit branch_code yet
                                        name=f'Branch {ba_code}',
                                        region_id=region.id if region else None,
                                        ba_code=ba_code,
                                        oracle_org_id=request.get('org_owner_id') 
                                    )
                                    self.db.add(branch)
                                    self.db.commit()
                                    self.db.refresh(branch)
                                    logger.info(f'Created new branch with ba_code: {ba_code}')
                            
                            # We use branch.ba_code directly now instead of branch_id
                                
                            # Get status
                            status_code = str(request.get("status_code")) if request.get("status_code") is not None else None
                            status = None
                            if status_code:
                                status = self.db.query(InstallationStatus).filter(
                                    InstallationStatus.code == status_code
                                ).first()
                                
                                if not status:
                                    logger.warning(f"Status not found for code: {status_code}")
                                    
                                    # Create a default status if not exists
                                    status = InstallationStatus(
                                        code=status_code,
                                        name=f"Status {status_code}",
                                        description=f"Auto-created during sync"
                                    )
                                    self.db.add(status)
                                    self.db.commit()
                                    self.db.refresh(status)
                                    logger.info(f"Created new installation status: {status_code}")
                                
                            status_id = status.id if status else None
                                
                            # Get installation type
                            installation_type_code = str(request.get("installation_type_code")) if request.get("installation_type_code") is not None else None
                            installation_type = None
                            if installation_type_code:
                                installation_type = self.db.query(InstallationType).filter(
                                    InstallationType.code == installation_type_code
                                ).first()
                                
                                if not installation_type:
                                    logger.warning(f"Installation type not found for code: {installation_type_code}")
                                    
                                    # Create a default installation type if not exists
                                    installation_type = InstallationType(
                                        code=installation_type_code,
                                        name=f"Installation Type {installation_type_code}",
                                        description=f"Auto-created during sync"
                                    )
                                    self.db.add(installation_type)
                                    self.db.commit()
                                    self.db.refresh(installation_type)
                                    logger.info(f"Created new installation type: {installation_type_code}")
                                
                            installation_type_id = installation_type.id if installation_type else None
                                
                            # Get meter size
                            meter_size_code = str(request.get("meter_size_code")) if request.get("meter_size_code") is not None else None
                            meter_size = None
                            if meter_size_code:
                                meter_size = self.db.query(MeterSize).filter(
                                    MeterSize.code == meter_size_code
                                ).first()
                                
                                if not meter_size:
                                    logger.warning(f"Meter size not found for code: {meter_size_code}")
                                    
                                    # Create a default meter size if not exists
                                    meter_size = MeterSize(
                                        code=meter_size_code,
                                        name=f"Meter Size {meter_size_code}",
                                        description=f"Auto-created during sync"
                                    )
                                    self.db.add(meter_size)
                                    self.db.commit()
                                    self.db.refresh(meter_size)
                                    logger.info(f"Created new meter size: {meter_size_code}")
                                
                            meter_size_id = meter_size.id if meter_size else None
                            
                            # Handle dates - convert to datetime if needed
                            try:
                                # Better handling of dates
                                def safe_date_parse(date_value):
                                    if not date_value:
                                        return None
                                    if isinstance(date_value, datetime):
                                        return date_value
                                    try:
                                        return datetime.fromisoformat(str(date_value).strip().replace(' ', 'T'))
                                    except (ValueError, TypeError):
                                        try:
                                            # Try different formats if ISO format fails
                                            return datetime.strptime(str(date_value).strip()[:19], '%Y-%m-%d %H:%M:%S')
                                        except (ValueError, TypeError):
                                            try:
                                                return datetime.strptime(str(date_value).strip()[:10], '%Y-%m-%d')
                                            except (ValueError, TypeError):
                                                logger.warning(f"Could not parse date: {date_value}, using None instead")
                                                return None
                                                
                                request_date = safe_date_parse(request.get("request_date"))
                                estimated_date = safe_date_parse(request.get("estimated_date"))
                                approved_date = safe_date_parse(request.get("approved_date"))
                                payment_date = safe_date_parse(request.get("payment_date"))
                                installation_date = safe_date_parse(request.get("installation_date"))
                                completion_date = safe_date_parse(request.get("completion_date"))
                                
                                logger.debug(f"Parsed dates for {request_no} - request_date: {request_date}, "
                                          f"estimated_date: {estimated_date}, completion_date: {completion_date}")
                            except Exception as e:
                                logger.error(f"Error parsing dates for request {request_no}: {str(e)}")
                                # Use None for all dates if there's an error
                                request_date = None
                                estimated_date = None
                                approved_date = None
                                payment_date = None
                                installation_date = None
                                completion_date = None
                            
                            if existing_request:
                                # Update existing request
                                existing_request.customer_id = customer.id if customer else None
                                existing_request.branch_code = branch.ba_code if branch else existing_request.branch_code
                                existing_request.ba_code = ba_code  # ใช้ ba_code จาก Oracle โดยตรง
                                existing_request.status_id = status_id
                                existing_request.installation_type_id = installation_type_id
                                existing_request.meter_size_id = meter_size_id
                                existing_request.request_date = request_date
                                existing_request.estimated_date = estimated_date
                                existing_request.approved_date = approved_date
                                existing_request.payment_date = payment_date
                                existing_request.installation_date = installation_date 
                                existing_request.completion_date = completion_date
                                existing_request.installation_fee = request.get("installation_fee")
                                existing_request.bill_no = request.get("bill_no")
                                existing_request.remarks = request.get("remarks")
                                existing_request.original_req_id = str(request.get("request_id")) if request.get("request_id") else None
                                
                                self.db.commit()
                                updated += 1
                                logger.debug(f"Updated installation request: {request_no}")
                            else:
                                # Create new request
                                try:
                                    new_request = InstallationRequest(
                                        request_no=request_no,
                                        customer_id=customer.id if customer else None,
                                        branch_code=branch.ba_code if branch else ba_code,  # ใช้ ba_code เนื่องจาก foreign key ชี้ไปที่ branches.ba_code
                                        created_by=user_id,
                                        status_id=status_id,
                                        installation_type_id=installation_type_id,
                                        meter_size_id=meter_size_id,
                                        request_date=request_date,
                                        estimated_date=estimated_date,
                                        approved_date=approved_date,
                                        payment_date=payment_date,
                                        installation_date=installation_date,
                                        completion_date=completion_date,
                                        installation_fee=request.get("installation_fee"),
                                        bill_no=request.get("bill_no"),
                                        remarks=request.get("remarks"),
                                        original_req_id=str(request.get("request_id")) if request.get("request_id") else None
                                    )
                                    logger.debug(f"Created new InstallationRequest object with request_no: {request_no}")
                                except Exception as e:
                                    logger.error(f"Error creating InstallationRequest object: {str(e)}")
                                    raise
                                
                                self.db.add(new_request)
                                self.db.commit()
                                created += 1
                                logger.debug(f"Created new installation request: {request_no}")
                        
                        except Exception as e:
                            # Improved error logging with specific key fields
                            request_no = request.get('request_no')
                            ba_code = request.get('branch_code')
                            status_code = request.get('status_code')
                            installation_type_code = request.get('installation_type_code')
                            meter_size_code = request.get('meter_size_code')
                            customer_id = request.get('customer_id')
                            
                            logger.error(f"Error processing installation request {request_no}: {str(e)}")
                            logger.error(f"Key fields - ba_code: {ba_code}, status_code: {status_code}, "
                                      f"installation_type_code: {installation_type_code}, meter_size_code: {meter_size_code}, "
                                      f"customer_id: {customer_id}")
                            
                            # Include traceback for more detailed debugging
                            import traceback
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            
                            failed += 1
                            self.db.rollback()
                    
                    # Update sync log for this batch
                    total_processed += processed
                    total_created += created
                    total_updated += updated
                    total_skipped += skipped
                    total_failed += failed
                    
                    self._update_sync_log(
                        records_processed=processed,
                        records_created=created,
                        records_updated=updated,
                        records_skipped=skipped,
                        records_failed=failed
                    )
                
                # Final stats
                logger.info(f"Installation requests sync completed: processed={total_processed}, created={total_created}, updated={total_updated}, skipped={total_skipped}, failed={total_failed}")
                
                return self._end_sync_log("success")
            
        except Exception as e:
            logger.error(f"Error syncing installation requests: {str(e)}")
            return self._end_sync_log("failed", str(e))
    
    def sync_temporary_installations(self, user_id: Optional[int] = None, is_full_sync: bool = True,
                                 year_month: Optional[str] = None) -> SyncLog:
        """
        Sync temporary installation data from Oracle database.
        
        Args:
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            year_month: Year and month in format 'YYYYMM' for filtering by completion date.
            
        Returns:
            The SyncLog object with the sync results.
        """
        # If year_month not provided, use current year and month
        if not year_month:
            current_date = datetime.now()
            year_month = f"{current_date.year}{current_date.month:02d}"
            
        query_params = {
            "year_month": year_month
        }
        
        self._start_sync_log("temporary_installation", user_id, is_full_sync, query_params)
        
        try:
            # Build the query - matching the old system query structure
            query = """
                SELECT 
                    CUS.ID as CUSTOMER_ID,
                    CUS.INSTALL_CUS_TITLE as TITLE,
                    CUS.INSTALL_CUS_NAME as FIRSTNAME,
                    CUS.INSTALL_CUS_SURNAME as LASTNAME,
                    CUS.CARD_ID as ID_CARD,
                    CAI.ADDRESS_NO as ADDRESS,
                    CAI.MOBILE,
                    RH.ID as REQUEST_ID,
                    RID.INSTALL_ID as INSTALLATION_ID,
                    RH.REQ_NO as REQUEST_NO,
                    REXP.EXP_DATE as EXPIRATION_DATE,
                    REXP.ADD_PRICE as ADDITIONAL_PRICE,
                    RH.CREATED_DATE as CREATED_DATE,
                    RH.UPDATED_DATE as UPDATED_DATE,
                    RH.ORG_OWNER_ID,
                    ORG.BA_CODE as BRANCH_CODE,
                    RH.RQFINISHDATE as ESTIMATED_DATE,
                    RH.APP_DATE as APPROVED_DATE,
                    RH.REMARK as REMARKS,
                    RH.INSTALL_TYPE as INSTALLATION_TYPE_CODE,
                    RH.DOC_STS as STATUS_CODE,
                    RID.METER_SIZE as METER_SIZE_CODE,
                    MIN(BILL.BILL_NO) as BILL_NO,
                    MIN(BILL.PAID_DATE) as PAYMENT_DATE,
                    REXP.INSTALL_DATE as INSTALLATION_DATE
                FROM PWACIS.TB_TR_REQ_HEAD_INF RH
                LEFT JOIN PWACIS.TB_TR_CUSTOMER_INF CUS ON RH.CUS_ID = CUS.ID
                LEFT JOIN PWACIS.TB_TR_CUSADDR_INF CAI ON RH.CUS_ID = CAI.CUS_ID
                LEFT JOIN PWACIS.TB_TR_REQ_INSTALL_DETAIL RID ON RH.ID = RID.REQ_ID
                LEFT JOIN PWACIS.TB_TR_INSTALL_TRN REXP ON RID.INSTALL_ID = REXP.ID
                LEFT JOIN PWACIS.TB_TR_BILL BILL ON RH.CUS_ID = BILL.CUST_ID AND (BILL.BILL_DETAIL = 2 AND BILL.IS_DELETED = 'F')
                LEFT JOIN PWACIS.TB_LT_ORGANIZATION ORG ON RH.ORG_OWNER_ID = ORG.ID
                WHERE RH.INSTALL_TYPE = '1' 
                  AND RH.UPDATED_DATE IS NOT NULL
                  AND (RH.ORG_OWNER_ID = 1060 OR RH.ORG_OWNER_ID = 1061 
                       OR RH.ORG_OWNER_ID = 1062 OR RH.ORG_OWNER_ID = 1063 
                       OR RH.ORG_OWNER_ID = 1064 OR RH.ORG_OWNER_ID = 1065 
                       OR RH.ORG_OWNER_ID = 1066 OR RH.ORG_OWNER_ID = 1067 
                       OR RH.ORG_OWNER_ID = 1068 OR RH.ORG_OWNER_ID = 1069 
                       OR RH.ORG_OWNER_ID = 1070 OR RH.ORG_OWNER_ID = 1071 
                       OR RH.ORG_OWNER_ID = 1072 OR RH.ORG_OWNER_ID = 1073 
                       OR RH.ORG_OWNER_ID = 1074 OR RH.ORG_OWNER_ID = 1075 
                       OR RH.ORG_OWNER_ID = 1076 OR RH.ORG_OWNER_ID = 1077 
                       OR RH.ORG_OWNER_ID = 1133 OR RH.ORG_OWNER_ID = 1134 
                       OR RH.ORG_OWNER_ID = 1135 OR RH.ORG_OWNER_ID = 1245)
                  AND (RH.DOC_STS = '13' OR RH.DOC_STS = '14' 
                       OR (RH.DOC_STS = '20' AND TO_CHAR(RH.RQFINISHDATE, 'YYYYMM', 'NLS_CALENDAR = ''THAI BUDDHA''') = :year_month))
                GROUP BY 
                    CUS.ID, CUS.INSTALL_CUS_TITLE, CUS.INSTALL_CUS_NAME, CUS.INSTALL_CUS_SURNAME, 
                    CUS.CARD_ID, CAI.ADDRESS_NO, CAI.MOBILE, RH.ID, RID.INSTALL_ID, RH.REQ_NO, 
                    REXP.EXP_DATE, RH.CREATED_DATE, RH.UPDATED_DATE, RH.ORG_OWNER_ID, ORG.BA_CODE,
                    RH.RQFINISHDATE, RH.APP_DATE, RH.REMARK, RH.INSTALL_TYPE, RH.DOC_STS, 
                    RID.METER_SIZE, REXP.INSTALL_DATE, REXP.ADD_PRICE
            """
            
            params = {"year_month": year_month}
            
            # Execute the query in batches
            with oracle_db as db:
                logger.info(f"Executing Oracle query for temporary installations: {query}")
                batches = db.fetch_batch(query, params, batch_size=100)
                
                total_processed = 0
                total_created = 0
                total_updated = 0
                total_skipped = 0
                total_failed = 0
                
                for batch in batches:
                    processed = 0
                    created = 0
                    updated = 0
                    skipped = 0
                    failed = 0
                    
                    logger.info(f"Processing batch of {len(batch)} temporary installations")
                    
                    for request in batch:
                        try:
                            processed += 1
                            
                            # Process customer first
                            customer_id = request.get("customer_id")
                            customer = None
                            
                            if customer_id:
                                # Check if customer exists
                                customer = self.db.query(Customer).filter(Customer.original_id == str(customer_id)).first()
                                
                                if not customer:
                                    # Get branch
                                    ba_code = str(request.get("branch_code")) if request.get("branch_code") is not None else None
                                    branch = None
                                    if ba_code:
                                        branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                        
                                        if not branch:
                                            logger.warning(f"Branch not found for code: {ba_code}")
                                            
                                            # Try to find the region for this branch (assuming branch code starts with region code)
                                            region_code = ba_code[:1] if len(ba_code) > 0 else None
                                            region = None
                                            if region_code:
                                                region = self.db.query(Region).filter(Region.code == region_code).first()
                                            
                                            # Create a default branch if not exists
                                            try:
                                                branch = Branch(
                                                    branch_code=ba_code,  # ใช้ ba_code เป็น branch_code เพื่อหลีกเลี่ยง not-null constraint
                                                    name=f"Branch {ba_code}",
                                                    region_id=region.id if region else None,
                                                    ba_code=ba_code,
                                                    oracle_org_id=request.get('org_owner_id') 
                                                )
                                                self.db.add(branch)
                                                self.db.commit()
                                                self.db.refresh(branch)
                                                logger.info(f"Created new branch: {ba_code}")
                                            except Exception as e:
                                                # หากเกิด error เช่น unique constraint อาจเป็นเพราะมี branch นี้อยู่แล้ว ลองค้นหาอีกครั้ง
                                                logger.warning(f"Error creating branch: {str(e)}")
                                                self.db.rollback()
                                                branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                                if not branch:
                                                    logger.error(f"Still cannot find branch for ba_code: {ba_code}")
                                                    raise
                                    
                                    # We use branch.ba_code directly now instead of branch_id
                                    
                                    # Create customer
                                    # การจัดการค่า NULL สำหรับฟิลด์ที่ต้องการ NOT NULL
                                    title = request.get("title") or ""
                                    firstname = request.get("firstname") or ""
                                    # สำหรับสถานที่ ใช้ชื่อเป็นนามสกุลถ้าไม่มีนามสกุล
                                    lastname = request.get("lastname")
                                    if lastname is None or (isinstance(lastname, str) and lastname.strip() == ""):
                                        # ถ้าไม่มีนามสกุล ใช้ชื่อเป็นนามสกุล หรือถ้าไม่มีทั้งชื่อและนามสกุล ใช้ค่าว่าง
                                        lastname = firstname or "-"
                                    
                                    customer = Customer(
                                        original_id=str(customer_id),
                                        title=title,
                                        firstname=firstname,
                                        lastname=lastname,
                                        id_card=request.get("id_card"),
                                        address=request.get("address"),
                                        mobile=request.get("mobile"),
                                        branch_code=ba_code
                                    )
                                    
                                    self.db.add(customer)
                                    self.db.commit()
                                    self.db.refresh(customer)
                                    logger.debug(f"Created new customer: ID {customer.id}, Original ID {customer_id}")
                            
                            # Process installation request
                            request_no = request.get("request_no")
                            if not request_no:
                                logger.warning(f"Skipping temporary installation without request_no: {request}")
                                skipped += 1
                                continue
                                
                            # Check if installation request exists
                            existing_request = self.db.query(InstallationRequest).filter(
                                InstallationRequest.request_no == request_no
                            ).first()
                            
                            # Get branch
                            ba_code = str(request.get("branch_code")) if request.get("branch_code") is not None else None
                            branch = None
                            if ba_code:
                                branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                
                                if not branch:
                                    logger.warning(f"Branch not found for code: {ba_code}")
                                    
                                    # Try to find the region for this branch (assuming branch code starts with region code)
                                    region_code = ba_code[:1] if len(ba_code) > 0 else None
                                    region = None
                                    if region_code:
                                        region = self.db.query(Region).filter(Region.code == region_code).first()
                                    
                                    # Create a default branch if not exists
                                    branch = Branch(
                                        branch_code=ba_code,
                                        name=f"Branch {ba_code}",
                                        region_id=region.id if region else None,
                                        ba_code=ba_code,
                                        oracle_org_id=request.get('org_owner_id') 
                                    )
                                    self.db.add(branch)
                                    self.db.commit()
                                    self.db.refresh(branch)
                                    logger.info(f"Created new branch: {ba_code}")
                            
                            # We use branch.ba_code directly now instead of branch_id
                                
                            # Get status
                            status_code = str(request.get("status_code")) if request.get("status_code") is not None else None
                            status = None
                            if status_code:
                                status = self.db.query(InstallationStatus).filter(
                                    InstallationStatus.code == status_code
                                ).first()
                                
                                if not status:
                                    logger.warning(f"Status not found for code: {status_code}")
                                    
                                    # Create a default status if not exists
                                    status = InstallationStatus(
                                        code=status_code,
                                        name=f"Status {status_code}",
                                        description=f"Auto-created during sync"
                                    )
                                    self.db.add(status)
                                    self.db.commit()
                                    self.db.refresh(status)
                                    logger.info(f"Created new installation status: {status_code}")
                                
                            status_id = status.id if status else None
                                
                            # For temporary installations, always use code '2' regardless of source value
                            installation_type_code = '2'  # Hardcoded for temporary installations
                            installation_type = self.db.query(InstallationType).filter(
                                InstallationType.code == installation_type_code
                            ).first()
                            
                            if not installation_type:
                                logger.warning(f"Installation type not found for code: {installation_type_code}")
                                
                                # Create a default installation type if not exists
                                installation_type = InstallationType(
                                    code=installation_type_code,
                                    name="Temporary Installation",
                                    description="Temporary meter installation"
                                )
                                self.db.add(installation_type)
                                self.db.commit()
                                self.db.refresh(installation_type)
                                logger.info(f"Created new installation type: {installation_type_code}")
                            
                            installation_type_id = installation_type.id if installation_type else None
                                
                            # Get meter size
                            meter_size_code = str(request.get("meter_size_code")) if request.get("meter_size_code") is not None else None
                            meter_size = None
                            if meter_size_code:
                                meter_size = self.db.query(MeterSize).filter(
                                    MeterSize.code == meter_size_code
                                ).first()
                                
                                if not meter_size:
                                    logger.warning(f"Meter size not found for code: {meter_size_code}")
                                    
                                    # Create a default meter size if not exists
                                    meter_size = MeterSize(
                                        code=meter_size_code,
                                        name=f"Meter Size {meter_size_code}",
                                        description=f"Auto-created during sync"
                                    )
                                    self.db.add(meter_size)
                                    self.db.commit()
                                    self.db.refresh(meter_size)
                                    logger.info(f"Created new meter size: {meter_size_code}")
                                
                            meter_size_id = meter_size.id if meter_size else None
                            
                            # Handle dates - convert to datetime if needed
                            request_date = request.get("created_date")
                            estimated_date = request.get("estimated_date")
                            approved_date = request.get("approved_date")
                            payment_date = request.get("payment_date")
                            installation_date = request.get("installation_date")
                            completion_date = request.get("updated_date")
                            expiration_date = request.get("expiration_date")
                            
                            # Additional fields for temporary installations
                            additional_price = request.get("additional_price")
                            installation_id = request.get("installation_id")
                            
                            if existing_request:
                                # Update existing request
                                existing_request.customer_id = customer.id if customer else None
                                existing_request.branch_code = branch.ba_code if branch else existing_request.branch_code
                                existing_request.ba_code = ba_code  # ใช้ ba_code จาก Oracle โดยตรง
                                existing_request.status_id = status_id
                                existing_request.installation_type_id = installation_type_id
                                existing_request.meter_size_id = meter_size_id
                                existing_request.request_date = request_date
                                existing_request.estimated_date = estimated_date
                                existing_request.approved_date = approved_date
                                existing_request.payment_date = payment_date
                                existing_request.installation_date = installation_date 
                                existing_request.completion_date = completion_date
                                existing_request.installation_fee = additional_price
                                existing_request.bill_no = request.get("bill_no")
                                existing_request.remarks = request.get("remarks")
                                existing_request.original_req_id = str(request.get("request_id")) if request.get("request_id") else None
                                existing_request.original_install_id = str(installation_id) if installation_id else None
                                
                                # Add expiration date for temporary installations
                                if hasattr(existing_request, 'expiration_date'):
                                    existing_request.expiration_date = expiration_date
                                
                                self.db.commit()
                                updated += 1
                                logger.debug(f"Updated temporary installation: {request_no}")
                            else:
                                # Create new request
                                new_request = InstallationRequest(
                                    request_no=request_no,
                                    customer_id=customer.id if customer else None,
                                    branch_code=branch.ba_code if branch else ba_code,  # ใช้ ba_code เนื่องจาก foreign key ชี้ไปที่ branches.ba_code
                                    created_by=user_id,
                                    status_id=status_id,
                                    installation_type_id=installation_type_id,
                                    meter_size_id=meter_size_id,
                                    request_date=request_date,
                                    estimated_date=estimated_date,
                                    approved_date=approved_date,
                                    payment_date=payment_date,
                                    installation_date=installation_date,
                                    completion_date=completion_date,
                                    installation_fee=additional_price,
                                    bill_no=request.get("bill_no"),
                                    remarks=request.get("remarks"),
                                    original_req_id=str(request.get("request_id")) if request.get("request_id") else None,
                                    original_install_id=str(installation_id) if installation_id else None,
                                    # Add expiration date for temporary installations if field exists in model
                                    **({"expiration_date": expiration_date} if hasattr(InstallationRequest, 'expiration_date') else {})
                                )
                                
                                self.db.add(new_request)
                                self.db.commit()
                                created += 1
                                logger.debug(f"Created new temporary installation: {request_no}")
                                
                        except Exception as e:
                            # Improved error logging with more details
                            request_no = request.get('request_no')
                            ba_code = request.get('branch_code')
                            status_code = request.get('status_code')
                            installation_type_code = request.get('installation_type_code')
                            meter_size_code = request.get('meter_size_code')
                            
                            logger.error(f"Error processing temporary installation {request_no}: {str(e)}")
                            logger.error(f"Request data - ba_code: {ba_code}, status_code: {status_code}, "
                                      f"installation_type_code: {installation_type_code}, meter_size_code: {meter_size_code}")
                            
                            # Include traceback for more detailed debugging
                            import traceback
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            
                            failed += 1
                            self.db.rollback()
                    
                    # Update sync log for this batch
                    total_processed += processed
                    total_created += created
                    total_updated += updated
                    total_skipped += skipped
                    total_failed += failed
                    
                    self._update_sync_log(
                        records_processed=processed,
                        records_created=created,
                        records_updated=updated,
                        records_skipped=skipped,
                        records_failed=failed
                    )
                
                # Final stats
                logger.info(f"Temporary installations sync completed: processed={total_processed}, created={total_created}, updated={total_updated}, skipped={total_skipped}, failed={total_failed}")
                
                return self._end_sync_log("success")
            
        except Exception as e:
            logger.error(f"Error syncing temporary installations: {str(e)}")
            return self._end_sync_log("failed", str(e))
    
    def get_sync_logs(self, sync_type: Optional[str] = None, limit: int = 10) -> List[SyncLog]:
        """
        Get recent sync logs.
        
        Args:
            sync_type: Type of sync logs to retrieve.
            limit: Maximum number of logs to retrieve.
            
        Returns:
            List of SyncLog objects.
        """
        try:
            query = self.db.query(SyncLog).order_by(SyncLog.start_time.desc())
            
            if sync_type:
                query = query.filter(SyncLog.sync_type == sync_type)
                
            return query.limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving sync logs: {str(e)}")
            return []
    
    def get_sync_log(self, log_id: int) -> Optional[SyncLog]:
        """
        Get a specific sync log.
        
        Args:
            log_id: ID of the sync log to retrieve.
            
        Returns:
            The SyncLog object if found, None otherwise.
        """
        try:
            return self.db.query(SyncLog).filter(SyncLog.id == log_id).first()
        except Exception as e:
            logger.error(f"Error retrieving sync log {log_id}: {str(e)}")
            return None
            
    def sync_new_customers(self, user_id: Optional[int] = None, is_full_sync: bool = True,
                          year: Optional[int] = None, month: Optional[int] = None) -> SyncLog:
        """
        Sync new customer data from Oracle database.
        
        Args:
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            year: Year for filtering customers (Gregorian year, e.g. 2023).
            month: Month for filtering customers (1-12).
            
        Returns:
            The SyncLog object with the sync results.
        """
        # If year/month not provided, use current year/month
        current_date = datetime.now()
        query_year = year if year is not None else current_date.year
        query_month = month if month is not None else current_date.month
        
        # Format year and month in YYYYMM format directly as needed for the query
        year_month = f"{query_year}{query_month:02d}"  # เช่น 202303
        
        query_params = {
            "year": query_year,
            "month": query_month,
            "year_month": year_month
        }
        
        self._start_sync_log("new_customer", user_id, is_full_sync, query_params)
        
        try:
            # Build the query based on the old system
            query = """
                SELECT V.CUS_CODE as CUST_CODE, 
                       o.ba_code as BA_CODE, 
                       :year_month as YM, 
                       to_char(V.RQFINISHDATE,'yyyy/mm/dd') as FINISH_DATE, 
                       TO_CHAR(SYSDATE, 'YYYY/MM/DD HH24:MI:SS') as UPDATE_DATETIME,
                       C.ID as CUSTOMER_ID,
                       C.INSTALL_CUS_TITLE as TITLE,
                       C.INSTALL_CUS_NAME as FIRSTNAME,
                       C.INSTALL_CUS_SURNAME as LASTNAME,
                       C.CARD_ID as ID_CARD,
                       CAI.ADDRESS_NO as ADDRESS,
                       CAI.MOBILE
                FROM PWACIS.V_R_005 V 
                LEFT JOIN pwacis.tb_lt_organization o on o.id = v.org_owner_id 
                LEFT JOIN PWACIS.TB_TR_CUSTOMER_INF C ON V.CUS_CODE = C.CUS_CODE
                LEFT JOIN PWACIS.TB_TR_CUSADDR_INF CAI ON C.ID = CAI.ID AND CAI.ADDR_TYPE = '1'
                WHERE to_number(to_char(V.RQFINISHDATE,'yyyymm')) = :year_month 
                  AND o.parent_id = 178
            """
            
            params = {
                "year_month": int(year_month)  # แปลงเป็น integer เพื่อตรงกับค่าในฐานข้อมูล
            }
            
            # Execute the query
            with oracle_db as db:
                logger.info(f"Executing Oracle query for new customers: {query}")
                customers = db.execute_query(query, params)
            
            processed = 0
            created = 0
            updated = 0
            skipped = 0
            failed = 0
            
            logger.info(f"Found {len(customers)} new customers to process")
            
            for customer_data in customers:
                try:
                    processed += 1
                    
                    customer_code = customer_data.get("cust_code")
                    customer_id = customer_data.get("customer_id")
                    finish_date = customer_data.get("finish_date")
                    ba_code = customer_data.get("ba_code")
                    
                    # Check if customer exists by original_id
                    customer = None
                    if customer_id:
                        customer = self.db.query(Customer).filter(Customer.original_id == str(customer_id)).first()
                    
                    # If not found by original_id, try customer_code
                    if not customer and customer_code:
                        customer = self.db.query(Customer).filter(
                            Customer.original_id == str(customer_code)
                        ).first()
                    
                    customer_created = False
                    if not customer:
                        # Create new customer if not found
                        title = customer_data.get("title") or ""
                        firstname = customer_data.get("firstname") or ""
                        lastname = customer_data.get("lastname")
                        if lastname is None or (isinstance(lastname, str) and lastname.strip() == ""):
                            lastname = firstname or "-"
                        
                        # Get or create branch
                        branch = None
                        if ba_code:
                            branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                            
                            if not branch:
                                # Try to find the region for this branch
                                region_code = ba_code[:1] if len(ba_code) > 0 else None
                                region = None
                                if region_code:
                                    region = self.db.query(Region).filter(Region.code == region_code).first()
                                
                                # Create a default branch if not exists - กำหนด branch_code ให้เป็น ba_code เพื่อหลีกเลี่ยง not-null constraint
                                try:
                                    branch = Branch(
                                        branch_code=ba_code,  # ใช้ ba_code เป็น branch_code เพื่อป้องกัน NotNullViolation
                                        name=f"Branch {ba_code}",
                                        region_id=region.id if region else None,
                                        ba_code=ba_code,
                                        oracle_org_id=None
                                    )
                                    self.db.add(branch)
                                    self.db.commit()
                                    self.db.refresh(branch)
                                    logger.info(f"Created new branch with ba_code: {ba_code}")
                                except Exception as e:
                                    # หากเกิด error เช่น unique constraint อาจเป็นเพราะมี branch นี้อยู่แล้ว ลองค้นหาอีกครั้ง
                                    logger.warning(f"Error creating branch: {str(e)}")
                                    self.db.rollback()
                                    branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                    if not branch:
                                        logger.error(f"Still cannot find branch for ba_code: {ba_code}")
                                        raise
                        
                        try:
                            customer = Customer(
                                original_id=str(customer_id or customer_code),
                                title=title,
                                firstname=firstname,
                                lastname=lastname,
                                id_card=customer_data.get("id_card"),
                                address=customer_data.get("address"),
                                mobile=customer_data.get("mobile"),
                                branch_code=ba_code
                            )
                            
                            self.db.add(customer)
                            self.db.commit()
                            self.db.refresh(customer)
                            customer_created = True
                            total_created += 1
                            logger.debug(f"Created new customer from type change data: {customer_id or customer_code}")
                        except Exception as e:
                            logger.error(f"Error creating customer: {str(e)}")
                            raise
                    
                    # Update sync log periodically
                    if processed % 10 == 0:
                        self._update_sync_log(
                            records_processed=processed,
                            records_created=created,
                            records_updated=updated,
                            records_skipped=skipped,
                            records_failed=failed
                        )
                
                except Exception as e:
                    logger.error(f"Error processing new customer {customer_id or customer_code}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    failed += 1
                    self.db.rollback()
                
                # Update sync log periodically
                if processed % 10 == 0:
                    self._update_sync_log(
                        records_processed=processed,
                        records_created=created,
                        records_updated=updated,
                        records_skipped=skipped,
                        records_failed=failed
                    )
            
            # Final update
            self._update_sync_log(
                records_processed=processed,
                records_created=created,
                records_updated=updated,
                records_skipped=skipped,
                records_failed=failed
            )
            
            logger.info(f"New customers sync completed: {created} created, {updated} updated, {skipped} skipped, {failed} failed")
            return self._end_sync_log("success")
            
        except Exception as e:
            logger.error(f"Error syncing new customers: {str(e)}")
            return self._end_sync_log("failed", str(e))
    
    def sync_customer_type_changes(self, user_id: Optional[int] = None, is_full_sync: bool = True,
                                  year: Optional[int] = None, month: Optional[int] = None) -> SyncLog:
        """
        Sync customer type change data from Oracle database.
        
        Args:
            user_id: ID of the user who initiated the sync.
            is_full_sync: Whether this is a full sync or a delta sync.
            year: Year for filtering data (Gregorian year, e.g. 2023).
            month: Month for filtering data (1-12).
            
        Returns:
            The SyncLog object with the sync results.
        """
        # If year/month not provided, use current year/month
        current_date = datetime.now()
        query_year = year if year is not None else current_date.year
        query_month = month if month is not None else current_date.month
        
        # Format year and month in YYYYMM format directly as needed for the query
        year_month = f"{query_year}{query_month:02d}"  # เช่น 202303
        
        # ปีพุทธศักราชสำหรับ debt_ym (เพราะระบบเดิมใช้ในบางตัวแปร)
        year_th = query_year + 543
        year_month_th = f"{year_th}{query_month:02d}" 
        
        query_params = {
            "year": query_year,
            "month": query_month,
            "year_month": year_month,
            "year_month_th": year_month_th
        }
        
        self._start_sync_log("customer_type_change", user_id, is_full_sync, query_params)
        
        try:
            # Build the query based on the old system
            query = """
                SELECT c.id as CUST_ID, 
                       c.CUS_CODE as CUST_CODE, 
                       USET.USETYPE as OLD_USETYPE, 
                       USET.USENAME as OLD_USETYPE_NAME, 
                       USET1.USETYPE as NEW_USETYPE, 
                       USET1.USENAME as NEW_USETYPE_NAME, 
                       dt.present_water_usg, 
                       o.ba_code as ORG_OWNER_ID, 
                       to_char(cch.CREATED_DATE,'yyyy/mm/dd') AS CHANGE_DATE, 
                       to_char(sysdate,'YYYY/MM/DD HH24:MI:SS') as UPDATE_DATETIME,
                       C.INSTALL_CUS_TITLE as TITLE,
                       C.INSTALL_CUS_NAME as FIRSTNAME,
                       C.INSTALL_CUS_SURNAME as LASTNAME,
                       C.CARD_ID as ID_CARD,
                       CAI.ADDRESS_NO as ADDRESS,
                       CAI.MOBILE
                FROM pwacis.tb_tr_cust_chg_his cch 
                INNER JOIN pwacis.TB_LT_USETYPE USET ON CCH.OLD_VALUE = USET.ID 
                INNER JOIN pwacis.TB_LT_USETYPE USET1 ON CCH.NEW_VALUE = USET1.ID 
                INNER JOIN pwacis.tb_tr_customer_inf c ON cch.CUS_ID = c.ID 
                INNER JOIN pwacis.tb_lt_organization o ON o.ID = cch.org_owner_id 
                INNER JOIN pwacis.tb_tr_debt_trn dt on dt.cust_id = c.id 
                LEFT JOIN PWACIS.TB_TR_CUSADDR_INF CAI ON C.ID = CAI.ID AND CAI.ADDR_TYPE = '1'
                WHERE SUBSTR(cch.FIELD_NAME, 20) = 'CUS_TYPE_ID' 
                  AND to_number(to_char(cch.CREATED_DATE,'yyyymm')) = :year_month 
                  AND o.parent_id = 178 
                  AND dt.debt_ym = :year_month_th 
                  AND cch.id in (select max(id) as id from pwacis.tb_tr_cust_chg_his 
                                 where FIELD_NAME LIKE '%CUS_TYPE_ID' 
                                 and to_char(created_date,'yyyymm') = :year_month 
                                 group by cus_id)
            """
            
            params = {
                "year_month_th": year_month_th,
                "year_month": int(year_month)
            }
            
            # Execute the query
            with oracle_db as db:
                logger.info(f"Executing Oracle query for customer type changes: {query}")
                type_changes = db.execute_query(query, params)
            
            # ตัวแปรนับจำนวนที่แยกกันอย่างชัดเจน
            total_processed = 0
            total_created = 0
            total_updated = 0
            total_skipped = 0
            total_failed = 0
            
            logger.info(f"Found {len(type_changes)} customer type changes to process")
            
            for change_data in type_changes:
                try:
                    total_processed += 1
                    
                    customer_id = change_data.get("cust_id")
                    customer_code = change_data.get("cust_code")
                    old_usetype = change_data.get("old_usetype")
                    new_usetype = change_data.get("new_usetype")
                    old_usetype_name = change_data.get("old_usetype_name")
                    new_usetype_name = change_data.get("new_usetype_name")
                    change_date = change_data.get("change_date")
                    ba_code = change_data.get("org_owner_id")
                    
                    # Log processing for debugging
                    logger.debug(f"Processing customer type change: ID={customer_id}, Code={customer_code}, "
                                f"Old Type={old_usetype}, New Type={new_usetype}")
                    
                    # Check if customer exists
                    customer = None
                    if customer_id:
                        customer = self.db.query(Customer).filter(Customer.original_id == str(customer_id)).first()
                    
                    # If not found by original_id, try customer_code
                    if not customer and customer_code:
                        customer = self.db.query(Customer).filter(
                            Customer.original_id == str(customer_code)
                        ).first()
                    
                    customer_created = False
                    if not customer:
                        # Create new customer if not found
                        title = change_data.get("title") or ""
                        firstname = change_data.get("firstname") or ""
                        lastname = change_data.get("lastname")
                        if lastname is None or (isinstance(lastname, str) and lastname.strip() == ""):
                            lastname = firstname or "-"
                        
                        # Get or create branch
                        branch = None
                        if ba_code:
                            branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                            
                            if not branch:
                                # Try to find the region for this branch
                                region_code = ba_code[:1] if len(ba_code) > 0 else None
                                region = None
                                if region_code:
                                    region = self.db.query(Region).filter(Region.code == region_code).first()
                                
                                # Create a default branch if not exists - กำหนด branch_code ให้เป็น ba_code เพื่อหลีกเลี่ยง not-null constraint
                                try:
                                    branch = Branch(
                                        branch_code=ba_code,  # ใช้ ba_code เป็น branch_code เพื่อป้องกัน NotNullViolation
                                        name=f"Branch {ba_code}",
                                        region_id=region.id if region else None,
                                        ba_code=ba_code,
                                        oracle_org_id=None
                                    )
                                    self.db.add(branch)
                                    self.db.commit()
                                    self.db.refresh(branch)
                                    logger.info(f"Created new branch with ba_code: {ba_code}")
                                except Exception as e:
                                    # หากเกิด error เช่น unique constraint อาจเป็นเพราะมี branch นี้อยู่แล้ว ลองค้นหาอีกครั้ง
                                    logger.warning(f"Error creating branch: {str(e)}")
                                    self.db.rollback()
                                    branch = self.db.query(Branch).filter(Branch.ba_code == ba_code).first()
                                    if not branch:
                                        logger.error(f"Still cannot find branch for ba_code: {ba_code}")
                                        raise
                        
                        try:
                            customer = Customer(
                                original_id=str(customer_id or customer_code),
                                title=title,
                                firstname=firstname,
                                lastname=lastname,
                                id_card=change_data.get("id_card"),
                                address=change_data.get("address"),
                                mobile=change_data.get("mobile"),
                                branch_code=ba_code
                            )
                            
                            self.db.add(customer)
                            self.db.commit()
                            self.db.refresh(customer)
                            customer_created = True
                            total_created += 1
                            logger.debug(f"Created new customer from type change data: {customer_id or customer_code}")
                        except Exception as e:
                            logger.error(f"Error creating customer: {str(e)}")
                            raise
                    
                    # Record the customer type change (this would typically be stored in a dedicated table)
                    # If you have a CustomerTypeChange model, you would create/update records here
                    # For this example, we'll just update the customer's metadata field if it exists
                    
                    # Check if the Customer model has a metadata field
                    type_updated = False
                    if hasattr(customer, 'metadata'):
                        # If metadata exists, update it with customer type change info
                        try:
                            metadata = json.loads(customer.metadata) if customer.metadata else {}
                            
                            # Add type change info
                            if 'type_changes' not in metadata:
                                metadata['type_changes'] = []
                                
                            metadata['type_changes'].append({
                                'change_date': change_date,
                                'old_type': {
                                    'code': old_usetype,
                                    'name': old_usetype_name
                                },
                                'new_type': {
                                    'code': new_usetype,
                                    'name': new_usetype_name
                                }
                            })
                            
                            # Update current customer type
                            metadata['current_type'] = {
                                'code': new_usetype,
                                'name': new_usetype_name
                            }
                            
                            customer.metadata = json.dumps(metadata)
                            self.db.commit()
                            
                            if not customer_created:  # อัพเดตเฉพาะถ้าไม่ได้นับเป็นการสร้างลูกค้าใหม่
                                total_updated += 1
                            
                            type_updated = True
                            logger.debug(f"Updated customer metadata with type change: {customer_id or customer_code}")
                        except Exception as e:
                            logger.error(f"Error updating customer metadata: {str(e)}")
                            raise
                    else:
                        # If no metadata field exists, just log the type change
                        logger.info(f"Customer type change: {customer_id or customer_code} " +
                                    f"from {old_usetype} ({old_usetype_name}) " +
                                    f"to {new_usetype} ({new_usetype_name})")
                        total_skipped += 1
                    
                    # ไม่มีการนับรายการที่ล้มเหลวในกรณีที่ทำงานสำเร็จ
                    
                except Exception as e:
                    logger.error(f"Error processing customer type change {customer_id or customer_code}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    failed += 1
                    self.db.rollback()
                
                # Update sync log periodically in smaller batches to avoid overloading the log
                if total_processed % 50 == 0:
                    # อัพเดตค่าในแต่ละรอบด้วยจำนวนที่เพิ่มขึ้นเท่านั้น (ไม่ใช่ค่ารวมทั้งหมด)
                    partial_update = min(50, total_processed % 50 or 50)
                    logger.info(f"Progress update: processed {total_processed} records so far")
                    
                    # ไม่ต้องอัพเดต log ทุกรอบ เพื่อหลีกเลี่ยงการนับซ้ำ
            
            # Final update - reset counters and set final values to avoid accumulation from periodic updates
            logger.info(f"Customer type changes sync completed: processed={total_processed}, created={total_created}, "
                      f"updated={total_updated}, skipped={total_skipped}, failed={total_failed}")
            
            self._update_sync_log(
                records_processed=total_processed,
                records_created=total_created,
                records_updated=total_updated,
                records_skipped=total_skipped,
                records_failed=total_failed,
                reset_counters=True  # รีเซ็ตตัวนับก่อนการอัพเดตรอบสุดท้าย
            )
            
            # ตรวจสอบสถานะสุดท้ายจากจำนวนรายการที่ประมวลผล
            if total_failed > 0:
                return self._end_sync_log(
                    "failed" if total_failed == total_processed else 
                    "partial" if total_failed > 0 else "success",
                    f"Failed records: {total_failed}/{total_processed}"
                )
            else:
                return self._end_sync_log("success")
            
        except Exception as e:
            logger.error(f"Error syncing customer type changes: {str(e)}")
            return self._end_sync_log("failed", str(e)) 