from typing import Any, Protocol
from urllib.parse import quote

import anthropic
import httpx

from titlegene.config import LLMSettings, get_settings, validate
from titlegene.services.prompt_service import PromptService
from titlegene.services.session_store import SessionStore


class LLMAPIError(Exception):
    """Configured LLM provider failed to return a response."""


class LLMClient(Protocol):
    def complete(self, messages: list[dict[str, Any]]) -> str: ...


class AnthropicClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self.client = anthropic.Anthropic(api_key=settings.api_key)

    def complete(self, messages: list[dict[str, Any]]) -> str:
        response = self.client.messages.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            messages=messages,
        )
        return response.content[0].text


class GeminiClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self.client = httpx.Client(timeout=60.0)

    def complete(self, messages: list[dict[str, Any]]) -> str:
        contents = [
            {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": str(m["content"])}]}
            for m in messages
        ]
        model = quote(self.settings.model, safe="")
        response = self.client.post(
            f"{self.settings.base_url}/models/{model}:generateContent",
            params={"key": self.settings.api_key},
            json={"contents": contents, "generationConfig": {"maxOutputTokens": self.settings.max_tokens}},
        )
        response.raise_for_status()
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMAPIError("Gemini 응답에 텍스트가 없습니다.") from exc


class OpenAICompatibleClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self.client = httpx.Client(timeout=60.0)

    def complete(self, messages: list[dict[str, Any]]) -> str:
        response = self.client.post(
            f"{self.settings.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.api_key}"},
            json={"model": self.settings.model, "max_tokens": self.settings.max_tokens, "messages": messages},
        )
        response.raise_for_status()
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMAPIError("OpenAI 호환 API 응답에 텍스트가 없습니다.") from exc


def create_client(settings: LLMSettings) -> LLMClient:
    clients = {"anthropic": AnthropicClient, "gemini": GeminiClient, "openai_compatible": OpenAICompatibleClient}
    return clients[settings.provider](settings)


class LLMService:
    def __init__(self, session_store: SessionStore, settings: LLMSettings | None = None, client: LLMClient | None = None) -> None:
        self._store = session_store
        self.settings = settings or get_settings()
        validate(self.settings)
        self._client = client or create_client(self.settings)

    def _call_api(self, session_id: str, user_message: str) -> str:
        history = list(self._store.get_history(session_id))
        history.append({"role": "user", "content": user_message})
        try:
            assistant_text = self._client.complete(history)
        except LLMAPIError:
            raise
        except Exception as exc:
            raise LLMAPIError(str(exc)) from exc
        history.append({"role": "assistant", "content": assistant_text})
        self._store.set_history(session_id, history)
        return assistant_text

    def analyze(self, session_id: str, product_name: str, content: str, target: str) -> str:
        return self._call_api(session_id, PromptService.build_analyze_prompt(product_name, content, target))

    def generate_title(self, session_id: str) -> str:
        return self._call_api(session_id, PromptService.build_title_prompt())

    def differentiate(self, session_id: str) -> str:
        return self._call_api(session_id, PromptService.build_differentiate_prompt())

    def refine(self, session_id: str, feedback: str) -> str:
        self._store.increment_loop(session_id)
        return self._call_api(session_id, PromptService.build_refine_prompt(feedback))
