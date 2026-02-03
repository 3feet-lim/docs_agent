# RAG 챗봇 시스템 요구사항

## 1. 프로젝트 개요

### 1.1 목적
사내 문서를 학습하여 질문에 답변하는 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇 시스템 구축

### 1.2 핵심 목표
- 기존 ai-agent-demo의 Backend 코드를 최대한 재활용
- RAG 파이프라인을 통한 정확한 문서 기반 답변 제공
- React + Vite 기반의 현대적인 채팅 UI 구축
- Docker 컨테이너 기반 배포 환경 구성

### 1.3 기술 스택

**Frontend**
- Node.js: 22.11.0 이상
- React: 18.3.1
- Vite: 6.0.5
- TypeScript: 5.7.2
- TailwindCSS: 3.4.17
- Socket.IO Client: 4.8.1
- React Query: 5.62.8
- Zustand: 5.0.2

**Backend**
- Python: 3.12
- FastAPI + WebSocket
- LangChain + LangGraph
- AWS Bedrock Claude Sonnet 4.5 (global.anthropic.claude-sonnet-4-5-20250929-v1:0)
- Vector Storage: AWS S3
- Socket.IO

**Infrastructure**
- Docker + Docker Compose
- 환경변수 기반 설정 관리

---

## 2. 기능 요구사항

### 2.1 문서 관리 및 RAG 파이프라인

#### 2.1.1 문서 로딩
**사용자 스토리**: 관리자로서, 사내 문서를 S3에 업로드하여 AI가 학습할 수 있도록 하고 싶다.

**인수 기준**:
- [ ] 다양한 문서 형식 지원 (PDF, Markdown, TXT, DOCX)
- [ ] S3 `raw-documents/` 버킷에서 문서 자동 스캔
- [ ] 문서 메타데이터 추출 (파일명, 생성일, 수정일)
- [ ] 대용량 문서 처리 지원 (청크 단위 분할)
- [ ] VPC 엔드포인트를 통한 S3 접근

#### 2.1.2 문서 벡터화
**사용자 스토리**: 시스템으로서, 문서를 벡터 임베딩으로 변환하여 의미 기반 검색이 가능하도록 하고 싶다.

**인수 기준**:
- [ ] AWS Bedrock Embeddings 모델 사용
- [ ] 문서를 적절한 크기의 청크로 분할 (500-1000 토큰)
- [ ] 청크 간 오버랩 설정 (50-100 토큰)
- [ ] AWS S3에 벡터 임베딩 저장
- [ ] 메타데이터와 함께 저장 (출처, 페이지 번호 등)
- [ ] S3 버킷 구조 설계 (효율적인 검색을 위한)

#### 2.1.3 의미 기반 검색
**사용자 스토리**: 사용자로서, 질문을 입력하면 관련 문서를 자동으로 찾아 답변에 활용하기를 원한다.

**인수 기준**:
- [ ] 사용자 질문을 벡터로 변환
- [ ] 유사도 기반 Top-K 문서 검색 (K=3-5)
- [ ] 검색 결과에 유사도 점수 포함
- [ ] 검색 결과 필터링 (최소 유사도 임계값)

#### 2.1.4 컨텍스트 기반 답변 생성
**사용자 스토리**: 사용자로서, 검색된 문서를 기반으로 정확하고 맥락에 맞는 답변을 받고 싶다.

**인수 기준**:
- [ ] 검색된 문서를 프롬프트에 컨텍스트로 포함
- [ ] AWS Bedrock Claude 3 Sonnet 모델 사용
- [ ] 출처 정보와 함께 답변 제공
- [ ] 관련 문서가 없을 경우 명확한 안내 메시지

### 2.2 실시간 채팅 인터페이스

#### 2.2.1 채팅 UI
**사용자 스토리**: 사용자로서, 직관적이고 사용하기 쉬운 채팅 인터페이스를 통해 AI와 대화하고 싶다.

**인수 기준**:
- [ ] 메시지 입력창 및 전송 버튼
- [ ] 사용자/AI 메시지 구분 표시
- [ ] 타임스탬프 표시
- [ ] 스크롤 자동 하단 이동
- [ ] 반응형 디자인 (모바일/데스크톱)
- [ ] TailwindCSS 기반 스타일링

