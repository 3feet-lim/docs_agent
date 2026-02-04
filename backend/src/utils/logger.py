"""
로깅 유틸리티 모듈

JSON 형식의 구조화된 로깅을 제공합니다.
환경변수를 통해 로그 레벨과 형식을 설정할 수 있습니다.
민감 정보 마스킹 기능을 포함합니다.
"""

import logging
import json
import re
import sys
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List

from ..config import get_settings


# 마스킹할 민감 정보 패턴
SENSITIVE_PATTERNS: List[tuple] = [
    # AWS 키
    (r'(AWS_ACCESS_KEY_ID["\s:=]+)[A-Z0-9]{20}', r'\1***MASKED***'),
    (r'(AWS_SECRET_ACCESS_KEY["\s:=]+)[A-Za-z0-9/+=]{40}', r'\1***MASKED***'),
    (r'(AKIA)[A-Z0-9]{16}', r'***AWS_KEY_MASKED***'),
    # 비밀번호
    (r'(password["\s:=]+)[^\s,}"\']+', r'\1***MASKED***'),
    (r'(secret["\s:=]+)[^\s,}"\']+', r'\1***MASKED***'),
    # API 키
    (r'(api[_-]?key["\s:=]+)[^\s,}"\']+', r'\1***MASKED***'),
    (r'(token["\s:=]+)[^\s,}"\']+', r'\1***MASKED***'),
    # 이메일 (부분 마스킹)
    (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'***@\2'),
]


def mask_sensitive_data(text: str) -> str:
    """
    민감 정보를 마스킹합니다.
    
    Args:
        text: 원본 텍스트
        
    Returns:
        str: 마스킹된 텍스트
    """
    if not isinstance(text, str):
        return text
    
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


class JSONFormatter(logging.Formatter):
    """
    JSON 형식의 로그 포매터
    
    로그 메시지를 JSON 형식으로 변환하여 구조화된 로깅을 제공합니다.
    민감 정보는 자동으로 마스킹됩니다.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        로그 레코드를 JSON 문자열로 변환
        
        Args:
            record: 로그 레코드
            
        Returns:
            str: JSON 형식의 로그 문자열
        """
        # 메시지 민감 정보 마스킹
        message = mask_sensitive_data(record.getMessage())
        
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 추가 필드가 있는 경우 포함 (민감 정보 마스킹)
        if hasattr(record, "extra_fields"):
            masked_extra = {}
            for key, value in record.extra_fields.items():
                if isinstance(value, str):
                    masked_extra[key] = mask_sensitive_data(value)
                else:
                    masked_extra[key] = value
            log_data.update(masked_extra)
        
        # 예외 정보가 있는 경우 포함
        if record.exc_info:
            log_data["exception"] = mask_sensitive_data(
                self.formatException(record.exc_info)
            )
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """
    텍스트 형식의 로그 포매터
    
    개발 환경에서 가독성 좋은 텍스트 형식의 로깅을 제공합니다.
    """
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    애플리케이션 로깅 설정
    
    환경변수 또는 파라미터를 통해 로그 레벨과 형식을 설정합니다.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 로그 형식 (json, text)
    """
    settings = get_settings()
    
    # 로그 레벨 결정
    level_str = log_level or settings.log_level
    level = getattr(logging, level_str.upper(), logging.INFO)
    
    # 로그 형식 결정
    format_type = log_format or settings.log_format
    
    # 포매터 선택
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # uvicorn 로거 설정 (FastAPI 서버)
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = []
        uvicorn_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    지정된 이름의 로거를 반환
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    추가 컨텍스트를 포함하는 로거 어댑터
    
    요청 ID, 세션 ID 등의 컨텍스트 정보를 로그에 자동으로 포함합니다.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        로그 메시지에 추가 컨텍스트 포함
        
        Args:
            msg: 로그 메시지
            kwargs: 추가 인자
            
        Returns:
            tuple: (처리된 메시지, 처리된 kwargs)
        """
        extra = kwargs.get("extra", {})
        extra["extra_fields"] = self.extra
        kwargs["extra"] = extra
        return msg, kwargs


def create_logger_with_context(
    name: str,
    **context: Any
) -> LoggerAdapter:
    """
    컨텍스트 정보가 포함된 로거 생성
    
    Args:
        name: 로거 이름
        **context: 컨텍스트 정보 (request_id, session_id 등)
        
    Returns:
        LoggerAdapter: 컨텍스트가 포함된 로거 어댑터
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)
