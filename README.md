# TitleGen

콘텐츠의 타깃을 분석하고 제목 생성·차별화·피드백 반영을 수행하는 Gemini 기반 제목 생성 서비스입니다. 화면은 Streamlit, 기능별 API는 FastAPI로 분리했습니다.

## 시스템 구조

```text
Streamlit 화면 → FastAPI 라우터 → Python 서비스 → Gemini API
                     ↕
                  세션 저장소
```

- `streamlit_app.py`: 사용자 입력과 결과 표시를 담당하는 Streamlit 화면
- `titlegene/routers/generate.py`: 분석·제목 생성·차별화·재생성 API 라우터
- `titlegene/services/llm_service.py`: Gemini 요청과 응답 처리
- `titlegene/services/prompt_service.py`: 기능별 프롬프트 구성
- `titlegene/services/session_store.py`: 세션 ID별 입력·응답 이력과 피드백 횟수 관리

## 로컬 실행

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

프로젝트 루트에 `.env` 파일을 만듭니다.

```dotenv
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
MAX_TOKENS=1024
```

터미널을 두 개 열어 아래 명령을 각각 실행합니다.

```powershell
# 1. FastAPI 서버
uvicorn titlegene.main:app --reload --port 8000

# 2. Streamlit 화면
$env:API_BASE_URL="http://127.0.0.1:8000"
streamlit run streamlit_app.py
```

Streamlit은 `http://localhost:8501`, FastAPI API 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다.

## API

| 기능 | 메서드·경로 | 역할 |
| --- | --- | --- |
| 타깃 분석 | `POST /api/analyze` | 세션 ID를 발급하고 분석 보고서를 생성 |
| 제목 생성 | `POST /api/generate-title` | 이전 분석 이력으로 제목을 생성 |
| 제목 차별화 | `POST /api/differentiate` | 생성 제목을 차별화 |
| 피드백 반영 | `POST /api/refine` | 피드백을 반영해 제목을 재생성 |

각 API는 같은 `session_id`를 사용해 앞선 분석 결과와 생성 이력을 이어갑니다. 피드백 재생성은 세션당 최대 2회입니다.

## Streamlit Community Cloud 배포

Streamlit Community Cloud는 Streamlit 앱만 실행하므로 FastAPI 서버는 Render, Railway, Cloud Run 같은 별도 Python 서버 환경에 배포해야 합니다.

1. FastAPI 서버에 `GEMINI_API_KEY`, `GEMINI_MODEL`을 설정하고 배포합니다.
2. Streamlit Cloud Secrets에 `API_BASE_URL`을 FastAPI 서버 주소로 설정합니다.
3. Streamlit Cloud에는 Gemini API 키를 넣지 않아도 됩니다. 키는 FastAPI 서버에서만 읽습니다.
4. 기본 브랜치에 push하면 Streamlit Cloud가 화면 앱을 다시 배포합니다.

`API_BASE_URL`이 없는 경우에는 기존 배포 호환을 위해 Streamlit이 Gemini를 직접 호출합니다. 실제 분리 구조로 운영할 때는 반드시 `API_BASE_URL`을 설정하세요.
