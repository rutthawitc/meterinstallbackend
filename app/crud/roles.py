"""
CRUD operations for Role model.
"""
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


def get_role(db: Session, id: int) -> Optional[Role]:
    """Get a role by ID."""
    return db.query(Role).filter(Role.id == id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get a role by name."""
    return db.query(Role).filter(Role.name == name).first()


def get_roles(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None
) -> List[Role]:
    """Get multiple roles with optional filtering."""
    query = db.query(Role)
    
    if search:
        query = query.filter(
            or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            )
        )
    
    return query.offset(skip).limit(limit).all()


def create_role(db: Session, obj_in: RoleCreate) -> Role:
    """Create a new role."""
    db_obj = Role(
        name=obj_in.name,
        description=obj_in.description,
        is_default=obj_in.is_default,
        permissions=obj_in.permissions
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_role(
    db: Session, 
    db_obj: Role, 
    obj_in: Union[RoleUpdate, Dict[str, Any]]
) -> Role:
    """Update a role."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    for field in update_data:
        if hasattr(db_obj, field) and update_data[field] is not None:
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_role(db: Session, id: int) -> Role:
    """Delete a role."""
    obj = db.query(Role).get(id)
    db.delete(obj)
    db.commit()
    return obj


def assign_role_to_user(db: Session, role_id: int, user_id: int) -> None:
    """Assign a role to a user."""
    from app.models.user import User
    
    role = db.query(Role).filter(Role.id == role_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not role or not user:
        return None
    
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    
    return user


def remove_role_from_user(db: Session, role_id: int, user_id: int) -> None:
    """Remove a role from a user."""
    from app.models.user import User
    
    role = db.query(Role).filter(Role.id == role_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not role or not user:
        return None
    
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
    
    return user 