"""
채팅 REST API 모듈

이 모듈은 HTTP 기반 채팅 API 엔드포인트를 제공합니다.
실시간 스트리밍이 필요 없는 경우 사용합니다.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import get_settings
from ..utils.logger import get_logger
from ..rag import BedrockKnowledgeBase, create_knowledge_base_client
from ..db import save_message, get_session_messages, get_session_history, delete_session, get_all_sessions


logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """
    채팅 요청 모델
    
    Attributes:
        session_id: 세션 식별자 (선택, 없으면 새로 생성)
        message: 사용자 메시지
    """
    session_id: Optional[str] = Field(default=None, description="세션 ID")
    message: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")


class Source(BaseModel):
    """
    출처 정보 모델
    
    Attributes:
        document: 문서명
        source_uri: S3 URI
        score: 관련성 점수
    """
    document: str
    source_uri: str
    score: float


class ChatResponse(BaseModel):
    """
    채팅 응답 모델
    
    Attributes:
        session_id: 세션 ID
        message_id: 메시지 고유 ID
        content: 응답 내용
        sources: 참조 문서 출처 목록
        timestamp: 응답 시간
    """
    session_id: str
    message_id: str
    content: str
    sources: List[Source] = Field(default_factory=list)
    timestamp: str


class ErrorResponse(BaseModel):
    """
    에러 응답 모델
    
    Attributes:
        code: 에러 코드
        message: 에러 메시지
        timestamp: 에러 발생 시간
    """
    code: str
    message: str
    timestamp: str


# Knowledge Base 클라이언트 (지연 초기화)
_kb_client: Optional[BedrockKnowledgeBase] = None


def get_kb_client() -> Optional[BedrockKnowledgeBase]:
    """Knowledge Base 클라이언트를 반환합니다."""
    global _kb_client
    if _kb_client is None:
        try:
            _kb_client = create_knowledge_base_client()
        except Exception as e:
            logger.warning(f"Knowledge Base 초기화 실패: {e}")
            _kb_client = None
    return _kb_client


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        500: {"model": ErrorResponse, "description": "서버 오류"}
    },
    summary="채팅 메시지 전송",
    description="사용자 메시지를 전송하고 AI 응답을 받습니다."
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    채팅 메시지를 처리하고 응답을 반환합니다.
    
    Args:
        request: 채팅 요청
        
    Returns:
        ChatResponse: AI 응답
    """
    # 세션 ID 생성 또는 사용
    session_id = request.session_id or str(uuid.uuid4())
    user_message_id = str(uuid.uuid4())
    ai_message_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # DB에서 대화 히스토리 가져오기
    history = get_session_history(session_id)
    
    # 사용자 메시지 DB에 저장
    save_message(
        message_id=user_message_id,
        session_id=session_id,
        role="user",
        content=request.message,
        timestamp=timestamp
    )
    
    logger.info(f"채팅 요청: session_id={session_id}, message={request.message[:50]}...")
    
    try:
        kb_client = get_kb_client()
        
        if kb_client:
            # Knowledge Base로 응답 생성
            response = kb_client.retrieve_and_generate(
                query=request.message,
                conversation_history=history
            )
            
            content = response.answer
            sources = [
                Source(
                    document=chunk.source_uri.split('/')[-1] if chunk.source_uri else 'unknown',
                    source_uri=chunk.source_uri,
                    score=round(chunk.score, 3)
                )
                for chunk in response.retrieved_chunks
            ]
            sources_dict = [s.model_dump() for s in sources]
        else:
            # 에코 모드
            content = f"[에코 모드] 메시지를 받았습니다: {request.message}"
            sources = []
            sources_dict = []
        
        # AI 응답 DB에 저장
        save_message(
            message_id=ai_message_id,
            session_id=session_id,
            role="assistant",
            content=content,
            sources=sources_dict if sources_dict else None,
            timestamp=timestamp
        )
        
        return ChatResponse(
            session_id=session_id,
            message_id=ai_message_id,
            content=content,
            sources=sources,
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CHAT_ERROR",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )


@router.delete(
    "/chat/{session_id}",
    summary="대화 히스토리 삭제",
    description="특정 세션의 대화 히스토리를 삭제합니다."
)
async def delete_chat_history(session_id: str) -> dict:
    """
    세션의 대화 히스토리를 삭제합니다.
    
    Args:
        session_id: 삭제할 세션 ID
        
    Returns:
        dict: 삭제 결과
    """
    deleted = delete_session(session_id)
    
    if deleted:
        return {"message": "대화 히스토리가 삭제되었습니다.", "session_id": session_id}
    else:
        return {"message": "해당 세션을 찾을 수 없습니다.", "session_id": session_id}


@router.get(
    "/chat/{session_id}/history",
    summary="대화 히스토리 조회",
    description="특정 세션의 대화 히스토리를 조회합니다."
)
async def get_chat_history_endpoint(session_id: str) -> dict:
    """
    세션의 대화 히스토리를 조회합니다.
    
    Args:
        session_id: 조회할 세션 ID
        
    Returns:
        dict: 대화 히스토리
    """
    messages = get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages)
    }


@router.get(
    "/sessions",
    summary="세션 목록 조회",
    description="모든 채팅 세션 목록을 조회합니다."
)
async def list_sessions() -> dict:
    """
    모든 세션 목록을 조회합니다.
    
    Returns:
        dict: 세션 목록
    """
    sessions = get_all_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }
