"""
CRUD operations for notifications.
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.notification import Notification
from app.models.notification_config import NotificationConfig
from app.models.pwa_notification_target import PWANotificationTarget
from app.schemas.notification import (
    NotificationCreate, NotificationConfigCreate, 
    NotificationConfigUpdate, PWANotificationTargetCreate
)


# Notification CRUD operations
def create_notification(db: Session, *, obj_in: NotificationCreate) -> Notification:
    """
    Create a new notification.
    """
    db_obj = Notification(
        type=obj_in.type,
        title=obj_in.title,
        message=obj_in.message,
        receiver=obj_in.receiver,
        link=obj_in.link,
        service_id=obj_in.service_id,
        ba_code=obj_in.ba_code,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_notification(db: Session, notification_id: int) -> Optional[Notification]:
    """
    Get a notification by ID.
    """
    return db.query(Notification).filter(Notification.id == notification_id).first()


def get_notifications(
    db: Session, 
    *, 
    skip: int = 0, 
    limit: int = 100,
    type: Optional[str] = None,
    is_sent: Optional[bool] = None
) -> List[Notification]:
    """
    Get all notifications with optional filters.
    """
    query = db.query(Notification)
    
    if type:
        query = query.filter(Notification.type == type)
    
    if is_sent is not None:
        query = query.filter(Notification.is_sent == is_sent)
    
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def update_notification(
    db: Session, 
    *, 
    db_obj: Notification, 
    obj_in: Union[Dict[str, Any], NotificationCreate]
) -> Notification:
    """
    Update a notification.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    for field in update_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_notification(db: Session, *, notification_id: int) -> Notification:
    """
    Delete a notification.
    """
    obj = db.query(Notification).get(notification_id)
    db.delete(obj)
    db.commit()
    return obj


# NotificationConfig CRUD operations
def create_notification_config(
    db: Session, *, obj_in: NotificationConfigCreate
) -> NotificationConfig:
    """
    Create a new notification config.
    """
    db_obj = NotificationConfig(
        name=obj_in.name,
        type=obj_in.type,
        receiver=obj_in.receiver,
        is_active=obj_in.is_active,
        schedule=obj_in.schedule,
        config_json=obj_in.config_json,
        service_id=obj_in.service_id,
        secret_key=obj_in.secret_key,
        created_by=obj_in.created_by,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_notification_config(
    db: Session, config_id: int
) -> Optional[NotificationConfig]:
    """
    Get a notification config by ID.
    """
    return db.query(NotificationConfig).filter(NotificationConfig.id == config_id).first()


def get_notification_configs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[NotificationConfig]:
    """
    Get all notification configs with optional filters.
    """
    query = db.query(NotificationConfig)
    
    if type:
        query = query.filter(NotificationConfig.type == type)
    
    if is_active is not None:
        query = query.filter(NotificationConfig.is_active == is_active)
    
    return query.order_by(NotificationConfig.name).offset(skip).limit(limit).all()


def update_notification_config(
    db: Session,
    *,
    db_obj: NotificationConfig,
    obj_in: Union[NotificationConfigUpdate, Dict[str, Any]]
) -> NotificationConfig:
    """
    Update a notification config.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    for field in update_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_notification_config(
    db: Session, *, config_id: int
) -> NotificationConfig:
    """
    Delete a notification config.
    """
    obj = db.query(NotificationConfig).get(config_id)
    db.delete(obj)
    db.commit()
    return obj


# PWANotificationTarget CRUD operations
def create_pwa_notification_target(
    db: Session, *, obj_in: PWANotificationTargetCreate
) -> PWANotificationTarget:
    """
    Create a new PWA notification target.
    """
    db_obj = PWANotificationTarget(
        config_id=obj_in.config_id,
        ba_code=obj_in.ba_code,
        is_active=obj_in.is_active,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_pwa_notification_targets(
    db: Session,
    *,
    config_id: int,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[PWANotificationTarget]:
    """
    Get all PWA notification targets for a config with optional filters.
    """
    query = db.query(PWANotificationTarget).filter(PWANotificationTarget.config_id == config_id)
    
    if is_active is not None:
        query = query.filter(PWANotificationTarget.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def delete_pwa_notification_target(
    db: Session, *, target_id: int
) -> PWANotificationTarget:
    """
    Delete a PWA notification target.
    """
    obj = db.query(PWANotificationTarget).get(target_id)
    db.delete(obj)
    db.commit()
    return obj 