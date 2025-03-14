"""
API routes for installation requests.
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, text
import logging

from app.api.dependencies import get_db, has_role
from app.models.installation_request import InstallationRequest
from app.schemas.installation_request import InstallationRequestSchema, InstallationRequestCreate, InstallationRequestUpdate
from app.models.installation_type import InstallationType
from app.models.branch import Branch
from app.models.customer import Customer
from app.models.installation_status import InstallationStatus
from app.models.meter_size import MeterSize

router = APIRouter()

@router.get("/", response_model=List[InstallationRequestSchema])
async def get_installation_requests(
    skip: int = 0,
    limit: int = 100,
    installation_type_id: Optional[int] = None,
    installation_type_code: Optional[str] = None,
    branch_id: Optional[int] = None,
    status_id: Optional[int] = None,
    is_temporary: bool = None,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve installation requests with optional filters.
    
    Parameters:
    - skip: Number of records to skip
    - limit: Maximum number of records to return
    - installation_type_id: Filter by installation type ID
    - installation_type_code: Filter by installation type code (e.g., '1' for permanent, '2' for temporary)
    - branch_id: Filter by branch ID
    - status_id: Filter by status ID
    - is_temporary: If True, returns only temporary installations (type_code='2'), if False, returns permanent installations
    """
    logger = logging.getLogger(__name__)
    
    # สร้าง SQL query ด้วย text() function
    sql_query = """
    SELECT 
        ir.id, ir.request_no, ir.customer_id, ir.branch_code, ir.status_id, 
        ir.installation_type_id, ir.meter_size_id, ir.request_date, ir.estimated_date,
        ir.approved_date, ir.payment_date, ir.installation_date, ir.completion_date,
        ir.installation_fee, ir.bill_no, ir.remarks, ir.original_req_id, 
        ir.original_install_id, ir.created_by, ir.created_at, ir.updated_at,
        ir.working_days_to_estimate, ir.working_days_to_payment, ir.working_days_to_install,
        ir.working_days_to_complete, ir.is_exceed_sla, ir.exceed_sla_reason,
        c.firstname as customer_firstname, c.lastname as customer_lastname,
        b.name as branch_name, 
        s.name as status_name,
        it.name as installation_type_name,
        ms.name as meter_size_name
    FROM 
        installation_requests ir
    LEFT JOIN 
        installation_types it ON ir.installation_type_id = it.id
    LEFT JOIN 
        branches b ON ir.branch_code = b.ba_code
    LEFT JOIN 
        customers c ON ir.customer_id = c.id
    LEFT JOIN 
        installation_statuses s ON ir.status_id = s.id
    LEFT JOIN 
        meter_sizes ms ON ir.meter_size_id = ms.id
    WHERE 1=1
    """
    
    # เตรียมพารามิเตอร์
    params = {}
    
    # Apply filters
    if installation_type_id is not None:
        sql_query += " AND ir.installation_type_id = :installation_type_id"
        params["installation_type_id"] = installation_type_id
    
    if installation_type_code is not None:
        sql_query += " AND it.code = :installation_type_code"
        params["installation_type_code"] = installation_type_code
    
    if branch_id is not None:
        sql_query += " AND ir.branch_code = :branch_id"
        params["branch_id"] = branch_id
    
    if status_id is not None:
        sql_query += " AND ir.status_id = :status_id"
        params["status_id"] = status_id
    
    # Filter for temporary/permanent installations
    if is_temporary is not None:
        code_to_filter = '2' if is_temporary else '1'
        sql_query += " AND it.code = :type_code"
        params["type_code"] = code_to_filter
    
    # Add order by, offset and limit
    sql_query += " ORDER BY ir.request_date DESC OFFSET :skip LIMIT :limit"
    params["skip"] = skip
    params["limit"] = limit
    
    # Execute query
    result = db.execute(text(sql_query), params)
    
    # Process results
    items = []
    for row in result:
        item = {
            "id": row.id,
            "request_no": row.request_no,
            "customer_id": row.customer_id,
            "branch_id": row.branch_code,
            "status_id": row.status_id,
            "installation_type_id": row.installation_type_id,
            "meter_size_id": row.meter_size_id,
            "request_date": row.request_date,
            "estimated_date": row.estimated_date,
            "approved_date": row.approved_date,
            "payment_date": row.payment_date,
            "installation_date": row.installation_date,
            "completion_date": row.completion_date,
            "installation_fee": row.installation_fee,
            "bill_no": row.bill_no,
            "remarks": row.remarks,
            "original_req_id": row.original_req_id,
            "original_install_id": row.original_install_id,
            "working_days_to_estimate": row.working_days_to_estimate,
            "working_days_to_payment": row.working_days_to_payment,
            "working_days_to_install": row.working_days_to_install,
            "working_days_to_complete": row.working_days_to_complete,
            "is_exceed_sla": row.is_exceed_sla,
            "exceed_sla_reason": row.exceed_sla_reason,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "customer_name": f"{row.customer_firstname or ''} {row.customer_lastname or ''}".strip(),
            "branch_name": row.branch_name,
            "status_name": row.status_name,
            "installation_type_name": row.installation_type_name,
            "meter_size_name": row.meter_size_name
        }
        items.append(item)
    
    return items

