# 유틸리티 모듈
"""
공통 유틸리티 함수 및 헬퍼를 포함하는 모듈입니다.

모듈 구성:
- logger.py: 로깅 유틸리티
- exceptions.py: 커스텀 예외 클래스
"""

from .logger import (
    setup_logging,
    get_logger,
    create_logger_with_context,
    mask_sensitive_data,
)

from .exceptions import (
    RAGChatbotException,
    ValidationError,
    SessionNotFoundError,
    KnowledgeBaseError,
    BedrockError,
    DatabaseError,
    ConnectionError,
    RateLimitError,
    ConfigurationError,
    get_user_friendly_message,
    is_retryable_error,
)

__all__ = [
    # Logger
    "setup_logging",
    "get_logger",
    "create_logger_with_context",
    "mask_sensitive_data",
    # Exceptions
    "RAGChatbotException",
    "ValidationError",
    "SessionNotFoundError",
    "KnowledgeBaseError",
    "BedrockError",
    "DatabaseError",
    "ConnectionError",
    "RateLimitError",
    "ConfigurationError",
    "get_user_friendly_message",
    "is_retryable_error",
]
