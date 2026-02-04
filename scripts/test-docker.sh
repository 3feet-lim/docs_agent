#!/bin/bash
# RAG 챗봇 시스템 Docker 통합 테스트
# 사용법: ./scripts/test-docker.sh

set -e

echo "=========================================="
echo "RAG 챗봇 시스템 Docker 테스트"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

run_test() {
    local name=$1
    local command=$2
    
    echo -n "테스트: $name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
        echo "  상세:"
        eval "$command" 2>&1 | head -20
        return 1
    fi
}

cleanup() {
    echo ""
    echo "정리 중..."
    docker-compose down --remove-orphans 2>/dev/null || true
}

trap cleanup EXIT

# 1. 환경 확인
echo ""
echo "1. 환경 확인"
echo "----------------------------------------"
docker --version
docker-compose --version

# 2. .env 파일 확인
echo ""
echo "2. 환경 설정"
echo "----------------------------------------"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env 파일이 없습니다. .env.example을 복사합니다.${NC}"
    cp .env.example .env
fi

# data 디렉토리 생성
mkdir -p data

# 3. Docker 이미지 빌드
echo ""
echo "3. Docker 이미지 빌드"
echo "----------------------------------------"
run_test "Backend 이미지 빌드" "docker-compose build backend"
run_test "Frontend 이미지 빌드" "docker-compose build frontend"

# 4. 컨테이너 시작
echo ""
echo "4. 컨테이너 시작"
echo "----------------------------------------"
docker-compose up -d

echo "서버 시작 대기 중 (15초)..."
sleep 15

# 컨테이너 상태 확인
echo ""
docker-compose ps

# 5. API 테스트
echo ""
echo "5. API 테스트"
echo "----------------------------------------"

# Health check
run_test "Backend Health Check" "curl -sf http://localhost:8000/api/health"

# Root endpoint
run_test "Root Endpoint" "curl -sf http://localhost:8000/"

# Chat API 테스트
echo -n "테스트: Chat API ... "
CHAT_RESPONSE=$(curl -sf -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "테스트 메시지입니다"}' 2>&1)

if echo "$CHAT_RESPONSE" | grep -q "session_id"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
    echo "  응답: $CHAT_RESPONSE"
fi

# 세션 목록 조회
run_test "세션 목록 API" "curl -sf http://localhost:8000/api/sessions"

# Frontend 접속
run_test "Frontend 접속" "curl -sf http://localhost:5173"

# 6. 로그 확인
echo ""
echo "6. 컨테이너 로그"
echo "----------------------------------------"
echo "=== Backend 로그 (최근 30줄) ==="
docker-compose logs --tail=30 backend

echo ""
echo "=== Frontend 로그 (최근 10줄) ==="
docker-compose logs --tail=10 frontend

# 7. 결과 출력
echo ""
echo "=========================================="
echo "테스트 결과"
echo "=========================================="
echo -e "통과: ${GREEN}$PASSED${NC}"
echo -e "실패: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}모든 테스트 통과!${NC}"
else
    echo -e "\n${RED}일부 테스트 실패${NC}"
fi

echo ""
echo "컨테이너가 종료됩니다..."
