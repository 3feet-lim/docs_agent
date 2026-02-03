# RAG 챗봇 시스템 구현 태스크

## Phase 1: 프로젝트 초기 설정

### 1. 프로젝트 구조 생성
- [x] 1.1 루트 디렉토리 구조 생성
  - `backend/`, `frontend/`, `documents/` 디렉토리 생성
  - `.env.example` 파일 생성
  - `.gitignore` 파일 생성
  - `README.md` 파일 생성

- [ ] 1.2 Backend 디렉토리 구조 생성
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

### 2. 기존 코드 마이그레이션
- [x] 2.1 ai-agent-demo 코드 복사 및 검토
  - `bedrock_client.py` 복사 및 Claude Sonnet 4.5 지원 확인
  - `config.py` 복사 및 환경변수 추가
  - `conversation_store.py` 복사
  - `mcp_manager.py` 복사

- [ ] 2.2 FastAPI 앱 초기화
  - `main.py` 작성 (FastAPI 앱 생성)
  - CORS 설정
  - Health check 엔드포인트 추가
  - 로깅 설정

- [ ] 2.3 Socket.IO 서버 설정
  - Socket.IO 서버 초기화
  - 연결/연결 해제 이벤트 핸들러
  - 기본 메시지 이벤트 핸들러

---

## Phase 3: RAG 파이프라인 구현

### 3. 문서 로딩 및 처리
- [ ] 3.1 문서 로더 구현 (`rag/document_loader.py`)
  - PDF 파서 구현
  - DOCX 파서 구현
  - Markdown 파서 구현
  - TXT 파서 구현
  - 디렉토리 스캔 기능

- [ ] 3.2 문서 청킹 구현
  - RecursiveCharacterTextSplitter 설정
  - 청크 크기 및 오버랩 설정
  - 메타데이터 첨부 로직
  - **Property Test**: 청킹 일관성 (Property 1.1)
  - **Property Test**: 청크 크기 제약 (Property 1.2)

### 4. 임베딩 및 벡터 저장
- [ ] 4.1 임베딩 생성 (`rag/embeddings.py`)
  - AWS Bedrock Embeddings 클라이언트 설정
  - 텍스트 → 벡터 변환 함수
  - 배치 처리 지원
  - 에러 처리 및 재시도 로직

- [ ] 4.2 S3 벡터 저장소 구현 (`rag/s3_vector_store.py`)
  - S3 클라이언트 초기화
  - 벡터 저장 함수 (JSON 형식)
  - 벡터 로드 함수
  - 인덱스 파일 관리
  - 메타데이터 저장/조회

### 5. 문서 검색
- [ ] 5.1 검색 엔진 구현 (`rag/retriever.py`)
  - 코사인 유사도 계산 함수
  - Top-K 검색 함수
  - 최소 유사도 필터링
  - **Property Test**: 검색 결과 정렬 (Property 2.1)
  - **Property Test**: 최소 유사도 필터링 (Property 2.2)
  - **Property Test**: Top-K 제약 (Property 2.3)

### 6. RAG 체인 구성
- [ ] 6.1 RAG 체인 구현 (`rag/chain.py`)
  - 프롬프트 템플릿 작성
  - 컨텍스트 구성 함수
  - LangChain RAG 체인 설정
  - 스트리밍 응답 처리
  - **Property Test**: 컨텍스트 포함 (Property 4.2)

- [ ] 6.2 Bedrock 클라이언트 개선
  - Claude Sonnet 4.5 모델 설정
  - 스트리밍 API 호출
  - 토큰 사용량 추적
  - 에러 처리

---

## Phase 4: API 엔드포인트

### 7. REST API 구현
- [ ] 7.1 채팅 API (`api/chat.py`)
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
- [ ] 8.1 Socket.IO 이벤트 핸들러 (`api/websocket.py`)
  - `chat_message` 이벤트 핸들러
  - `chat_response_chunk` 이벤트 발신
  - `chat_response_complete` 이벤트 발신
  - `chat_error` 이벤트 발신
  - 세션 관리

---

## Phase 5: Frontend 구현

