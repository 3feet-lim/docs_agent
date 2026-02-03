"""
RAG 챗봇 시스템 - FastAPI 메인 애플리케이션

이 모듈은 FastAPI 애플리케이션의 진입점입니다.
CORS 설정, 라우터 등록, Socket.IO 통합, 로깅 설정 등을 담당합니다.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio

from .config import get_settings
from .utils.logger import setup_logging, get_logger
from .api.websocket import sio, get_socket_app


# 로깅 설정
setup_logging()
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """
    Health Check 응답 모델
    
    Attributes:
        status: 서버 상태 ("ok" 또는 "error")
        timestamp: 응답 시간 (ISO 8601 형식)
    """
    status: str
    timestamp: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    애플리케이션 생명주기 관리
    
    시작 시 초기화 작업, 종료 시 정리 작업을 수행합니다.
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # 시작 시 실행
    logger.info("RAG 챗봇 시스템 시작")
    settings = get_settings()
    logger.info(
        f"서버 설정: host={settings.backend_host}, port={settings.backend_port}"
    )
    
    yield
    
    # 종료 시 실행
    logger.info("RAG 챗봇 시스템 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="RAG 챗봇 시스템",
    description="사내 문서 기반 RAG(Retrieval-Augmented Generation) AI 챗봇 API",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS 설정
settings = get_settings()

# 허용할 오리진 목록 (Frontend 개발 서버 및 프로덕션)
allowed_origins = [
    f"http://localhost:{settings.frontend_port}",
    f"http://127.0.0.1:{settings.frontend_port}",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Docker 환경에서의 Frontend 컨테이너
    "http://frontend:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

logger.info(f"CORS 설정 완료: allowed_origins={allowed_origins}")


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="서버 상태 확인",
    description="서버의 현재 상태와 타임스탬프를 반환합니다.",
)
async def health_check() -> HealthResponse:
    """
    Health Check 엔드포인트
    
    서버가 정상적으로 동작하는지 확인합니다.
    
    Returns:
        HealthResponse: 서버 상태 및 타임스탬프
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


@app.get(
    "/",
    tags=["Root"],
    summary="루트 엔드포인트",
    description="API 서버 정보를 반환합니다.",
)
async def root() -> dict:
    """
    루트 엔드포인트
    
    API 서버의 기본 정보를 반환합니다.
    
    Returns:
        dict: API 서버 정보
    """
    return {
        "name": "RAG 챗봇 시스템 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# 추후 라우터 등록 예정
# from .api import chat, documents
# app.include_router(chat.router, prefix="/api", tags=["Chat"])
# app.include_router(documents.router, prefix="/api", tags=["Documents"])


# Socket.IO ASGI 앱 생성 (FastAPI와 Socket.IO 통합)
# Socket.IO는 /socket.io 경로에서 처리됨
socket_app = socketio.ASGIApp(sio, app)

logger.info("Socket.IO 서버 초기화 완료")

