import os

import streamlit as st

from titlegene import config
from titlegene.services.llm_service import GeminiAPIError, GeminiService
from titlegene.services.session_store import LoopLimitError, SessionStore


st.set_page_config(page_title="TitleGen", page_icon="✨", layout="centered")


def load_cloud_secrets() -> None:
    """Expose Streamlit Cloud secrets through the same env-based config API."""
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL", "LLM_MODEL", "MAX_TOKENS"):
        try:
            if name in st.secrets:
                os.environ[name] = str(st.secrets[name])
        except FileNotFoundError:
            return


def initialize() -> None:
    if "store" not in st.session_state:
        settings = config.get_settings()
        config.validate(settings)
        store = SessionStore()
        st.session_state.store = store
        st.session_state.service = GeminiService(store, settings)
        st.session_state.session_id = None
        st.session_state.report = ""
        st.session_state.title = ""
        st.session_state.differentiated = ""
        st.session_state.refined = ""


def reset_workflow() -> None:
    for key in ("store", "service", "session_id", "report", "title", "differentiated", "refined"):
        st.session_state.pop(key, None)
    st.rerun()


try:
    load_cloud_secrets()
    initialize()
except Exception as exc:
    st.error(f"LLM 설정을 확인해주세요: {exc}")
    st.info("프로젝트 폴더의 .env 파일에 GEMINI_API_KEY와 GEMINI_MODEL을 설정한 뒤 앱을 다시 실행하세요.")
    st.stop()

settings = st.session_state.service.settings

st.title("TitleGen")
st.caption(f"Gemini · {settings.model}")
st.write("상품과 타겟을 분석하여 마케팅 제목을 단계별로 생성합니다.")

with st.sidebar:
    st.subheader("연결 설정")
    st.text("공급자: Gemini")
    st.text(f"모델: {settings.model}")
    st.caption("API 키는 서버의 .env에서만 읽으며 화면에 표시하지 않습니다.")
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
            sid = st.session_state.store.create_session()
            with st.spinner("타겟을 분석하고 있습니다..."):
                st.session_state.report = st.session_state.service.analyze(
                    sid, product_name.strip(), content.strip(), target.strip()
                )
            st.session_state.session_id = sid
            st.session_state.title = ""
            st.session_state.differentiated = ""
            st.session_state.refined = ""
        except GeminiAPIError as exc:
            st.error(f"Gemini 호출에 실패했습니다: {exc}")

if st.session_state.report:
    st.success("타겟 분석 완료")
    with st.container(border=True):
        st.markdown(st.session_state.report)

    if st.button("3. 제목 생성", type="primary", use_container_width=True):
        try:
            with st.spinner("제목을 생성하고 있습니다..."):
                st.session_state.title = st.session_state.service.generate_title(st.session_state.session_id)
        except GeminiAPIError as exc:
            st.error(f"Gemini 호출에 실패했습니다: {exc}")

if st.session_state.title:
    st.subheader("생성된 제목")
    with st.container(border=True):
        st.markdown(st.session_state.title)

    if st.button("4. 제목 차별화", type="primary", use_container_width=True):
        try:
            with st.spinner("제목을 차별화하고 있습니다..."):
                st.session_state.differentiated = st.session_state.service.differentiate(
                    st.session_state.session_id
                )
        except GeminiAPIError as exc:
            st.error(f"Gemini 호출에 실패했습니다: {exc}")

if st.session_state.differentiated:
    st.subheader("차별화된 제목")
    with st.container(border=True):
        st.markdown(st.session_state.differentiated)

    st.subheader("5. 피드백 반영")
    loop_count = st.session_state.store.get_loop_count(st.session_state.session_id)
    st.caption(f"남은 피드백 횟수: {2 - loop_count} / 2")
    feedback = st.text_area("개선하고 싶은 부분", placeholder="예: 좀 더 젊고 친근한 어조로 바꿔줘")
    if st.button("피드백으로 재생성", disabled=loop_count >= 2, use_container_width=True):
        if not feedback.strip():
            st.warning("개선 내용을 입력해주세요.")
        else:
            try:
                with st.spinner("피드백을 반영하고 있습니다..."):
                    st.session_state.refined = st.session_state.service.refine(
                        st.session_state.session_id, feedback.strip()
                    )
                st.rerun()
            except LoopLimitError as exc:
                st.warning(str(exc))
            except GeminiAPIError as exc:
                st.error(f"Gemini 호출에 실패했습니다: {exc}")

if st.session_state.refined:
    st.subheader("최종 제목")
    with st.container(border=True):
        st.markdown(st.session_state.refined)
    st.success("제목이 완성되었습니다.")
