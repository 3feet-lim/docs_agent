# RAG 챗봇 시스템 설계 문서

## 1. 시스템 아키텍처

### 1.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                          │
│                     (React + Vite UI)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ WebSocket (Socket.IO)
                     │ HTTP REST API
┌────────────────────▼────────────────────────────────────────┐
│                    Frontend Container                        │
│                  (Node.js 22.11 Alpine)                      │
│                                                              │
│  - React 18.3.1 + TypeScript                                │
│  - Vite 6.0.5 (Dev Server + Build)                          │
│  - Socket.IO Client                                          │
│  - TailwindCSS                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Socket.IO / HTTP
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Backend Container                         │
│                   (Python 3.12 Slim)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastAPI + Socket.IO Server                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────▼──────────────────────────────┐  │
│  │              RAG Pipeline                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │  Document  │→ │ Embeddings │→ │  S3 Vector   │  │  │
│  │  │   Loader   │  │  Generator │  │    Store     │  │  │
│  │  └────────────┘  └────────────┘  └──────────────┘  │  │
│  │                                                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │   Query    │→ │ Retriever  │→ │  LLM Chain   │  │  │
│  │  │  Processor │  │  (Search)  │  │  (Generate)  │  │  │
│  │  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────▼──────────────────────────────┐  │
│  │         Conversation Store (In-Memory)               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ AWS SDK (boto3)
                     │
┌────────────────────▼────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AWS Bedrock                             │  │
│  │  - Claude Sonnet 4.5                                 │  │
│  │  - Embeddings Model                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AWS S3                                  │  │
│  │  - Vector Embeddings Storage                         │  │
│  │  - Document Metadata                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 컴포넌트 설명

#### Frontend (React + Vite)
- **역할**: 사용자 인터페이스 제공
- **기술**: React 18.3.1, TypeScript, Vite, TailwindCSS
- **주요 기능**:
  - 채팅 UI 렌더링
  - Socket.IO를 통한 실시간 통신
  - 상태 관리 (Zustand)
  - API 호출 관리 (React Query)

#### Backend (FastAPI + Python)
- **역할**: 비즈니스 로직 및 AI 처리
- **기술**: Python 3.12, FastAPI, LangChain, Socket.IO
- **주요 기능**:
  - RESTful API 제공
  - WebSocket 실시간 통신
  - RAG 파이프라인 실행
  - 대화 히스토리 관리

#### AWS Bedrock
- **역할**: LLM 및 임베딩 모델 제공
- **모델**: 
  - LLM: Claude Sonnet 4.5 (`global.anthropic.claude-sonnet-4-5-20250929-v1:0`)
  - Embeddings: Titan Embeddings 또는 Cohere
- **기능**:
  - 자연어 이해 및 생성
  - 텍스트 임베딩 생성

#### AWS S3
- **역할**: 문서 및 벡터 임베딩 저장소
- **구조**:
  ```
  s3://bucket-name/
    ├── raw-documents/          # 원본 문서 (관리자 업로드)
    │   ├── user_manual.pdf
    │   ├── policy.docx
    │   └── guide.md
    └── vectors/                # 처리된 벡터 임베딩
        ├── user_manual_chunk_001.json
        ├── user_manual_chunk_002.json
        ├── policy_chunk_001.json
        └── index.json          # 벡터 인덱스
  ```
- **저장 형식**: JSON (벡터 + 메타데이터)
- **접근**: VPC 엔드포인트를 통한 폐쇄망 접근

---

## 2. 데이터 흐름

### 2.1 문서 인덱싱 플로우

```
1. 문서 업로드/스캔
   └─> /documents 디렉토리에서 파일 읽기

2. 문서 파싱
   └─> PDF, DOCX, MD, TXT 파서 사용
   └─> 텍스트 추출 및 정제

3. 청킹 (Chunking)
   └─> 500-1000 토큰 단위로 분할
   └─> 50-100 토큰 오버랩 설정
   └─> 메타데이터 첨부 (파일명, 페이지, 섹션)

4. 임베딩 생성
   └─> AWS Bedrock Embeddings API 호출
   └─> 각 청크를 벡터로 변환

5. S3 저장
   └─> 벡터 + 메타데이터를 JSON으로 저장
   └─> 인덱스 파일 업데이트
```

