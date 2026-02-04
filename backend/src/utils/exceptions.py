"""
커스텀 예외 클래스 모듈

애플리케이션에서 사용하는 예외 클래스들을 정의합니다.
각 예외는 에러 코드와 사용자 친화적 메시지를 포함합니다.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone


class RAGChatbotException(Exception):
    """
    RAG 챗봇 기본 예외 클래스
    
    모든 커스텀 예외의 기본 클래스입니다.
    
    Attributes:
        code: 에러 코드
        message: 사용자 친화적 에러 메시지
        details: 추가 상세 정보
        retryable: 재시도 가능 여부
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환합니다."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "retryable": self.retryable,
                "timestamp": self.timestamp
            }
        }


class ValidationError(RAGChatbotException):
    """
    입력 검증 오류
    
    사용자 입력이 유효하지 않을 때 발생합니다.
    """
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details=details,
            retryable=False
        )


class SessionNotFoundError(RAGChatbotException):
    """
    세션 없음 오류
    
    요청한 세션을 찾을 수 없을 때 발생합니다.
    """
    
    def __init__(self, session_id: str):
        super().__init__(
            code="SESSION_NOT_FOUND",
            message=f"세션을 찾을 수 없습니다: {session_id}",
            details={"session_id": session_id},
            retryable=False
        )


class KnowledgeBaseError(RAGChatbotException):
    """
    Knowledge Base 오류
    
    Bedrock Knowledge Base 연동 중 오류가 발생했을 때 사용합니다.
    """
    
    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            code="KNOWLEDGE_BASE_ERROR",
            message=f"Knowledge Base 오류: {message}",
            details={"original_error": original_error} if original_error else {},
            retryable=True  # 일시적 오류일 수 있음
        )


class BedrockError(RAGChatbotException):
    """
    Bedrock API 오류
    
    AWS Bedrock API 호출 중 오류가 발생했을 때 사용합니다.
    """
    
    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            code="BEDROCK_ERROR",
            message=f"Bedrock API 오류: {message}",
            details={"original_error": original_error} if original_error else {},
            retryable=True  # Rate limit 등 일시적 오류일 수 있음
        )


class DatabaseError(RAGChatbotException):
    """
    데이터베이스 오류
    
    SQLite 데이터베이스 작업 중 오류가 발생했을 때 사용합니다.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            code="DATABASE_ERROR",
            message=f"데이터베이스 오류: {message}",
            details={"operation": operation} if operation else {},
            retryable=False
        )


class ConnectionError(RAGChatbotException):
    """
    연결 오류
    
    네트워크 연결 문제가 발생했을 때 사용합니다.
    """
    
    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(
            code="CONNECTION_ERROR",
            message=f"연결 오류: {message}",
            details={"service": service} if service else {},
            retryable=True  # 네트워크 오류는 재시도 가능
        )


class RateLimitError(RAGChatbotException):
    """
    Rate Limit 오류
    
    API 호출 제한에 도달했을 때 사용합니다.
    """
    
    def __init__(self, message: str = "요청 한도를 초과했습니다", retry_after: Optional[int] = None):
        details = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(
            code="RATE_LIMIT_ERROR",
            message=message,
            details=details,
            retryable=True
        )


class ConfigurationError(RAGChatbotException):
    """
    설정 오류
    
    필수 환경변수나 설정이 누락되었을 때 사용합니다.
    """
    
    def __init__(self, message: str, missing_config: Optional[str] = None):
        super().__init__(
            code="CONFIGURATION_ERROR",
            message=f"설정 오류: {message}",
            details={"missing_config": missing_config} if missing_config else {},
            retryable=False
        )


def get_user_friendly_message(error: Exception) -> str:
    """
    예외에서 사용자 친화적 메시지를 추출합니다.
    
    Args:
        error: 예외 객체
        
    Returns:
        str: 사용자 친화적 메시지
    """
    if isinstance(error, RAGChatbotException):
        return error.message
    
    # 일반 예외의 경우 기본 메시지 반환
    error_str = str(error).lower()
    
    if "timeout" in error_str:
        return "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    elif "connection" in error_str:
        return "서버 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
    elif "rate limit" in error_str or "throttl" in error_str:
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    elif "permission" in error_str or "access denied" in error_str:
        return "접근 권한이 없습니다."
    else:
        return "요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def is_retryable_error(error: Exception) -> bool:
    """
    재시도 가능한 오류인지 확인합니다.
    
    Args:
        error: 예외 객체
        
    Returns:
        bool: 재시도 가능 여부
    """
    if isinstance(error, RAGChatbotException):
        return error.retryable
    
    # 일반 예외의 경우 문자열로 판단
    error_str = str(error).lower()
    retryable_keywords = [
        "timeout", "connection", "rate limit", "throttl",
        "temporary", "unavailable", "retry"
    ]
    
    return any(keyword in error_str for keyword in retryable_keywords)
