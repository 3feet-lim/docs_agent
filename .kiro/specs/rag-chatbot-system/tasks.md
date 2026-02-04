# RAG 챗봇 시스템 구현 태스크

## Phase 1: 프로젝트 초기 설정

### 1. 프로젝트 구조 생성
- [x] 1.1 루트 디렉토리 구조 생성
  - `backend/`, `frontend/`, `documents/` 디렉토리 생성
  - `.env.example` 파일 생성
  - `.gitignore` 파일 생성
  - `README.md` 파일 생성

- [x] 1.2 Backend 디렉토리 구조 생성
  - `backend/src/` 하위 디렉토리 생성 (`api/`, `rag/`, `utils/`)
  - `backend/tests/` 디렉토리 생성
  - `backend/requirements.txt` 생성
  - `backend/Dockerfile` 생성

- [x] 1.3 Frontend 디렉토리 구조 생성
  - Vite + React + TypeScript 프로젝트 초기화
  - `src/` 하위 디렉토리 생성 (`components/`, `hooks/`, `store/`, `api/`, `types/`)
  - TailwindCSS 설정
  - `frontend/Dockerfile` 생성

- [x] 1.4 Docker Compose 설정
  - `docker-compose.yml` 작성
  - 네트워크 및 볼륨 설정
  - 환경변수 주입 설정

---

## Phase 2: Backend 기본 구조

### 2. 환경 설정 모듈 (`config.py`)
- [x] 2.1 Pydantic Settings 기반 설정 클래스 구현
  - `pydantic_settings.BaseSettings` 상속
  - `.env` 파일 자동 로드 지원
  - 타입 검증 및 기본값 설정

- [x] 2.2 AWS 관련 설정
  - `aws_access_key_id`, `aws_secret_access_key`: AWS 인증 (선택, IAM Role 사용 시 불필요)
  - `aws_region`: AWS 리전 (기본값: us-east-1)

- [x] 2.3 Bedrock 설정
  - `bedrock_model_id`: LLM 모델 ID (기본값: global.anthropic.claude-sonnet-4-5-20250929-v1:0)
  - `bedrock_model_arn`: Knowledge Base용 모델 ARN
  - `bedrock_embeddings_model_id`: 임베딩 모델 ID
  - `bedrock_max_tokens`, `bedrock_temperature`, `bedrock_top_p`: LLM 파라미터

- [x] 2.4 Knowledge Base 및 S3 설정
  - `knowledge_base_id`: Bedrock Knowledge Base ID
  - `s3_bucket_name`, `s3_vector_prefix`, `s3_raw_documents_prefix`: S3 경로 설정

- [x] 2.5 서버 및 RAG 설정
  - `backend_port`, `backend_host`, `frontend_port`: 서버 포트/호스트
  - `chunk_size`, `chunk_overlap`, `top_k_results`, `min_similarity`: RAG 파라미터
  - `db_path`: SQLite DB 경로
  - `log_level`, `log_format`: 로깅 설정

- [x] 2.6 설정 헬퍼 함수
  - `get_settings()`: 싱글톤 설정 인스턴스 반환
  - `get_aws_config()`, `get_bedrock_config()`, `get_rag_config()`, `get_s3_config()`: 카테고리별 설정 딕셔너리 반환

### 3. Bedrock 클라이언트 (`bedrock_client.py`)
- [x] 3.1 BedrockClient 클래스 구현
  - boto3 `bedrock-runtime` 클라이언트 초기화
  - 재시도 설정 (max_attempts=3, adaptive mode)
  - 타임아웃 설정 (connect=30s, read=60s)

- [x] 3.2 메시지 빌드 함수
  - `_build_messages()`: 대화 히스토리 + 현재 메시지를 Claude 형식으로 변환
  - `_build_request_body()`: Anthropic API 요청 본문 생성 (anthropic_version, max_tokens, messages, system, temperature, top_p)

- [x] 3.3 비스트리밍 호출 (`invoke()`)
  - `invoke_model()` API 호출
  - 응답 파싱: content, stop_reason, input_tokens, output_tokens
  - `BedrockResponse` 데이터클래스로 반환

