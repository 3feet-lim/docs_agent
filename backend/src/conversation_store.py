"""
대화 히스토리 저장소 모듈

이 모듈은 세션별 대화 히스토리를 메모리에 저장하고 관리합니다.
각 세션은 고유한 ID로 식별되며, 대화 메시지들을 순서대로 저장합니다.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
from threading import Lock


# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    대화 메시지 데이터 클래스
    
    Attributes:
        id: 메시지 고유 ID
        session_id: 세션 ID
        role: 메시지 역할 (user, assistant)
        content: 메시지 내용
        timestamp: 메시지 생성 시간
        sources: 출처 정보 (RAG 응답의 경우)
        metadata: 추가 메타데이터
    """
    id: str
    session_id: str
    role: str  # "user" 또는 "assistant"
    content: str
    timestamp: str
    sources: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """메시지를 딕셔너리로 변환"""
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }
        if self.sources:
            result["sources"] = self.sources
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """딕셔너리에서 메시지 생성"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            sources=data.get("sources"),
            metadata=data.get("metadata"),
        )


@dataclass
class Session:
    """
    대화 세션 데이터 클래스
    
    Attributes:
        id: 세션 고유 ID
        created_at: 세션 생성 시간
        updated_at: 세션 마지막 업데이트 시간
        messages: 세션의 메시지 리스트
        metadata: 세션 메타데이터
    """
    id: str
    created_at: str
    updated_at: str
    messages: List[Message] = field(default_factory=list)
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """세션을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
        }


