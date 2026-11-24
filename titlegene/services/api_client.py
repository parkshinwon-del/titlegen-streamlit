from typing import Any

import httpx


class TitleGenAPIError(Exception):
    """FastAPI 서버가 요청을 처리하지 못했을 때 발생한다."""


class TitleGenAPIClient:
    """Streamlit 화면에서 별도 배포된 TitleGen FastAPI 서버를 호출한다."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, timeout=60.0)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json().get("detail", exc.response.text)
            except ValueError:
                detail = exc.response.text
            raise TitleGenAPIError(str(detail)) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise TitleGenAPIError(f"FastAPI 서버 연결에 실패했습니다: {exc}") from exc

    def analyze(self, product_name: str, content: str, target: str) -> tuple[str, str]:
        data = self._post(
            "/api/analyze",
            {"product_name": product_name, "content": content, "target": target},
        )
        return str(data["session_id"]), str(data["report_text"])

    def generate_title(self, session_id: str) -> str:
        return str(self._post("/api/generate-title", {"session_id": session_id})["title_text"])

    def differentiate(self, session_id: str) -> str:
        return str(self._post("/api/differentiate", {"session_id": session_id})["title_text"])

    def refine(self, session_id: str, feedback: str) -> str:
        return str(
            self._post("/api/refine", {"session_id": session_id, "feedback": feedback})["title_text"]
        )
