"""
AWS Bedrock 클라이언트 모듈

이 모듈은 AWS Bedrock 서비스와의 통신을 담당합니다.
Claude Sonnet 4.5 모델 호출 및 스트리밍 응답을 지원합니다.
"""

import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, BotoCoreError

from .config import get_settings, get_aws_config, get_bedrock_config


# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class BedrockResponse:
    """Bedrock 응답 데이터 클래스"""
    content: str
    stop_reason: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    model_id: str = ""


class BedrockError(Exception):
    """Bedrock 관련 기본 예외 클래스"""
    pass


class BedrockConnectionError(BedrockError):
    """Bedrock 연결 실패 예외"""
    pass


class BedrockInvocationError(BedrockError):
    """Bedrock 모델 호출 실패 예외"""
    pass


class BedrockRateLimitError(BedrockError):
    """Bedrock Rate Limit 초과 예외"""
    pass


class BedrockClient:
    """
    AWS Bedrock 클라이언트 클래스
    
    Claude Sonnet 4.5 모델을 사용하여 텍스트 생성을 수행합니다.
    스트리밍 및 비스트리밍 응답을 모두 지원합니다.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        region_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ):
        """
        BedrockClient 초기화
        
        Args:
            model_id: Bedrock 모델 ID (기본값: 설정에서 로드)
            region_name: AWS 리전 (기본값: 설정에서 로드)
            max_tokens: 최대 토큰 수 (기본값: 설정에서 로드)
            temperature: 온도 설정 (기본값: 설정에서 로드)
            top_p: Top-P 설정 (기본값: 설정에서 로드)
        """
        settings = get_settings()
        bedrock_config = get_bedrock_config()
        aws_config = get_aws_config()
        
        self.model_id = model_id or bedrock_config["model_id"]
        self.max_tokens = max_tokens or bedrock_config["max_tokens"]
        self.temperature = temperature or bedrock_config["temperature"]
        self.top_p = top_p or bedrock_config["top_p"]
        
        # boto3 설정
        boto_config = BotoConfig(
            region_name=region_name or aws_config["region_name"],
            retries={
                "max_attempts": 3,
                "mode": "adaptive"
            },
            connect_timeout=30,
            read_timeout=60,
        )
        
        # Bedrock Runtime 클라이언트 생성
        try:
            client_kwargs = {
                "service_name": "bedrock-runtime",
                "config": boto_config,
            }
            
            # Access Key가 설정된 경우에만 추가
            if aws_config.get("aws_access_key_id"):
                client_kwargs["aws_access_key_id"] = aws_config["aws_access_key_id"]
                client_kwargs["aws_secret_access_key"] = aws_config["aws_secret_access_key"]
            
            self._client = boto3.client(**client_kwargs)
            logger.info(f"Bedrock 클라이언트 초기화 완료: model_id={self.model_id}")
            
        except Exception as e:
            logger.error(f"Bedrock 클라이언트 초기화 실패: {e}")
            raise BedrockConnectionError(f"Bedrock 클라이언트 초기화 실패: {e}")
    
    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[List[Dict], Optional[str]]:
        """
        Claude 메시지 형식으로 변환
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            conversation_history: 대화 히스토리 (선택)
        
        Returns:
            tuple: (messages 리스트, system 프롬프트)
        """
        messages = []
        
        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    messages.append({
                        "role": role,
                        "content": content
                    })
        
        # 현재 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return messages, system_prompt
    
    def _build_request_body(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Bedrock API 요청 본문 생성
        
        Args:
            messages: 메시지 리스트
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            top_p: Top-P 설정
        
        Returns:
            dict: API 요청 본문
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
        }
        
        # 선택적 파라미터 추가
        if system_prompt:
            body["system"] = system_prompt
        
        # Claude 모델은 temperature와 top_p를 동시에 사용할 수 없음
        # temperature만 사용
        if temperature is not None:
            body["temperature"] = temperature
        else:
            body["temperature"] = self.temperature
        
        return body
    
    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> BedrockResponse:
        """
        Bedrock 모델 호출 (비스트리밍)
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            conversation_history: 대화 히스토리 (선택)
            max_tokens: 최대 토큰 수 (선택)
            temperature: 온도 설정 (선택)
            top_p: Top-P 설정 (선택)
        
        Returns:
            BedrockResponse: 모델 응답
        
        Raises:
            BedrockInvocationError: 모델 호출 실패 시
            BedrockRateLimitError: Rate Limit 초과 시
        """
        messages, system = self._build_messages(
            prompt, system_prompt, conversation_history
        )
        
        body = self._build_request_body(
            messages, system, max_tokens, temperature, top_p
        )
        
        try:
            logger.debug(f"Bedrock 호출 시작: model_id={self.model_id}")
            
            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response["body"].read())
            
            # 응답 파싱
            content = ""
            if "content" in response_body and len(response_body["content"]) > 0:
                content = response_body["content"][0].get("text", "")
            
            result = BedrockResponse(
                content=content,
                stop_reason=response_body.get("stop_reason"),
                input_tokens=response_body.get("usage", {}).get("input_tokens", 0),
                output_tokens=response_body.get("usage", {}).get("output_tokens", 0),
                model_id=self.model_id,
            )
            
            logger.debug(
                f"Bedrock 호출 완료: "
                f"input_tokens={result.input_tokens}, "
                f"output_tokens={result.output_tokens}"
            )
            
            return result
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "ThrottlingException":
                logger.warning(f"Bedrock Rate Limit 초과: {error_message}")
                raise BedrockRateLimitError(f"Rate Limit 초과: {error_message}")
            
            logger.error(f"Bedrock 호출 실패: {error_code} - {error_message}")
            raise BedrockInvocationError(f"모델 호출 실패: {error_message}")
            
        except BotoCoreError as e:
            logger.error(f"Bedrock 연결 오류: {e}")
            raise BedrockConnectionError(f"연결 오류: {e}")
            
        except Exception as e:
            logger.error(f"Bedrock 예상치 못한 오류: {e}")
            raise BedrockError(f"예상치 못한 오류: {e}")
    
    async def invoke_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Bedrock 모델 스트리밍 호출
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            conversation_history: 대화 히스토리 (선택)
            max_tokens: 최대 토큰 수 (선택)
            temperature: 온도 설정 (선택)
            top_p: Top-P 설정 (선택)
        
        Yields:
            str: 스트리밍 텍스트 청크
        
        Raises:
            BedrockInvocationError: 모델 호출 실패 시
            BedrockRateLimitError: Rate Limit 초과 시
        """
        messages, system = self._build_messages(
            prompt, system_prompt, conversation_history
        )
        
        body = self._build_request_body(
            messages, system, max_tokens, temperature, top_p
        )
        
        try:
            logger.debug(f"Bedrock 스트리밍 호출 시작: model_id={self.model_id}")
            
            response = self._client.invoke_model_with_response_stream(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            stream = response.get("body")
            
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        chunk_data = json.loads(chunk.get("bytes").decode())
                        
                        # content_block_delta 이벤트에서 텍스트 추출
                        if chunk_data.get("type") == "content_block_delta":
                            delta = chunk_data.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                yield text
                        
                        # message_stop 이벤트 처리
                        elif chunk_data.get("type") == "message_stop":
                            logger.debug("Bedrock 스트리밍 완료")
                            break
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "ThrottlingException":
                logger.warning(f"Bedrock Rate Limit 초과: {error_message}")
                raise BedrockRateLimitError(f"Rate Limit 초과: {error_message}")
            
            logger.error(f"Bedrock 스트리밍 호출 실패: {error_code} - {error_message}")
            raise BedrockInvocationError(f"스트리밍 호출 실패: {error_message}")
            
        except BotoCoreError as e:
            logger.error(f"Bedrock 연결 오류: {e}")
            raise BedrockConnectionError(f"연결 오류: {e}")
            
        except Exception as e:
            logger.error(f"Bedrock 스트리밍 예상치 못한 오류: {e}")
            raise BedrockError(f"예상치 못한 오류: {e}")


# 전역 클라이언트 인스턴스
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """
    Bedrock 클라이언트 싱글톤 인스턴스 반환
    
    Returns:
        BedrockClient: Bedrock 클라이언트 인스턴스
    """
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client


def reset_bedrock_client() -> None:
    """
    Bedrock 클라이언트 인스턴스 초기화
    
    테스트나 설정 변경 시 사용합니다.
    """
    global _bedrock_client
    _bedrock_client = None
