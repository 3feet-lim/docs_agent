"""
문서 검색 모듈

이 모듈은 벡터 유사도 기반 문서 검색 기능을 제공합니다.
코사인 유사도를 사용하여 관련 문서를 검색합니다.
"""

import math
from typing import List, Optional
from dataclasses import dataclass

from .s3_vector_store import S3VectorStore, VectorRecord
from .embeddings import EmbeddingsGenerator
from ..config import get_settings
from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class SearchResult:
    """
    검색 결과 클래스
    
    Attributes:
        chunk_id: 청크 ID
        document_id: 문서 ID
        content: 청크 내용
        similarity: 유사도 점수 (0~1)
        metadata: 메타데이터
    """
    chunk_id: str
    document_id: str
    content: str
    similarity: float
    metadata: dict


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    두 벡터 간의 코사인 유사도를 계산합니다.
    
    Args:
        vec1: 첫 번째 벡터
        vec2: 두 번째 벡터
        
    Returns:
        float: 코사인 유사도 (-1 ~ 1)
    """
    if len(vec1) != len(vec2):
        raise ValueError("벡터 차원이 일치하지 않습니다.")
    
    if not vec1 or not vec2:
        return 0.0
    
    # 내적 계산
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # 노름 계산
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    # 0으로 나누기 방지
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


class Retriever:
    """
    문서 검색 클래스
    
    벡터 유사도 기반으로 관련 문서를 검색합니다.
    """
    
    def __init__(
        self,
        vector_store: Optional[S3VectorStore] = None,
        embeddings_generator: Optional[EmbeddingsGenerator] = None,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ):
        """
        Retriever 초기화
        
        Args:
            vector_store: S3 벡터 저장소. None이면 새로 생성
            embeddings_generator: 임베딩 생성기. None이면 새로 생성
            top_k: 반환할 최대 결과 수. None이면 설정에서 로드
            min_similarity: 최소 유사도 임계값. None이면 설정에서 로드
        """
        settings = get_settings()
        
        self.vector_store = vector_store or S3VectorStore()
        self.embeddings_generator = embeddings_generator or EmbeddingsGenerator()
        self.top_k = top_k or settings.top_k_results
        self.min_similarity = min_similarity or settings.min_similarity
        
        # 벡터 캐시 (메모리에 로드)
        self._vectors_cache: Optional[List[VectorRecord]] = None
        
        logger.info(
            f"Retriever 초기화: top_k={self.top_k}, "
            f"min_similarity={self.min_similarity}"
        )
    
    def load_vectors(self, force_reload: bool = False):
        """
        벡터를 메모리에 로드합니다.
        
        Args:
            force_reload: 강제 재로드 여부
        """
        if self._vectors_cache is None or force_reload:
            self._vectors_cache = self.vector_store.load_all_vectors()
            logger.info(f"벡터 로드 완료: {len(self._vectors_cache)}개")
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[SearchResult]:
        """
        쿼리와 유사한 문서를 검색합니다.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수 (선택)
            min_similarity: 최소 유사도 임계값 (선택)
            
        Returns:
            List[SearchResult]: 검색 결과 목록 (유사도 내림차순)
        """
        k = top_k or self.top_k
        min_sim = min_similarity or self.min_similarity
        
        # 벡터 로드
        self.load_vectors()
        
        if not self._vectors_cache:
            logger.warning("검색할 벡터가 없습니다.")
            return []
        
        # 쿼리 임베딩 생성
        query_embedding = self.embeddings_generator.embed_text(query)
        
        # 유사도 계산
        results = []
        for record in self._vectors_cache:
            similarity = cosine_similarity(query_embedding, record.embedding)
            
            # 최소 유사도 필터링
            if similarity >= min_sim:
                results.append(SearchResult(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    content=record.content,
                    similarity=similarity,
                    metadata=record.metadata
                ))
        
        # 유사도 내림차순 정렬
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Top-K 제한
        results = results[:k]
        
        logger.info(
            f"검색 완료: query='{query[:50]}...', "
            f"결과={len(results)}개"
        )
        
        return results
    
    def search_by_embedding(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[SearchResult]:
        """
        임베딩 벡터로 직접 검색합니다.
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            top_k: 반환할 최대 결과 수 (선택)
            min_similarity: 최소 유사도 임계값 (선택)
            
        Returns:
            List[SearchResult]: 검색 결과 목록 (유사도 내림차순)
        """
        k = top_k or self.top_k
        min_sim = min_similarity or self.min_similarity
        
        # 벡터 로드
        self.load_vectors()
        
        if not self._vectors_cache:
            return []
        
        # 유사도 계산
        results = []
        for record in self._vectors_cache:
            similarity = cosine_similarity(query_embedding, record.embedding)
            
            if similarity >= min_sim:
                results.append(SearchResult(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    content=record.content,
                    similarity=similarity,
                    metadata=record.metadata
                ))
        
        # 유사도 내림차순 정렬
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Top-K 제한
        return results[:k]
    
    def clear_cache(self):
        """벡터 캐시를 초기화합니다."""
        self._vectors_cache = None
        self.vector_store.clear_cache()


def search_similar_chunks(
    query_embedding: List[float],
    vector_store: S3VectorStore,
    top_k: int = 5,
    min_similarity: float = 0.7
) -> List[SearchResult]:
    """
    코사인 유사도 기반 검색 함수
    
    Property 테스트용 함수입니다.
    
    Args:
        query_embedding: 쿼리 임베딩
        vector_store: S3 벡터 저장소
        top_k: 반환할 최대 결과 수
        min_similarity: 최소 유사도 임계값
        
    Returns:
        List[SearchResult]: 검색 결과 목록
    """
    retriever = Retriever(
        vector_store=vector_store,
        top_k=top_k,
        min_similarity=min_similarity
    )
    
    return retriever.search_by_embedding(
        query_embedding,
        top_k=top_k,
        min_similarity=min_similarity
    )
