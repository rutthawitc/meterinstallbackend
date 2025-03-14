"""
SQLAlchemy models module.
Import all model classes here to make them available when importing from app.models.
"""

from app.models.user import User
from app.models.region import Region
from app.models.branch import Branch
from app.models.customer import Customer
from app.models.installation_status import InstallationStatus
from app.models.installation_type import InstallationType
from app.models.meter_size import MeterSize
from app.models.installation_request import InstallationRequest
from app.models.installation_log import InstallationLog
from app.models.holiday import Holiday
from app.models.target import Target
from app.models.sla_config import SLAConfig
from app.models.notification import Notification
from app.models.notification_config import NotificationConfig
from app.models.pwa_notification_target import PWANotificationTarget
from app.models.sync_log import SyncLog 