- [x] 3.4 스트리밍 호출 (`invoke_stream()`)
  - `invoke_model_with_response_stream()` API 호출
  - `content_block_delta` 이벤트에서 텍스트 추출
  - `AsyncGenerator[str, None]`으로 토큰 단위 yield

- [x] 3.5 예외 클래스 정의
  - `BedrockError`: 기본 예외
  - `BedrockConnectionError`: 연결 실패
  - `BedrockInvocationError`: 모델 호출 실패
  - `BedrockRateLimitError`: Rate Limit 초과 (ThrottlingException)

- [x] 3.6 싱글톤 패턴
  - `get_bedrock_client()`: 전역 클라이언트 인스턴스 반환
  - `reset_bedrock_client()`: 테스트용 인스턴스 초기화

### 4. 대화 저장소 (`conversation_store.py`)
- [x] 4.1 데이터 클래스 정의
  - `Message`: id, session_id, role, content, timestamp, sources, metadata
  - `Session`: id, created_at, updated_at, messages, metadata

- [x] 4.2 ConversationStore 클래스 구현
  - `OrderedDict` 기반 LRU 캐시 (max_sessions=1000)
  - 세션당 최대 메시지 수 제한 (max_messages_per_session=100)
  - `threading.Lock`으로 스레드 안전성 보장

- [x] 4.3 세션 관리 메서드
  - `create_session()`: 새 세션 생성 (자동 ID 생성)
  - `get_session()`: 세션 조회 (LRU 업데이트)
  - `get_or_create_session()`: 조회 또는 생성
  - `clear_session()`: 세션 메시지 삭제
  - `delete_session()`: 세션 완전 삭제
  - `list_sessions()`: 모든 세션 목록

- [x] 4.4 메시지 관리 메서드
  - `add_message()`: 메시지 추가 (오래된 메시지 자동 제거)
  - `get_messages()`: 메시지 목록 조회 (limit, include_system 옵션)
  - `get_conversation_history()`: LLM 컨텍스트용 형식 반환 [{role, content}]

- [x] 4.5 싱글톤 패턴
  - `get_conversation_store()`: 전역 저장소 인스턴스 반환
  - `reset_conversation_store()`: 테스트용 인스턴스 초기화

### 5. MCP 관리자 (`mcp_manager.py`)
- [x] 5.1 MCP 데이터 클래스 및 Enum
  - `MCPServerStatus`: DISCONNECTED, CONNECTING, CONNECTED, ERROR
  - `MCPTool`: name, description, input_schema
  - `MCPToolResult`: tool_name, success, result, error

- [x] 5.2 MCPServerBase 추상 클래스
  - `connect()`, `disconnect()`: 연결 관리
  - `list_tools()`: 도구 목록 반환
  - `call_tool()`: 도구 실행
  - `status` 프로퍼티

- [x] 5.3 MCPManager 클래스 구현
  - `register_server()`, `unregister_server()`: 서버 등록/해제
  - `get_server()`, `list_servers()`: 서버 조회
  - `connect_all()`, `disconnect_all()`: 전체 서버 연결 관리
  - `list_all_tools()`: 모든 서버의 도구 목록
  - `call_tool()`: 특정 서버의 도구 실행

- [x] 5.4 AWSDocsMCPServer 예시 구현 (플레이스홀더)
  - `search_aws_docs`, `get_aws_doc_page` 도구 정의
  - 실제 구현은 향후 Phase 8에서 진행

### 6. FastAPI 앱 (`main.py`)
- [x] 6.1 FastAPI 앱 초기화
  - `FastAPI()` 인스턴스 생성 (title, description, version)
  - `lifespan` 컨텍스트 매니저로 시작/종료 로깅

- [x] 6.2 CORS 미들웨어 설정
  - `CORSMiddleware` 추가
  - Frontend 개발 서버 오리진 허용 (localhost:5173, frontend:5173)
  - 모든 메서드/헤더 허용

- [x] 6.3 기본 엔드포인트
  - `GET /`: API 서버 정보 반환
  - `GET /api/health`: Health Check (status, timestamp)

