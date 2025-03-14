"""
API dependencies module.
"""
from typing import List, Callable, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current active user from the token.
    
    Args:
        current_user: Current user from the JWT token.
        db: Database session.
        
    Returns:
        The user object if active.
        
    Raises:
        HTTPException: If the user is not found or not active.
    """
    user = db.query(User).filter(User.id == current_user.get("id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current superuser from the token.
    
    Args:
        current_user: Current active user.
        
    Returns:
        The user object if it's a superuser.
        
    Raises:
        HTTPException: If the user is not a superuser.
    """
    # Check if the user has the "admin" role in either the roles relationship or legacy role field
    if not current_user.has_role(["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def has_role(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory to check if the current user has one of the allowed roles.
    
    Args:
        allowed_roles: List of allowed roles.
        
    Returns:
        A dependency function that checks if the user has one of the allowed roles.
    """
    
    def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if the current user has one of the allowed roles.
        
        Args:
            current_user: Current active user.
            
        Returns:
            The user object if it has one of the allowed roles.
            
        Raises:
            HTTPException: If the user doesn't have one of the allowed roles.
        """
        # Use the has_role method of the User model
        if not current_user.has_role(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user
    
    return check_role 