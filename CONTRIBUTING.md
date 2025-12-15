# 贡献指南 | Contributing Guide

[English](#english) | [中文](#中文)

---

## 中文

感谢你对 SnapImg 的关注！我们欢迎任何形式的贡献。

### 如何贡献

#### 报告 Bug

如果你发现了 bug，请创建一个 Issue，包含以下信息：

- 问题的简要描述
- 复现步骤
- 期望的行为
- 实际的行为
- 截图（如果适用）
- 环境信息（浏览器、操作系统等）

#### 提出新功能

如果你有新功能的想法，请先创建一个 Issue 讨论：

- 描述你想要的功能
- 解释为什么这个功能有用
- 如果可能，提供实现思路

#### 提交代码

1. Fork 这个仓库
2. 创建你的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个 Pull Request

### 开发环境设置

#### 前端

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建
npm run build

# 代码检查
npm run lint
```

#### 后端

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

### 代码规范

#### 前端

- 使用 TypeScript
- 遵循 ESLint 配置
- 组件使用函数式组件 + Hooks
- 使用 Tailwind CSS 进行样式设计

#### 后端

- 遵循 PEP 8 规范
- 使用类型注解
- 函数和类需要有文档字符串

### 提交信息规范

提交信息请遵循以下格式：

```
<type>: <description>

[optional body]
```

类型（type）：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat: 添加 AVIF 格式支持
fix: 修复深色模式下文字颜色问题
docs: 更新 README 安装说明
```

---

## English

Thank you for your interest in SnapImg! We welcome all forms of contributions.

### How to Contribute

#### Reporting Bugs

If you find a bug, please create an Issue with the following information:

- Brief description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment info (browser, OS, etc.)

#### Suggesting Features

If you have an idea for a new feature, please create an Issue first:

- Describe the feature you want
- Explain why it would be useful
- Provide implementation ideas if possible

#### Submitting Code

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

### Development Setup

#### Frontend

```bash
npm install
npm run dev
```

#### Backend

```bash
cd serve
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Code Style

#### Frontend

- Use TypeScript
- Follow ESLint configuration
- Use functional components with Hooks
- Use Tailwind CSS for styling

#### Backend

- Follow PEP 8
- Use type annotations
- Add docstrings to functions and classes

### Commit Message Format

```
<type>: <description>

[optional body]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code formatting
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Build/tooling

Examples:
```
feat: add AVIF format support
fix: fix text color in dark mode
docs: update README installation guide
```
