"""
AWS Bedrock Knowledge Base 클라이언트 모듈

이 모듈은 AWS Bedrock Knowledge Base를 사용하여 RAG 기능을 제공합니다.
문서 검색과 응답 생성을 Knowledge Base API를 통해 처리합니다.
"""

import json
from typing import List, Optional, AsyncGenerator
from dataclasses import dataclass, field

import boto3
from botocore.exceptions import ClientError

from ..config import get_settings, get_aws_config
from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """
    검색된 문서 청크
    
    Attributes:
        content: 청크 텍스트 내용
        score: 관련성 점수
        source_uri: 원본 문서 S3 URI
        metadata: 추가 메타데이터
    """
    content: str
    score: float
    source_uri: str
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeBaseResponse:
    """
    Knowledge Base 응답
    
    Attributes:
        answer: 생성된 답변
        citations: 인용 정보 목록
        retrieved_chunks: 검색된 청크 목록
    """
    answer: str
    citations: List[dict] = field(default_factory=list)
    retrieved_chunks: List[RetrievedChunk] = field(default_factory=list)


class BedrockKnowledgeBase:
    """
    AWS Bedrock Knowledge Base 클라이언트
    
    Knowledge Base를 사용하여 문서 검색 및 RAG 응답을 생성합니다.
    """
    
    def __init__(
        self,
        knowledge_base_id: Optional[str] = None,
        model_arn: Optional[str] = None
    ):
        """
        BedrockKnowledgeBase 초기화
        
        Args:
            knowledge_base_id: Knowledge Base ID. None이면 설정에서 로드
            model_arn: 응답 생성에 사용할 모델 ARN. None이면 설정에서 로드
        """
        settings = get_settings()
        aws_config = get_aws_config()
        
        self.knowledge_base_id = knowledge_base_id or settings.knowledge_base_id
        self.model_arn = model_arn or settings.bedrock_model_arn
        
        if not self.knowledge_base_id:
            raise ValueError("Knowledge Base ID가 설정되지 않았습니다.")
        
        # Bedrock Agent Runtime 클라이언트 (Knowledge Base API용)
        self._client = boto3.client(
            'bedrock-agent-runtime',
            **aws_config
        )
        
        logger.info(
            f"BedrockKnowledgeBase 초기화: "
            f"kb_id={self.knowledge_base_id}"
        )
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Knowledge Base에서 관련 문서를 검색합니다.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            
        Returns:
            List[RetrievedChunk]: 검색된 청크 목록
        """
        try:
            response = self._client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': top_k
                    }
                }
            )
            
            chunks = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0.0)
                location = result.get('location', {})
                
                # S3 위치 정보 추출
                s3_location = location.get('s3Location', {})
                source_uri = s3_location.get('uri', '')
                
                chunks.append(RetrievedChunk(
                    content=content,
                    score=score,
                    source_uri=source_uri,
                    metadata={
                        'location_type': location.get('type', ''),
                    }
                ))
            
            logger.info(f"검색 완료: query='{query[:50]}...', 결과={len(chunks)}개")
            return chunks
            
        except ClientError as e:
            logger.error(f"Knowledge Base 검색 실패: {e}")
            raise
    
    def retrieve_and_generate(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None
    ) -> KnowledgeBaseResponse:
        """
        Knowledge Base에서 검색하고 응답을 생성합니다.
        
        Args:
            query: 사용자 질문
            conversation_history: 대화 히스토리 (선택)
            
        Returns:
            KnowledgeBaseResponse: 생성된 응답
        """
        try:
            # 요청 구성
            request_params = {
                'input': {
                    'text': query
                },
                'retrieveAndGenerateConfiguration': {
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.knowledge_base_id,
                        'modelArn': self.model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 5
                            }
                        }
                    }
                }
            }
            
            # 대화 히스토리가 있으면 세션 컨텍스트 추가
            if conversation_history:
                # sessionId를 사용하여 대화 컨텍스트 유지 가능
                pass
            
            response = self._client.retrieve_and_generate(**request_params)
            
            # 응답 파싱
            output = response.get('output', {})
            answer = output.get('text', '')
            
            # 인용 정보 추출
            citations = []
            retrieved_chunks = []
            
            for citation in response.get('citations', []):
                citation_info = {
                    'generated_text': citation.get('generatedResponsePart', {}).get('textResponsePart', {}).get('text', ''),
                    'references': []
                }
                
                for ref in citation.get('retrievedReferences', []):
                    content = ref.get('content', {}).get('text', '')
                    location = ref.get('location', {})
                    s3_location = location.get('s3Location', {})
                    
                    citation_info['references'].append({
                        'content': content[:200] + '...' if len(content) > 200 else content,
                        'source_uri': s3_location.get('uri', '')
                    })
                    
                    retrieved_chunks.append(RetrievedChunk(
                        content=content,
                        score=1.0,  # RetrieveAndGenerate는 점수를 반환하지 않음
                        source_uri=s3_location.get('uri', ''),
                        metadata={}
                    ))
                
                citations.append(citation_info)
            
            logger.info(f"응답 생성 완료: query='{query[:50]}...'")
            
            return KnowledgeBaseResponse(
                answer=answer,
                citations=citations,
                retrieved_chunks=retrieved_chunks
            )
            
        except ClientError as e:
            logger.error(f"RetrieveAndGenerate 실패: {e}")
            raise
    
    async def retrieve_and_generate_stream(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None
    ) -> AsyncGenerator[tuple[str, Optional[KnowledgeBaseResponse]], None]:
        """
        Knowledge Base에서 검색하고 스트리밍으로 응답을 생성합니다.
        
        Note: Bedrock Knowledge Base는 현재 스트리밍을 직접 지원하지 않으므로,
        전체 응답을 받은 후 청크 단위로 yield합니다.
        
        Args:
            query: 사용자 질문
            conversation_history: 대화 히스토리 (선택)
            
        Yields:
            tuple[str, Optional[KnowledgeBaseResponse]]: (토큰, 완료 시 전체 응답)
        """
        try:
            # 전체 응답 생성
            response = self.retrieve_and_generate(query, conversation_history)
            
            # 응답을 단어 단위로 스트리밍 시뮬레이션
            words = response.answer.split()
            
            for i, word in enumerate(words):
                is_last = (i == len(words) - 1)
                yield word + (" " if not is_last else ""), None
            
            # 마지막에 전체 응답 반환
            yield "", response
            
        except Exception as e:
            logger.error(f"스트리밍 응답 생성 실패: {e}")
            raise


# 편의 함수
def create_knowledge_base_client() -> BedrockKnowledgeBase:
    """
    Knowledge Base 클라이언트를 생성하는 편의 함수
    
    Returns:
        BedrockKnowledgeBase: Knowledge Base 클라이언트
    """
    return BedrockKnowledgeBase()
