"""
Notification service for sending notifications.
"""
import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.notification_config import NotificationConfig
from app.models.pwa_notification_target import PWANotificationTarget
from app.crud import notifications as notifications_crud

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Base notification service.
    """
    def __init__(self, db: Session):
        self.db = db

    def send_notification(self, *args, **kwargs):
        """
        Abstract method for sending notification.
        """
        raise NotImplementedError("Subclasses must implement send_notification")


class PWANotificationService(NotificationService):
    """
    PWA API notification service.
    """
    def __init__(self, db: Session):
        super().__init__(db)
        self.api_endpoint = "https://notify.pwa.co.th/api/sendNotify"

    def send_notification(
        self,
        config_id: int,
        message: str,
        link: Optional[str] = None,
        ba_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification using PWA API.
        """
        try:
            # Get notification config
            config = self.db.query(NotificationConfig).filter(
                NotificationConfig.id == config_id,
                NotificationConfig.type == "pwa_api",
                NotificationConfig.is_active == True
            ).first()
            
            if not config:
                logger.error(f"PWA notification config not found: {config_id}")
                return {"success": False, "error": "Notification config not found or inactive"}
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "pwasecretnoti": config.secret_key
            }
            
            # Prepare data
            data = {
                "service_id": config.service_id,
                "message": message,
                "ba_code": ba_code if ba_code else "all"
            }
            
            if link:
                data["link"] = link
            
            # Create notification record
            notification = Notification(
                type="pwa_api",
                title=f"PWA API Notification - {config.name}",
                message=message,
                receiver=config.service_id,
                link=link,
                service_id=config.service_id,
                ba_code=ba_code
            )
            self.db.add(notification)
            self.db.commit()
            
            # Send API request
            logger.info(f"Sending PWA notification: {json.dumps(data)}")
            response = requests.post(self.api_endpoint, json=data, headers=headers)
            response_data = response.json()
            
            # Update notification record
            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            notification.response_data = response_data
            
            if response.status_code == 200:
                notification.total_sent = response_data.get("total_send_user", 0)
                notification.success_count = response_data.get("total_send_token", {}).get("success", 0)
                notification.failure_count = response_data.get("total_send_token", {}).get("failure", 0)
                logger.info(f"PWA notification sent successfully: {response_data}")
            else:
                notification.error_message = response.text
                logger.error(f"PWA notification failed: {response.text}")
                
            self.db.commit()
            
            return {
                "success": response.status_code == 200,
                "notification_id": notification.id,
                "response": response_data
            }
            
        except Exception as e:
            logger.exception(f"Error sending PWA notification: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}


class SystemNotificationService(NotificationService):
    """
    System notification service for in-app notifications.
    """
    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send in-app notification to a user.
        """
        try:
            # Create notification record
            notification = Notification(
                type="system",
                title=title,
                message=message,
                receiver=str(user_id),
                link=link,
                is_sent=True,
                sent_at=datetime.utcnow(),
                total_sent=1,
                success_count=1
            )
            
            self.db.add(notification)
            self.db.commit()
            
            return {
                "success": True,
                "notification_id": notification.id
            }
            
        except Exception as e:
            logger.exception(f"Error sending system notification: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}


class SLANotificationService:
    """
    Service for SLA-based notifications.
    """
    def __init__(self, db: Session):
        self.db = db
        self.pwa_service = PWANotificationService(db)
        self.system_service = SystemNotificationService(db)
    
    def notify_approaching_sla(
        self,
        installation_request_id: int,
        days_remaining: int,
        config_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send notification for approaching SLA.
        """
        from app.models.installation_request import InstallationRequest
        
        # Get the installation request
        request = self.db.query(InstallationRequest).filter(
            InstallationRequest.id == installation_request_id
        ).first()
        
        if not request:
            return {"success": False, "error": "Installation request not found"}
        
        message = f"คำขอหมายเลข {request.request_number} กำลังจะครบกำหนด SLA ในอีก {days_remaining} วัน"
        
        # Send system notification
        system_result = self.system_service.send_notification(
            user_id=request.created_by,
            title="แจ้งเตือนใกล้ครบกำหนด SLA",
            message=message,
            link=f"/installation-requests/{request.id}"
        )
        
        # Send PWA notification if config is provided
        pwa_result = None
        if config_id:
            pwa_result = self.pwa_service.send_notification(
                config_id=config_id,
                message=message,
                link=f"/installation-requests/{request.id}",
                ba_code=request.branch.ba_code
            )
        
        return {
            "success": system_result["success"],
            "system_notification": system_result,
            "pwa_notification": pwa_result
        }
    
    def notify_sla_exceeded(
        self,
        installation_request_id: int,
        days_exceeded: int,
        config_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send notification for exceeded SLA.
        """
        from app.models.installation_request import InstallationRequest
        
        # Get the installation request
        request = self.db.query(InstallationRequest).filter(
            InstallationRequest.id == installation_request_id
        ).first()
        
        if not request:
            return {"success": False, "error": "Installation request not found"}
        
        message = f"คำขอหมายเลข {request.request_number} เกินกำหนด SLA แล้ว {days_exceeded} วัน"
        
        # Send system notification
        system_result = self.system_service.send_notification(
            user_id=request.created_by,
            title="แจ้งเตือนเกินกำหนด SLA",
            message=message,
            link=f"/installation-requests/{request.id}"
        )
        
        # Send PWA notification if config is provided
        pwa_result = None
        if config_id:
            pwa_result = self.pwa_service.send_notification(
                config_id=config_id,
                message=message,
                link=f"/installation-requests/{request.id}",
                ba_code=request.branch.ba_code
            )
        
        return {
            "success": system_result["success"],
            "system_notification": system_result,
            "pwa_notification": pwa_result
        } 