"""
RAG (Retrieval-Augmented Generation) 모듈 패키지

이 패키지는 AWS Bedrock Knowledge Base를 사용한 RAG 기능을 제공합니다.
Knowledge Base가 문서 청킹, 임베딩, 벡터 저장, 검색을 모두 처리합니다.
"""

from .knowledge_base import (
    BedrockKnowledgeBase,
    RetrievedChunk,
    KnowledgeBaseResponse,
    create_knowledge_base_client,
)


__all__ = [
    # knowledge_base
    "BedrockKnowledgeBase",
    "RetrievedChunk",
    "KnowledgeBaseResponse",
    "create_knowledge_base_client",
]
