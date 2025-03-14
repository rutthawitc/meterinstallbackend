"""
Script to initialize roles in the database.
"""
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic roles to initialize
INITIAL_ROLES = [
    {
        "name": "admin",
        "description": "Full system administrator with all privileges",
        "is_default": False,
        "permissions": "admin,users,roles,regions,branches,installation_types,installation_statuses,meter_sizes,installation_requests,targets"
    },
    {
        "name": "manager",
        "description": "Branch manager with managerial privileges",
        "is_default": False,
        "permissions": "users:read,regions:read,branches:read,installation_types:read,installation_statuses:read,meter_sizes:read,installation_requests:*,targets:*"
    },
    {
        "name": "supervisor",
        "description": "Team supervisor with team management privileges",
        "is_default": False,
        "permissions": "users:read,regions:read,branches:read,installation_types:read,installation_statuses:read,meter_sizes:read,installation_requests:*,targets:read"
    },
    {
        "name": "user",
        "description": "Regular user with basic privileges",
        "is_default": True,
        "permissions": "users:self,regions:read,branches:read,installation_types:read,installation_statuses:read,meter_sizes:read,installation_requests:create,installation_requests:read"
    }
]


def init_roles(db: Session) -> None:
    """
    Initialize roles in the database.
    
    Args:
        db: Database session.
    """
    # Check if roles already exist
    existing_roles = db.query(Role).count()
    if existing_roles > 0:
        logger.info(f"Database already has {existing_roles} roles. Skipping role initialization.")
        return

    # Create roles
    for role_data in INITIAL_ROLES:
        role = Role(**role_data)
        db.add(role)
        logger.info(f"Adding role: {role.name}")
    
    try:
        db.commit()
        logger.info(f"Created {len(INITIAL_ROLES)} initial roles.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating roles: {e}")


def migrate_user_roles(db: Session) -> None:
    """
    Migrate existing users to the new role system.
    
    Args:
        db: Database session.
    """
    # Get all users
    users = db.query(User).all()
    
    # Get all roles
    roles = {role.name: role for role in db.query(Role).all()}
    
    if not roles:
        logger.warning("No roles found in database. Run init_roles first.")
        return
    
    migrated_count = 0
    
    for user in users:
        # Skip users that already have roles assigned
        if user.roles:
            continue
        
        # Map legacy role to new role
        if user.role in roles:
            user.roles.append(roles[user.role])
            migrated_count += 1
        else:
            # Default to "user" role if legacy role doesn't exist
            if "user" in roles:
                user.roles.append(roles["user"])
                migrated_count += 1
    
    try:
        db.commit()
        logger.info(f"Migrated {migrated_count} users to the new role system.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating user roles: {e}")


def main() -> None:
    """Main function to initialize database with roles."""
    logger.info("Creating initial roles")
    db = SessionLocal()
    try:
        init_roles(db)
        migrate_user_roles(db)
    finally:
        db.close()
    logger.info("Initial roles created")


if __name__ == "__main__":
    main() 