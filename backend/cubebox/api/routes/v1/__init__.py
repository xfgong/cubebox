"""V1 API Routes

Exports all v1 API routers.
"""

from cubebox.api.routes.v1.agents import router as agents_router

__all__ = ["agents_router"]
