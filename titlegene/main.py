from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from titlegene import config
from titlegene.routers.generate import router as generate_router
from titlegene.services.llm_service import GeminiService
from titlegene.services.session_store import SessionStore


def cors_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8501")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = config.get_settings()
    config.validate(settings)
    store = SessionStore()
    app.state.session_store = store
    app.state.gemini_service = GeminiService(store, settings)
    yield


app = FastAPI(
    title="TitleGen API",
    version="2.0.0",
    description="Gemini 기반 제목 생성 워크플로 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(generate_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
