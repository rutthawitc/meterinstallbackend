"""
User management routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_superuser, get_current_active_user, has_role
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema
from app.crud import roles as role_crud

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in username, firstname, or lastname"),
    current_user: User = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve users. Requires admin or manager role.
    """
    query = db.query(User)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term))
            | (User.firstname.ilike(search_term))
            | (User.lastname.ilike(search_term))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=UserSchema)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create new user. Requires admin role.
    """
    # Check if user with this username already exists
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Create new user
    try:
        user = User(
            username=user_in.username,
            firstname=user_in.firstname,
            lastname=user_in.lastname,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            costcenter=user_in.costcenter,
            ba=user_in.ba,
            part=user_in.part,
            area=user_in.area,
            job_name=user_in.job_name,
            level=user_in.level,
            div_name=user_in.div_name,
            dep_name=user_in.dep_name,
            org_name=user_in.org_name,
            position=user_in.position,
            role=user_in.role,  # Legacy field
            is_active=user_in.is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign roles if specified
        if user_in.role_ids:
            for role_id in user_in.role_ids:
                role = db.query(Role).filter(Role.id == role_id).first()
                if role:
                    user.roles.append(role)
            db.commit()
            db.refresh(user)
        # If no roles specified but a role is given, try to find or create that role
        elif user_in.role:
            role = db.query(Role).filter(Role.name == user_in.role).first()
            if not role:
                # Create the role if it doesn't exist
                from app.schemas.role import RoleCreate
                role_data = RoleCreate(name=user_in.role, description=f"Auto-created {user_in.role} role")
                role = role_crud.create_role(db, obj_in=role_data)
            user.roles.append(role)
            db.commit()
            db.refresh(user)
            
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_user: User = Depends(has_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id. Requires admin or manager role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a user. Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user fields, excluding role_ids for special handling
    update_data = user_in.dict(exclude={"role_ids"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Handle role assignments
    if user_in.role_ids is not None:
        # Clear existing roles
        user.roles = []
        
        # Assign new roles
        for role_id in user_in.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role:
                user.roles.append(role)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating user",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a user. Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete own user",
        )
    
    try:
        db.delete(user)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Assign a role to a user. Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Check if the user already has this role
    if role in user.roles:
        return {"message": f"User already has role: {role.name}"}
    
    # Assign the role
    user.roles.append(role)
    db.commit()
    
    return {"message": f"Role {role.name} assigned to user {user.username}"}


@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Remove a role from a user. Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Check if the user has this role
    if role not in user.roles:
        return {"message": f"User does not have role: {role.name}"}
    
    # Remove the role
    user.roles.remove(role)
    db.commit()
    
    return {"message": f"Role {role.name} removed from user {user.username}"} 