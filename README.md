# TitleGen

상품 정보와 타겟을 분석하고 제목 생성, 차별화, 피드백 반영을 순서대로 수행하는 FastAPI 웹 서비스입니다.

## 실행

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 사용할 공급자와 API 키 입력
uvicorn titlegene.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. API 문서는 `/docs`, 상태 확인은 `/health`에서 볼 수 있습니다.

## Streamlit 화면 실행

가장 간단한 방법은 `Streamlit 실행.bat`을 더블클릭하는 것입니다. 처음 실행할 때 가상환경과 필요한 패키지를 자동으로 준비하고 브라우저를 엽니다.

터미널에서 직접 실행하려면:

```powershell
cd "C:\Users\jubub\Downloads\TitleGen-multi-llm"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

기본 주소는 `http://localhost:8501`입니다. `.env`를 바꾸었다면 실행 중인 Streamlit을 종료한 뒤 다시 시작하세요.

## LLM 공급자 설정

Claude:

```dotenv
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=...
```

Gemini:

```dotenv
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=...
```

OpenAI 또는 Chat Completions 호환 서버:

```dotenv
LLM_PROVIDER=openai_compatible
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=...
```

모든 공급자에서 전용 키 대신 `LLM_API_KEY`를 사용할 수도 있습니다. 키는 브라우저로 전달되지 않고 서버에서만 사용됩니다.

## 구조와 웹 프런트엔드 검토

- `titlegene/services/llm_service.py`: 공급자별 API 차이를 감추는 어댑터 계층
- `titlegene/routers/generate.py`: 제목 생성 워크플로 API
- `titlegene/services/session_store.py`: 현재 프로세스 메모리 기반 대화 상태
- `titlegene/static/index.html`: 현재 즉시 실행 가능한 웹 UI

현재 화면은 별도 빌드가 없는 HTML/JavaScript라 MVP 배포에는 가장 단순합니다. React 전환도 가능하며 FastAPI는 그대로 API 서버로 유지할 수 있습니다. 전환 시 권장 구조는 `frontend/`의 Vite + React 앱과 현재 `titlegene/` 백엔드를 분리하고, 개발 중에는 Vite 프록시로 `/api`를 연결하며 운영에서는 빌드 산출물을 FastAPI 또는 별도 정적 호스팅에서 제공합니다.

운영 서비스 전에 세션 저장소를 Redis/DB로 바꾸고, CORS 허용 출처 제한, 요청 인증, API 사용량 제한, 구조화 로그를 추가하는 것이 필요합니다.
