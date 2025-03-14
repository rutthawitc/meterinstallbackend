"""
Authentication routes for user login, refresh token, and logout.
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from app.crud import roles as role_crud
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User as UserModel
from app.schemas.role import RoleCreate
from app.schemas.token import Token, TokenPayload, RefreshTokenRequest
from app.schemas.user import User
from app.services.auth import authenticate_user, verify_refresh_token, authenticate_with_pwa_api

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Login attempt for username: {form_data.username}")
    
    # Try PWA API authentication first if the username doesn't contain underscore
    # or if it starts with pwa_ prefix
    try_pwa_auth = not "_" in form_data.username or form_data.username.startswith("pwa_")
    
    try:
        # Try to authenticate with local database first
        user = authenticate_user(db, form_data.username, form_data.password)
        
        # If local authentication fails and username format suggests PWA user, try PWA API
        if not user and try_pwa_auth:
            logger.info(f"Local authentication failed, trying PWA API for: {form_data.username}")
            user_data = await authenticate_with_pwa_api(form_data.username, form_data.password)
            
            if user_data:
                logger.info(f"PWA API authentication successful for: {form_data.username}")
                # Check if we already have this PWA user in our database
                
                pwa_user = db.query(UserModel).filter(UserModel.username == user_data["username"]).first()
                
                if pwa_user:
                    logger.info(f"Updating existing PWA user in database: {user_data['username']}")
                    # Update existing user with latest data from PWA
                    pwa_user.firstname = user_data["firstname"]
                    pwa_user.lastname = user_data["lastname"]
                    pwa_user.email = user_data.get("email", "")
                    pwa_user.role = user_data["role"]  # Legacy role field
                    pwa_user.is_active = True
                    pwa_user.last_login = datetime.utcnow()
                    
                    # Update additional PWA user fields
                    pwa_user.costcenter = user_data.get("costcenter", "")
                    pwa_user.ba = user_data.get("ba", "")
                    pwa_user.part = user_data.get("part", "")
                    pwa_user.area = user_data.get("area", "")
                    pwa_user.job_name = user_data.get("job_name", "")
                    pwa_user.level = user_data.get("level", "")
                    pwa_user.div_name = user_data.get("div_name", "")
                    pwa_user.dep_name = user_data.get("dep_name", "")
                    pwa_user.org_name = user_data.get("org_name", "")
                    pwa_user.position = user_data.get("position", "")
                    
                    # Update roles based on role_names from PWA API
                    if user_data.get("role_names"):
                        # Clear existing roles
                        pwa_user.roles = []
                        
                        # For each role name, find or create the role and assign it
                        for role_name in user_data["role_names"]:
                            role = db.query(Role).filter(Role.name == role_name).first()
                            if not role:
                                # Create the role if it doesn't exist
                                role_data = RoleCreate(name=role_name, description=f"Auto-created {role_name} role")
                                role = role_crud.create_role(db, obj_in=role_data)
                            pwa_user.roles.append(role)
                    
                    db.commit()
                    db.refresh(pwa_user)
                else:
                    logger.info(f"Creating new PWA user in database: {user_data['username']}")
                    # Create a new user for this PWA user
                    from passlib.context import CryptContext
                    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                    
                    # Generate a random password for the local account
                    import secrets
                    import string
                    random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16))
                    hashed_password = pwd_context.hash(random_password)
                    
                    # Create new user from PWA data
                    pwa_user = UserModel(
                        username=user_data["username"],
                        firstname=user_data["firstname"],
                        lastname=user_data["lastname"],
                        email=user_data.get("email", ""),
                        role=user_data["role"],  # Legacy role field
                        password_hash=hashed_password,
                        is_active=True,
                        last_login=datetime.utcnow(),
                        costcenter=user_data.get("costcenter", ""),
                        ba=user_data.get("ba", ""),
                        part=user_data.get("part", ""),
                        area=user_data.get("area", ""),
                        job_name=user_data.get("job_name", ""),
                        level=user_data.get("level", ""),
                        div_name=user_data.get("div_name", ""),
                        dep_name=user_data.get("dep_name", ""),
                        org_name=user_data.get("org_name", ""),
                        position=user_data.get("position", "")
                    )
                    
                    db.add(pwa_user)
                    db.commit()
                    db.refresh(pwa_user)
                    
                    # Assign roles based on role_names from PWA API
                    if user_data.get("role_names"):
                        for role_name in user_data["role_names"]:
                            role = db.query(Role).filter(Role.name == role_name).first()
                            if not role:
                                # Create the role if it doesn't exist
                                role_data = RoleCreate(name=role_name, description=f"Auto-created {role_name} role")
                                role = role_crud.create_role(db, obj_in=role_data)
                            pwa_user.roles.append(role)
                        db.commit()
                        db.refresh(pwa_user)
                
                # Create JWT tokens for PWA authenticated user
                access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": pwa_user.username, "role": pwa_user.role, "id": pwa_user.id},
                    expires_delta=access_token_expires
                )
                refresh_token = create_refresh_token(
                    data={"sub": pwa_user.username, "id": pwa_user.id}
                )
                
                # Return tokens and user data
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "refresh_token": refresh_token,
                    "user": {
                        "id": pwa_user.id,
                        "username": pwa_user.username,
                        "email": pwa_user.email,
                        "firstname": pwa_user.firstname,
                        "lastname": pwa_user.lastname,
                        "role": pwa_user.role,
                        "costcenter": pwa_user.costcenter,
                        "ba": pwa_user.ba,
                        "part": pwa_user.part,
                        "area": pwa_user.area,
                        "job_name": pwa_user.job_name,
                        "level": pwa_user.level,
                        "div_name": pwa_user.div_name,
                        "dep_name": pwa_user.dep_name,
                        "org_name": pwa_user.org_name,
                        "position": pwa_user.position
                    }
                }
        
        # If authentication failed, raise an error
        if not user:
            logger.warning(f"Authentication failed for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # If user is inactive, raise an error
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )
        
        # Update last_login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"Local authentication successful for: {form_data.username}")
        
        # Create tokens for local authenticated user
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role, "id": user.id}, 
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "id": user.id}
        )
        
        # Return tokens and user data
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "role": user.role,
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}",
        )


@router.post("/refresh-token", response_model=Token)
async def refresh_token_endpoint(
    token_payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Refresh access token using refresh token.
    """
    user = verify_refresh_token(db, token_payload.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Logout the current user.
    
    Note: This is a placeholder since JWT tokens are stateless. 
    Real logout would be handled client-side by removing the token.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get current user information.
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.get("id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user 