- [x] 6.4 전역 예외 핸들러
  - `RAGChatbotException` 핸들러: 커스텀 예외를 JSON 응답으로 변환
  - `Exception` 핸들러: 처리되지 않은 예외를 사용자 친화적 메시지로 변환

- [x] 6.5 Socket.IO 통합
  - `socketio.AsyncServer(async_mode='asgi')` 생성
  - `socketio.ASGIApp(sio, app)`으로 FastAPI와 통합
  - `/socket.io` 경로에서 WebSocket 처리

- [x] 6.6 라우터 등록
  - `app.include_router(chat_router, prefix="/api")`

---

## Phase 3: RAG 파이프라인 구현 (Bedrock Knowledge Base 사용)

### 3. Bedrock Knowledge Base 연동
- [x] 3.1 Knowledge Base 클라이언트 구현 (`rag/knowledge_base.py`)
  - `bedrock-agent-runtime` 클라이언트 설정
  - `retrieve` API 호출 (문서 검색)
  - `retrieve_and_generate` API 호출 (검색 + 응답 생성)
  - 스트리밍 응답 시뮬레이션
  - 출처 정보 추출

> **참고**: Bedrock Knowledge Base가 문서 청킹, 임베딩, 벡터 저장, 검색을 모두 처리합니다.
> S3에 문서를 업로드하면 Knowledge Base가 자동으로 인덱싱합니다.

---

## Phase 4: API 엔드포인트

### 7. REST API 구현
- [x] 7.1 채팅 API (`api/chat.py`)
  - `POST /api/chat` 엔드포인트
  - 요청 검증 (Pydantic 모델)
  - RAG 파이프라인 호출
  - 응답 형식 정의
  - **Property Test**: 메시지 ID 유일성 (Property 3.1)

- [ ] 7.2 문서 관리 API (`api/documents.py`) (선택)
  - `GET /api/documents` 엔드포인트
  - `POST /api/documents/upload` 엔드포인트
  - 문서 목록 조회
  - 문서 업로드 처리

### 8. WebSocket 통신
- [x] 8.1 Socket.IO 이벤트 핸들러 (`api/websocket.py`)
  - `chat_message` 이벤트 핸들러
  - `chat_response_chunk` 이벤트 발신
  - `chat_response_complete` 이벤트 발신
  - `chat_error` 이벤트 발신
  - 세션 관리

---

## Phase 5: Frontend 구현

### 9. 기본 UI 컴포넌트
- [x] 9.1 레이아웃 컴포넌트
  - `App.tsx` 루트 컴포넌트
  - `ChatContainer.tsx` 채팅 컨테이너
  - TailwindCSS 스타일링

- [x] 9.2 메시지 컴포넌트
  - `MessageList.tsx` 메시지 목록
  - `MessageItem.tsx` 개별 메시지
  - 사용자/AI 메시지 구분 스타일
  - 타임스탬프 표시

- [x] 9.3 입력 컴포넌트
  - `MessageInput.tsx` 입력창
  - 전송 버튼
  - Enter 키 전송
  - 입력 검증

- [x] 9.4 상태 표시 컴포넌트
  - `TypingIndicator.tsx` 타이핑 인디케이터
  - `ConnectionStatus.tsx` 연결 상태
  - 로딩 스피너

### 10. 상태 관리
- [x] 10.1 Zustand 스토어 설정
  - `store/chatStore.ts` 채팅 상태
  - `store/uiStore.ts` UI 상태
  - 메시지 추가/업데이트 액션
  - 세션 관리 액션

### 11. API 통신
- [x] 11.1 Socket.IO 클라이언트 (`api/socket.ts`)
  - Socket.IO 연결 설정
  - 이벤트 리스너 등록
  - 메시지 전송 함수
  - 재연결 로직

- [x] 11.2 React 훅 구현
  - `hooks/useSocket.ts` Socket.IO 훅
  - `hooks/useChat.ts` 채팅 로직 훅
  - `hooks/useMessages.ts` 메시지 관리 훅

### 12. 스트리밍 응답
- [x] 12.1 스트리밍 UI 구현
  - 토큰 단위 메시지 업데이트
  - 타이핑 효과 애니메이션
  - 스트리밍 완료 처리
  - 스크롤 자동 하단 이동