class ConversationStore:
    """
    대화 히스토리 저장소 클래스
    
    메모리 기반으로 세션별 대화 히스토리를 관리합니다.
    스레드 안전성을 위해 Lock을 사용합니다.
    """
    
    def __init__(self, max_sessions: int = 1000, max_messages_per_session: int = 100):
        """
        ConversationStore 초기화
        
        Args:
            max_sessions: 최대 세션 수 (LRU 방식으로 오래된 세션 제거)
            max_messages_per_session: 세션당 최대 메시지 수
        """
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._max_sessions = max_sessions
        self._max_messages_per_session = max_messages_per_session
        self._lock = Lock()
        
        logger.info(
            f"ConversationStore 초기화: "
            f"max_sessions={max_sessions}, "
            f"max_messages_per_session={max_messages_per_session}"
        )
    
    def _generate_message_id(self) -> str:
        """고유한 메시지 ID 생성"""
        return f"msg_{uuid.uuid4().hex[:12]}"
    
    def _generate_session_id(self) -> str:
        """고유한 세션 ID 생성"""
        return f"session_{uuid.uuid4().hex[:12]}"
    
    def _get_current_timestamp(self) -> str:
        """현재 UTC 타임스탬프 반환"""
        return datetime.utcnow().isoformat() + "Z"
    
    def _evict_old_sessions(self) -> None:
        """오래된 세션 제거 (LRU 방식)"""
        while len(self._sessions) > self._max_sessions:
            oldest_session_id = next(iter(self._sessions))
            del self._sessions[oldest_session_id]
            logger.debug(f"오래된 세션 제거: {oldest_session_id}")
    
    def create_session(self, session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Session:
        """
        새 세션 생성
        
        Args:
            session_id: 세션 ID (선택, 미지정 시 자동 생성)
            metadata: 세션 메타데이터 (선택)
        
        Returns:
            Session: 생성된 세션
        """
        with self._lock:
            if session_id is None:
                session_id = self._generate_session_id()
            
            # 이미 존재하는 세션이면 반환
            if session_id in self._sessions:
                # LRU 업데이트: 세션을 맨 뒤로 이동
                self._sessions.move_to_end(session_id)
                return self._sessions[session_id]
            
            now = self._get_current_timestamp()
            session = Session(
                id=session_id,
                created_at=now,
                updated_at=now,
                messages=[],
                metadata=metadata,
            )
            
            self._sessions[session_id] = session
            self._evict_old_sessions()
            
            logger.info(f"새 세션 생성: {session_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        세션 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            Optional[Session]: 세션 (없으면 None)
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # LRU 업데이트
                self._sessions.move_to_end(session_id)
            return session
    
    def get_or_create_session(self, session_id: str, metadata: Optional[Dict] = None) -> Session:
        """
        세션 조회 또는 생성
        
        Args:
            session_id: 세션 ID
            metadata: 세션 메타데이터 (새 세션 생성 시 사용)
        
        Returns:
            Session: 세션
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, metadata)
        return session
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
    ) -> Message:
        """
        세션에 메시지 추가
        
        Args:
            session_id: 세션 ID
            role: 메시지 역할 (user, assistant)
            content: 메시지 내용
            sources: 출처 정보 (선택)
            metadata: 메시지 메타데이터 (선택)
        
        Returns:
            Message: 추가된 메시지
        """
        with self._lock:
            # 세션이 없으면 생성
            if session_id not in self._sessions:
                self.create_session(session_id)
            
            session = self._sessions[session_id]
            
            # 메시지 생성
            message = Message(
                id=self._generate_message_id(),
                session_id=session_id,
                role=role,
                content=content,
                timestamp=self._get_current_timestamp(),
                sources=sources,
                metadata=metadata,
            )
            
            # 메시지 추가
            session.messages.append(message)
            session.updated_at = message.timestamp
            
            # 최대 메시지 수 초과 시 오래된 메시지 제거
            while len(session.messages) > self._max_messages_per_session:
                removed = session.messages.pop(0)
                logger.debug(f"오래된 메시지 제거: {removed.id}")
            
            # LRU 업데이트
            self._sessions.move_to_end(session_id)
            
            logger.debug(f"메시지 추가: session={session_id}, role={role}, id={message.id}")
            return message
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = False,
    ) -> List[Message]:
        """
        세션의 메시지 목록 조회
        
        Args:
            session_id: 세션 ID
            limit: 반환할 최대 메시지 수 (최근 메시지부터)
            include_system: 시스템 메시지 포함 여부
        
        Returns:
            List[Message]: 메시지 리스트
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []
            
            messages = session.messages
            
            # 시스템 메시지 필터링
            if not include_system:
                messages = [m for m in messages if m.role != "system"]
            
            # 최근 메시지만 반환
            if limit is not None and limit > 0:
                messages = messages[-limit:]
            
            return messages
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        LLM 컨텍스트용 대화 히스토리 반환
        
        Args:
            session_id: 세션 ID
            limit: 반환할 최대 메시지 수
        
        Returns:
            List[Dict[str, str]]: 대화 히스토리 (role, content 형식)
        """
        messages = self.get_messages(session_id, limit)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """
        세션의 모든 메시지 삭제
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            
            session.messages.clear()
            session.updated_at = self._get_current_timestamp()
            
            logger.info(f"세션 메시지 삭제: {session_id}")
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"세션 삭제: {session_id}")
                return True
            return False
    
    def list_sessions(self) -> List[Dict]:
        """
        모든 세션 목록 조회
        
        Returns:
            List[Dict]: 세션 정보 리스트 (id, created_at, updated_at, message_count)
        """
        with self._lock:
            return [
                {
                    "id": session.id,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": len(session.messages),
                }
                for session in self._sessions.values()
            ]
    
    def get_session_count(self) -> int:
        """현재 세션 수 반환"""
        with self._lock:
            return len(self._sessions)
    
    def get_total_message_count(self) -> int:
        """전체 메시지 수 반환"""
        with self._lock:
            return sum(len(s.messages) for s in self._sessions.values())


# 전역 저장소 인스턴스
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """
    대화 저장소 싱글톤 인스턴스 반환
    
    Returns:
        ConversationStore: 대화 저장소 인스턴스
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store


def reset_conversation_store() -> None:
    """
    대화 저장소 인스턴스 초기화
    
    테스트나 설정 변경 시 사용합니다.
    """
    global _conversation_store
    _conversation_store = None
