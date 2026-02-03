# RAG 챗봇 시스템

사내 문서를 학습하여 질문에 답변하는 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇 시스템입니다.

## 📋 개요

이 프로젝트는 AWS Bedrock Claude Sonnet 4.5를 활용하여 사내 문서 기반의 지능형 질의응답 시스템을 제공합니다.

### 주요 기능

- 📄 **문서 기반 답변**: PDF, DOCX, MD, TXT 형식의 문서를 학습하여 정확한 답변 제공
- 🔍 **의미 기반 검색**: 벡터 임베딩을 통한 유사도 기반 문서 검색
- 💬 **실시간 채팅**: Socket.IO를 통한 실시간 양방향 통신
- 🌊 **스트리밍 응답**: 토큰 단위 스트리밍으로 빠른 응답 체감
- 🐳 **Docker 지원**: 컨테이너 기반 배포 환경

## 🛠 기술 스택

### Frontend
- React 18.3.1 + TypeScript 5.7.2
- Vite 6.0.5
- TailwindCSS 3.4.17
- Socket.IO Client 4.8.1
- Zustand 5.0.2 (상태 관리)
- React Query 5.62.8 (서버 상태 관리)

### Backend
- Python 3.12
- FastAPI + Socket.IO
- LangChain + LangGraph
- AWS Bedrock (Claude Sonnet 4.5)
- AWS S3 (벡터 저장소)

### Infrastructure
- Docker + Docker Compose
- Node.js 22.11.0+

## 📁 프로젝트 구조

```
rag-chatbot/
├── backend/                 # Python FastAPI 서버
│   ├── src/
│   │   ├── api/            # API 엔드포인트
│   │   ├── rag/            # RAG 파이프라인
│   │   └── utils/          # 유틸리티
│   ├── tests/              # 테스트
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # React + Vite 앱
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   ├── hooks/          # React 훅
│   │   ├── store/          # Zustand 스토어
│   │   ├── api/            # API 클라이언트
│   │   └── types/          # TypeScript 타입
│   ├── Dockerfile
│   └── package.json
│
├── documents/              # RAG 학습용 문서
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 시작하기

### 사전 요구사항

- Docker & Docker Compose
- AWS 계정 및 Bedrock 접근 권한
- Node.js 22.11.0+ (로컬 개발 시)
- Python 3.12+ (로컬 개발 시)

### 환경 설정

1. 저장소 클론
```bash
git clone <repository-url>
cd rag-chatbot
```

2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 AWS 인증 정보 및 설정 입력
```

3. 문서 준비
```bash
# documents/ 디렉토리에 학습할 문서 추가
# 지원 형식: PDF, DOCX, MD, TXT
```

### Docker로 실행

```bash
# 전체 스택 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 로컬 개발

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔧 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 | - |
| `AWS_REGION` | AWS 리전 | `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock LLM 모델 ID | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `BEDROCK_EMBEDDINGS_MODEL_ID` | 임베딩 모델 ID | `amazon.titan-embed-text-v2:0` |
| `S3_BUCKET_NAME` | S3 버킷 이름 | - |
| `BACKEND_PORT` | Backend 포트 | `8000` |
| `FRONTEND_PORT` | Frontend 포트 | `5173` |
| `CHUNK_SIZE` | 문서 청크 크기 | `1000` |
| `CHUNK_OVERLAP` | 청크 오버랩 | `100` |
| `TOP_K_RESULTS` | 검색 결과 수 | `5` |
| `MIN_SIMILARITY` | 최소 유사도 | `0.7` |

## 📖 API 문서

### REST API

- `GET /api/health` - 서버 상태 확인
- `POST /api/chat` - 채팅 메시지 전송
- `GET /api/documents` - 문서 목록 조회 (선택)

### WebSocket (Socket.IO)

- `chat_message` - 메시지 전송
- `chat_response_chunk` - 스트리밍 응답 수신
- `chat_response_complete` - 응답 완료
- `chat_error` - 에러 수신

## 🧪 테스트

```bash
# Backend 테스트
cd backend
pytest tests/ -v

# Frontend 테스트
cd frontend
npm run test
```

## 📝 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 🤝 기여

프로젝트 개선을 위한 제안이나 버그 리포트는 이슈를 통해 제출해주세요.
