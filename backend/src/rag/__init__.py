"""
RAG (Retrieval-Augmented Generation) 모듈 패키지

이 패키지는 RAG 파이프라인의 모든 구성 요소를 포함합니다:
- document_loader: 문서 로딩 및 파싱
- chunker: 문서 청킹
- embeddings: 벡터 임베딩 생성
- s3_vector_store: S3 벡터 저장소
- retriever: 문서 검색
- chain: RAG 체인 구성
"""

from .document_loader import (
    Document,
    DocumentMetadata,
    DocumentLoader,
    load_document,
    load_documents_from_directory,
)

from .chunker import (
    Chunk,
    DocumentChunker,
    chunk_document,
    chunk_text,
    remove_overlap,
)

from .embeddings import (
    EmbeddingsGenerator,
    EmbeddingError,
    embed_text,
    embed_texts,
)

from .s3_vector_store import (
    S3VectorStore,
    VectorRecord,
    VectorIndex,
    S3Error,
)

from .retriever import (
    Retriever,
    SearchResult,
    cosine_similarity,
    search_similar_chunks,
)

from .chain import (
    RAGChain,
    RAGResponse,
    Message,
    build_rag_prompt,
    create_rag_chain,
    DEFAULT_SYSTEM_PROMPT,
)


__all__ = [
    # document_loader
    "Document",
    "DocumentMetadata",
    "DocumentLoader",
    "load_document",
    "load_documents_from_directory",
    # chunker
    "Chunk",
    "DocumentChunker",
    "chunk_document",
    "chunk_text",
    "remove_overlap",
    # embeddings
    "EmbeddingsGenerator",
    "EmbeddingError",
    "embed_text",
    "embed_texts",
    # s3_vector_store
    "S3VectorStore",
    "VectorRecord",
    "VectorIndex",
    "S3Error",
    # retriever
    "Retriever",
    "SearchResult",
    "cosine_similarity",
    "search_similar_chunks",
    # chain
    "RAGChain",
    "RAGResponse",
    "Message",
    "build_rag_prompt",
    "create_rag_chain",
    "DEFAULT_SYSTEM_PROMPT",
]
