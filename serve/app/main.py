"""
图片压缩服务 - FastAPI
"""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.core.config import settings
from app.api import compress

app = FastAPI(
    title="图片压缩服务",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(compress.router, prefix="/api", tags=["压缩"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


STATIC_DIR = None
possible_paths = [
    Path(__file__).parent.parent / "static",
    Path("/app/static"),
]

for p in possible_paths:
    if p.exists() and (p / "index.html").exists():
        STATIC_DIR = p
        print(f"[静态文件] 找到目录: {STATIC_DIR}")
        break

if STATIC_DIR:
    
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return HTMLResponse(status_code=404)

    @app.get("/vite.svg")
    async def vite_svg():
        svg_path = STATIC_DIR / "vite.svg"
        if svg_path.exists():
            return FileResponse(svg_path)
        return HTMLResponse(status_code=404)

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
    
        if full_path.startswith("api"):
            return HTMLResponse(content='{"error": "not found"}', status_code=404)
        return FileResponse(STATIC_DIR / "index.html")

else:
    print("[静态文件] 未找到静态目录，仅提供 API")

    @app.get("/")
    async def root():
        return {
            "name": "图片压缩服务",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/api/health"
        }
