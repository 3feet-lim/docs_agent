"""
RAG 체인 모듈

이 모듈은 RAG(Retrieval-Augmented Generation) 파이프라인을 구성합니다.
문서 검색, 프롬프트 구성, LLM 호출을 통합합니다.
"""

from typing import List, Optional, AsyncGenerator
from dataclasses import dataclass, field
import json

import boto3
from botocore.exceptions import ClientError

from .retriever import Retriever, SearchResult
from .s3_vector_store import S3VectorStore
from .embeddings import EmbeddingsGenerator
from ..config import get_settings, get_aws_config, get_bedrock_config
from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class Message:
    """
    대화 메시지 클래스
    
    Attributes:
        role: 역할 ('user' 또는 'assistant')
        content: 메시지 내용
    """
    role: str
    content: str


@dataclass
class RAGResponse:
    """
    RAG 응답 클래스
    
    Attributes:
        content: 응답 내용
        sources: 참조 문서 출처 목록
        usage: 토큰 사용량 정보
    """
    content: str
    sources: List[SearchResult] = field(default_factory=list)
    usage: dict = field(default_factory=dict)


# 기본 RAG 프롬프트 템플릿
DEFAULT_SYSTEM_PROMPT = """당신은 사내 문서를 기반으로 질문에 답변하는 AI 어시스턴트입니다.

다음 규칙을 따라주세요:
1. 제공된 문서 내용을 기반으로 정확하게 답변하세요.
2. 문서에 없는 내용은 추측하지 말고, 모른다고 솔직하게 말하세요.
3. 답변 시 관련 문서의 출처를 언급해주세요.
4. 한국어로 친절하고 명확하게 답변하세요.
5. 필요한 경우 단계별로 설명해주세요."""


