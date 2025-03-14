"""
API routes for notification system.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_active_user, get_current_superuser
from app.models.user import User
from app.schemas.notification import (
    Notification, NotificationCreate,
    NotificationConfig, NotificationConfigCreate, NotificationConfigUpdate,
    PWANotificationTarget, PWANotificationTargetCreate
)
from app.services.notification_service import PWANotificationService
from app.crud import notifications as notifications_crud

router = APIRouter()


@router.post("/", response_model=Notification)
def create_notification(
    *,
    db: Session = Depends(get_db),
    notification_in: NotificationCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new notification.
    """
    notification = notifications_crud.create_notification(db, obj_in=notification_in)
    return notification


@router.get("/", response_model=List[Notification])
def get_notifications(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    is_sent: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve notifications with optional filters.
    """
    notifications = notifications_crud.get_notifications(
        db, skip=skip, limit=limit, type=type, is_sent=is_sent
    )
    return notifications


@router.get("/{notification_id}", response_model=Notification)
def get_notification(
    *,
    db: Session = Depends(get_db),
    notification_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific notification by ID.
    """
    notification = notifications_crud.get_notification(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.delete("/{notification_id}", response_model=Notification)
def delete_notification(
    *,
    db: Session = Depends(get_db),
    notification_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Delete a notification (admin only).
    """
    notification = notifications_crud.get_notification(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = notifications_crud.delete_notification(db, notification_id=notification_id)
    return notification


# NotificationConfig endpoints
@router.post("/configs/", response_model=NotificationConfig)
def create_notification_config(
    *,
    db: Session = Depends(get_db),
    config_in: NotificationConfigCreate,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Create a new notification config (admin only).
    """
    config = notifications_crud.create_notification_config(db, obj_in=config_in)
    return config


@router.get("/configs/", response_model=List[NotificationConfig])
def get_notification_configs(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve notification configs with optional filters.
    """
    configs = notifications_crud.get_notification_configs(
        db, skip=skip, limit=limit, type=type, is_active=is_active
    )
    return configs


@router.get("/configs/{config_id}", response_model=NotificationConfig)
def get_notification_config(
    *,
    db: Session = Depends(get_db),
    config_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific notification config by ID.
    """
    config = notifications_crud.get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")
    return config


@router.put("/configs/{config_id}", response_model=NotificationConfig)
def update_notification_config(
    *,
    db: Session = Depends(get_db),
    config_id: int,
    config_in: NotificationConfigUpdate,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Update a notification config (admin only).
    """
    config = notifications_crud.get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")
    config = notifications_crud.update_notification_config(db, db_obj=config, obj_in=config_in)
    return config


@router.delete("/configs/{config_id}", response_model=NotificationConfig)
def delete_notification_config(
    *,
    db: Session = Depends(get_db),
    config_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Delete a notification config (admin only).
    """
    config = notifications_crud.get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")
    config = notifications_crud.delete_notification_config(db, config_id=config_id)
    return config


# PWA API specific endpoints
@router.post("/pwa", response_model=Dict[str, Any])
def send_pwa_notification(
    *,
    db: Session = Depends(get_db),
    config_id: int = Body(...),
    message: str = Body(...),
    link: Optional[str] = Body(None),
    ba_code: Optional[str] = Body(None),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Send a notification using PWA API.
    """
    service = PWANotificationService(db)
    result = service.send_notification(
        config_id=config_id,
        message=message,
        link=link,
        ba_code=ba_code
    )
    
    if not result["success"]:
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        raise HTTPException(status_code=500, detail="Failed to send notification")
    
    return result


# PWA NotificationTarget endpoints
@router.post("/configs/{config_id}/targets", response_model=PWANotificationTarget)
def create_pwa_notification_target(
    *,
    db: Session = Depends(get_db),
    config_id: int,
    target_in: PWANotificationTargetCreate,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Create a new PWA notification target for a config (admin only).
    """
    config = notifications_crud.get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")
    
    if config.type != "pwa_api":
        raise HTTPException(
            status_code=400, 
            detail="Cannot add PWA targets to non-PWA notification config"
        )
    
    target = notifications_crud.create_pwa_notification_target(db, obj_in=target_in)
    return target


@router.get("/configs/{config_id}/targets", response_model=List[PWANotificationTarget])
def get_pwa_notification_targets(
    *,
    db: Session = Depends(get_db),
    config_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all PWA notification targets for a config.
    """
    config = notifications_crud.get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")
    
    if config.type != "pwa_api":
        raise HTTPException(
            status_code=400, 
            detail="Cannot get PWA targets from non-PWA notification config"
        )
    
    targets = notifications_crud.get_pwa_notification_targets(db, config_id=config_id)
    return targets 