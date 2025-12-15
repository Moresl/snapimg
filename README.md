# SnapImg

![License](https://img.shields.io/badge/license-MIT-blue)
![React](https://img.shields.io/badge/React-19-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed)

[English](README_EN.md) | 中文

---

一个快速、注重隐私的在线图片压缩工具。支持 PNG、JPEG、WebP、AVIF 格式，高压缩率同时保持画质。

## 功能特点

- **多格式支持** - 支持 PNG、JPEG、WebP、AVIF 格式输入输出
- **高压缩率** - PNG 使用 pngquant/imagequant 算法，压缩率可达 70%+
- **保持质量** - 智能压缩算法，最大程度保留图片质量
- **本地处理** - 图片在服务器内存中处理，不保存到磁盘
- **批量压缩** - 单次最多处理 20 张图片
- **效果对比** - 滑动对比压缩前后效果
- **深色模式** - 支持浅色/深色主题切换

## 截图

![主界面](image.png)
![压缩效果](image-1.png)

## 技术栈

**前端：**
- React 19 + TypeScript
- Tailwind CSS + Shadcn UI
- Vite

**后端：**
- FastAPI + Python
- Pillow + imagequant + pngquant
- 纯内存处理，无数据库

## 快速开始

### Docker 部署（推荐）

```bash
# 构建镜像
docker build -t snapimg .

# 运行容器
docker run -d -p 80:80 --name snapimg snapimg
```

访问 http://localhost 即可使用。

### 本地开发

**前端：**

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**后端：**

```bash
cd serve

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

## 项目结构

```
snapimg/
├── src/                    # 前端源码
│   ├── components/         # React 组件
│   │   ├── ui/            # Shadcn UI 组件
│   │   ├── UploadZone.tsx
│   │   └── ImageCompare.tsx
│   ├── lib/               # 工具函数
│   ├── App.tsx
│   └── main.tsx
├── serve/                  # 后端服务
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心压缩逻辑
│   │   └── models/        # 数据模型
│   └── requirements.txt
├── Dockerfile             # Docker 构建文件
└── docker-compose.yml
```

## API 接口

### POST /api/compress/single

压缩单张图片。

**请求：** `multipart/form-data`
- `file`: 图片文件
- `format`: 输出格式 (original/png/jpeg/webp/avif)

**响应：**
```json
{
  "filename": "image.png",
  "original_size": 1024000,
  "compressed_size": 307200,
  "compression_ratio": 70.0,
  "format": "png",
  "data": "data:image/png;base64,...",
  "success": true
}
```

## 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

[MIT License](LICENSE)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Moresl/snapimg&type=date)](https://www.star-history.com/#Moresl/snapimg&type=date)
