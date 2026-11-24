# TitleGen

Gemini를 활용해 콘텐츠의 타깃을 분석하고, 제목 생성·차별화·피드백 반영을 한 화면에서 수행하는 Streamlit 앱입니다.

## 실행

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

프로젝트 루트에 `.env` 파일을 만들고 Gemini 키를 설정합니다.

```dotenv
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
MAX_TOKENS=1024
```

그다음 아래 명령으로 실행합니다.

```powershell
streamlit run streamlit_app.py
```

기본 주소는 `http://localhost:8501`입니다. API 키는 Python 서버 프로세스에서만 읽고 브라우저로 보내지 않습니다.

## Streamlit Community Cloud 배포

1. GitHub 저장소의 기본 브랜치와 `streamlit_app.py`를 배포 대상으로 선택합니다.
2. Cloud의 **Settings → Secrets**에 `GEMINI_API_KEY`를 추가합니다.
3. 필요하면 `GEMINI_MODEL`과 `MAX_TOKENS`도 Secrets에 설정합니다.
4. 기본 브랜치에 push하면 Streamlit Community Cloud가 앱을 다시 배포합니다.

기존 Cloud Secret에 이미 `LLM_MODEL`이 있다면 호환을 위해 계속 읽습니다. 새 설정은 `GEMINI_MODEL`을 사용하면 됩니다.

## 구조

- `streamlit_app.py`: 입력·버튼·결과 표시를 담당하는 Python 화면
- `titlegene/services/llm_service.py`: Gemini 요청, 응답 처리, 단계별 워크플로
- `titlegene/services/prompt_service.py`: 분석·제목 생성·차별화·피드백 프롬프트
- `titlegene/services/session_store.py`: 세션 ID별 대화 맥락과 피드백 횟수 보관
- `titlegene/config.py`: `.env`와 Cloud Secrets에서 Gemini 설정을 읽고 검증

사용자가 분석을 시작하면 세션 ID가 만들어집니다. 이후 제목 생성, 차별화, 재생성 단계는 같은 세션의 분석 결과와 대화 이력을 이어서 Gemini에 전달합니다. 피드백 재생성은 세션당 최대 2회입니다.

이 저장소에는 직접 작성한 HTML, JavaScript, FastAPI 라우터가 없습니다. 화면과 서버 로직은 Python과 Streamlit으로 구성되어 있습니다. Streamlit이 브라우저에 화면을 표시하기 위해 사용하는 내부 웹 기술은 프레임워크가 관리합니다.
