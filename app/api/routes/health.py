from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Check service health",
    description="Verifies that the API is running and can connect to PostgreSQL.",
)
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    settings: Settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
