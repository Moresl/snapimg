# 单镜像：Nginx + Python

# 阶段1: 构建前端
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY index.html vite.config.ts tsconfig*.json tailwind.config.js postcss.config.js ./
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build

# 阶段2: 最终镜像
FROM python:3.10-slim

WORKDIR /app

# 安装 nginx 和系统依赖
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    libpng-dev \
    libjpeg-dev \
    libwebp-dev \
    pngquant \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY serve/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY serve/app/ ./app/
COPY serve/main.py ./

# 复制前端构建产物
COPY --from=frontend-builder /app/dist/ /usr/share/nginx/html/

# 配置 nginx
RUN rm -f /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 配置 supervisord
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
