# ===================================
# Backend Dockerfile (멀티 스테이지 빌드)
# ===================================

# 1단계: 빌드 스테이지
FROM python:3.12-slim AS builder

WORKDIR /app

# 시스템 의존성 (빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 2단계: 런타임 스테이지
FROM python:3.12-slim AS runtime

WORKDIR /app

# 런타임에 필요한 최소 패키지만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 빌드 스테이지에서 설치된 패키지 복사
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 소스 코드 복사
COPY src/ ./src/

# 데이터 디렉토리 생성
RUN mkdir -p /app/data

# 볼륨 설정
VOLUME ["/app/documents", "/app/data"]

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 실행 (개발 모드)
CMD ["uvicorn", "src.main:socket_app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
