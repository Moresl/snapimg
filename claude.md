# 更新记录

## 2024-11-28

### 项目重构 - 桌面应用转 Web 应用

将 PyQt5 桌面图片压缩工具重构为 Web 应用。

### 简化后端架构

- 移除数据库 (SQLAlchemy, SQLite)
- 移除文件存储 (不保存上传/压缩图片)
- 内存中处理图片，返回 base64 数据
- 移除历史记录和统计功能

**后端 (serve/):**
- FastAPI + Pillow (纯内存处理)
- 压缩引擎支持 PNG/JPEG/WebP
- PNG 使用 256 色量化 (FASTOCTREE)
- API: `/api/compress/batch` 返回 base64

**前端 (src/):**
- React + TypeScript + Vite
- UnoCSS + Shadcn UI 风格
- 组件: UploadZone, CompressResult
- 拖拽上传，批量压缩，直接下载

### 目录结构调整

- 前端文件移至根目录
- 后端目录命名为 `serve`

### 当前项目结构

```
img-yasuo/
├── src/                    # 前端源码
│   ├── components/
│   │   ├── UploadZone.tsx
│   │   └── ImageCompare.tsx
│   ├── styles/
│   │   └── theme.css       # 主题变量
│   ├── lib/api.ts
│   ├── App.tsx
│   └── main.tsx
├── serve/                  # 后端服务
│   ├── app/
│   │   ├── api/compress.py
│   │   ├── core/compressor.py
│   │   ├── core/config.py
│   │   ├── models/schemas.py
│   │   └── main.py
│   └── requirements.txt
├── package.json
├── vite.config.ts
├── uno.config.ts
└── index.html
```

### 启动命令

```bash
# 后端
cd serve && python -m uvicorn app.main:app --reload --port 8001

# 前端
npm run dev
```

### 前端优化

- 缩小上传区域，更紧凑的布局
- 支持单个/多个文件上传
- 显示压缩进度
- 显示压缩体积和比例
- 多文件自动打包 ZIP 下载
- 单文件直接下载
- 刷新页面清空所有数据（无持久化）
- **图片对比功能** - 点击眼睛图标打开对比视图，拖动滑块查看压缩前后效果

### UI/主题优化

- **深色/浅色主题切换**
  - 使用 CSS 变量实现主题系统
  - localStorage 持久化用户偏好
  - 自动检测系统主题偏好
  - 点击 Sun/Moon 图标切换

- **首页 Hero 区域**
  - 渐变文字标题
  - 功能特性徽章（智能压缩、极速压缩、本地处理、效果对比）
  - 上传文件后自动隐藏

- **统计卡片优化**
  - 大字体数字展示
  - 大写标签文字
  - 节省空间百分比和具体大小

- **按钮样式增强**
  - 绿色下载按钮 (btn-success)
  - 阴影效果和悬停动画
  - 箭头图标指示

- **文件列表优化**
  - 圆角卡片设计
  - 状态颜色区分（待处理/压缩中/完成/错误）
  - 实时进度条（0-90% 模拟进度，完成后 100%）

- **新增文件**
  - `src/styles/theme.css` - 主题 CSS 变量定义

### UI 简化优化

- 移除按钮发光/阴影效果
- 文件列表显示缩略图（替代颜色方块）
- 压缩比例使用纯文字显示（移除背景色）
- Hero 标题单行显示，移除上方徽章
- Footer 固定在页面底部（flex 布局）
- 按钮使用简洁默认样式

### 压缩库升级

**PNG 压缩升级:**
- 使用 `imagequant` (libimagequant Python 绑定)
- pngquant / TinyPNG 同款算法
- 比 Pillow FASTOCTREE 压缩率更高、质量更好

**JPEG 压缩升级:**
- 使用 `mozjpeg-lossless-optimization` 后处理
- 无损优化，额外减少 5-15% 体积

**新增依赖:**
```
imagequant
mozjpeg-lossless-optimization
```

**兼容性:** 两个库都使用 try/except 导入，失败时自动回退到 Pillow

### 依赖

**后端 (pip):**
- fastapi
- uvicorn
- python-multipart
- Pillow
- pydantic

**前端 (npm):**
- react, react-dom
- vite, typescript
- unocss
- lucide-react
- react-dropzone
- jszip (ZIP 打包)
