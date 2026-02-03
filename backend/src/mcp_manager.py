"""
MCP (Model Context Protocol) 관리자 모듈

이 모듈은 MCP 서버와의 연결을 관리합니다.
MCP는 선택적 기능으로, 외부 도구 및 데이터 소스와의 통합을 지원합니다.

현재는 기본 구조만 제공하며, 향후 확장을 위한 인터페이스를 정의합니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .config import get_settings


# 로거 설정
logger = logging.getLogger(__name__)


class MCPServerStatus(Enum):
    """MCP 서버 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """
    MCP 도구 정의
    
    Attributes:
        name: 도구 이름
        description: 도구 설명
        input_schema: 입력 스키마 (JSON Schema)
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """도구를 딕셔너리로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class MCPToolResult:
    """
    MCP 도구 실행 결과
    
    Attributes:
        tool_name: 실행된 도구 이름
        success: 성공 여부
        result: 실행 결과
        error: 에러 메시지 (실패 시)
    """
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """결과를 딕셔너리로 변환"""
        data = {
            "tool_name": self.tool_name,
            "success": self.success,
        }
        if self.success:
            data["result"] = self.result
        else:
            data["error"] = self.error
        return data


class MCPServerBase(ABC):
    """
    MCP 서버 기본 클래스 (추상)
    
    모든 MCP 서버 구현은 이 클래스를 상속해야 합니다.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """서버에 연결"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """서버 연결 해제"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """사용 가능한 도구 목록 반환"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """도구 실행"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> MCPServerStatus:
        """서버 상태 반환"""
        pass


class MCPManager:
    """
    MCP 서버 관리자 클래스
    
    여러 MCP 서버를 등록하고 관리합니다.
    """
    
    def __init__(self):
        """MCPManager 초기화"""
        self._servers: Dict[str, MCPServerBase] = {}
        self._enabled = get_settings().mcp_enabled
        
        logger.info(f"MCPManager 초기화: enabled={self._enabled}")
    
    @property
    def enabled(self) -> bool:
        """MCP 활성화 여부"""
        return self._enabled
    
    def register_server(self, name: str, server: MCPServerBase) -> None:
        """
        MCP 서버 등록
        
        Args:
            name: 서버 이름 (고유 식별자)
            server: MCP 서버 인스턴스
        """
        if not self._enabled:
            logger.warning("MCP가 비활성화되어 있어 서버를 등록할 수 없습니다.")
            return
        
        self._servers[name] = server
        logger.info(f"MCP 서버 등록: {name}")
    
    def unregister_server(self, name: str) -> bool:
        """
        MCP 서버 등록 해제
        
        Args:
            name: 서버 이름
        
        Returns:
            bool: 성공 여부
        """
        if name in self._servers:
            del self._servers[name]
            logger.info(f"MCP 서버 등록 해제: {name}")
            return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServerBase]:
        """
        MCP 서버 조회
        
        Args:
            name: 서버 이름
        
        Returns:
            Optional[MCPServerBase]: 서버 인스턴스 (없으면 None)
        """
        return self._servers.get(name)
    
    def list_servers(self) -> List[Dict]:
        """
        등록된 모든 서버 목록 반환
        
        Returns:
            List[Dict]: 서버 정보 리스트
        """
        return [
            {
                "name": name,
                "status": server.status.value,
            }
            for name, server in self._servers.items()
        ]
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        모든 서버에 연결
        
        Returns:
            Dict[str, bool]: 서버별 연결 결과
        """
        if not self._enabled:
            logger.warning("MCP가 비활성화되어 있습니다.")
            return {}
        
        results = {}
        for name, server in self._servers.items():
            try:
                results[name] = await server.connect()
                logger.info(f"MCP 서버 연결 성공: {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"MCP 서버 연결 실패: {name} - {e}")
        
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """
        모든 서버 연결 해제
        
        Returns:
            Dict[str, bool]: 서버별 연결 해제 결과
        """
        results = {}
        for name, server in self._servers.items():
            try:
                results[name] = await server.disconnect()
                logger.info(f"MCP 서버 연결 해제: {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"MCP 서버 연결 해제 실패: {name} - {e}")
        
        return results
    
    async def list_all_tools(self) -> Dict[str, List[MCPTool]]:
        """
        모든 서버의 도구 목록 반환
        
        Returns:
            Dict[str, List[MCPTool]]: 서버별 도구 목록
        """
        if not self._enabled:
            return {}
        
        tools = {}
        for name, server in self._servers.items():
            if server.status == MCPServerStatus.CONNECTED:
                try:
                    tools[name] = await server.list_tools()
                except Exception as e:
                    logger.error(f"도구 목록 조회 실패: {name} - {e}")
                    tools[name] = []
        
        return tools
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """
        특정 서버의 도구 실행
        
        Args:
            server_name: 서버 이름
            tool_name: 도구 이름
            arguments: 도구 인자
        
        Returns:
            MCPToolResult: 실행 결과
        """
        if not self._enabled:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error="MCP가 비활성화되어 있습니다.",
            )
        
        server = self._servers.get(server_name)
        if server is None:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=f"서버를 찾을 수 없습니다: {server_name}",
            )
        
        if server.status != MCPServerStatus.CONNECTED:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=f"서버가 연결되어 있지 않습니다: {server_name}",
            )
        
        try:
            return await server.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"도구 실행 실패: {server_name}/{tool_name} - {e}")
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
            )


# 전역 MCP 관리자 인스턴스
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """
    MCP 관리자 싱글톤 인스턴스 반환
    
    Returns:
        MCPManager: MCP 관리자 인스턴스
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


