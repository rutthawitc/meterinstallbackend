"""
Authentication service for user login and token management.
"""
from typing import Optional
import jwt
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, decode_token
from app.models.user import User
from app.schemas.token import TokenPayload

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user using username and password.
    
    Args:
        db: Database session.
        username: Username to authenticate.
        password: Password to authenticate.
        
    Returns:
        User object if authentication is successful, None otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def verify_refresh_token(db: Session, refresh_token: str) -> Optional[User]:
    """
    Verify a refresh token and return the associated user.
    
    Args:
        db: Database session.
        refresh_token: Refresh token to verify.
        
    Returns:
        User object if the token is valid, None otherwise.
    """
    try:
        payload = decode_token(refresh_token)
        token_data = TokenPayload(**payload)
        
        if not token_data.sub or not token_data.id:
            logger.warning("Invalid token payload: missing sub or id")
            return None
            
        user = db.query(User).filter(User.id == token_data.id).first()
        if not user:
            logger.warning(f"User with id {token_data.id} not found")
            return None
            
        if user.username != token_data.sub:
            logger.warning(f"Username mismatch: {user.username} != {token_data.sub}")
            return None
            
        return user
    except jwt.PyJWTError as e:
        logger.error(f"JWT error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None


async def authenticate_with_pwa_api(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user using PWA Authentication API.
    
    Args:
        username: Username to authenticate.
        password: Password to authenticate.
        
    Returns:
        Dict with user information if authentication is successful, None otherwise.
    """
    import httpx
    
    # Remove 'pwa_' prefix if present
    clean_username = username.replace("pwa_", "") if username.startswith("pwa_") else username
    
    logger.info(f"Attempting PWA API authentication for username: {clean_username}")
    
    # Call the PWA authentication service
    try:
        async with httpx.AsyncClient(timeout=settings.PWA_AUTH_API_TIMEOUT) as client:
            logger.debug(f"Sending request to {settings.PWA_AUTH_URL}")
            
            payload = {
                "username": clean_username,
                "pwd": password
            }
            logger.debug(f"Request payload: {payload}")
            
            response = await client.post(
                settings.PWA_AUTH_URL,
                json=payload
            )
            
            logger.debug(f"Response status code: {response.status_code}")
            
            # Check if authentication was successful
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.debug(f"Response data: {response_data}")
                    
                    if response_data.get("status") == "success":
                        # Format user data for our system
                        formatted_user = {
                            "id": clean_username,  # Use username as ID for PWA users
                            "username": f"pwa_{clean_username}",  # Add prefix to indicate PWA user
                            "firstname": response_data.get("firstname", ""),
                            "lastname": response_data.get("lastname", ""),
                            "email": response_data.get("email", ""),
                            # We'll set the legacy role for compatibility, but also pass role_names for multi-role support
                            "role": "admin" if clean_username in settings.PWA_ADMIN_USERS else "user",
                            "role_names": ["admin"] if clean_username in settings.PWA_ADMIN_USERS else ["user"],
                            # Additional fields from PWA API
                            "costcenter": response_data.get("costcenter", ""),
                            "ba": response_data.get("ba", ""),
                            "part": response_data.get("part", ""),
                            "area": response_data.get("area", ""),
                            "job_name": response_data.get("job_name", ""),
                            "level": response_data.get("level", ""),
                            "div_name": response_data.get("div_name", ""),
                            "dep_name": response_data.get("dep_name", ""),
                            "org_name": response_data.get("org_name", ""),
                            "position": response_data.get("position", ""),
                        }
                        
                        logger.info(f"Successfully authenticated PWA user: {clean_username}")
                        return formatted_user
                    else:
                        logger.warning(f"PWA API authentication failed for user {clean_username}: {response_data.get('status_desc', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Failed to parse PWA API response: {str(e)}")
            else:
                logger.warning(f"PWA API returned status code {response.status_code}: {response.text}")
            
            return None
            
    except Exception as e:
        logger.error(f"PWA API authentication error: {str(e)}")
        return None
    
    # Fallback for development/testing (disabled in production)
    if settings.APP_ENV == "development" and username == "pwa_test" and password == "test":
        logger.warning("Using development test user for PWA authentication")
        return {
            "id": "test",
            "username": "pwa_test",
            "firstname": "Test",
            "lastname": "User",
            "email": "test@pwa.co.th",
            "role": "user",
            "role_names": ["user"],
            "costcenter": "1000",
            "ba": "1000",
            "part": "IT",
            "area": "HQ",
            "job_name": "Developer",
            "level": "5",
            "div_name": "IT Division",
            "dep_name": "Software Development",
            "org_name": "PWA",
            "position": "Developer",
        }
    
    return None 