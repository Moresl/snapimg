


FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY index.html vite.config.ts tsconfig*.json tailwind.config.js postcss.config.js ./
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    libpng-dev \
    libjpeg-dev \
    libwebp-dev \
    pngquant \
    && rm -rf /var/lib/apt/lists/*
COPY serve/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY serve/app/ ./app/
COPY serve/main.py ./
COPY --from=frontend-builder /app/dist/ /usr/share/nginx/html/
RUN rm -f /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/app.conf
EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