def reset_mcp_manager() -> None:
    """
    MCP 관리자 인스턴스 초기화
    
    테스트나 설정 변경 시 사용합니다.
    """
    global _mcp_manager
    _mcp_manager = None


# 예시: AWS Docs MCP 서버 구현 (향후 확장용)
class AWSDocsMCPServer(MCPServerBase):
    """
    AWS 문서 MCP 서버 (예시 구현)
    
    AWS 공식 문서를 검색하고 조회하는 기능을 제공합니다.
    실제 구현은 향후 Phase 3에서 진행됩니다.
    """
    
    def __init__(self, server_url: Optional[str] = None):
        """
        AWSDocsMCPServer 초기화
        
        Args:
            server_url: MCP 서버 URL
        """
        self._server_url = server_url or get_settings().mcp_server_url
        self._status = MCPServerStatus.DISCONNECTED
        self._tools: List[MCPTool] = []
    
    @property
    def status(self) -> MCPServerStatus:
        """서버 상태 반환"""
        return self._status
    
    async def connect(self) -> bool:
        """서버에 연결"""
        if not self._server_url:
            logger.warning("MCP 서버 URL이 설정되지 않았습니다.")
            self._status = MCPServerStatus.ERROR
            return False
        
        try:
            self._status = MCPServerStatus.CONNECTING
            # TODO: 실제 연결 로직 구현
            # 현재는 플레이스홀더
            self._status = MCPServerStatus.CONNECTED
            
            # 사용 가능한 도구 정의
            self._tools = [
                MCPTool(
                    name="search_aws_docs",
                    description="AWS 공식 문서에서 정보를 검색합니다.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색 쿼리"
                            },
                            "service": {
                                "type": "string",
                                "description": "AWS 서비스 이름 (선택)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                MCPTool(
                    name="get_aws_doc_page",
                    description="특정 AWS 문서 페이지의 내용을 가져옵니다.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "AWS 문서 URL"
                            }
                        },
                        "required": ["url"]
                    }
                ),
            ]
            
            logger.info("AWS Docs MCP 서버 연결 성공")
            return True
            
        except Exception as e:
            self._status = MCPServerStatus.ERROR
            logger.error(f"AWS Docs MCP 서버 연결 실패: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """서버 연결 해제"""
        self._status = MCPServerStatus.DISCONNECTED
        self._tools = []
        logger.info("AWS Docs MCP 서버 연결 해제")
        return True
    
    async def list_tools(self) -> List[MCPTool]:
        """사용 가능한 도구 목록 반환"""
        return self._tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """도구 실행"""
        if self._status != MCPServerStatus.CONNECTED:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error="서버가 연결되어 있지 않습니다.",
            )
        
        # TODO: 실제 도구 실행 로직 구현
        # 현재는 플레이스홀더
        
        if tool_name == "search_aws_docs":
            query = arguments.get("query", "")
            return MCPToolResult(
                tool_name=tool_name,
                success=True,
                result={
                    "query": query,
                    "results": [],
                    "message": "AWS Docs 검색 기능은 향후 구현 예정입니다."
                }
            )
        
        elif tool_name == "get_aws_doc_page":
            url = arguments.get("url", "")
            return MCPToolResult(
                tool_name=tool_name,
                success=True,
                result={
                    "url": url,
                    "content": "",
                    "message": "AWS Docs 페이지 조회 기능은 향후 구현 예정입니다."
                }
            )
        
        return MCPToolResult(
            tool_name=tool_name,
            success=False,
            error=f"알 수 없는 도구: {tool_name}",
        )