### 2.2 질의응답 플로우

```
1. 사용자 질문 입력
   └─> Frontend에서 Socket.IO로 전송

2. 질문 임베딩 생성
   └─> AWS Bedrock Embeddings API 호출
   └─> 질문을 벡터로 변환

3. 유사도 검색
   └─> S3에서 벡터 인덱스 로드
   └─> 코사인 유사도 계산
   └─> Top-K 문서 청크 선택 (K=3-5)

4. 컨텍스트 구성
   └─> 검색된 청크들을 프롬프트에 포함
   └─> 대화 히스토리 추가

5. LLM 호출
   └─> AWS Bedrock Claude Sonnet 4.5 API 호출
   └─> 스트리밍 모드로 응답 생성

6. 응답 스트리밍
   └─> 토큰 단위로 Socket.IO를 통해 전송
   └─> Frontend에서 실시간 렌더링

7. 대화 저장
   └─> Conversation Store에 저장
   └─> 세션 ID로 관리
```

---

## 3. 모듈 설계

### 3.1 Backend 디렉토리 구조

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 앱 진입점
│   ├── config.py                  # 환경변수 및 설정 (재활용)
│   ├── bedrock_client.py          # AWS Bedrock 클라이언트 (재활용/개선)
│   ├── conversation_store.py      # 대화 저장소 (재활용)
│   ├── mcp_manager.py             # MCP 통합 (재활용)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py                # 채팅 API 엔드포인트
│   │   ├── documents.py           # 문서 관리 API
│   │   └── websocket.py           # Socket.IO 핸들러
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_loader.py     # 문서 로딩 및 파싱
│   │   ├── embeddings.py          # 임베딩 생성
│   │   ├── s3_vector_store.py     # S3 벡터 저장소
│   │   ├── retriever.py           # 문서 검색
│   │   └── chain.py               # RAG 체인 구성
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # 로깅 유틸리티
│       └── validators.py          # 입력 검증
│
├── tests/
│   ├── test_rag.py
│   ├── test_api.py
│   └── test_bedrock.py
│
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

### 3.2 Frontend 디렉토리 구조

```
frontend/
├── src/
│   ├── main.tsx                   # 앱 진입점
│   ├── App.tsx                    # 루트 컴포넌트
│   │
│   ├── components/
│   │   ├── ChatContainer.tsx      # 채팅 컨테이너
│   │   ├── MessageList.tsx        # 메시지 목록
│   │   ├── MessageItem.tsx        # 개별 메시지
│   │   ├── MessageInput.tsx       # 입력창
│   │   ├── TypingIndicator.tsx   # 타이핑 인디케이터
│   │   └── ConnectionStatus.tsx  # 연결 상태
│   │
│   ├── hooks/
│   │   ├── useSocket.ts           # Socket.IO 훅
│   │   ├── useChat.ts             # 채팅 로직 훅
│   │   └── useMessages.ts         # 메시지 관리 훅
│   │
│   ├── store/
│   │   ├── chatStore.ts           # 채팅 상태 (Zustand)
│   │   └── uiStore.ts             # UI 상태
│   │
│   ├── api/
│   │   ├── socket.ts              # Socket.IO 클라이언트
│   │   └── http.ts                # HTTP 클라이언트
│   │
│   ├── types/
│   │   ├── message.ts             # 메시지 타입
│   │   └── chat.ts                # 채팅 타입
│   │
│   └── styles/
│       └── globals.css            # TailwindCSS 설정
│
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

---

## 4. API 설계

### 4.1 REST API

#### 4.1.1 Health Check
```
GET /api/health
```
**응답**:
```json
{
  "status": "ok",
  "timestamp": "2026-02-03T15:30:00Z"
}
```

#### 4.1.2 문서 목록 조회 (선택)
```
GET /api/documents
```
**응답**:
```json
{
  "documents": [
    {
      "id": "doc_001",
      "filename": "user_manual.pdf",
      "uploaded_at": "2026-02-01T10:00:00Z",
      "chunks": 45
    }
  ]
}
```

#### 4.1.3 문서 업로드 (선택)
```
POST /api/documents/upload
Content-Type: multipart/form-data
```
**요청**:
```
file: <binary>
```
**응답**:
```json
{
  "id": "doc_002",
  "filename": "policy.pdf",
  "status": "processing"
}
```

### 4.2 WebSocket API (Socket.IO)

#### 4.2.1 연결
```javascript
// Client
const socket = io('http://localhost:8000');

