"""
User model for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.role import user_roles


class User(Base):
    """
    User model representing system users.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(100), index=True)
    password_hash = Column(String(255))
    costcenter = Column(String(50))
    ba = Column(String(50))
    part = Column(String(100))
    area = Column(String(100))
    job_name = Column(String(100))
    level = Column(String(20))
    div_name = Column(String(100))
    dep_name = Column(String(100))
    org_name = Column(String(100))
    position = Column(String(100))
    # For backward compatibility, will be deprecated
    role = Column(String(20), default="user", nullable=False)  
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    installation_requests = relationship("InstallationRequest", back_populates="created_by_user")
    installation_logs = relationship("InstallationLog", back_populates="changed_by_user")
    holidays = relationship("Holiday", back_populates="updated_by_user")
    sla_configs = relationship("SLAConfig", back_populates="created_by_user")
    notification_configs = relationship("NotificationConfig", back_populates="created_by_user")
    sync_logs = relationship("SyncLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"
        
    @property
    def primary_role(self):
        """Get the primary role for backward compatibility."""
        # Return the first role from the roles list if available, otherwise use the legacy role field
        return self.roles[0].name if self.roles else self.role
        
    def has_role(self, role_names):
        """Check if the user has any of the specified roles."""
        if not self.roles:
            # If using the legacy role field
            return self.role in role_names
        
        # Check if any of the user's roles match the specified roles
        return any(role.name in role_names for role in self.roles) 