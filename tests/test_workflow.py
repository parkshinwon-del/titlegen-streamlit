from titlegene.config import GeminiSettings
from titlegene.services.llm_service import GeminiService
from titlegene.services.session_store import LoopLimitError, SessionStore


class FakeGeminiClient:
    def __init__(self) -> None:
        self.requests: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.requests.append([dict(message) for message in messages])
        return f"response-{len(self.requests)}"


def make_service() -> tuple[GeminiService, SessionStore, FakeGeminiClient]:
    store = SessionStore()
    client = FakeGeminiClient()
    settings = GeminiSettings(
        api_key="test-key",
        model="gemini-test",
        base_url="https://example.test",
        max_tokens=32,
    )
    return GeminiService(store, settings, client), store, client


def test_title_workflow_keeps_prior_context() -> None:
    service, store, client = make_service()
    session_id = store.create_session()

    assert service.analyze(session_id, "텀블러", "친환경 텀블러 소개", "20대 직장인") == "response-1"
    assert service.generate_title(session_id) == "response-2"
    assert service.differentiate(session_id) == "response-3"

    assert len(client.requests[1]) == 3
    assert client.requests[1][1]["content"] == "response-1"
    assert len(client.requests[2]) == 5
    assert client.requests[2][3]["content"] == "response-2"


def test_feedback_is_limited_to_two_attempts() -> None:
    service, store, _ = make_service()
    session_id = store.create_session()

    service.refine(session_id, "더 짧게")
    service.refine(session_id, "조금 더 친근하게")

    try:
        service.refine(session_id, "다시 만들어줘")
    except LoopLimitError:
        pass
    else:
        raise AssertionError("세 번째 피드백은 제한되어야 합니다.")