socket.on('connect', () => {
  console.log('Connected:', socket.id);
});
```

#### 4.2.2 메시지 전송
```javascript
// Client → Server
socket.emit('chat_message', {
  session_id: 'session_123',
  message: '사용자 매뉴얼은 어디서 찾을 수 있나요?',
  timestamp: '2026-02-03T15:30:00Z'
});
```

#### 4.2.3 스트리밍 응답 수신
```javascript
// Server → Client (스트리밍)
socket.on('chat_response_chunk', (data) => {
  console.log('Chunk:', data.content);
  // data = {
  //   session_id: 'session_123',
  //   content: '사용자 ',
  //   is_final: false
  // }
});

socket.on('chat_response_complete', (data) => {
  console.log('Complete:', data);
  // data = {
  //   session_id: 'session_123',
  //   message_id: 'msg_456',
  //   sources: [
  //     {
  //       document: 'user_manual.pdf',
  //       page: 5,
  //       similarity: 0.92
  //     }
  //   ]
  // }
});
```

#### 4.2.4 에러 처리
```javascript
socket.on('chat_error', (error) => {
  console.error('Error:', error);
  // error = {
  //   session_id: 'session_123',
  //   code: 'BEDROCK_ERROR',
  //   message: 'Failed to generate response'
  // }
});
```

---

## 5. 데이터 모델

### 5.1 Message
```typescript
interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
}
```

### 5.2 Source
```typescript
interface Source {
  document: string;
  page?: number;
  chunk_id: string;
  similarity: number;
  content: string;
}
```

### 5.3 Document
```typescript
interface Document {
  id: string;
  filename: string;
  file_type: 'pdf' | 'docx' | 'md' | 'txt';
  uploaded_at: string;
  chunks: number;
  metadata: {
    size: number;
    pages?: number;
  };
}
```

### 5.4 VectorChunk (S3 저장 형식)
```json
{
  "chunk_id": "doc_001_chunk_003",
  "document_id": "doc_001",
  "content": "사용자 매뉴얼의 3장에서는...",
  "embedding": [0.123, -0.456, 0.789, ...],
  "metadata": {
    "filename": "user_manual.pdf",
    "page": 5,
    "section": "3. 시작하기",
    "chunk_index": 3
  }
}
```

---

## 6. 핵심 알고리즘

### 6.1 문서 청킹 전략

```python
def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    문서를 오버랩이 있는 청크로 분할
    
    Args:
        text: 원본 텍스트
        chunk_size: 청크 크기 (토큰 수)
        overlap: 오버랩 크기 (토큰 수)
    
    Returns:
        청크 리스트
    """
    # RecursiveCharacterTextSplitter 사용
    # 문장 경계를 고려한 분할
    # 메타데이터 보존
    pass
```

### 6.2 유사도 검색

```python
def search_similar_chunks(
    query_embedding: List[float],
    vector_store: S3VectorStore,
    top_k: int = 5,
    min_similarity: float = 0.7
) -> List[VectorChunk]:
    """
    코사인 유사도 기반 검색
    
    Args:
        query_embedding: 질문 임베딩
        vector_store: S3 벡터 저장소
        top_k: 반환할 최대 결과 수
        min_similarity: 최소 유사도 임계값
    
    Returns:
        유사한 청크 리스트
    """
    # 1. S3에서 모든 벡터 로드
    # 2. 코사인 유사도 계산
    # 3. 정렬 및 필터링
    # 4. Top-K 반환
    pass
```

### 6.3 RAG 프롬프트 구성

```python
def build_rag_prompt(
    query: str,
    context_chunks: List[VectorChunk],
    conversation_history: List[Message]
) -> str:
    """
    RAG 프롬프트 생성
    
    Args:
        query: 사용자 질문
        context_chunks: 검색된 문서 청크
        conversation_history: 대화 히스토리
    
    Returns:
        완성된 프롬프트
    """
    prompt = f"""당신은 사내 문서를 기반으로 질문에 답변하는 AI 어시스턴트입니다.

