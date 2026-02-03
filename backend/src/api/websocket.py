"""
Socket.IO 이벤트 핸들러 모듈

이 모듈은 Socket.IO 서버 설정 및 실시간 통신 이벤트를 처리합니다.
채팅 메시지 송수신, 스트리밍 응답 등을 담당합니다.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
import asyncio

import socketio
from pydantic import BaseModel, Field

from ..config import get_settings
from ..utils.logger import get_logger
from ..rag import RAGChain, Message as RAGMessage, create_rag_chain


logger = get_logger(__name__)


# Socket.IO 서버 인스턴스 생성
# async_mode='asgi'로 FastAPI와 통합
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],  # CORS는 FastAPI에서 처리
    logger=False,
    engineio_logger=False,
)


class ChatMessageRequest(BaseModel):
    """
    채팅 메시지 요청 모델
    
    Attributes:
        session_id: 세션 식별자
        message: 사용자 메시지 내용
        timestamp: 메시지 전송 시간 (선택)
    """
    session_id: str = Field(..., description="세션 식별자")
    message: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")
    timestamp: Optional[str] = Field(default=None, description="메시지 전송 시간")


class ChatResponseChunk(BaseModel):
    """
    스트리밍 응답 청크 모델
    
    Attributes:
        session_id: 세션 식별자
        content: 응답 내용 (토큰)
        is_final: 마지막 청크 여부
    """
    session_id: str
    content: str
    is_final: bool = False


class ChatResponseComplete(BaseModel):
    """
    응답 완료 모델
    
    Attributes:
        session_id: 세션 식별자
        message_id: 메시지 고유 ID
        sources: 참조 문서 출처 목록
    """
    session_id: str
    message_id: str
    sources: list = Field(default_factory=list)


class ChatError(BaseModel):
    """
    에러 응답 모델
    
    Attributes:
        session_id: 세션 식별자
        code: 에러 코드
        message: 에러 메시지
    """
    session_id: str
    code: str
    message: str


# 연결된 클라이언트 세션 관리
connected_sessions: dict[str, str] = {}  # sid -> session_id

# 세션별 대화 히스토리
conversation_histories: dict[str, list[RAGMessage]] = {}

# RAG 체인 인스턴스 (지연 초기화)
_rag_chain: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """RAG 체인 인스턴스를 반환합니다."""
    global _rag_chain
    if _rag_chain is None:
        try:
            _rag_chain = create_rag_chain()
        except Exception as e:
            logger.warning(f"RAG 체인 초기화 실패 (에코 모드로 동작): {e}")
            _rag_chain = None
    return _rag_chain


@sio.event
async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
    """
    클라이언트 연결 이벤트 핸들러
    
    새로운 클라이언트가 연결되면 호출됩니다.
    
    Args:
        sid: Socket.IO 세션 ID
        environ: WSGI 환경 변수
        auth: 인증 정보 (선택)
    """
    logger.info(f"클라이언트 연결: sid={sid}")
    
    # 세션 ID 생성 또는 auth에서 가져오기
    session_id = auth.get("session_id") if auth else None
    if not session_id:
        session_id = str(uuid.uuid4())
    
    connected_sessions[sid] = session_id
    
    # 연결 확인 메시지 전송
    await sio.emit('connection_established', {
        'session_id': session_id,
        'message': '연결되었습니다.'
    }, to=sid)
    
    logger.info(f"세션 생성: sid={sid}, session_id={session_id}")


@sio.event
async def disconnect(sid: str):
    """
    클라이언트 연결 해제 이벤트 핸들러
    
    클라이언트 연결이 끊어지면 호출됩니다.
    
    Args:
        sid: Socket.IO 세션 ID
    """
    session_id = connected_sessions.pop(sid, None)
    logger.info(f"클라이언트 연결 해제: sid={sid}, session_id={session_id}")


@sio.event
async def chat_message(sid: str, data: dict):
    """
    채팅 메시지 이벤트 핸들러
    
    사용자로부터 채팅 메시지를 받아 처리합니다.
    RAG 파이프라인을 통해 응답을 생성하고 스트리밍합니다.
    
    Args:
        sid: Socket.IO 세션 ID
        data: 메시지 데이터 (session_id, message, timestamp)
    """
    try:
        # 요청 데이터 검증
        request = ChatMessageRequest(**data)
        logger.info(f"메시지 수신: sid={sid}, session_id={request.session_id}")
        
        # 세션 ID 업데이트
        connected_sessions[sid] = request.session_id
        
        # 대화 히스토리 가져오기
        if request.session_id not in conversation_histories:
            conversation_histories[request.session_id] = []
        
        history = conversation_histories[request.session_id]
        
        # 사용자 메시지를 히스토리에 추가
        history.append(RAGMessage(role="user", content=request.message))
        
        message_id = str(uuid.uuid4())
        sources = []
        
        # RAG 체인 사용 시도
        rag_chain = get_rag_chain()
        
        if rag_chain:
            try:
                # RAG 스트리밍 응답 생성
                full_response = ""
                
                async for token, final_response in rag_chain.generate_stream(
                    query=request.message,
                    conversation_history=history[:-1]  # 현재 메시지 제외
                ):
                    if token:
                        full_response += token
                        chunk = ChatResponseChunk(
                            session_id=request.session_id,
                            content=token,
                            is_final=False
                        )
                        await sio.emit('chat_response_chunk', chunk.model_dump(), to=sid)
                    
                    if final_response:
                        sources = [
                            {
                                'document': s.metadata.get('filename', 'unknown'),
                                'chunk_id': s.chunk_id,
                                'similarity': round(s.similarity, 3)
                            }
                            for s in final_response.sources
                        ]
                
                # 어시스턴트 응답을 히스토리에 추가
                history.append(RAGMessage(role="assistant", content=full_response))
                
            except Exception as e:
                logger.error(f"RAG 처리 오류, 에코 모드로 폴백: {e}")
                # 에코 모드로 폴백
                await _send_echo_response(sid, request, message_id)
                return
        else:
            # RAG 체인이 없으면 에코 모드
            await _send_echo_response(sid, request, message_id)
            return
        
        # 응답 완료 이벤트
        complete = ChatResponseComplete(
            session_id=request.session_id,
            message_id=message_id,
            sources=sources
        )
        await sio.emit('chat_response_complete', complete.model_dump(), to=sid)
        
        logger.info(f"응답 완료: sid={sid}, message_id={message_id}")
        
    except Exception as e:
        logger.error(f"메시지 처리 오류: sid={sid}, error={str(e)}")
        
        session_id = connected_sessions.get(sid, data.get('session_id', 'unknown'))
        error = ChatError(
            session_id=session_id,
            code="MESSAGE_PROCESSING_ERROR",
            message=str(e)
        )
        await sio.emit('chat_error', error.model_dump(), to=sid)


async def _send_echo_response(sid: str, request: ChatMessageRequest, message_id: str):
    """에코 응답을 전송합니다 (RAG 미사용 시)."""
    response_content = f"[에코 모드] 메시지를 받았습니다: {request.message}"
    
    # 스트리밍 시뮬레이션
    tokens = response_content.split()
    for i, token in enumerate(tokens):
        is_final = (i == len(tokens) - 1)
        chunk = ChatResponseChunk(
            session_id=request.session_id,
            content=token + (" " if not is_final else ""),
            is_final=is_final
        )
        await sio.emit('chat_response_chunk', chunk.model_dump(), to=sid)
        await asyncio.sleep(0.05)  # 타이핑 효과
    
    # 응답 완료
    complete = ChatResponseComplete(
        session_id=request.session_id,
        message_id=message_id,
        sources=[]
    )
    await sio.emit('chat_response_complete', complete.model_dump(), to=sid)


@sio.event
async def ping(sid: str, data: dict = None):
    """
    Ping 이벤트 핸들러
    
    클라이언트의 연결 상태 확인용 ping에 응답합니다.
    
    Args:
        sid: Socket.IO 세션 ID
        data: 추가 데이터 (선택)
    """
    await sio.emit('pong', {
        'timestamp': datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }, to=sid)


def get_socket_app():
    """
    Socket.IO ASGI 앱을 반환합니다.
    
    FastAPI 앱과 마운트하여 사용합니다.
    
    Returns:
        socketio.ASGIApp: Socket.IO ASGI 애플리케이션
    """
    return socketio.ASGIApp(sio)


def get_sio():
    """
    Socket.IO 서버 인스턴스를 반환합니다.
    
    다른 모듈에서 이벤트 발신 등에 사용합니다.
    
    Returns:
        socketio.AsyncServer: Socket.IO 서버 인스턴스
    """
    return sio
