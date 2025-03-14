"""
Branch management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_superuser, has_role
from app.db.session import get_db
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchUpdate, Branch as BranchSchema, BranchWithRegion

router = APIRouter()


@router.get("/", response_model=List[BranchWithRegion])
async def get_branches(
    skip: int = 0,
    limit: int = 100,
    region_id: Optional[int] = Query(None, description="Filter by region ID"),
    region_code: Optional[str] = Query(None, description="Filter by region code"),
    search: Optional[str] = Query(None, description="Search in branch_code, ba_code, name or region_code"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve branches with optional filtering.
    """
    query = db.query(Branch).options(joinedload(Branch.region))
    
    # Apply region filter if provided
    if region_id:
        query = query.filter(Branch.region_id == region_id)
    
    # Apply region_code filter if provided
    if region_code:
        query = query.filter(Branch.region_code == region_code)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Branch.branch_code.ilike(search_term))
            | (Branch.ba_code.ilike(search_term))
            | (Branch.name.ilike(search_term))
            | (Branch.region_code.ilike(search_term))
        )
    
    branches = query.offset(skip).limit(limit).all()
    return branches


@router.post("/", response_model=BranchSchema)
async def create_branch(
    branch_in: BranchCreate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new branch. Requires admin or manager role.
    """
    # Check if branch with this code already exists
    db_branch_code = db.query(Branch).filter(Branch.branch_code == branch_in.branch_code).first()
    if db_branch_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch with this branch_code already exists",
        )
    
    db_ba_code = db.query(Branch).filter(Branch.ba_code == branch_in.ba_code).first()
    if db_ba_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch with this ba_code already exists",
        )
    
    # Create new branch
    try:
        branch = Branch(
            branch_code=branch_in.branch_code,
            ba_code=branch_in.ba_code,
            name=branch_in.name,
            region_id=branch_in.region_id,
            region_code=branch_in.region_code,
            oracle_org_id=branch_in.oracle_org_id
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating branch: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{branch_id}", response_model=BranchWithRegion)
async def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific branch by id.
    """
    branch = db.query(Branch).options(joinedload(Branch.region)).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    return branch


@router.put("/{branch_id}", response_model=BranchSchema)
async def update_branch(
    branch_id: int,
    branch_in: BranchUpdate,
    current_user = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a branch. Requires admin or manager role.
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    
    # Check if branch_code is being updated and if the new branch_code already exists
    if branch_in.branch_code and branch_in.branch_code != branch.branch_code:
        db_branch = db.query(Branch).filter(Branch.branch_code == branch_in.branch_code).first()
        if db_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch with this branch_code already exists",
            )
            
    # Check if ba_code is being updated and if the new ba_code already exists
    if branch_in.ba_code and branch_in.ba_code != branch.ba_code:
        db_branch = db.query(Branch).filter(Branch.ba_code == branch_in.ba_code).first()
        if db_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch with this ba_code already exists",
            )
    
    # Update branch fields
    update_data = branch_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)
    
    try:
        db.commit()
        db.refresh(branch)
        return branch
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating branch",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{branch_id}", response_model=BranchSchema)
async def delete_branch(
    branch_id: int,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a branch. Requires admin role.
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    
    # Check if the branch has associated data
    if branch.customers or branch.installation_requests or branch.targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete branch with associated data",
        )
    
    try:
        db.delete(branch)
        db.commit()
        return branch
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) 