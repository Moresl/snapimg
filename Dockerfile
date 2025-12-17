# Stage 1: 前端构建
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY index.html vite.config.ts tsconfig*.json tailwind.config.js postcss.config.js ./
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build

# Stage 2: Python 依赖构建
FROM python:3.10-slim AS python-builder
WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    libjpeg-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY serve/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: 最终运行镜像
FROM python:3.10-slim
WORKDIR /app

# 只安装运行时依赖（不带 -dev）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    libpng16-16 \
    libjpeg62-turbo \
    libwebp7 \
    pngquant \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/*

# 从构建阶段复制虚拟环境
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY serve/app/ ./app/
COPY serve/main.py ./

# 复制前端构建产物
COPY --from=frontend-builder /app/dist/ /usr/share/nginx/html/

# 配置 nginx
RUN rm -f /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
