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
from ..rag import BedrockKnowledgeBase, create_knowledge_base_client
from ..db import save_message, get_session_history


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
    session_id: str = Field(..., alias="sessionId", description="세션 식별자")
    message: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")
    timestamp: Optional[str] = Field(default=None, description="메시지 전송 시간")
    
    model_config = {"populate_by_name": True}


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

# Knowledge Base 클라이언트 (지연 초기화)
_kb_client: Optional[BedrockKnowledgeBase] = None


def get_kb_client() -> Optional[BedrockKnowledgeBase]:
    """Knowledge Base 클라이언트를 반환합니다."""
    global _kb_client
    if _kb_client is None:
        try:
            _kb_client = create_knowledge_base_client()
        except Exception as e:
            logger.warning(f"Knowledge Base 초기화 실패 (에코 모드로 동작): {e}")
            _kb_client = None
    return _kb_client


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
    Bedrock Knowledge Base를 통해 응답을 생성하고 스트리밍합니다.
    
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
        
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        user_message_id = str(uuid.uuid4())
        ai_message_id = str(uuid.uuid4())
        
        # DB에서 대화 히스토리 가져오기
        history = get_session_history(request.session_id)
        
        # 사용자 메시지 DB에 저장
        save_message(
            message_id=user_message_id,
            session_id=request.session_id,
            role="user",
            content=request.message,
            timestamp=timestamp
        )
        
        sources = []
        
        # Knowledge Base 클라이언트 사용 시도
        kb_client = get_kb_client()
        
        if kb_client:
            try:
                # Knowledge Base 스트리밍 응답 생성
                full_response = ""
                
                async for token, final_response in kb_client.retrieve_and_generate_stream(
                    query=request.message,
                    conversation_history=history
                ):
                    if token:
                        full_response += token
                        chunk = ChatResponseChunk(
                            session_id=request.session_id,
                            content=token,
                            is_final=False
                        )
                        await sio.emit('chat_response_chunk', chunk.model_dump(), to=sid)
                        await asyncio.sleep(0.02)  # 자연스러운 타이핑 효과
                    
                    if final_response:
                        # 출처 정보 추출
                        for chunk_info in final_response.retrieved_chunks:
                            uri = chunk_info.source_uri
                            filename = uri.split('/')[-1] if uri else 'unknown'
                            
                            sources.append({
                                'document': filename,
                                'source_uri': uri,
                                'score': round(chunk_info.score, 3)
                            })
                
                # Knowledge Base가 답변을 거부한 경우 일반 Bedrock으로 fallback
                if full_response.strip().lower().startswith("sorry, i am unable"):
                    logger.info("Knowledge Base 답변 거부, Bedrock 직접 호출로 fallback")
                    await _send_bedrock_response(sid, request, ai_message_id, timestamp, history)
                    return
                
                # AI 응답 DB에 저장
                save_message(
                    message_id=ai_message_id,
                    session_id=request.session_id,
                    role="assistant",
                    content=full_response,
                    sources=sources if sources else None,
                    timestamp=timestamp
                )
                
            except Exception as e:
                logger.error(f"Knowledge Base 처리 오류, Bedrock 직접 호출로 폴백: {e}")
                await _send_bedrock_response(sid, request, ai_message_id, timestamp, history)
                return
        else:
            # Knowledge Base가 없으면 Bedrock 직접 호출
            await _send_bedrock_response(sid, request, ai_message_id, timestamp, history)
            return
        
        # 응답 완료 이벤트
        complete = ChatResponseComplete(
            session_id=request.session_id,
            message_id=ai_message_id,
            sources=sources
        )
        await sio.emit('chat_response_complete', complete.model_dump(), to=sid)
        
        logger.info(f"응답 완료: sid={sid}, message_id={ai_message_id}")
        
    except Exception as e:
        logger.error(f"메시지 처리 오류: sid={sid}, error={str(e)}")
        
        session_id = connected_sessions.get(sid, data.get('session_id', 'unknown'))
        error = ChatError(
            session_id=session_id,
            code="MESSAGE_PROCESSING_ERROR",
            message=str(e)
        )
        await sio.emit('chat_error', error.model_dump(), to=sid)


async def _send_bedrock_response(
    sid: str, 
    request: ChatMessageRequest, 
    message_id: str, 
    timestamp: str,
    history: list
):
    """Bedrock 모델을 직접 호출하여 응답을 전송합니다."""
    from ..bedrock_client import get_bedrock_client, BedrockError
    
    try:
        bedrock_client = get_bedrock_client()
        full_response = ""
        
        # 시스템 프롬프트
        system_prompt = """당신은 친절하고 도움이 되는 AI 어시스턴트입니다. 
사용자의 질문에 정확하고 유용한 답변을 제공해주세요.
한국어로 질문하면 한국어로 답변하고, 영어로 질문하면 영어로 답변해주세요."""
        
        # 스트리밍 응답 생성
        async for token in bedrock_client.invoke_stream(
            prompt=request.message,
            system_prompt=system_prompt,
            conversation_history=history
        ):
            if token:
                full_response += token
                chunk = ChatResponseChunk(
                    session_id=request.session_id,
                    content=token,
                    is_final=False
                )
                await sio.emit('chat_response_chunk', chunk.model_dump(), to=sid)
        
        # DB에 저장
        save_message(
            message_id=message_id,
            session_id=request.session_id,
            role="assistant",
            content=full_response,
            timestamp=timestamp
        )
        
        # 응답 완료
        complete = ChatResponseComplete(
            session_id=request.session_id,
            message_id=message_id,
            sources=[]
        )
        await sio.emit('chat_response_complete', complete.model_dump(), to=sid)
        
        logger.info(f"Bedrock 직접 응답 완료: sid={sid}, message_id={message_id}")
        
    except BedrockError as e:
        logger.error(f"Bedrock 호출 실패: {e}")
        # Bedrock도 실패하면 에코 모드로 fallback
        await _send_echo_response(sid, request, message_id, timestamp)


async def _send_echo_response(sid: str, request: ChatMessageRequest, message_id: str, timestamp: str):
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
    
    # 에코 응답도 DB에 저장
    save_message(
        message_id=message_id,
        session_id=request.session_id,
        role="assistant",
        content=response_content,
        timestamp=timestamp
    )
    
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
