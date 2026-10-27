import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = {"anthropic", "gemini", "openai_compatible"}


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str
    model: str
    base_url: str
    max_tokens: int


def get_settings() -> LLMSettings:
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    defaults = {
        "anthropic": ("ANTHROPIC_API_KEY", "claude-sonnet-4-6", ""),
        "gemini": ("GEMINI_API_KEY", "gemini-2.5-flash", "https://generativelanguage.googleapis.com/v1beta"),
        "openai_compatible": ("OPENAI_API_KEY", "gpt-4o-mini", "https://api.openai.com/v1"),
    }
    key_name, default_model, default_url = defaults.get(provider, ("LLM_API_KEY", "", ""))
    api_key = os.getenv("LLM_API_KEY", "") or os.getenv(key_name, "")
    return LLMSettings(
        provider=provider,
        api_key=api_key,
        model=os.getenv("LLM_MODEL", os.getenv("MODEL", default_model)),
        base_url=os.getenv("LLM_BASE_URL", default_url).rstrip("/"),
        max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
    )


def validate(settings: LLMSettings | None = None) -> None:
    settings = settings or get_settings()
    if settings.provider not in SUPPORTED_PROVIDERS:
        choices = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise RuntimeError(f"지원하지 않는 LLM_PROVIDER입니다: {settings.provider} (지원: {choices})")
    if not settings.api_key:
        raise RuntimeError(f"{settings.provider} 공급자의 API 키가 설정되지 않았습니다.")
    if not settings.model:
        raise RuntimeError("LLM_MODEL이 설정되지 않았습니다.")
    if settings.provider in {"gemini", "openai_compatible"} and not settings.base_url:
        raise RuntimeError("LLM_BASE_URL이 설정되지 않았습니다.")
