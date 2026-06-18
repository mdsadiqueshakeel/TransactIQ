import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def validate_startup_configuration() -> None:
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.error(
            "GEMINI_API_KEY is not configured; LLM classification and narrative will use graceful fallbacks."
        )
        return

    if settings.gemini_model != "gemini-2.5-flash":
        logger.warning(
            "Unexpected Gemini model configured",
            extra={"gemini_model": settings.gemini_model},
        )

    logger.info(
        "Gemini configuration detected",
        extra={"gemini_model": settings.gemini_model},
    )
