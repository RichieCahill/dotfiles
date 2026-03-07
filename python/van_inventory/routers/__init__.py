"""Van inventory API routers."""

from python.van_inventory.routers.api import router as api_router
from python.van_inventory.routers.frontend import router as frontend_router

__all__ = ["api_router", "frontend_router"]