다음 문서들을 참고하여 질문에 답변해주세요:

"""
    
    for i, chunk in enumerate(context_chunks, 1):
        prompt += f"""
[문서 {i}] {chunk.metadata['filename']} (페이지 {chunk.metadata.get('page', 'N/A')})
{chunk.content}
---
"""
    
    if conversation_history:
        prompt += "\n이전 대화:\n"
        for msg in conversation_history[-3:]:  # 최근 3개만
            prompt += f"{msg.role}: {msg.content}\n"
    
    prompt += f"\n질문: {query}\n\n답변:"
    
    return prompt
```

---

## 7. 기술 스택 상세

### 7.1 Backend 의존성

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-socketio==5.11.0
python-multipart==0.0.12

# LangChain
langchain==0.3.0
langchain-aws==0.2.0
langgraph==0.2.0

# AWS
boto3==1.35.0
botocore==1.35.0

# Vector & ML
numpy==2.1.0
scikit-learn==1.5.0

# Document Processing
pypdf==5.0.0
python-docx==1.1.0
markdown==3.7.0

# Utils
pydantic==2.9.0
python-dotenv==1.0.0
```

### 7.2 Frontend 의존성

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@tanstack/react-query": "^5.62.8",
    "zustand": "^5.0.2",
    "socket.io-client": "^4.8.1",
    "lucide-react": "^0.468.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "tailwindcss": "^3.4.17",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49"
  }
}
```

---

## 8. 환경 설정

### 8.1 환경변수 (.env)

```bash
# AWS 인증
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# AWS Bedrock
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_EMBEDDINGS_MODEL_ID=amazon.titan-embed-text-v2:0

# S3 Vector Store
S3_BUCKET_NAME=your-vector-bucket
S3_VECTOR_PREFIX=vectors/
S3_METADATA_PREFIX=metadata/

# 서버 설정
BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_HOST=0.0.0.0

# RAG 설정
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K_RESULTS=5
MIN_SIMILARITY=0.7

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=json

# MCP (선택)
MCP_ENABLED=false
MCP_SERVER_URL=
```

---

## 9. Docker 구성

### 9.1 Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY src/ ./src/

# 문서 디렉토리
VOLUME /app/documents

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 9.2 Frontend Dockerfile

```dockerfile
FROM node:22.11-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci

# 소스 코드
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 9.3 docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - ./backend/src:/app/src
      - ./documents:/app/documents
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "${FRONTEND_PORT:-5173}:5173"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - VITE_BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  documents:
```

---

## 10. 보안 고려사항

### 10.1 인증 및 권한
- AWS IAM 역할 기반 접근 제어
- 환경변수를 통한 민감 정보 관리
- `.env` 파일 `.gitignore`에 추가

### 10.2 API 보안
- CORS 설정 (허용된 오리진만)
- Rate Limiting (요청 제한)
- 입력 검증 (Pydantic 모델)

### 10.3 데이터 보안
- S3 버킷 암호화 (SSE-S3 또는 SSE-KMS)
- 전송 중 암호화 (HTTPS/WSS)
- 민감 정보 마스킹 (로그)

---

## 11. 성능 최적화

### 11.1 벡터 검색 최적화
- **인덱싱**: S3에 인덱스 파일 생성 (빠른 로드)
- **캐싱**: 자주 사용되는 벡터 메모리 캐시
- **배치 처리**: 여러 문서 동시 임베딩

### 11.2 LLM 호출 최적화
- **스트리밍**: 토큰 단위 응답으로 체감 속도 향상
- **컨텍스트 압축**: 불필요한 정보 제거
- **프롬프트 최적화**: 토큰 수 최소화

### 11.3 Frontend 최적화
- **코드 스플리팅**: Vite 자동 처리
- **가상 스크롤**: 대량 메시지 렌더링
- **메모이제이션**: React.memo, useMemo 활용

---

## 12. 에러 처리

### 12.1 Backend 에러 처리

```python
class RAGException(Exception):
    """RAG 관련 기본 예외"""
    pass

class DocumentLoadError(RAGException):
    """문서 로딩 실패"""
    pass

class EmbeddingError(RAGException):
    """임베딩 생성 실패"""
    pass

class BedrockError(RAGException):
    """Bedrock API 호출 실패"""
    pass

class S3Error(RAGException):
    """S3 작업 실패"""
    pass
```

### 12.2 에러 응답 형식

```json
{
  "error": {
    "code": "BEDROCK_ERROR",
    "message": "Failed to generate response",
    "details": "Rate limit exceeded",
    "timestamp": "2026-02-03T15:30:00Z"
  }
}
```

### 12.3 Frontend 에러 처리

```typescript
// 에러 타입 정의
type ErrorType = 
  | 'NETWORK_ERROR'
  | 'BEDROCK_ERROR'
  | 'VALIDATION_ERROR'
  | 'UNKNOWN_ERROR';

interface ChatError {
  type: ErrorType;
  message: string;
  retryable: boolean;
}

// 에러 핸들러
function handleChatError(error: ChatError) {
  if (error.retryable) {
    // 재시도 로직
  } else {
    // 사용자에게 에러 표시
  }
}
```

---

## 13. 로깅 및 모니터링

### 13.1 로깅 전략

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# 사용 예시
logger = logging.getLogger(__name__)
logger.info("Document indexed", extra={
    "document_id": "doc_001",
    "chunks": 45,
    "duration_ms": 1234
})
```

### 13.2 모니터링 메트릭

- **요청 메트릭**:
  - 총 요청 수
  - 평균 응답 시간
  - 에러율

- **RAG 메트릭**:
  - 문서 검색 시간
  - 임베딩 생성 시간
  - LLM 응답 시간

- **시스템 메트릭**:
  - CPU 사용률
  - 메모리 사용률
  - 네트워크 I/O

---

## 14. 테스트 전략

### 14.1 Backend 테스트

#### Unit Tests
```python
# tests/test_rag.py
def test_document_chunking():
    """문서 청킹 테스트"""
    text = "..." * 1000
    chunks = chunk_document(text, chunk_size=500, overlap=50)
    assert len(chunks) > 0
    assert all(len(chunk) <= 500 for chunk in chunks)

def test_similarity_search():
    """유사도 검색 테스트"""
    query_embedding = [0.1, 0.2, 0.3]
    results = search_similar_chunks(query_embedding, mock_store)
    assert len(results) <= 5
    assert all(r.similarity >= 0.7 for r in results)
```

#### Integration Tests
```python
# tests/test_api.py
def test_chat_endpoint():
    """채팅 API 통합 테스트"""
    response = client.post("/api/chat", json={
        "session_id": "test_session",
        "message": "테스트 질문"
    })
    assert response.status_code == 200
```

### 14.2 Frontend 테스트

#### Component Tests
```typescript
// tests/MessageItem.test.tsx
describe('MessageItem', () => {
  it('renders user message correctly', () => {
    const message = {
      id: '1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date().toISOString()
    };
    render(<MessageItem message={message} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

#### E2E Tests (선택)
- Playwright 또는 Cypress 사용
- 전체 채팅 플로우 테스트

---

## 15. 배포 전략

### 15.1 개발 환경
```bash
# 로컬 개발
docker-compose up --build

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 15.2 프로덕션 환경
- **Frontend**: Nginx로 정적 파일 서빙
- **Backend**: Gunicorn + Uvicorn workers
- **로드 밸런싱**: AWS ALB
- **오토 스케일링**: ECS 또는 EKS

---

## 16. 확장 계획

### 16.1 Phase 2 기능
- 다중 사용자 지원 (세션 관리)
- 대화 히스토리 영구 저장 (DynamoDB)
- 문서 업로드 UI
- 출처 하이라이팅

### 16.2 Phase 3 기능
- MCP 서버 통합 (AWS Docs 등)
- 고급 검색 필터 (날짜, 문서 타입)
- 사용자 피드백 수집
- A/B 테스트 프레임워크

### 16.3 기술 부채 관리
- 벡터 DB 마이그레이션 (S3 → Pinecone/Weaviate)
- 캐싱 레이어 추가 (Redis)
- API 버전 관리
- 문서 자동화

---

## 17. 정확성 속성 (Correctness Properties)

이 섹션은 시스템이 올바르게 동작하는지 검증하기 위한 속성들을 정의합니다. 각 속성은 Property-Based Testing을 통해 검증됩니다.

### 17.1 문서 처리 속성

**Property 1.1: 청킹 일관성**
- **설명**: 문서를 청킹한 후 모든 청크를 합치면 원본 텍스트와 동일해야 함 (오버랩 제외)
- **검증**: 
  ```python
  def test_chunking_preserves_content(text: str):
      chunks = chunk_document(text)
      reconstructed = "".join(remove_overlap(chunks))
      assert reconstructed == text
  ```
- **요구사항 링크**: 2.1.1, 2.1.2

**Property 1.2: 청크 크기 제약**
- **설명**: 모든 청크는 설정된 최대 크기를 초과하지 않아야 함
- **검증**:
  ```python
  def test_chunk_size_constraint(text: str, max_size: int):
      chunks = chunk_document(text, chunk_size=max_size)
      assert all(len(chunk) <= max_size for chunk in chunks)
  ```
- **요구사항 링크**: 2.1.2

### 17.2 벡터 검색 속성

**Property 2.1: 검색 결과 정렬**
- **설명**: 검색 결과는 유사도 점수 내림차순으로 정렬되어야 함
- **검증**:
  ```python
  def test_search_results_sorted(query_embedding: List[float]):
      results = search_similar_chunks(query_embedding, vector_store)
      similarities = [r.similarity for r in results]
      assert similarities == sorted(similarities, reverse=True)
  ```
- **요구사항 링크**: 2.1.3

**Property 2.2: 최소 유사도 필터링**
- **설명**: 모든 검색 결과는 최소 유사도 임계값 이상이어야 함
- **검증**:
  ```python
  def test_minimum_similarity_threshold(query_embedding: List[float], min_sim: float):
      results = search_similar_chunks(query_embedding, vector_store, min_similarity=min_sim)
      assert all(r.similarity >= min_sim for r in results)
  ```
- **요구사항 링크**: 2.1.3

**Property 2.3: Top-K 제약**
- **설명**: 검색 결과는 요청한 K개 이하여야 함
- **검증**:
  ```python
  def test_top_k_constraint(query_embedding: List[float], k: int):
      results = search_similar_chunks(query_embedding, vector_store, top_k=k)
      assert len(results) <= k
  ```
- **요구사항 링크**: 2.1.3

### 17.3 API 속성

**Property 3.1: 메시지 ID 유일성**
- **설명**: 생성된 모든 메시지 ID는 유일해야 함
- **검증**:
  ```python
  def test_message_id_uniqueness(messages: List[Message]):
      ids = [msg.id for msg in messages]
      assert len(ids) == len(set(ids))
  ```
- **요구사항 링크**: 2.2.4

**Property 3.2: 타임스탬프 순서**
- **설명**: 대화 히스토리의 메시지는 타임스탬프 순서대로 정렬되어야 함
- **검증**:
  ```python
  def test_conversation_timestamp_order(conversation: List[Message]):
      timestamps = [msg.timestamp for msg in conversation]
      assert timestamps == sorted(timestamps)
  ```
- **요구사항 링크**: 2.2.4

### 17.4 RAG 파이프라인 속성

**Property 4.1: 출처 추적 가능성**
- **설명**: AI 응답에 포함된 모든 출처는 실제 문서에 존재해야 함
- **검증**:
  ```python
  def test_source_traceability(response: Message, document_store: DocumentStore):
      for source in response.sources:
          assert document_store.exists(source.document)
          assert document_store.has_chunk(source.chunk_id)
  ```
- **요구사항 링크**: 2.1.4

**Property 4.2: 컨텍스트 포함**
- **설명**: RAG 프롬프트는 검색된 모든 문서 청크를 포함해야 함
- **검증**:
  ```python
  def test_context_inclusion(query: str, chunks: List[VectorChunk]):
      prompt = build_rag_prompt(query, chunks, [])
      for chunk in chunks:
          assert chunk.content in prompt
  ```
- **요구사항 링크**: 2.1.4

### 17.5 에러 처리 속성

**Property 5.1: 에러 응답 형식**
- **설명**: 모든 에러 응답은 정의된 형식을 따라야 함
- **검증**:
  ```python
  def test_error_response_format(error_response: dict):
      assert "error" in error_response
      assert "code" in error_response["error"]
      assert "message" in error_response["error"]
      assert "timestamp" in error_response["error"]
  ```
- **요구사항 링크**: 12.2

**Property 5.2: 재시도 가능 에러 분류**
- **설명**: 네트워크 에러는 재시도 가능으로 표시되어야 함
- **검증**:
  ```python
  def test_retryable_error_classification(error: ChatError):
      if error.type == 'NETWORK_ERROR':
          assert error.retryable == True
  ```
- **요구사항 링크**: 12.3

---

## 18. 테스트 프레임워크

### 18.1 Property-Based Testing 설정

**Backend (Python)**
```python
# pytest + hypothesis
import hypothesis
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=100, max_size=10000),
    chunk_size=st.integers(min_value=100, max_value=2000)
)
def test_chunking_property(text: str, chunk_size: int):
    chunks = chunk_document(text, chunk_size=chunk_size)
    # Property assertions
    assert len(chunks) > 0
    assert all(len(chunk) <= chunk_size for chunk in chunks)
```

**Frontend (TypeScript)**
```typescript
// fast-check
import fc from 'fast-check';

describe('Message Properties', () => {
  it('should maintain message ID uniqueness', () => {
    fc.assert(
      fc.property(
        fc.array(messageArbitrary(), { minLength: 1, maxLength: 100 }),
        (messages) => {
          const ids = messages.map(m => m.id);
          return new Set(ids).size === ids.length;
        }
      )
    );
  });
});
```

### 18.2 테스트 실행

```bash
# Backend PBT
pytest tests/ -v --hypothesis-show-statistics

# Frontend PBT
npm run test:pbt
```

---

## 19. 참고 문서

### 19.1 기술 문서
- [LangChain Documentation](https://python.langchain.com/)
- [AWS Bedrock API Reference](https://docs.aws.amazon.com/bedrock/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Socket.IO Documentation](https://socket.io/docs/)

### 19.2 관련 프로젝트
- ai-agent-demo: `C:\Users\superuser\git\ai-agent-demo`

---

## 20. 용어 정의

- **RAG**: Retrieval-Augmented Generation, 검색 증강 생성
- **Embedding**: 텍스트를 고차원 벡터로 변환한 것
- **Chunk**: 문서를 분할한 작은 단위
- **Top-K**: 상위 K개의 결과
- **Cosine Similarity**: 코사인 유사도, 벡터 간 유사성 측정
- **Streaming**: 데이터를 조각내어 순차적으로 전송
- **MCP**: Model Context Protocol, 모델 컨텍스트 프로토콜
