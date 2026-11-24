from fastapi import APIRouter, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from titlegene.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DifferentiateResponse,
    RefineRequest,
    RefineResponse,
    SessionRequest,
    TitleResponse,
)
from titlegene.services.llm_service import GeminiAPIError, GeminiService
from titlegene.services.session_store import LoopLimitError, SessionStore

router = APIRouter(prefix="/api", tags=["title-generation"])


def get_service(request: Request) -> GeminiService:
    return request.app.state.gemini_service


def get_store(request: Request) -> SessionStore:
    return request.app.state.session_store


def require_session(store: SessionStore, session_id: str) -> None:
    try:
        store.get_history(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        ) from exc


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request, payload: AnalyzeRequest) -> AnalyzeResponse:
    store = get_store(request)
    service = get_service(request)
    session_id = store.create_session()
    try:
        report = await run_in_threadpool(
            service.analyze, session_id, payload.product_name, payload.content, payload.target
        )
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return AnalyzeResponse(session_id=session_id, report_text=report)


@router.post("/generate-title", response_model=TitleResponse)
async def generate_title(request: Request, payload: SessionRequest) -> TitleResponse:
    store = get_store(request)
    require_session(store, payload.session_id)
    try:
        title = await run_in_threadpool(get_service(request).generate_title, payload.session_id)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return TitleResponse(session_id=payload.session_id, title_text=title)


@router.post("/differentiate", response_model=DifferentiateResponse)
async def differentiate(request: Request, payload: SessionRequest) -> DifferentiateResponse:
    store = get_store(request)
    require_session(store, payload.session_id)
    try:
        title = await run_in_threadpool(get_service(request).differentiate, payload.session_id)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return DifferentiateResponse(session_id=payload.session_id, title_text=title)


@router.post("/refine", response_model=RefineResponse)
async def refine(request: Request, payload: RefineRequest) -> RefineResponse:
    store = get_store(request)
    require_session(store, payload.session_id)
    try:
        title = await run_in_threadpool(get_service(request).refine, payload.session_id, payload.feedback)
    except LoopLimitError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return RefineResponse(session_id=payload.session_id, title_text=title)