#### 2.2.2 실시간 통신
**사용자 스토리**: 사용자로서, 메시지를 보내면 즉시 AI의 응답을 받고 싶다.

**인수 기준**:
- [ ] Socket.IO 기반 WebSocket 연결
- [ ] 메시지 송신 이벤트 처리
- [ ] 메시지 수신 이벤트 처리
- [ ] 연결 상태 표시 (연결됨/연결 끊김)
- [ ] 재연결 자동 처리

#### 2.2.3 스트리밍 응답
**사용자 스토리**: 사용자로서, AI가 답변을 생성하는 과정을 실시간으로 보고 싶다.

**인수 기준**:
- [ ] LLM 응답을 토큰 단위로 스트리밍
- [ ] 타이핑 효과로 응답 표시
- [ ] 스트리밍 중 로딩 인디케이터
- [ ] 스트리밍 완료 상태 표시

#### 2.2.4 대화 히스토리
**사용자 스토리**: 사용자로서, 이전 대화 내용을 확인하고 맥락을 유지하며 대화하고 싶다.

**인수 기준**:
- [ ] 세션별 대화 히스토리 저장
- [ ] 대화 히스토리를 컨텍스트로 활용
- [ ] 새 대화 시작 기능
- [ ] 대화 히스토리 초기화 기능

### 2.3 Backend 시스템

#### 2.3.1 기존 코드 재활용
**사용자 스토리**: 개발자로서, ai-agent-demo의 검증된 코드를 재사용하여 개발 시간을 단축하고 싶다.

**인수 기준**:
- [ ] `bedrock_client.py` 재활용 및 개선 (Claude Sonnet 4.5 지원)
- [ ] `config.py` 재활용 (환경변수 관리)
- [ ] `conversation_store.py` 재활용 (대화 저장)
- [ ] `mcp_manager.py` 재활용 (MCP 통합 준비)
- [ ] `main.py` 확장 (RAG 엔드포인트 추가)
- [ ] 필요시 새로운 모듈 작성 (유연한 접근)

#### 2.3.2 RAG 모듈 추가
**사용자 스토리**: 개발자로서, RAG 기능을 모듈화하여 유지보수가 쉽도록 하고 싶다.

**인수 기준**:
- [ ] `rag/document_loader.py` - 문서 로딩 로직
- [ ] `rag/embeddings.py` - 벡터 임베딩 생성
- [ ] `rag/s3_vector_store.py` - S3 기반 벡터 저장소 관리
- [ ] `rag/retriever.py` - 문서 검색 로직
- [ ] `rag/chain.py` - RAG 체인 구성

#### 2.3.3 API 엔드포인트
**사용자 스토리**: Frontend 개발자로서, 명확한 API를 통해 Backend와 통신하고 싶다.

**인수 기준**:
- [ ] `POST /api/chat` - 채팅 메시지 전송
- [ ] `GET /api/health` - 서버 상태 확인
- [ ] WebSocket `/socket.io` - 실시간 통신
- [ ] `POST /api/documents/upload` - 문서 업로드 (선택)
- [ ] `GET /api/documents` - 문서 목록 조회 (선택)

### 2.4 인프라 및 배포

#### 2.4.1 Docker 컨테이너화
**사용자 스토리**: DevOps 엔지니어로서, 폐쇄망 환경에서 일관된 환경으로 애플리케이션을 실행하고 싶다.

**인수 기준**:
- [ ] Frontend Dockerfile (Node.js 22.11 Alpine)
- [ ] Backend Dockerfile (Python 3.12 Slim)
- [ ] docker-compose.yml 구성
- [ ] 컨테이너 간 네트워크 설정
- [ ] Stateless 컨테이너 설계 (모든 데이터는 S3)
- [ ] VPC 엔드포인트를 통한 AWS 서비스 접근

#### 2.4.2 환경변수 관리
**사용자 스토리**: 운영자로서, 폐쇄망 환경에서 환경별로 다른 설정을 쉽게 적용하고 싶다.

