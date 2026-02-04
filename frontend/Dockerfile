# ===================================
# Frontend Dockerfile (멀티 스테이지 빌드)
# ===================================

# 1단계: 의존성 설치
FROM node:22-alpine AS deps

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY package.json ./
RUN npm install

# 2단계: 개발 서버 (개발용)
FROM node:22-alpine AS development

WORKDIR /app

# 의존성 복사
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 3단계: 빌드 (프로덕션용)
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# 4단계: 프로덕션 서버
FROM nginx:alpine AS production

# Nginx 설정
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA 라우팅을 위한 Nginx 설정
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
