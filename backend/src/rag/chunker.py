"""
문서 청킹 모듈

이 모듈은 문서를 적절한 크기의 청크로 분할하는 기능을 제공합니다.
RecursiveCharacterTextSplitter를 사용하여 문장 경계를 고려한 분할을 수행합니다.
"""

from typing import List, Optional
from dataclasses import dataclass, field
import uuid
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter

from .document_loader import Document, DocumentMetadata
from ..config import get_settings
from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class Chunk:
    """
    문서 청크 클래스
    
    Attributes:
        chunk_id: 청크 고유 ID
        content: 청크 텍스트 내용
        document_id: 원본 문서 ID
        chunk_index: 청크 순서 인덱스
        metadata: 청크 메타데이터
    """
    chunk_id: str
    content: str
    document_id: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    """
    문서 청킹 클래스
    
    문서를 설정된 크기의 청크로 분할합니다.
    오버랩을 적용하여 컨텍스트 연속성을 유지합니다.
    """
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        DocumentChunker 초기화
        
        Args:
            chunk_size: 청크 크기 (문자 수). None이면 설정에서 로드
            chunk_overlap: 오버랩 크기 (문자 수). None이면 설정에서 로드
            separators: 분할에 사용할 구분자 목록
        """
        settings = get_settings()
        
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # 기본 구분자 (한국어 문서에 적합하게 조정)
        self.separators = separators or [
            "\n\n",      # 단락
            "\n",        # 줄바꿈
            "。",        # 일본어/중국어 마침표
            ".",         # 영어 마침표
            "!",         # 느낌표
            "?",         # 물음표
            ";",         # 세미콜론
            ":",         # 콜론
            " ",         # 공백
            "",          # 문자 단위
        ]
        
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
        )
        
        logger.info(
            f"DocumentChunker 초기화: chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )
    
    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        단일 문서를 청크로 분할합니다.
        
        Args:
            document: 분할할 문서
            
        Returns:
            List[Chunk]: 청크 목록
        """
        if not document.content or not document.content.strip():
            logger.warning(f"빈 문서: {document.metadata.filename}")
            return []
        
        # 문서 ID 생성 (파일명 기반)
        document_id = self._generate_document_id(document.metadata.filename)
        
        # 텍스트 분할
        text_chunks = self._splitter.split_text(document.content)
        
        chunks = []
        for i, text in enumerate(text_chunks):
            chunk = Chunk(
                chunk_id=f"{document_id}_chunk_{i:04d}",
                content=text,
                document_id=document_id,
                chunk_index=i,
                metadata={
                    'filename': document.metadata.filename,
                    'file_type': document.metadata.file_type,
                    'file_path': document.metadata.file_path,
                    'chunk_index': i,
                    'total_chunks': len(text_chunks),
                    'chunk_size': len(text),
                    **document.metadata.extra
                }
            )
            chunks.append(chunk)
        
        logger.info(
            f"문서 청킹 완료: {document.metadata.filename}, "
            f"{len(chunks)}개 청크 생성"
        )
        
        return chunks
    
    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        여러 문서를 청크로 분할합니다.
        
        Args:
            documents: 분할할 문서 목록
            
        Returns:
            List[Chunk]: 모든 청크 목록
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        logger.info(f"전체 청킹 완료: {len(documents)}개 문서, {len(all_chunks)}개 청크")
        
        return all_chunks
    
    def chunk_text(
        self,
        text: str,
        document_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> List[Chunk]:
        """
        텍스트를 직접 청크로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            document_id: 문서 ID (선택)
            metadata: 추가 메타데이터 (선택)
            
        Returns:
            List[Chunk]: 청크 목록
        """
        if not text or not text.strip():
            return []
        
        doc_id = document_id or str(uuid.uuid4())[:8]
        text_chunks = self._splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = Chunk(
                chunk_id=f"{doc_id}_chunk_{i:04d}",
                content=chunk_text,
                document_id=doc_id,
                chunk_index=i,
                metadata={
                    'chunk_index': i,
                    'total_chunks': len(text_chunks),
                    'chunk_size': len(chunk_text),
                    **(metadata or {})
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _generate_document_id(self, filename: str) -> str:
        """
        파일명에서 문서 ID를 생성합니다.
        
        Args:
            filename: 파일명
            
        Returns:
            str: 문서 ID
        """
        # 특수문자 제거 및 소문자 변환
        clean_name = re.sub(r'[^\w\-]', '_', filename.lower())
        # 확장자 제거
        clean_name = re.sub(r'\.[^.]+$', '', clean_name)
        # 연속 언더스코어 정리
        clean_name = re.sub(r'_+', '_', clean_name).strip('_')
        
        return clean_name or str(uuid.uuid4())[:8]


def remove_overlap(chunks: List[Chunk], overlap_size: Optional[int] = None) -> List[str]:
    """
    청크에서 오버랩을 제거하고 원본 텍스트를 재구성합니다.
    
    Property 1.1 검증용 함수입니다.
    
    Args:
        chunks: 청크 목록
        overlap_size: 오버랩 크기. None이면 설정에서 로드
        
    Returns:
        List[str]: 오버랩이 제거된 텍스트 목록
    """
    if not chunks:
        return []
    
    settings = get_settings()
    overlap = overlap_size or settings.chunk_overlap
    
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            # 첫 번째 청크는 전체 포함
            result.append(chunk.content)
        else:
            # 이후 청크는 오버랩 부분 제거
            if len(chunk.content) > overlap:
                result.append(chunk.content[overlap:])
            else:
                result.append(chunk.content)
    
    return result


# 편의 함수
def chunk_document(
    document: Document,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[Chunk]:
    """
    문서를 청크로 분할하는 편의 함수
    
    Args:
        document: 분할할 문서
        chunk_size: 청크 크기 (선택)
        chunk_overlap: 오버랩 크기 (선택)
        
    Returns:
        List[Chunk]: 청크 목록
    """
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_document(document)


def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[Chunk]:
    """
    텍스트를 청크로 분할하는 편의 함수
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (선택)
        chunk_overlap: 오버랩 크기 (선택)
        
    Returns:
        List[Chunk]: 청크 목록
    """
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text)
