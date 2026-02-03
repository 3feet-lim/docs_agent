"""
S3 벡터 저장소 모듈

이 모듈은 AWS S3를 사용하여 벡터 임베딩을 저장하고 관리합니다.
JSON 형식으로 벡터와 메타데이터를 저장합니다.
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from .chunker import Chunk
from ..config import get_settings, get_aws_config, get_s3_config
from ..utils.logger import get_logger


logger = get_logger(__name__)


class S3Error(Exception):
    """S3 작업 관련 예외"""
    pass


@dataclass
class VectorRecord:
    """
    벡터 레코드 클래스
    
    S3에 저장되는 벡터 데이터 형식입니다.
    
    Attributes:
        chunk_id: 청크 고유 ID
        document_id: 원본 문서 ID
        content: 청크 텍스트 내용
        embedding: 벡터 임베딩
        metadata: 추가 메타데이터
        created_at: 생성 시간
    """
    chunk_id: str
    document_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VectorRecord':
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class VectorIndex:
    """
    벡터 인덱스 클래스
    
    S3에 저장된 모든 벡터의 인덱스 정보입니다.
    
    Attributes:
        records: 벡터 레코드 목록 (chunk_id -> s3_key 매핑)
        document_count: 문서 수
        chunk_count: 청크 수
        updated_at: 마지막 업데이트 시간
    """
    records: Dict[str, str]  # chunk_id -> s3_key
    document_count: int = 0
    chunk_count: int = 0
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VectorIndex':
        return cls(**data)


class S3VectorStore:
    """
    S3 벡터 저장소 클래스
    
    AWS S3를 사용하여 벡터 임베딩을 저장하고 검색합니다.
    """
    
    INDEX_FILE = "index.json"
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        vector_prefix: Optional[str] = None
    ):
        """
        S3VectorStore 초기화
        
        Args:
            bucket_name: S3 버킷 이름. None이면 설정에서 로드
            vector_prefix: 벡터 저장 경로 접두사. None이면 설정에서 로드
        """
        s3_config = get_s3_config()
        aws_config = get_aws_config()
        
        self.bucket_name = bucket_name or s3_config['bucket_name']
        self.vector_prefix = vector_prefix or s3_config['vector_prefix']
        
        if not self.bucket_name:
            raise S3Error("S3 버킷 이름이 설정되지 않았습니다.")
        
        # S3 클라이언트 생성
        self._client = boto3.client('s3', **aws_config)
        
        # 인덱스 캐시
        self._index_cache: Optional[VectorIndex] = None
        
        logger.info(
            f"S3VectorStore 초기화: bucket={self.bucket_name}, "
            f"prefix={self.vector_prefix}"
        )
    
    def _get_vector_key(self, chunk_id: str) -> str:
        """청크 ID에서 S3 키 생성"""
        return f"{self.vector_prefix}{chunk_id}.json"
    
    def _get_index_key(self) -> str:
        """인덱스 파일 S3 키"""
        return f"{self.vector_prefix}{self.INDEX_FILE}"
    
    def save_vector(
        self,
        chunk: Chunk,
        embedding: List[float]
    ) -> str:
        """
        단일 벡터를 S3에 저장합니다.
        
        Args:
            chunk: 청크 정보
            embedding: 벡터 임베딩
            
        Returns:
            str: 저장된 S3 키
        """
        record = VectorRecord(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=embedding,
            metadata=chunk.metadata
        )
        
        s3_key = self._get_vector_key(chunk.chunk_id)
        
        try:
            self._client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(record.to_dict(), ensure_ascii=False),
                ContentType='application/json'
            )
            
            logger.debug(f"벡터 저장 완료: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"벡터 저장 실패: {s3_key}, {e}")
            raise S3Error(f"S3 저장 실패: {e}") from e
    
    def save_vectors(
        self,
        chunks_with_embeddings: List[tuple[Chunk, List[float]]],
        update_index: bool = True
    ) -> List[str]:
        """
        여러 벡터를 S3에 저장합니다.
        
        Args:
            chunks_with_embeddings: (청크, 임베딩) 튜플 목록
            update_index: 인덱스 파일 업데이트 여부
            
        Returns:
            List[str]: 저장된 S3 키 목록
        """
        saved_keys = []
        
        for chunk, embedding in chunks_with_embeddings:
            try:
                key = self.save_vector(chunk, embedding)
                saved_keys.append(key)
            except S3Error as e:
                logger.error(f"벡터 저장 실패: {chunk.chunk_id}, {e}")
        
        if update_index and saved_keys:
            self._update_index(chunks_with_embeddings)
        
        logger.info(f"벡터 저장 완료: {len(saved_keys)}/{len(chunks_with_embeddings)}")
        
        return saved_keys
    
    def load_vector(self, chunk_id: str) -> Optional[VectorRecord]:
        """
        S3에서 벡터를 로드합니다.
        
        Args:
            chunk_id: 청크 ID
            
        Returns:
            Optional[VectorRecord]: 벡터 레코드 또는 None
        """
        s3_key = self._get_vector_key(chunk_id)
        
        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            return VectorRecord.from_dict(data)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"벡터를 찾을 수 없음: {chunk_id}")
                return None
            raise S3Error(f"S3 로드 실패: {e}") from e
    
    def load_all_vectors(self) -> List[VectorRecord]:
        """
        S3에서 모든 벡터를 로드합니다.
        
        Returns:
            List[VectorRecord]: 모든 벡터 레코드 목록
        """
        records = []
        
        try:
            paginator = self._client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.vector_prefix
            ):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    
                    # 인덱스 파일 제외
                    if key.endswith(self.INDEX_FILE):
                        continue
                    
                    # JSON 파일만 처리
                    if not key.endswith('.json'):
                        continue
                    
                    try:
                        response = self._client.get_object(
                            Bucket=self.bucket_name,
                            Key=key
                        )
                        data = json.loads(response['Body'].read().decode('utf-8'))
                        records.append(VectorRecord.from_dict(data))
                    except Exception as e:
                        logger.error(f"벡터 로드 실패: {key}, {e}")
            
            logger.info(f"전체 벡터 로드 완료: {len(records)}개")
            return records
            
        except ClientError as e:
            logger.error(f"벡터 목록 조회 실패: {e}")
            raise S3Error(f"S3 조회 실패: {e}") from e
    
    def load_index(self) -> VectorIndex:
        """
        인덱스 파일을 로드합니다.
        
        Returns:
            VectorIndex: 벡터 인덱스
        """
        if self._index_cache:
            return self._index_cache
        
        index_key = self._get_index_key()
        
        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=index_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            self._index_cache = VectorIndex.from_dict(data)
            return self._index_cache
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info("인덱스 파일이 없습니다. 새로 생성합니다.")
                return VectorIndex(records={})
            raise S3Error(f"인덱스 로드 실패: {e}") from e
    
    def _update_index(
        self,
        chunks_with_embeddings: List[tuple[Chunk, List[float]]]
    ):
        """
        인덱스 파일을 업데이트합니다.
        
        Args:
            chunks_with_embeddings: 새로 추가된 (청크, 임베딩) 목록
        """
        index = self.load_index()
        
        # 새 레코드 추가
        document_ids = set()
        for chunk, _ in chunks_with_embeddings:
            s3_key = self._get_vector_key(chunk.chunk_id)
            index.records[chunk.chunk_id] = s3_key
            document_ids.add(chunk.document_id)
        
        # 통계 업데이트
        index.chunk_count = len(index.records)
        index.document_count = len(document_ids)
        index.updated_at = datetime.now(timezone.utc).isoformat()
        
        # S3에 저장
        index_key = self._get_index_key()
        
        try:
            self._client.put_object(
                Bucket=self.bucket_name,
                Key=index_key,
                Body=json.dumps(index.to_dict(), ensure_ascii=False),
                ContentType='application/json'
            )
            
            self._index_cache = index
            logger.info(f"인덱스 업데이트 완료: {index.chunk_count}개 청크")
            
        except ClientError as e:
            logger.error(f"인덱스 저장 실패: {e}")
            raise S3Error(f"인덱스 저장 실패: {e}") from e
    
    def delete_vector(self, chunk_id: str) -> bool:
        """
        벡터를 삭제합니다.
        
        Args:
            chunk_id: 삭제할 청크 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        s3_key = self._get_vector_key(chunk_id)
        
        try:
            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # 인덱스에서도 제거
            index = self.load_index()
            if chunk_id in index.records:
                del index.records[chunk_id]
                index.chunk_count = len(index.records)
                index.updated_at = datetime.now(timezone.utc).isoformat()
                
                # 인덱스 저장
                self._client.put_object(
                    Bucket=self.bucket_name,
                    Key=self._get_index_key(),
                    Body=json.dumps(index.to_dict(), ensure_ascii=False),
                    ContentType='application/json'
                )
                self._index_cache = index
            
            logger.info(f"벡터 삭제 완료: {chunk_id}")
            return True
            
        except ClientError as e:
            logger.error(f"벡터 삭제 실패: {chunk_id}, {e}")
            return False
    
    def clear_cache(self):
        """인덱스 캐시를 초기화합니다."""
        self._index_cache = None
