import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


@dataclass(frozen=True)
class GeminiSettings:
    """Settings used by the server-side Gemini client."""

    api_key: str
    model: str
    base_url: str
    max_tokens: int


def get_settings() -> GeminiSettings:
    """Load Gemini-only settings without exposing the key to the browser."""
    return GeminiSettings(
        api_key=os.getenv("GEMINI_API_KEY", "") or os.getenv("LLM_API_KEY", ""),
        # LLM_MODEL is retained as a deployment-compatible alias for the existing Cloud secret.
        model=os.getenv("GEMINI_MODEL") or os.getenv("LLM_MODEL") or "gemini-2.5-flash",
        base_url=(os.getenv("GEMINI_BASE_URL") or GEMINI_BASE_URL).rstrip("/"),
        max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
    )


def validate(settings: GeminiSettings | None = None) -> None:
    settings = settings or get_settings()
    if not settings.api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")
    if not settings.model:
        raise RuntimeError("GEMINI_MODEL이 설정되지 않았습니다.")
    if not settings.base_url:
        raise RuntimeError("GEMINI_BASE_URL이 설정되지 않았습니다.")
    if settings.max_tokens <= 0:
        raise RuntimeError("MAX_TOKENS는 1 이상의 정수여야 합니다.")