**인수 기준**:
- [ ] `.env.example` 파일 제공
- [ ] AWS 인증 정보 환경변수 주입 (IAM Role 또는 Access Key)
- [ ] Bedrock 모델 ID 설정 (global.anthropic.claude-sonnet-4-5-20250929-v1:0)
- [ ] S3 버킷 정보 설정 (raw-documents, vectors)
- [ ] VPC 엔드포인트 URL 설정
- [ ] 포트 설정 (Frontend: 5173, Backend: 8000)

#### 2.4.3 개발 환경
**사용자 스토리**: 개발자로서, 코드 변경 시 자동으로 반영되는 개발 환경을 원한다.

**인수 기준**:
- [ ] Frontend Hot Reload (Vite HMR)
- [ ] Backend Hot Reload (uvicorn --reload)
- [ ] 소스코드 볼륨 마운트
- [ ] 로그 실시간 확인

---

## 3. 비기능 요구사항

### 3.1 성능
- [ ] 문서 검색 응답 시간 < 2초
- [ ] LLM 첫 토큰 응답 시간 < 3초
- [ ] 동시 사용자 10명 지원

### 3.2 보안
- [ ] AWS 인증 정보 환경변수로 관리
- [ ] `.env` 파일 `.gitignore`에 추가
- [ ] API 요청 검증
- [ ] CORS 설정

### 3.3 확장성
- [ ] MCP 서버 추가 가능한 플러그인 구조
- [ ] 다양한 벡터 저장소 지원 가능한 인터페이스
- [ ] LLM 모델 교체 가능한 추상화

### 3.4 모니터링
- [ ] 구조화된 로깅 (JSON 형식)
- [ ] 에러 추적 및 로깅
- [ ] 요청/응답 로깅

---

## 4. 제약사항

### 4.1 기술적 제약
- Python 3.12 필수
- Node.js 22.11.0 이상 필수
- AWS Bedrock 접근 권한 필요
- 명시된 패키지 버전 사용 (호환성)

### 4.2 운영 제약
- 폐쇄망 환경 (퍼블릭 인터넷 접속 불가)
- VPC 엔드포인트를 통한 AWS 서비스 접근만 가능
- 컨테이너 이미지는 불변 (실시간 문서 추가 불가)
- 문서는 S3 `raw-documents/`에 사전 업로드 필요
- 초기 문서 인덱싱 시간 필요
- AWS Bedrock API 비용 발생

---

## 5. 우선순위

### Phase 1 (MVP)
1. Backend RAG 파이프라인 구축
2. 기본 채팅 UI (React + Vite)
3. Socket.IO 실시간 통신
4. Docker 컨테이너 구성

### Phase 2 (개선)
1. 스트리밍 응답
2. 대화 히스토리 관리
3. 문서 업로드 UI
4. 출처 표시 기능

### Phase 3 (확장)
1. MCP 서버 통합
2. 다중 사용자 지원
3. 대화 세션 관리
4. 고급 검색 필터

---

## 6. 성공 기준

### 6.1 기능적 성공
- [ ] 사용자가 질문을 입력하면 관련 문서 기반 답변을 받을 수 있다
- [ ] 답변에 출처 정보가 포함된다
- [ ] 실시간으로 응답이 스트리밍된다
- [ ] Docker Compose로 전체 시스템을 실행할 수 있다

### 6.2 기술적 성공
- [ ] 기존 ai-agent-demo 코드의 유용한 부분 최대한 재활용
- [ ] 모든 테스트 통과
- [ ] 문서화 완료 (README, API 문서)
- [ ] 환경변수 기반 설정 완료

---

## 7. 참고 자료

### 7.1 기존 프로젝트
- ai-agent-demo: `C:\Users\superuser\git\ai-agent-demo`
- Backend 구조: `backend/src/`
- Frontend 구조: `frontend/static/`

### 7.2 기술 문서
- LangChain: https://python.langchain.com/
- AWS Bedrock: https://docs.aws.amazon.com/bedrock/
- React Query: https://tanstack.com/query/
- Socket.IO: https://socket.io/docs/
