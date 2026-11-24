import os

import streamlit as st

from titlegene import config
from titlegene.services.api_client import TitleGenAPIClient, TitleGenAPIError
from titlegene.services.llm_service import GeminiAPIError, GeminiService
from titlegene.services.session_store import LoopLimitError, SessionStore


st.set_page_config(page_title="TitleGen", page_icon="✨", layout="centered")


def load_cloud_secrets() -> None:
    """Streamlit Cloud Secrets를 환경 변수 기반 설정으로 전달한다."""
    for name in ("API_BASE_URL", "GEMINI_API_KEY", "GEMINI_MODEL", "LLM_MODEL", "MAX_TOKENS"):
        try:
            if name in st.secrets:
                os.environ[name] = str(st.secrets[name])
        except FileNotFoundError:
            return


def initialize() -> None:
    if "workflow" in st.session_state:
        return

    api_base_url = os.getenv("API_BASE_URL", "").strip()
    if api_base_url:
        st.session_state.workflow = TitleGenAPIClient(api_base_url)
        st.session_state.execution_mode = "FastAPI API"
        st.session_state.connection_detail = api_base_url
    else:
        settings = config.get_settings()
        config.validate(settings)
        store = SessionStore()
        st.session_state.store = store
        st.session_state.workflow = GeminiService(store, settings)
        st.session_state.execution_mode = "직접 실행 모드"
        st.session_state.connection_detail = f"Gemini · {settings.model}"

    st.session_state.session_id = None
    st.session_state.report = ""
    st.session_state.title = ""
    st.session_state.differentiated = ""
    st.session_state.refined = ""
    st.session_state.feedback_count = 0


def reset_workflow() -> None:
    for key in (
        "store",
        "workflow",
        "execution_mode",
        "connection_detail",
        "session_id",
        "report",
        "title",
        "differentiated",
        "refined",
        "feedback_count",
    ):
        st.session_state.pop(key, None)
    st.rerun()


def analyze(product_name: str, content: str, target: str) -> tuple[str, str]:
    workflow = st.session_state.workflow
    if st.session_state.execution_mode == "FastAPI API":
        return workflow.analyze(product_name, content, target)

    session_id = st.session_state.store.create_session()
    report = workflow.analyze(session_id, product_name, content, target)
    return session_id, report


try:
    load_cloud_secrets()
    initialize()
except Exception as exc:
    st.error(f"연결 설정을 확인해주세요: {exc}")
    st.info("API_BASE_URL 또는 GEMINI_API_KEY와 GEMINI_MODEL을 설정한 뒤 앱을 다시 실행하세요.")
    st.stop()


st.title("TitleGen")
st.caption(f"{st.session_state.execution_mode} · {st.session_state.connection_detail}")
st.write("상품과 타겟을 분석하여 마케팅 제목을 단계별로 생성합니다.")

with st.sidebar:
    st.subheader("연결 설정")
    st.text(f"실행 방식: {st.session_state.execution_mode}")
    st.caption(st.session_state.connection_detail)
    st.caption("Gemini API 키는 FastAPI 서버 또는 로컬 Python 환경에서만 읽습니다.")
    if st.button("처음부터 다시 시작", use_container_width=True):
        reset_workflow()

st.subheader("1. 데이터 입력")
content = st.text_area("콘텐츠 텍스트", placeholder="글 내용, 주제, 키워드를 입력하세요", height=130)
left, right = st.columns(2)
with left:
    product_name = st.text_input("상품명", placeholder="예: 무릎 보호대 실리콘")
with right:
    target = st.text_input("타겟 성별·나이대", placeholder="예: 50~60대 여성")

if st.button("2. 타겟 분석 시작", type="primary", use_container_width=True):
    if not all((content.strip(), product_name.strip(), target.strip())):
        st.warning("콘텐츠, 상품명, 타겟을 모두 입력해주세요.")
    else:
        try:
            with st.spinner("타겟을 분석하고 있습니다..."):
                session_id, report = analyze(product_name.strip(), content.strip(), target.strip())
            st.session_state.session_id = session_id
            st.session_state.report = report
            st.session_state.title = ""
            st.session_state.differentiated = ""
            st.session_state.refined = ""
            st.session_state.feedback_count = 0
        except (GeminiAPIError, TitleGenAPIError) as exc:
            st.error(f"분석에 실패했습니다: {exc}")

if st.session_state.report:
    st.success("타겟 분석 완료")
    with st.container(border=True):
        st.markdown(st.session_state.report)

    if st.button("3. 제목 생성", type="primary", use_container_width=True):
        try:
            with st.spinner("제목을 생성하고 있습니다..."):
                st.session_state.title = st.session_state.workflow.generate_title(st.session_state.session_id)
        except (GeminiAPIError, TitleGenAPIError) as exc:
            st.error(f"제목 생성에 실패했습니다: {exc}")

if st.session_state.title:
    st.subheader("생성된 제목")
    with st.container(border=True):
        st.markdown(st.session_state.title)

    if st.button("4. 제목 차별화", type="primary", use_container_width=True):
        try:
            with st.spinner("제목을 차별화하고 있습니다..."):
                st.session_state.differentiated = st.session_state.workflow.differentiate(
                    st.session_state.session_id
                )
        except (GeminiAPIError, TitleGenAPIError) as exc:
            st.error(f"제목 차별화에 실패했습니다: {exc}")

if st.session_state.differentiated:
    st.subheader("차별화된 제목")
    with st.container(border=True):
        st.markdown(st.session_state.differentiated)

    st.subheader("5. 피드백 반영")
    loop_count = st.session_state.feedback_count
    st.caption(f"남은 피드백 횟수: {2 - loop_count} / 2")
    feedback = st.text_area("개선하고 싶은 부분", placeholder="예: 좀 더 젊고 친근한 어조로 바꿔줘")
    if st.button("피드백으로 재생성", disabled=loop_count >= 2, use_container_width=True):
        if not feedback.strip():
            st.warning("개선 내용을 입력해주세요.")
        else:
            try:
                with st.spinner("피드백을 반영하고 있습니다..."):
                    st.session_state.refined = st.session_state.workflow.refine(
                        st.session_state.session_id, feedback.strip()
                    )
                st.session_state.feedback_count += 1
                st.rerun()
            except LoopLimitError as exc:
                st.warning(str(exc))
            except (GeminiAPIError, TitleGenAPIError) as exc:
                st.error(f"피드백 반영에 실패했습니다: {exc}")

if st.session_state.refined:
    st.subheader("최종 제목")
    with st.container(border=True):
        st.markdown(st.session_state.refined)
    st.success("제목이 완성되었습니다.")