def build_rag_prompt(
    query: str,
    context_chunks: List[SearchResult],
    conversation_history: Optional[List[Message]] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    RAG 프롬프트를 생성합니다.
    
    Args:
        query: 사용자 질문
        context_chunks: 검색된 문서 청크
        conversation_history: 대화 히스토리 (선택)
        system_prompt: 시스템 프롬프트 (선택)
        
    Returns:
        str: 완성된 프롬프트
    """
    prompt_parts = []
    
    # 시스템 프롬프트
    system = system_prompt or DEFAULT_SYSTEM_PROMPT
    prompt_parts.append(system)
    
    # 문서 컨텍스트
    if context_chunks:
        prompt_parts.append("\n\n## 참고 문서\n")
        
        for i, chunk in enumerate(context_chunks, 1):
            filename = chunk.metadata.get('filename', '알 수 없음')
            page = chunk.metadata.get('page', 'N/A')
            similarity = f"{chunk.similarity:.2f}"
            
            prompt_parts.append(
                f"[문서 {i}] {filename} (유사도: {similarity})\n"
                f"{chunk.content}\n"
                f"---\n"
            )
    else:
        prompt_parts.append("\n\n(관련 문서를 찾지 못했습니다.)\n")
    
    # 대화 히스토리
    if conversation_history:
        prompt_parts.append("\n## 이전 대화\n")
        
        # 최근 3개 대화만 포함
        recent_history = conversation_history[-6:]  # 3쌍의 대화
        for msg in recent_history:
            role_name = "사용자" if msg.role == "user" else "AI"
            prompt_parts.append(f"{role_name}: {msg.content}\n")
    
    # 현재 질문
    prompt_parts.append(f"\n## 질문\n{query}\n")
    prompt_parts.append("\n## 답변\n")
    
    return "".join(prompt_parts)


class RAGChain:
    """
    RAG 체인 클래스
    
    문서 검색과 LLM 응답 생성을 통합합니다.
    """
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """
        RAGChain 초기화
        
        Args:
            retriever: 문서 검색기. None이면 새로 생성
            model_id: Bedrock 모델 ID. None이면 설정에서 로드
            system_prompt: 시스템 프롬프트 (선택)
        """
        settings = get_settings()
        bedrock_config = get_bedrock_config()
        aws_config = get_aws_config()
        
        self.retriever = retriever or Retriever()
        self.model_id = model_id or bedrock_config['model_id']
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        
        # Bedrock 설정
        self.max_tokens = bedrock_config['max_tokens']
        self.temperature = bedrock_config['temperature']
        self.top_p = bedrock_config['top_p']
        
        # Bedrock Runtime 클라이언트
        self._client = boto3.client('bedrock-runtime', **aws_config)
        
        logger.info(f"RAGChain 초기화: model_id={self.model_id}")
    
    def generate(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        top_k: Optional[int] = None
    ) -> RAGResponse:
        """
        RAG 응답을 생성합니다.
        
        Args:
            query: 사용자 질문
            conversation_history: 대화 히스토리 (선택)
            top_k: 검색할 문서 수 (선택)
            
        Returns:
            RAGResponse: RAG 응답
        """
        # 1. 관련 문서 검색
        search_results = self.retriever.search(query, top_k=top_k)
        
        # 2. 프롬프트 구성
        prompt = build_rag_prompt(
            query=query,
            context_chunks=search_results,
            conversation_history=conversation_history,
            system_prompt=self.system_prompt
        )
        
        # 3. LLM 호출
        try:
            response_content, usage = self._invoke_llm(prompt)
            
            return RAGResponse(
                content=response_content,
                sources=search_results,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            raise
    
    async def generate_stream(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        top_k: Optional[int] = None
    ) -> AsyncGenerator[tuple[str, Optional[RAGResponse]], None]:
        """
        RAG 응답을 스트리밍으로 생성합니다.
        
        Args:
            query: 사용자 질문
            conversation_history: 대화 히스토리 (선택)
            top_k: 검색할 문서 수 (선택)
            
        Yields:
            tuple[str, Optional[RAGResponse]]: (토큰, 완료 시 RAGResponse)
        """
        # 1. 관련 문서 검색
        search_results = self.retriever.search(query, top_k=top_k)
        
        # 2. 프롬프트 구성
        prompt = build_rag_prompt(
            query=query,
            context_chunks=search_results,
            conversation_history=conversation_history,
            system_prompt=self.system_prompt
        )
        
        # 3. 스트리밍 LLM 호출
        full_response = ""
        usage = {}
        
        try:
            async for token, token_usage in self._invoke_llm_stream(prompt):
                full_response += token
                if token_usage:
                    usage = token_usage
                yield token, None
            
            # 완료 시 전체 응답 반환
            final_response = RAGResponse(
                content=full_response,
                sources=search_results,
                usage=usage
            )
            yield "", final_response
            
        except Exception as e:
            logger.error(f"스트리밍 LLM 호출 실패: {e}")
            raise
    
    def _invoke_llm(self, prompt: str) -> tuple[str, dict]:
        """
        Bedrock LLM을 호출합니다.
        
        Args:
            prompt: 프롬프트
            
        Returns:
            tuple[str, dict]: (응답 내용, 토큰 사용량)
        """
        # Claude 메시지 형식
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self._client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        content = ""
        if response_body.get('content'):
            content = response_body['content'][0].get('text', '')
        
        usage = response_body.get('usage', {})
        
        return content, usage
    
    async def _invoke_llm_stream(
        self,
        prompt: str
    ) -> AsyncGenerator[tuple[str, Optional[dict]], None]:
        """
        Bedrock LLM을 스트리밍으로 호출합니다.
        
        Args:
            prompt: 프롬프트
            
        Yields:
            tuple[str, Optional[dict]]: (토큰, 완료 시 사용량)
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = self._client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            stream = response.get('body')
            
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # 델타 텍스트 추출
                        if chunk_data.get('type') == 'content_block_delta':
                            delta = chunk_data.get('delta', {})
                            text = delta.get('text', '')
                            if text:
                                yield text, None
                        
                        # 메시지 완료 시 사용량 정보
                        elif chunk_data.get('type') == 'message_delta':
                            usage = chunk_data.get('usage', {})
                            yield "", usage
                            
        except ClientError as e:
            logger.error(f"Bedrock 스트리밍 오류: {e}")
            raise


# 편의 함수
def create_rag_chain(
    vector_store: Optional[S3VectorStore] = None,
    embeddings_generator: Optional[EmbeddingsGenerator] = None
) -> RAGChain:
    """
    RAG 체인을 생성하는 편의 함수
    
    Args:
        vector_store: S3 벡터 저장소 (선택)
        embeddings_generator: 임베딩 생성기 (선택)
        
    Returns:
        RAGChain: RAG 체인 인스턴스
    """
    retriever = Retriever(
        vector_store=vector_store,
        embeddings_generator=embeddings_generator
    )
    
    return RAGChain(retriever=retriever)
