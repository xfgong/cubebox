"""Health check endpoints"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}