@router.get("/by-request-no", response_model=InstallationRequestSchema)
async def get_installation_request_by_no(
    request_no: str = Query(..., description="Installation request number, e.g. 'RQ1068/680000640'"),
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific installation request by request number.
    """
    logger = logging.getLogger(__name__)
    
    # สร้าง SQL query ด้วย text() function
    sql_query = """
    SELECT 
        ir.id, ir.request_no, ir.customer_id, ir.branch_code, ir.status_id, 
        ir.installation_type_id, ir.meter_size_id, ir.request_date, ir.estimated_date,
        ir.approved_date, ir.payment_date, ir.installation_date, ir.completion_date,
        ir.installation_fee, ir.bill_no, ir.remarks, ir.original_req_id, 
        ir.original_install_id, ir.created_by, ir.created_at, ir.updated_at,
        ir.working_days_to_estimate, ir.working_days_to_payment, ir.working_days_to_install,
        ir.working_days_to_complete, ir.is_exceed_sla, ir.exceed_sla_reason,
        c.firstname as customer_firstname, c.lastname as customer_lastname,
        b.name as branch_name, 
        s.name as status_name,
        it.name as installation_type_name,
        ms.name as meter_size_name
    FROM 
        installation_requests ir
    LEFT JOIN 
        installation_types it ON ir.installation_type_id = it.id
    LEFT JOIN 
        branches b ON ir.branch_code = b.ba_code
    LEFT JOIN 
        customers c ON ir.customer_id = c.id
    LEFT JOIN 
        installation_statuses s ON ir.status_id = s.id
    LEFT JOIN 
        meter_sizes ms ON ir.meter_size_id = ms.id
    WHERE 
        ir.request_no = :request_no
    """
    
    # Execute query with parameters
    result = db.execute(text(sql_query), {"request_no": request_no})
    
    # Get the first row
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Installation request not found")
    
    # Convert row to dictionary format
    item = {
        "id": row.id,
        "request_no": row.request_no,
        "customer_id": row.customer_id,
        "branch_id": row.branch_code,
        "status_id": row.status_id,
        "installation_type_id": row.installation_type_id,
        "meter_size_id": row.meter_size_id,
        "request_date": row.request_date,
        "estimated_date": row.estimated_date,
        "approved_date": row.approved_date,
        "payment_date": row.payment_date,
        "installation_date": row.installation_date,
        "completion_date": row.completion_date,
        "installation_fee": row.installation_fee,
        "bill_no": row.bill_no,
        "remarks": row.remarks,
        "original_req_id": row.original_req_id,
        "original_install_id": row.original_install_id,
        "working_days_to_estimate": row.working_days_to_estimate,
        "working_days_to_payment": row.working_days_to_payment,
        "working_days_to_install": row.working_days_to_install,
        "working_days_to_complete": row.working_days_to_complete,
        "is_exceed_sla": row.is_exceed_sla,
        "exceed_sla_reason": row.exceed_sla_reason,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "customer_name": f"{row.customer_firstname or ''} {row.customer_lastname or ''}".strip(),
        "branch_name": row.branch_name,
        "status_name": row.status_name,
        "installation_type_name": row.installation_type_name,
        "meter_size_name": row.meter_size_name
    }
    
    return item

@router.get("/{installation_id}", response_model=InstallationRequestSchema)
async def get_installation_request(
    installation_id: int,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific installation request by ID.
    """
    logger = logging.getLogger(__name__)
    
    # สร้าง SQL query ด้วย text() function
    sql_query = """
    SELECT 
        ir.id, ir.request_no, ir.customer_id, ir.branch_code, ir.status_id, 
        ir.installation_type_id, ir.meter_size_id, ir.request_date, ir.estimated_date,
        ir.approved_date, ir.payment_date, ir.installation_date, ir.completion_date,
        ir.installation_fee, ir.bill_no, ir.remarks, ir.original_req_id, 
        ir.original_install_id, ir.created_by, ir.created_at, ir.updated_at,
        ir.working_days_to_estimate, ir.working_days_to_payment, ir.working_days_to_install,
        ir.working_days_to_complete, ir.is_exceed_sla, ir.exceed_sla_reason,
        c.firstname as customer_firstname, c.lastname as customer_lastname,
        b.name as branch_name, 
        s.name as status_name,
        it.name as installation_type_name,
        ms.name as meter_size_name
    FROM 
        installation_requests ir
    LEFT JOIN 
        installation_types it ON ir.installation_type_id = it.id
    LEFT JOIN 
        branches b ON ir.branch_code = b.ba_code
    LEFT JOIN 
        customers c ON ir.customer_id = c.id
    LEFT JOIN 
        installation_statuses s ON ir.status_id = s.id
    LEFT JOIN 
        meter_sizes ms ON ir.meter_size_id = ms.id
    WHERE 
        ir.id = :installation_id
    """
    
    # Execute query with parameters
    result = db.execute(text(sql_query), {"installation_id": installation_id})
    
    # Get the first row
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Installation request not found")
    
    # Convert row to dictionary format
    item = {
        "id": row.id,
        "request_no": row.request_no,
        "customer_id": row.customer_id,
        "branch_id": row.branch_code,
        "status_id": row.status_id,
        "installation_type_id": row.installation_type_id,
        "meter_size_id": row.meter_size_id,
        "request_date": row.request_date,
        "estimated_date": row.estimated_date,
        "approved_date": row.approved_date,
        "payment_date": row.payment_date,
        "installation_date": row.installation_date,
        "completion_date": row.completion_date,
        "installation_fee": row.installation_fee,
        "bill_no": row.bill_no,
        "remarks": row.remarks,
        "original_req_id": row.original_req_id,
        "original_install_id": row.original_install_id,
        "working_days_to_estimate": row.working_days_to_estimate,
        "working_days_to_payment": row.working_days_to_payment,
        "working_days_to_install": row.working_days_to_install,
        "working_days_to_complete": row.working_days_to_complete,
        "is_exceed_sla": row.is_exceed_sla,
        "exceed_sla_reason": row.exceed_sla_reason,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "customer_name": f"{row.customer_firstname or ''} {row.customer_lastname or ''}".strip(),
        "branch_name": row.branch_name,
        "status_name": row.status_name,
        "installation_type_name": row.installation_type_name,
        "meter_size_name": row.meter_size_name
    }
    
    return item

@router.get("/temporary/all", response_model=List[InstallationRequestSchema])
async def get_temporary_installations(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[int] = None,
    status_id: Optional[int] = None,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all temporary installation requests.
    """
    logger = logging.getLogger(__name__)
    
    # สร้าง SQL query ด้วย text() function
    sql_query = """
    SELECT 
        ir.id, ir.request_no, ir.customer_id, ir.branch_code, ir.status_id, 
        ir.installation_type_id, ir.meter_size_id, ir.request_date, ir.estimated_date,
        ir.approved_date, ir.payment_date, ir.installation_date, ir.completion_date,
        ir.installation_fee, ir.bill_no, ir.remarks, ir.original_req_id, 
        ir.original_install_id, ir.created_by, ir.created_at, ir.updated_at,
        ir.working_days_to_estimate, ir.working_days_to_payment, ir.working_days_to_install,
        ir.working_days_to_complete, ir.is_exceed_sla, ir.exceed_sla_reason,
        c.firstname as customer_firstname, c.lastname as customer_lastname,
        b.name as branch_name, 
        s.name as status_name,
        it.name as installation_type_name,
        ms.name as meter_size_name
    FROM 
        installation_requests ir
    LEFT JOIN 
        installation_types it ON ir.installation_type_id = it.id
    LEFT JOIN 
        branches b ON ir.branch_code = b.ba_code
    LEFT JOIN 
        customers c ON ir.customer_id = c.id
    LEFT JOIN 
        installation_statuses s ON ir.status_id = s.id
    LEFT JOIN 
        meter_sizes ms ON ir.meter_size_id = ms.id
    WHERE 
        it.code = :type_code
    """
    
    # เตรียมพารามิเตอร์
    params = {"type_code": "2"}
    
    # Add filters if specified
    if branch_id is not None:
        sql_query += " AND ir.branch_code = :branch_id"
        params["branch_id"] = str(branch_id)  # Convert branch_id to string
    
    if status_id is not None:
        sql_query += " AND ir.status_id = :status_id"
        params["status_id"] = status_id
    
    # Add ORDER BY and LIMIT
    sql_query += " ORDER BY ir.request_date DESC"
    sql_query += " LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    # สร้าง SQLAlchemy text object
    query = text(sql_query)
    
    # Execute the query with parameters
    result = db.execute(query, params)
    
    # Convert result to list of dictionaries using SQLAlchemy's _asdict() method or column access
    items = []
    for row in result:
        # Create a dictionary manually by mapping column names to values
        item = {
            "id": row.id,
            "request_no": row.request_no,
            "customer_id": row.customer_id,
            "branch_id": row.branch_code,
            "status_id": row.status_id,
            "installation_type_id": row.installation_type_id,
            "meter_size_id": row.meter_size_id,
            "request_date": row.request_date,
            "estimated_date": row.estimated_date,
            "approved_date": row.approved_date,
            "payment_date": row.payment_date,
            "installation_date": row.installation_date,
            "completion_date": row.completion_date,
            "installation_fee": row.installation_fee,
            "bill_no": row.bill_no,
            "remarks": row.remarks,
            "original_req_id": row.original_req_id,
            "original_install_id": row.original_install_id,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "working_days_to_estimate": row.working_days_to_estimate,
            "working_days_to_payment": row.working_days_to_payment,
            "working_days_to_install": row.working_days_to_install,
            "working_days_to_complete": row.working_days_to_complete,
            "is_exceed_sla": row.is_exceed_sla,
            "exceed_sla_reason": row.exceed_sla_reason,
            # Add relationship fields
            "status_name": row.status_name,
            "branch_name": row.branch_name,
            "customer_name": f"{row.customer_firstname or ''} {row.customer_lastname or ''}".strip(),
            "installation_type_name": row.installation_type_name,
            "meter_size_name": row.meter_size_name
        }
        items.append(item)
    
    return items

@router.get("/permanent/all", response_model=List[InstallationRequestSchema])
async def get_permanent_installations(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[int] = None,
    status_id: Optional[int] = None,
    current_user = Depends(has_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all permanent installation requests.
    """
    logger = logging.getLogger(__name__)
    
    # สร้าง SQL query ด้วย text() function
    sql_query = """
    SELECT 
        ir.id, ir.request_no, ir.customer_id, ir.branch_code, ir.status_id, 
        ir.installation_type_id, ir.meter_size_id, ir.request_date, ir.estimated_date,
        ir.approved_date, ir.payment_date, ir.installation_date, ir.completion_date,
        ir.installation_fee, ir.bill_no, ir.remarks, ir.original_req_id, 
        ir.original_install_id, ir.created_by, ir.created_at, ir.updated_at,
        ir.working_days_to_estimate, ir.working_days_to_payment, ir.working_days_to_install,
        ir.working_days_to_complete, ir.is_exceed_sla, ir.exceed_sla_reason,
        c.firstname as customer_firstname, c.lastname as customer_lastname,
        b.name as branch_name, 
        s.name as status_name,
        it.name as installation_type_name,
        ms.name as meter_size_name
    FROM 
        installation_requests ir
    LEFT JOIN 
        installation_types it ON ir.installation_type_id = it.id
    LEFT JOIN 
        branches b ON ir.branch_code = b.ba_code
    LEFT JOIN 
        customers c ON ir.customer_id = c.id
    LEFT JOIN 
        installation_statuses s ON ir.status_id = s.id
    LEFT JOIN 
        meter_sizes ms ON ir.meter_size_id = ms.id
    WHERE 
        it.code = :type_code
    """
    
    # เตรียมพารามิเตอร์
    params = {"type_code": "1"}
    
    # Add filters if specified
    if branch_id is not None:
        sql_query += " AND ir.branch_code = :branch_id"
        params["branch_id"] = str(branch_id)  # Convert branch_id to string
    
    if status_id is not None:
        sql_query += " AND ir.status_id = :status_id"
        params["status_id"] = status_id
    
    # Add order by, offset and limit
    sql_query += " ORDER BY ir.request_date DESC OFFSET :skip LIMIT :limit"
    params["skip"] = skip
    params["limit"] = limit
    
    # Execute query
    result = db.execute(text(sql_query), params)
    
    # Process results
    items = []
    for row in result:
        item = {
            "id": row.id,
            "request_no": row.request_no,
            "customer_id": row.customer_id,
            "branch_id": row.branch_code,
            "status_id": row.status_id,
            "installation_type_id": row.installation_type_id,
            "meter_size_id": row.meter_size_id,
            "request_date": row.request_date,
            "estimated_date": row.estimated_date,
            "approved_date": row.approved_date,
            "payment_date": row.payment_date,
            "installation_date": row.installation_date,
            "completion_date": row.completion_date,
            "installation_fee": row.installation_fee,
            "bill_no": row.bill_no,
            "remarks": row.remarks,
            "original_req_id": row.original_req_id,
            "original_install_id": row.original_install_id,
            "working_days_to_estimate": row.working_days_to_estimate,
            "working_days_to_payment": row.working_days_to_payment,
            "working_days_to_install": row.working_days_to_install,
            "working_days_to_complete": row.working_days_to_complete,
            "is_exceed_sla": row.is_exceed_sla,
            "exceed_sla_reason": row.exceed_sla_reason,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "customer_name": f"{row.customer_firstname or ''} {row.customer_lastname or ''}".strip(),
            "branch_name": row.branch_name,
            "status_name": row.status_name,
            "installation_type_name": row.installation_type_name,
            "meter_size_name": row.meter_size_name
        }
        items.append(item)
    
    return items 