"""
임베딩 생성 모듈

이 모듈은 AWS Bedrock을 사용하여 텍스트를 벡터 임베딩으로 변환합니다.
배치 처리 및 에러 처리/재시도 로직을 포함합니다.
"""

import time
from typing import List, Optional
import json

import boto3
from botocore.exceptions import ClientError

from .chunker import Chunk
from ..config import get_settings, get_aws_config
from ..utils.logger import get_logger


logger = get_logger(__name__)


class EmbeddingError(Exception):
    """임베딩 생성 관련 예외"""
    pass


class EmbeddingsGenerator:
    """
    임베딩 생성 클래스
    
    AWS Bedrock Embeddings API를 사용하여 텍스트를 벡터로 변환합니다.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        EmbeddingsGenerator 초기화
        
        Args:
            model_id: Bedrock 임베딩 모델 ID. None이면 설정에서 로드
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간 (초)
        """
        settings = get_settings()
        aws_config = get_aws_config()
        
        self.model_id = model_id or settings.bedrock_embeddings_model_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Bedrock Runtime 클라이언트 생성
        self._client = boto3.client(
            'bedrock-runtime',
            **aws_config
        )
        
        logger.info(f"EmbeddingsGenerator 초기화: model_id={self.model_id}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트를 임베딩으로 변환합니다.
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            List[float]: 임베딩 벡터
            
        Raises:
            EmbeddingError: 임베딩 생성 실패 시
        """
        if not text or not text.strip():
            raise EmbeddingError("빈 텍스트는 임베딩할 수 없습니다.")
        
        for attempt in range(self.max_retries):
            try:
                # Titan Embeddings 모델 요청 형식
                request_body = {
                    "inputText": text[:8000]  # 최대 입력 길이 제한
                }
                
                response = self._client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType="application/json",
                    accept="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                embedding = response_body.get('embedding', [])
                
                if not embedding:
                    raise EmbeddingError("응답에 임베딩이 없습니다.")
                
                return embedding
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                
                if error_code in ['ThrottlingException', 'ServiceUnavailableException']:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"임베딩 API 제한, {wait_time}초 후 재시도 "
                            f"(시도 {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                
                logger.error(f"임베딩 생성 실패: {e}")
                raise EmbeddingError(f"Bedrock API 오류: {error_code}") from e
                
            except Exception as e:
                logger.error(f"임베딩 생성 중 예외 발생: {e}")
                raise EmbeddingError(f"임베딩 생성 실패: {str(e)}") from e
        
        raise EmbeddingError(f"최대 재시도 횟수({self.max_retries}) 초과")
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 10,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        여러 텍스트를 배치로 임베딩합니다.
        
        Args:
            texts: 임베딩할 텍스트 목록
            batch_size: 배치 크기
            show_progress: 진행 상황 로깅 여부
            
        Returns:
            List[List[float]]: 임베딩 벡터 목록
        """
        embeddings = []
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    embedding = self.embed_text(text)
                    batch_embeddings.append(embedding)
                except EmbeddingError as e:
                    logger.error(f"텍스트 임베딩 실패: {e}")
                    # 실패한 경우 빈 벡터 추가 (또는 예외 발생)
                    batch_embeddings.append([])
            
            embeddings.extend(batch_embeddings)
            
            if show_progress:
                processed = min(i + batch_size, total)
                logger.info(f"임베딩 진행: {processed}/{total} ({processed/total*100:.1f}%)")
        
        return embeddings
    
    def embed_chunks(
        self,
        chunks: List[Chunk],
        batch_size: int = 10
    ) -> List[tuple[Chunk, List[float]]]:
        """
        청크 목록을 임베딩합니다.
        
        Args:
            chunks: 임베딩할 청크 목록
            batch_size: 배치 크기
            
        Returns:
            List[tuple[Chunk, List[float]]]: (청크, 임베딩) 튜플 목록
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(texts, batch_size=batch_size)
        
        results = []
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:  # 빈 임베딩 제외
                results.append((chunk, embedding))
            else:
                logger.warning(f"청크 임베딩 실패: {chunk.chunk_id}")
        
        logger.info(f"청크 임베딩 완료: {len(results)}/{len(chunks)} 성공")
        
        return results


# 편의 함수
def embed_text(text: str) -> List[float]:
    """
    텍스트를 임베딩하는 편의 함수
    
    Args:
        text: 임베딩할 텍스트
        
    Returns:
        List[float]: 임베딩 벡터
    """
    generator = EmbeddingsGenerator()
    return generator.embed_text(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    여러 텍스트를 임베딩하는 편의 함수
    
    Args:
        texts: 임베딩할 텍스트 목록
        
    Returns:
        List[List[float]]: 임베딩 벡터 목록
    """
    generator = EmbeddingsGenerator()
    return generator.embed_texts(texts)
