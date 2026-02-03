"""
환경변수 및 설정 관리 모듈

이 모듈은 애플리케이션의 모든 설정을 환경변수에서 로드하고 관리합니다.
Pydantic Settings를 사용하여 타입 안전성과 검증을 제공합니다.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    환경변수에서 설정을 로드하며, .env 파일도 지원합니다.
    """
    
    # AWS 인증 설정
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key"
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS 리전"
    )
    
    # AWS Bedrock 설정
    bedrock_model_id: str = Field(
        default="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        description="Bedrock LLM 모델 ID (Claude Sonnet 4.5)"
    )
    bedrock_embeddings_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        description="Bedrock 임베딩 모델 ID"
    )
    
    # S3 벡터 저장소 설정
    s3_bucket_name: str = Field(
        default="",
        description="S3 버킷 이름"
    )
    s3_vector_prefix: str = Field(
        default="vectors/",
        description="S3 벡터 저장 경로 접두사"
    )
    s3_metadata_prefix: str = Field(
        default="metadata/",
        description="S3 메타데이터 저장 경로 접두사"
    )
    s3_raw_documents_prefix: str = Field(
        default="raw-documents/",
        description="S3 원본 문서 저장 경로 접두사"
    )
    
    # 서버 설정
    backend_port: int = Field(
        default=8000,
        description="Backend 서버 포트"
    )
    backend_host: str = Field(
        default="0.0.0.0",
        description="Backend 서버 호스트"
    )
    frontend_port: int = Field(
        default=5173,
        description="Frontend 서버 포트"
    )
    
    # RAG 설정
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="문서 청크 크기 (토큰 수)"
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="청크 간 오버랩 크기 (토큰 수)"
    )
    top_k_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="검색 결과 반환 개수"
    )
    min_similarity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="최소 유사도 임계값"
    )
    
    # 로깅 설정
    log_level: str = Field(
        default="INFO",
        description="로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="로그 형식 (json, text)"
    )
    
    # MCP 설정 (선택적)
    mcp_enabled: bool = Field(
        default=False,
        description="MCP 서버 활성화 여부"
    )
    mcp_server_url: Optional[str] = Field(
        default=None,
        description="MCP 서버 URL"
    )
    
    # Bedrock 추가 설정
    bedrock_max_tokens: int = Field(
        default=4096,
        description="LLM 최대 토큰 수"
    )
    bedrock_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM 온도 설정"
    )
    bedrock_top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="LLM Top-P 설정"
    )
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# 전역 설정 인스턴스
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    설정 인스턴스를 반환합니다.
    
    싱글톤 패턴을 사용하여 설정을 한 번만 로드합니다.
    
    Returns:
        Settings: 애플리케이션 설정 인스턴스
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    설정을 다시 로드합니다.
    
    테스트나 설정 변경 시 사용합니다.
    
    Returns:
        Settings: 새로 로드된 설정 인스턴스
    """
    global _settings
    _settings = Settings()
    return _settings


# 편의를 위한 설정 접근 함수들
def get_aws_config() -> dict:
    """
    AWS 관련 설정을 딕셔너리로 반환합니다.
    
    Returns:
        dict: AWS 설정 딕셔너리
    """
    settings = get_settings()
    config = {
        "region_name": settings.aws_region,
    }
    
    # Access Key가 설정된 경우에만 추가 (IAM Role 사용 시 불필요)
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        config["aws_access_key_id"] = settings.aws_access_key_id
        config["aws_secret_access_key"] = settings.aws_secret_access_key
    
    return config


def get_bedrock_config() -> dict:
    """
    Bedrock 관련 설정을 딕셔너리로 반환합니다.
    
    Returns:
        dict: Bedrock 설정 딕셔너리
    """
    settings = get_settings()
    return {
        "model_id": settings.bedrock_model_id,
        "embeddings_model_id": settings.bedrock_embeddings_model_id,
        "max_tokens": settings.bedrock_max_tokens,
        "temperature": settings.bedrock_temperature,
        "top_p": settings.bedrock_top_p,
    }


def get_rag_config() -> dict:
    """
    RAG 관련 설정을 딕셔너리로 반환합니다.
    
    Returns:
        dict: RAG 설정 딕셔너리
    """
    settings = get_settings()
    return {
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "top_k_results": settings.top_k_results,
        "min_similarity": settings.min_similarity,
    }


def get_s3_config() -> dict:
    """
    S3 관련 설정을 딕셔너리로 반환합니다.
    
    Returns:
        dict: S3 설정 딕셔너리
    """
    settings = get_settings()
    return {
        "bucket_name": settings.s3_bucket_name,
        "vector_prefix": settings.s3_vector_prefix,
        "metadata_prefix": settings.s3_metadata_prefix,
        "raw_documents_prefix": settings.s3_raw_documents_prefix,
    }
