# 테스트 스크립트 가이드

## 사용법

### 1. 스크립트 실행 권한 부여
```bash
chmod +x scripts/test-docker.sh
```

### 2. 테스트 실행
```bash
./scripts/test-docker.sh
```

## 테스트 내용

1. Docker 이미지 빌드 (Backend, Frontend)
2. 컨테이너 시작
3. API 테스트
   - Health Check (`GET /api/health`)
   - Chat API (`POST /api/chat`)
   - 세션 목록 (`GET /api/sessions`)
   - Frontend 접속
4. 로그 출력
5. 자동 정리 (컨테이너 종료)

## 수동 테스트

### 컨테이너 시작
```bash
cp .env.example .env
docker compose up -d
```

### API 테스트
```bash
# Health check
curl http://localhost:8000/api/health

# 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'

# 세션 목록
curl http://localhost:8000/api/sessions
```

### 로그 확인
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### 컨테이너 종료
```bash
docker compose down
```

## 예상 에러

### `port is already allocated`
```bash
docker compose down
# 또는 포트 변경: .env에서 BACKEND_PORT, FRONTEND_PORT 수정
```

### `Knowledge Base 초기화 실패`
- 정상 동작 (에코 모드로 폴백)
- Knowledge Base 연동하려면 `.env`에 `KNOWLEDGE_BASE_ID` 설정
