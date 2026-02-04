# 개발자 가이드

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     사용자 브라우저                           │
│                   (React + Vite UI)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket / HTTP
┌────────────────────────▼────────────────────────────────────┐
│                  Frontend Container                          │
│                 (Node.js 22 Alpine)                          │
│  - React 18 + TypeScript                                     │
│  - Socket.IO Client                                          │
│  - Zustand (상태 관리)                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Backend Container                           │
│                 (Python 3.12 Slim)                           │
│  - FastAPI + Socket.IO                                       │
│  - Bedrock Knowledge Base 연동                               │
│  - SQLite (대화 히스토리)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      AWS Cloud                               │
│  - Bedrock Knowledge Base (문서 검색 + 답변 생성)             │
│  - S3 (문서 저장소)                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Backend 구조

### 디렉토리 구조

```
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py          # REST API 엔드포인트
│   │   └── websocket.py     # Socket.IO 이벤트 핸들러
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      # SQLite 데이터베이스
│   ├── rag/
│   │   ├── __init__.py
│   │   └── knowledge_base.py # Bedrock KB 클라이언트
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py        # 로깅 유틸리티
│   ├── __init__.py
│   ├── bedrock_client.py    # Bedrock 클라이언트
│   ├── config.py            # 환경변수 설정
│   ├── conversation_store.py # 대화 저장소 (메모리)
│   ├── main.py              # 앱 진입점
│   └── mcp_manager.py       # MCP 매니저
├── tests/
├── Dockerfile
└── requirements.txt
```

### 주요 모듈

#### 1. main.py
FastAPI 앱과 Socket.IO 서버를 초기화합니다.

```python
# FastAPI 앱 생성
app = FastAPI(title="RAG 챗봇 API")

# Socket.IO 서버 생성
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)
```

#### 2. rag/knowledge_base.py
Bedrock Knowledge Base와 통신합니다.

```python
class KnowledgeBaseClient:
    def __init__(self):
        self.client = boto3.client('bedrock-agent-runtime')
        self.knowledge_base_id = settings.KNOWLEDGE_BASE_ID
    
    async def retrieve_and_generate(self, query: str, session_id: str):
        # Knowledge Base에서 검색 + 답변 생성
        pass
```

#### 3. db/database.py
SQLite로 대화 히스토리를 관리합니다.

```python
def save_message(session_id: str, role: str, content: str):
    # 메시지 저장
    pass

def get_history(session_id: str) -> List[dict]:
    # 히스토리 조회
    pass
```

---

## Frontend 구조

### 디렉토리 구조

```
frontend/
├── src/
│   ├── api/
│   │   ├── http.ts          # HTTP 클라이언트
│   │   └── socket.ts        # Socket.IO 클라이언트
│   ├── components/
│   │   ├── ChatContainer.tsx
│   │   ├── ConnectionStatus.tsx
│   │   ├── MessageInput.tsx
│   │   ├── MessageItem.tsx
│   │   ├── MessageList.tsx
│   │   └── TypingIndicator.tsx
│   ├── hooks/
│   │   ├── useChat.ts       # 채팅 로직
│   │   ├── useMessages.ts   # 메시지 관리
│   │   └── useSocket.ts     # Socket.IO 연결
│   ├── store/
│   │   ├── chatStore.ts     # 채팅 상태
│   │   └── uiStore.ts       # UI 상태
│   ├── types/
│   │   ├── chat.ts
│   │   └── message.ts
│   ├── styles/
│   │   └── globals.css
│   ├── App.tsx
│   └── main.tsx
├── Dockerfile
├── package.json
└── vite.config.ts
```

### 상태 관리 (Zustand)

```typescript
// store/chatStore.ts
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  sessionId: generateSessionId(),
  // ...
}));
```

### Socket.IO 연결

```typescript
// hooks/useSocket.ts
export function useSocket() {
  useEffect(() => {
    socket.on('chat_response_chunk', handleChunk);
    socket.on('chat_response_complete', handleComplete);
    socket.on('chat_error', handleError);
    
    return () => {
      socket.off('chat_response_chunk');
      // ...
    };
  }, []);
}
```

---

## 데이터 흐름

### 채팅 메시지 처리

```
1. 사용자가 메시지 입력
   └─> MessageInput.tsx

2. Socket.IO로 메시지 전송
   └─> socket.emit('chat_message', {...})

3. Backend에서 메시지 수신
   └─> websocket.py: handle_chat_message()

4. Knowledge Base 검색 + 답변 생성
   └─> knowledge_base.py: retrieve_and_generate()

5. 스트리밍 응답 전송
   └─> socket.emit('chat_response_chunk', {...})

6. Frontend에서 실시간 렌더링
   └─> MessageItem.tsx 업데이트

7. 응답 완료
   └─> socket.emit('chat_response_complete', {...})

8. DB에 저장
   └─> database.py: save_message()
```

---

## 개발 환경 설정

### Docker 개발 (권장)

```bash
# 컨테이너 빌드 및 실행
docker compose up --build

# 로그 확인
docker compose logs -f backend
docker compose logs -f frontend

# 컨테이너 재시작
docker compose restart backend
```

### 로컬 개발 (선택)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경변수 설정
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export KNOWLEDGE_BASE_ID=your_kb_id

# 서버 실행
uvicorn src.main:socket_app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 테스트

### Docker 테스트

```bash
./scripts/test-docker.sh
```

### API 테스트

```bash
# Health Check
curl http://localhost:8000/api/health

# 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "안녕하세요"}'
```

---

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | O |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | O |
| `AWS_REGION` | AWS 리전 | O |
| `KNOWLEDGE_BASE_ID` | Bedrock KB ID | O |
| `BEDROCK_MODEL_ARN` | Bedrock 모델 ARN | O |
| `DB_PATH` | SQLite DB 경로 | X |
| `LOG_LEVEL` | 로그 레벨 | X |

---

## 코드 스타일

### Python
- Black 포매터 사용
- isort로 import 정렬
- Type hints 필수

### TypeScript
- ESLint + Prettier
- 함수형 컴포넌트 사용
- 타입 정의 필수

---

## 트러블슈팅

### Socket.IO 연결 실패

```
원인: CORS 설정 또는 네트워크 문제
해결: 
1. Backend CORS 설정 확인
2. Frontend의 VITE_BACKEND_URL 확인
3. Docker 네트워크 확인
```

### Knowledge Base 오류

```
원인: AWS 인증 또는 KB 설정 문제
해결:
1. AWS 자격 증명 확인
2. KNOWLEDGE_BASE_ID 확인
3. IAM 권한 확인 (bedrock:Retrieve, bedrock:RetrieveAndGenerate)
```

### SQLite 오류

```
원인: 파일 권한 또는 경로 문제
해결:
1. data/ 디렉토리 권한 확인
2. Docker 볼륨 마운트 확인
```

---

## 기여 가이드

1. 이슈 생성 또는 기존 이슈 확인
2. 브랜치 생성: `feature/기능명` 또는 `fix/버그명`
3. 코드 작성 및 테스트
4. PR 생성
5. 코드 리뷰 후 머지