---

## Phase 6: 통합 및 테스트

> **참고**: Bedrock Knowledge Base를 사용하므로 문서 인덱싱 스크립트(13.1)는 불필요합니다.
> AWS 콘솔에서 Knowledge Base를 생성하고 S3 데이터 소스를 연결하면 자동으로 인덱싱됩니다.

### 14. 통합 테스트
- [x] 14.1 Backend 통합 테스트
  - API 엔드포인트 테스트
  - Knowledge Base 연동 테스트
  - Socket.IO 통신 테스트

- [x] 14.2 Frontend 통합 테스트
  - 컴포넌트 렌더링 테스트
  - 사용자 인터랙션 테스트
  - Socket.IO 통신 테스트

### 15. Property-Based Testing (선택)
- [ ] 15.1* Backend PBT 설정
  - Hypothesis 설정
  - 테스트 전략 정의

- [ ] 15.2* Frontend PBT 설정
  - fast-check 설정
  - 메시지 관련 Property Tests

---

## Phase 7: 배포 준비

### 16. Docker 최적화
- [x] 16.1 Dockerfile 최적화
  - 멀티 스테이지 빌드
  - 이미지 크기 최적화
  - 캐싱 전략

- [x] 16.2 Docker Compose 테스트
  - 전체 스택 실행 테스트
  - 볼륨 마운트 확인
  - 환경변수 주입 확인

### 17. 문서화
- [x] 17.1 README 작성
  - 프로젝트 소개
  - 설치 방법
  - 실행 방법
  - 환경변수 설명

- [x] 17.2 API 문서 작성
  - REST API 문서
  - WebSocket 이벤트 문서
  - 예제 코드

- [x] 17.3 개발자 가이드
  - 아키텍처 설명
  - 코드 구조 설명
  - 기여 가이드

### 18. 에러 처리 및 로깅
- [x] 18.1 에러 처리 개선
  - 모든 예외 처리
  - 사용자 친화적 에러 메시지
  - **Property Test**: 에러 응답 형식 (Property 5.1)
  - **Property Test**: 재시도 가능 에러 분류 (Property 5.2)

- [x] 18.2 로깅 시스템
  - 구조화된 로깅 (JSON)
  - 로그 레벨 설정
  - 민감 정보 마스킹

---

## Phase 8: 최적화 및 개선 (선택)

### 19. 성능 최적화
- [ ] 19.1* 벡터 검색 최적화
  - 인덱스 파일 캐싱
  - 배치 임베딩 처리
  - 병렬 처리

- [ ] 19.2* Frontend 최적화
  - 코드 스플리팅
  - 가상 스크롤
  - 메모이제이션

### 20. 추가 기능
- [ ] 20.1* 출처 표시 기능
  - 응답에 출처 링크 추가
  - 출처 하이라이팅
  - **Property Test**: 출처 추적 가능성 (Property 4.1)

- [ ] 20.2* 대화 히스토리 UI
  - 이전 대화 목록
  - 대화 검색
  - 대화 삭제
  - **Property Test**: 타임스탬프 순서 (Property 3.2)

- [ ] 20.3* MCP 통합
  - MCP 서버 연결
  - AWS Docs MCP 통합
  - 도구 호출 UI

---

## 우선순위 요약

**High Priority (MVP)**:
- Phase 1-6: 기본 기능 구현
- 문서 인덱싱, RAG 파이프라인, 채팅 UI, Docker 설정

**Medium Priority**:
- Phase 7: 배포 준비 및 문서화

**Low Priority (Optional)**:
- Phase 8: 최적화 및 추가 기능

---

## 예상 소요 시간

- Phase 1: 2-3시간
- Phase 2: 2-3시간
- Phase 3: 6-8시간
- Phase 4: 3-4시간
- Phase 5: 6-8시간
- Phase 6: 4-5시간
- Phase 7: 3-4시간
- Phase 8: 4-6시간 (선택)

**총 예상 시간**: 26-35시간 (MVP), 30-41시간 (전체)
