# RAG 챗봇 시스템

AWS Bedrock Knowledge Base를 활용한 사내 문서 기반 AI 챗봇 시스템입니다.

## 주요 기능

- 🔍 **RAG 기반 답변**: Bedrock Knowledge Base를 통한 문서 검색 및 답변 생성
- 💬 **실시간 채팅**: Socket.IO 기반 실시간 스트리밍 응답
- 📚 **대화 히스토리**: SQLite 기반 대화 내역 저장
- 🐳 **Docker 지원**: Docker Compose로 간편한 배포

## 기술 스택

### Backend
- Python 3.12
- FastAPI + Socket.IO
- AWS Bedrock (Knowledge Base)
- SQLite

### Frontend
- React 18 + TypeScript
- Vite
- TailwindCSS
- Socket.IO Client
- Zustand

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd docs_agent

# 환경변수 설정
cp .env.example .env
```

`.env` 파일을 편집하여 필요한 값을 설정합니다:

```bash
# AWS 인증 (필수)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Bedrock Knowledge Base (필수)
KNOWLEDGE_BASE_ID=your_knowledge_base_id
BEDROCK_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0
```

### 2. Docker로 실행

```bash
# 컨테이너 빌드 및 시작
docker compose up -d

# 로그 확인
docker compose logs -f
```

### 3. 접속

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## API 엔드포인트

### REST API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/chat` | 채팅 메시지 전송 |
| GET | `/api/sessions` | 세션 목록 조회 |
| GET | `/api/chat/{session_id}/history` | 대화 히스토리 조회 |
| DELETE | `/api/chat/{session_id}` | 대화 히스토리 삭제 |

### WebSocket 이벤트

| 이벤트 | 방향 | 설명 |
|--------|------|------|
| `chat_message` | Client → Server | 채팅 메시지 전송 |
| `chat_response_chunk` | Server → Client | 스트리밍 응답 청크 |
| `chat_response_complete` | Server → Client | 응답 완료 |
| `chat_error` | Server → Client | 에러 발생 |

## 프로젝트 구조

```
.
├── backend/
│   ├── src/
│   │   ├── api/          # API 엔드포인트
│   │   ├── db/           # 데이터베이스
│   │   ├── rag/          # Knowledge Base 연동
│   │   ├── utils/        # 유틸리티
│   │   ├── config.py     # 설정
│   │   └── main.py       # 앱 진입점
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # API 클라이언트
│   │   ├── components/   # React 컴포넌트
│   │   ├── hooks/        # Custom Hooks
│   │   ├── store/        # Zustand 스토어
│   │   └── types/        # TypeScript 타입
│   ├── Dockerfile
│   └── package.json
├── docs/                 # 문서
│   ├── API.md            # API 문서
│   └── DEVELOPER.md      # 개발자 가이드
├── scripts/              # 테스트 스크립트
├── docker-compose.yml
└── .env.example
```

## 문서

- [API 문서](docs/API.md) - REST API 및 WebSocket 이벤트 상세
- [개발자 가이드](docs/DEVELOPER.md) - 아키텍처 및 개발 환경 설정

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | - |
| `AWS_REGION` | AWS 리전 | us-east-1 |
| `KNOWLEDGE_BASE_ID` | Bedrock Knowledge Base ID | - |
| `BEDROCK_MODEL_ARN` | Bedrock 모델 ARN | - |
| `BACKEND_PORT` | Backend 포트 | 8000 |
| `FRONTEND_PORT` | Frontend 포트 | 5173 |
| `DB_PATH` | SQLite DB 경로 | data/chat_history.db |
| `LOG_LEVEL` | 로그 레벨 | INFO |

## Knowledge Base 설정

1. AWS 콘솔에서 Bedrock → Knowledge bases 이동
2. Create knowledge base 클릭
3. S3 데이터 소스 연결 (문서가 저장된 버킷)
4. Sync 실행
5. Knowledge Base ID를 `.env`에 설정

## 개발

### Backend 개발

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:socket_app --reload
```

### Frontend 개발

```bash
cd frontend
npm install
npm run dev
```

## 테스트

```bash
chmod +x scripts/test-docker.sh
./scripts/test-docker.sh
```

## 라이선스

MIT License
