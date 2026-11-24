from fastapi.testclient import TestClient

from titlegene.main import app


class FakeGeminiService:
    def __init__(self, store, settings) -> None:
        self.store = store

    def analyze(self, session_id: str, product_name: str, content: str, target: str) -> str:
        self.store.set_history(session_id, [{"role": "assistant", "content": "분석 결과"}])
        return "분석 결과"

    def generate_title(self, session_id: str) -> str:
        return "생성 제목"

    def differentiate(self, session_id: str) -> str:
        return "차별화 제목"

    def refine(self, session_id: str, feedback: str) -> str:
        return "개선 제목"


def test_title_api_routes_share_a_session(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("titlegene.main.GeminiService", FakeGeminiService)

    with TestClient(app) as client:
        analyzed = client.post(
            "/api/analyze",
            json={"product_name": "텀블러", "content": "친환경 텀블러", "target": "20대 직장인"},
        )
        assert analyzed.status_code == 200
        session_id = analyzed.json()["session_id"]
        assert analyzed.json()["report_text"] == "분석 결과"

        generated = client.post("/api/generate-title", json={"session_id": session_id})
        differentiated = client.post("/api/differentiate", json={"session_id": session_id})
        refined = client.post("/api/refine", json={"session_id": session_id, "feedback": "더 짧게"})

        assert generated.json()["title_text"] == "생성 제목"
        assert differentiated.json()["title_text"] == "차별화 제목"
        assert refined.json()["title_text"] == "개선 제목"


def test_title_api_rejects_an_unknown_session(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("titlegene.main.GeminiService", FakeGeminiService)

    with TestClient(app) as client:
        response = client.post("/api/generate-title", json={"session_id": "unknown"})

    assert response.status_code == 404
