"""Frontend SPA router."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def create_frontend_router(frontend_dir: Path) -> APIRouter:
    """Create a router for serving the frontend SPA."""
    router = APIRouter(tags=["frontend"])

    router.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

    @router.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve React SPA for all non-API routes."""
        file_path = frontend_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dir / "index.html")

    return router