### 9. 기본 UI 컴포넌트
- [ ] 9.1 레이아웃 컴포넌트
  - `App.tsx` 루트 컴포넌트
  - `ChatContainer.tsx` 채팅 컨테이너
  - TailwindCSS 스타일링

- [ ] 9.2 메시지 컴포넌트
  - `MessageList.tsx` 메시지 목록
  - `MessageItem.tsx` 개별 메시지
  - 사용자/AI 메시지 구분 스타일
  - 타임스탬프 표시

- [ ] 9.3 입력 컴포넌트
  - `MessageInput.tsx` 입력창
  - 전송 버튼
  - Enter 키 전송
  - 입력 검증

- [ ] 9.4 상태 표시 컴포넌트
  - `TypingIndicator.tsx` 타이핑 인디케이터
  - `ConnectionStatus.tsx` 연결 상태
  - 로딩 스피너

### 10. 상태 관리
- [ ] 10.1 Zustand 스토어 설정
  - `store/chatStore.ts` 채팅 상태
  - `store/uiStore.ts` UI 상태
  - 메시지 추가/업데이트 액션
  - 세션 관리 액션

### 11. API 통신
- [ ] 11.1 Socket.IO 클라이언트 (`api/socket.ts`)
  - Socket.IO 연결 설정
  - 이벤트 리스너 등록
  - 메시지 전송 함수
  - 재연결 로직

- [ ] 11.2 React 훅 구현
  - `hooks/useSocket.ts` Socket.IO 훅
  - `hooks/useChat.ts` 채팅 로직 훅
  - `hooks/useMessages.ts` 메시지 관리 훅

### 12. 스트리밍 응답
- [ ] 12.1 스트리밍 UI 구현
  - 토큰 단위 메시지 업데이트
  - 타이핑 효과 애니메이션
  - 스트리밍 완료 처리
  - 스크롤 자동 하단 이동

---

## Phase 6: 통합 및 테스트

### 13. 문서 인덱싱 스크립트
- [ ] 13.1 인덱싱 CLI 도구
  - 문서 디렉토리 스캔
  - 문서 처리 및 임베딩
  - S3 업로드
  - 진행 상황 표시

### 14. 통합 테스트
- [ ] 14.1 Backend 통합 테스트
  - API 엔드포인트 테스트
  - RAG 파이프라인 E2E 테스트
  - Socket.IO 통신 테스트

- [ ] 14.2 Frontend 통합 테스트
  - 컴포넌트 렌더링 테스트
  - 사용자 인터랙션 테스트
  - Socket.IO 통신 테스트

### 15. Property-Based Testing
- [ ] 15.1 Backend PBT 설정
  - Hypothesis 설정
  - 테스트 전략 정의
  - 모든 Property Tests 실행 및 검증

- [ ] 15.2 Frontend PBT 설정 (선택)
  - fast-check 설정
  - 메시지 관련 Property Tests

---

## Phase 7: 배포 준비

### 16. Docker 최적화
- [ ] 16.1 Dockerfile 최적화
  - 멀티 스테이지 빌드
  - 이미지 크기 최적화
  - 캐싱 전략

- [ ] 16.2 Docker Compose 테스트
  - 전체 스택 실행 테스트
  - 볼륨 마운트 확인
  - 환경변수 주입 확인

### 17. 문서화
- [ ] 17.1 README 작성
  - 프로젝트 소개
  - 설치 방법
  - 실행 방법
  - 환경변수 설명

- [ ] 17.2 API 문서 작성
  - REST API 문서
  - WebSocket 이벤트 문서
  - 예제 코드

- [ ] 17.3 개발자 가이드
  - 아키텍처 설명
  - 코드 구조 설명
  - 기여 가이드

### 18. 에러 처리 및 로깅
- [ ] 18.1 에러 처리 개선
  - 모든 예외 처리
  - 사용자 친화적 에러 메시지
  - **Property Test**: 에러 응답 형식 (Property 5.1)
  - **Property Test**: 재시도 가능 에러 분류 (Property 5.2)

- [ ] 18.2 로깅 시스템
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
