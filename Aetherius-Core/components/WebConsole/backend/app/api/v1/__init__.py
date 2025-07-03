"""
API v1 endpoints.
"""

from fastapi import APIRouter

from .server import router as server_router
from .console import router as console_router
from .players import router as players_router
from .files import router as files_router
from .monitoring import router as monitoring_router
from .enhanced_monitoring import router as enhanced_monitoring_router
from .auth import router as auth_router
from .components import router as components_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(server_router, prefix="/server", tags=["Server Management"])
api_router.include_router(console_router, prefix="/console", tags=["Console"])
api_router.include_router(players_router, prefix="/players", tags=["Player Management"])
api_router.include_router(files_router, prefix="/files", tags=["File Management"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(enhanced_monitoring_router, prefix="/enhanced-monitoring", tags=["Enhanced Monitoring"])
api_router.include_router(components_router, tags=["Component Management"])

__all__ = ["api_router"]