# RAG 챗봇 API 문서

## 개요

이 문서는 RAG 챗봇 시스템의 REST API와 WebSocket 이벤트를 설명합니다.

- **Base URL**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000/socket.io`

---

## REST API

### 1. Health Check

서버 상태를 확인합니다.

```
GET /api/health
```

**응답 예시**:
```json
{
  "status": "ok",
  "timestamp": "2026-02-04T10:30:00Z"
}
```

---

### 2. 채팅 메시지 전송

RAG 기반 답변을 요청합니다.

```
POST /api/chat
Content-Type: application/json
```

**요청 본문**:
```json
{
  "session_id": "session_123",
  "message": "사용자 매뉴얼은 어디서 찾을 수 있나요?"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `session_id` | string | 예 | 세션 식별자 |
| `message` | string | 예 | 사용자 메시지 |

**응답 예시**:
```json
{
  "session_id": "session_123",
  "message_id": "msg_456",
  "response": "사용자 매뉴얼은 문서 포털에서 확인하실 수 있습니다...",
  "sources": [
    {
      "title": "사용자 가이드",
      "uri": "s3://bucket/docs/user-guide.pdf",
      "score": 0.92
    }
  ],
  "timestamp": "2026-02-04T10:30:00Z"
}
```

---

### 3. 세션 목록 조회

저장된 모든 세션 목록을 조회합니다.

```
GET /api/sessions
```

**응답 예시**:
```json
{
  "sessions": [
    {
      "session_id": "session_123",
      "message_count": 10,
      "created_at": "2026-02-04T09:00:00Z",
      "updated_at": "2026-02-04T10:30:00Z"
    }
  ]
}
```

---

### 4. 대화 히스토리 조회

특정 세션의 대화 내역을 조회합니다.

```
GET /api/chat/{session_id}/history
```

**경로 파라미터**:
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `session_id` | string | 세션 식별자 |

**응답 예시**:
```json
{
  "session_id": "session_123",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "안녕하세요",
      "timestamp": "2026-02-04T10:00:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "안녕하세요! 무엇을 도와드릴까요?",
      "timestamp": "2026-02-04T10:00:01Z",
      "sources": []
    }
  ]
}
```

---

### 5. 대화 히스토리 삭제

특정 세션의 대화 내역을 삭제합니다.

```
DELETE /api/chat/{session_id}
```

**응답 예시**:
```json
{
  "success": true,
  "message": "세션이 삭제되었습니다"
}
```

---

## WebSocket API (Socket.IO)

### 연결

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8000', {
  transports: ['websocket']
});

socket.on('connect', () => {
  console.log('연결됨:', socket.id);
});

socket.on('disconnect', () => {
  console.log('연결 해제됨');
});
```

---

### 이벤트

#### 1. chat_message (Client → Server)

채팅 메시지를 서버로 전송합니다.

```javascript
socket.emit('chat_message', {
  session_id: 'session_123',
  message: '질문 내용',
  timestamp: new Date().toISOString()
});
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 식별자 |
| `message` | string | 사용자 메시지 |
| `timestamp` | string | ISO 8601 형식 타임스탬프 |

---

#### 2. chat_response_chunk (Server → Client)

스트리밍 응답의 각 청크를 수신합니다.

```javascript
socket.on('chat_response_chunk', (data) => {
  console.log('청크:', data.content);
  // UI에 실시간으로 텍스트 추가
});
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 식별자 |
| `content` | string | 응답 텍스트 청크 |
| `is_final` | boolean | 마지막 청크 여부 |

---

#### 3. chat_response_complete (Server → Client)

응답 생성이 완료되었음을 알립니다.

```javascript
socket.on('chat_response_complete', (data) => {
  console.log('완료:', data);
  // 출처 정보 표시
});
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 식별자 |
| `message_id` | string | 메시지 ID |
| `sources` | array | 참조 문서 목록 |

---

#### 4. chat_error (Server → Client)

에러 발생 시 수신합니다.

```javascript
socket.on('chat_error', (error) => {
  console.error('에러:', error);
  // 에러 메시지 표시
});
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 식별자 |
| `code` | string | 에러 코드 |
| `message` | string | 에러 메시지 |

---

## 에러 코드

| 코드 | 설명 | HTTP 상태 |
|------|------|-----------|
| `VALIDATION_ERROR` | 요청 데이터 검증 실패 | 400 |
| `SESSION_NOT_FOUND` | 세션을 찾을 수 없음 | 404 |
| `KNOWLEDGE_BASE_ERROR` | Knowledge Base 연동 오류 | 500 |
| `BEDROCK_ERROR` | Bedrock API 호출 실패 | 500 |
| `INTERNAL_ERROR` | 내부 서버 오류 | 500 |

---

## 데이터 타입

### Message

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

### Source

```typescript
interface Source {
  title: string;
  uri: string;
  score: number;
}
```

### Session

```typescript
interface Session {
  session_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}
```

---

## 사용 예시

### Python (requests)

```python
import requests

# 채팅 메시지 전송
response = requests.post(
    'http://localhost:8000/api/chat',
    json={
        'session_id': 'my_session',
        'message': '안녕하세요'
    }
)
print(response.json())
```

### JavaScript (fetch)

```javascript
// 채팅 메시지 전송
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'my_session',
    message: '안녕하세요'
  })
});
const data = await response.json();
console.log(data);
```

### cURL

```bash
# Health Check
curl http://localhost:8000/api/health

# 채팅 메시지 전송
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "안녕하세요"}'

# 세션 목록 조회
curl http://localhost:8000/api/sessions

# 대화 히스토리 조회
curl http://localhost:8000/api/chat/test/history
```
