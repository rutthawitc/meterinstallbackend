"""
API routes module.
"""
from fastapi import APIRouter

from app.api.routes import (
    auth, users, regions, branches, installation_statuses, 
    installation_types, meter_sizes, sync, holidays, 
    installation_requests, targets, notifications, reports,
    legacy_reports
)

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Region routes
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])

# Branch routes
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])

# Installation status routes
api_router.include_router(
    installation_statuses.router, 
    prefix="/installation-statuses", 
    tags=["installation-statuses"]
)

# Installation type routes
api_router.include_router(
    installation_types.router, 
    prefix="/installation-types", 
    tags=["installation-types"]
)

# Meter size routes
api_router.include_router(
    meter_sizes.router, 
    prefix="/meter-sizes", 
    tags=["meter-sizes"]
)

# Sync routes
api_router.include_router(sync.router, prefix="/sync", tags=["oracle-sync"])

# Holiday routes
api_router.include_router(holidays.router, prefix="/holidays", tags=["holidays"])

# Installation request routes
api_router.include_router(
    installation_requests.router, 
    prefix="/installation-requests", 
    tags=["installation-requests"]
)

# Target routes
api_router.include_router(
    targets.router, 
    prefix="/targets", 
    tags=["targets"]
)

# Notification routes
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"]
)

# Report routes
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"]
)

# Legacy Report routes
api_router.include_router(
    legacy_reports.router,
    prefix="/legacy-reports",
    tags=["legacy-reports"]
) 