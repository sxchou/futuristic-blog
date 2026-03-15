# 🚀 Futuristic Blog

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/network/members)
[![GitHub license](https://img.shields.io/github/license/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/issues)

**A modern, futuristic personal blog system built with Vue 3, FastAPI, and PostgreSQL**

**一个基于 Vue 3、FastAPI 和 PostgreSQL 的现代化个人博客系统**

[🌐 **Live Preview / 在线预览**](https://zhouzhouya.top/)

---

**📖 Language / 语言选择**

[🇨🇳 中文文档](#-中文文档) | [🇺🇸 English Documentation](#-english-documentation)

</div>

---

# 📖 中文文档

## 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [本地开发](#本地开发)
- [Railway 免费部署](#railway-部署)
- [重要说明](#重要说明)
- [许可证](#许可证)

---

## 项目概述

Futuristic Blog 是一个具有未来感设计风格的现代化个人博客系统，采用前后端分离架构，提供完整的博客管理功能和极佳的用户体验。

### 🎯 目标用户

- 个人博主和内容创作者
- 技术文章写作者
- 希望搭建个人品牌网站的开发者
- 学习全栈开发的开发者

### ✨ 核心亮点

- 🎨 **未来感 UI 设计** - 采用粒子背景、渐变色彩和流畅动画
- 📱 **完全响应式** - 完美适配桌面端和移动端
- 🔐 **完整的用户系统** - JWT 认证、邮箱验证、权限管理
- 📝 **Markdown 支持** - 实时预览、代码高亮
- 💬 **评论系统** - 嵌套回复、审核机制、邮件通知
- 📊 **管理后台** - 数据可视化、内容管理

---

## 功能特性

### 📄 文章管理

| 功能 | 描述 |
|------|------|
| Markdown 编辑器 | 支持 Markdown 语法，实时预览，代码高亮 |
| 文章发布 | 支持草稿/发布状态，精选文章标记 |
| 分类与标签 | 灵活的分类和标签系统，支持多标签 |
| 封面图片 | 支持文章封面图片上传和展示 |
| 文件附件 | 支持文章附件上传和下载 |
| 阅读统计 | 自动统计文章阅读量、点赞数、评论数 |
| 归档功能 | 按年月归档文章，方便查阅 |

### 💬 评论系统

| 功能 | 描述 |
|------|------|
| 嵌套回复 | 支持多级嵌套评论回复 |
| 审核机制 | 评论审核（待审核/已通过/已拒绝） |
| 邮件通知 | 评论回复邮件通知、审核结果通知 |
| 删除管理 | 用户删除和管理员删除，支持软删除 |
| 表情支持 | 内置表情选择器 |

### 👤 用户系统

| 功能 | 描述 |
|------|------|
| 用户注册/登录 | 支持用户名密码注册登录 |
| 邮箱验证 | 注册邮箱验证功能 |
| JWT 认证 | 基于 JWT 的无状态认证 |
| 权限管理 | 管理员/普通用户权限分离 |
| 个人资料 | 用户头像、简介等个人信息管理 |

### 📊 管理后台

| 功能 | 描述 |
|------|------|
| 数据仪表盘 | 文章、评论、用户数据统计可视化 |
| 文章管理 | 文章增删改查，发布状态管理 |
| 评论管理 | 评论审核、批量操作 |
| 分类标签 | 分类和标签的增删改查 |
| 用户管理 | 用户列表、权限管理 |
| 资源管理 | 文件资源管理 |
| 系统设置 | 站点配置、邮件设置 |
| 访问日志 | 系统访问日志记录 |

### 🎨 前端特性

| 功能 | 描述 |
|------|------|
| 粒子背景 | 首页动态粒子背景效果 |
| 暗黑模式 | 支持亮色/暗色主题切换 |
| 响应式设计 | 完美适配各种设备尺寸 |
| 阅读进度条 | 文章阅读进度指示 |
| 全局搜索 | 文章标题、内容全文搜索 |
| 平滑动画 | 页面切换和交互动画效果 |

---

## 技术栈

### 前端技术

| 技术 | 版本 | 描述 |
|------|------|------|
| [Vue 3](https://vuejs.org/) | 3.4.x | 渐进式 JavaScript 框架 |
| [TypeScript](https://www.typescriptlang.org/) | 5.3.x | JavaScript 的超集，提供类型安全 |
| [Vite](https://vitejs.dev/) | 5.0.x | 下一代前端构建工具 |
| [Pinia](https://pinia.vuejs.org/) | 2.1.x | Vue 3 官方状态管理库 |
| [Vue Router](https://router.vuejs.org/) | 4.2.x | Vue.js 官方路由 |
| [Tailwind CSS](https://tailwindcss.com/) | 3.4.x | 实用优先的 CSS 框架 |
| [ECharts](https://echarts.apache.org/) | 6.0.x | 数据可视化图表库 |
| [Marked](https://marked.js.org/) | 11.x | Markdown 解析器 |
| [Highlight.js](https://highlightjs.org/) | 11.x | 代码语法高亮 |

### 后端技术

| 技术 | 版本 | 描述 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.109.x | 高性能 Python Web 框架 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0.x | Python SQL 工具包和 ORM |
| [PostgreSQL](https://www.postgresql.org/) | - | 开源关系型数据库 |
| [Redis](https://redis.io/) | - | 内存数据结构存储 |
| [Pydantic](https://pydantic-docs.helpmanual.io/) | 2.5.x | 数据验证和设置管理 |
| [Python-JOSE](https://github.com/mpdavis/python-jose) | 3.3.x | JWT 令牌处理 |
| [Uvicorn](https://www.uvicorn.org/) | 0.27.x | ASGI 服务器 |

---

## 本地开发

### 前置要求

- **Node.js** >= 18.0
- **Python** >= 3.11
- **PostgreSQL** >= 14 (或使用 SQLite 开发)
- **Git**

### 克隆项目

```bash
# 克隆仓库
git clone https://github.com/sxchou/futuristic-blog.git
cd futuristic-blog
```

### 后端配置

1. **创建 Python 虚拟环境**

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件：

```bash
# 数据库配置 (开发环境可使用 SQLite)
DATABASE_URL=sqlite:///./futuristic_blog.db

# 生产环境使用 PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/futuristic_blog

# 安全配置
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# 前端地址
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# 时区
TIMEZONE=Asia/Shanghai

# 邮件配置 (可选)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com

# Resend 邮件服务 (可选)
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=resend
```

4. **启动后端服务**

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端服务将在 `http://127.0.0.1:8000` 启动，API 文档地址：`http://127.0.0.1:8000/api/docs`

### 前端配置

1. **安装依赖**

```bash
cd frontend
npm install
```

2. **配置环境变量**

创建 `.env` 文件：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

3. **启动开发服务器**

```bash
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

### 常见问题

<details>
<summary><b>🔧 数据库连接失败</b></summary>

确保 PostgreSQL 服务正在运行，并检查 `.env` 中的 `DATABASE_URL` 配置是否正确。开发环境可使用 SQLite：

```bash
DATABASE_URL=sqlite:///./futuristic_blog.db
```

</details>

<details>
<summary><b>🔧 前端无法连接后端</b></summary>

1. 确认后端服务已启动
2. 检查 CORS 配置是否包含前端地址
3. 检查 `vite.config.ts` 中的代理配置

</details>

<details>
<summary><b>🔧 邮件发送失败</b></summary>

邮件功能需要正确配置 SMTP 或 Resend。如仅需测试，可暂时跳过邮件配置，相关功能会优雅降级。

</details>

---

## Railway 部署

Railway 提供免费的 PostgreSQL 数据库和应用托管服务，非常适合部署本项目。

### 部署优势

- ✅ **免费额度充足** - 每月 $5 免费额度，个人博客完全够用
- ✅ **自动 HTTPS** - 免费 SSL 证书
- ✅ **PostgreSQL 支持** - 内置 PostgreSQL 数据库
- ✅ **自动部署** - 连接 GitHub 自动部署
- ✅ **环境变量管理** - 便捷的环境变量配置界面

### 部署步骤

#### 1. Fork 项目

点击 GitHub 页面右上角的 **Fork** 按钮，将项目 Fork 到您的账户。

#### 2. 创建 Railway 账户

访问 [Railway.app](https://railway.app/)，使用 GitHub 账户登录。

#### 3. 创建新项目

1. 点击 **New Project**
2. 选择 **Deploy from GitHub repo**
3. 选择您 Fork 的 `futuristic-blog` 仓库

#### 4. 添加 PostgreSQL 数据库

1. 在项目中点击 **Add Service**
2. 选择 **Database** → **PostgreSQL**
3. Railway 会自动创建数据库并生成连接字符串

#### 5. 配置后端服务

创建后端服务：

1. 点击 **Add Service** → **GitHub Repo**
2. 选择 `backend` 目录作为根目录
3. 配置环境变量：

```bash
# 数据库 (Railway 自动提供)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 安全配置 (请修改)
SECRET_KEY=your-production-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员账户 (请修改)
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=your-email@example.com

# 前端地址 (部署后更新)
FRONTEND_URL=https://your-frontend.railway.app
CORS_ORIGINS=["https://your-frontend.railway.app"]

# 时区
TIMEZONE=Asia/Shanghai

# 邮件配置 (可选)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
```

#### 6. 配置前端服务

创建前端服务：

1. 点击 **Add Service** → **GitHub Repo**
2. 选择 `frontend` 目录作为根目录
3. 配置环境变量：

```bash
VITE_API_BASE_URL=https://your-backend.railway.app
```

#### 7. 配置自定义域名（可选）

在 Railway 项目设置中，可以为服务配置自定义域名：

1. 进入服务设置 → **Domains**
2. 添加自定义域名
3. 按照提示配置 DNS 记录

### 环境变量说明

| 变量名 | 必填 | 描述 | 示例值 |
|--------|------|------|--------|
| `DATABASE_URL` | ✅ | 数据库连接字符串 | Railway 自动提供 |
| `SECRET_KEY` | ✅ | JWT 密钥 | 至少 32 位随机字符串 |
| `ADMIN_USERNAME` | ✅ | 管理员用户名 | admin |
| `ADMIN_PASSWORD` | ✅ | 管理员密码 | 强密码 |
| `ADMIN_EMAIL` | ✅ | 管理员邮箱 | admin@example.com |
| `FRONTEND_URL` | ✅ | 前端地址 | https://your-domain.com |
| `CORS_ORIGINS` | ✅ | CORS 允许的源 | JSON 数组格式 |
| `TIMEZONE` | ⬜ | 时区设置 | Asia/Shanghai |
| `SMTP_*` | ⬜ | SMTP 邮件配置 | 见上文 |
| `RESEND_*` | ⬜ | Resend 邮件配置 | 见上文 |

---

## 重要说明

### 📧 邮件功能要求

完整的邮件功能需要以下条件：

1. **SMTP 方式**
   - 需要有可用的 SMTP 服务器
   - 支持常见邮件服务商（QQ邮箱、163邮箱、Gmail等）
   - 可能需要开启"应用专用密码"

2. **Resend 方式（推荐）**
   - 注册 [Resend](https://resend.com/) 账户
   - **注意**：免费版只能发送邮件给自己注册时的邮箱
   - 如需发送给其他邮箱，需要验证域名所有权

### 🔒 安全建议

1. **生产环境必须修改**：
   - `SECRET_KEY`：使用强随机字符串
   - `ADMIN_PASSWORD`：设置强密码
   - 数据库密码

2. **HTTPS**：
   - 生产环境务必启用 HTTPS
   - Railway 自动提供 HTTPS

3. **敏感信息**：
   - 不要将 `.env` 文件提交到版本控制
   - 使用环境变量管理敏感配置

### ⚠️ 已知限制

1. **邮件发送**
   - Resend 免费版每日限制 100 封
   - 需验证域名才能发送给任意邮箱

2. **文件上传**
   - 默认使用本地文件系统存储
   - 生产环境建议使用云存储服务

3. **缓存**
   - Redis 为可选配置
   - 未配置时部分缓存功能不可用

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个 Star！⭐**

Made with ❤️ by [sxchou](https://github.com/sxchou)

</div>

---

# 📖 English Documentation

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
- [Railway free Deployment](#railway-deployment-1)
- [Important Notes](#important-notes)
- [License](#license)

---

## Project Overview

Futuristic Blog is a modern personal blog system with a futuristic design aesthetic, built with a decoupled frontend-backend architecture, providing complete blog management functionality and an excellent user experience.

### 🎯 Target Audience

- Personal bloggers and content creators
- Technical article writers
- Developers looking to build personal brand websites
- Developers learning full-stack development

### ✨ Key Highlights

- 🎨 **Futuristic UI Design** - Particle backgrounds, gradient colors, and smooth animations
- 📱 **Fully Responsive** - Perfect adaptation for desktop and mobile devices
- 🔐 **Complete User System** - JWT authentication, email verification, permission management
- 📝 **Markdown Support** - Real-time preview, code highlighting
- 💬 **Comment System** - Nested replies, moderation, email notifications
- 📊 **Admin Dashboard** - Data visualization, content management

---

## Features

### 📄 Article Management

| Feature | Description |
|---------|-------------|
| Markdown Editor | Markdown syntax support with real-time preview and code highlighting |
| Article Publishing | Draft/published status support, featured article marking |
| Categories & Tags | Flexible category and tag system with multi-tag support |
| Cover Images | Article cover image upload and display |
| File Attachments | Article attachment upload and download |
| Reading Statistics | Automatic tracking of views, likes, and comments |
| Archive | Articles organized by year and month |

### 💬 Comment System

| Feature | Description |
|---------|-------------|
| Nested Replies | Multi-level nested comment support |
| Moderation | Comment review (pending/approved/rejected) |
| Email Notifications | Reply notifications, moderation result notifications |
| Delete Management | User and admin deletion with soft delete support |
| Emoji Support | Built-in emoji picker |

### 👤 User System

| Feature | Description |
|---------|-------------|
| Registration/Login | Username/password registration and login |
| Email Verification | Registration email verification |
| JWT Authentication | Stateless JWT-based authentication |
| Permission Management | Admin/user permission separation |
| Profile | User avatar, bio, and personal information management |

### 📊 Admin Dashboard

| Feature | Description |
|---------|-------------|
| Data Dashboard | Article, comment, user statistics visualization |
| Article Management | Article CRUD, publish status management |
| Comment Management | Comment moderation, batch operations |
| Categories & Tags | Category and tag CRUD |
| User Management | User list, permission management |
| Resource Management | File resource management |
| System Settings | Site configuration, email settings |
| Access Logs | System access log records |

### 🎨 Frontend Features

| Feature | Description |
|---------|-------------|
| Particle Background | Dynamic particle background on homepage |
| Dark Mode | Light/dark theme switching |
| Responsive Design | Perfect adaptation for all device sizes |
| Reading Progress | Article reading progress indicator |
| Global Search | Full-text search in titles and content |
| Smooth Animations | Page transitions and interaction animations |

---

## Tech Stack

### Frontend

| Technology | Version | Description |
|------------|---------|-------------|
| [Vue 3](https://vuejs.org/) | 3.4.x | Progressive JavaScript Framework |
| [TypeScript](https://www.typescriptlang.org/) | 5.3.x | JavaScript superset with type safety |
| [Vite](https://vitejs.dev/) | 5.0.x | Next-generation frontend build tool |
| [Pinia](https://pinia.vuejs.org/) | 2.1.x | Official Vue 3 state management |
| [Vue Router](https://router.vuejs.org/) | 4.2.x | Official Vue.js router |
| [Tailwind CSS](https://tailwindcss.com/) | 3.4.x | Utility-first CSS framework |
| [ECharts](https://echarts.apache.org/) | 6.0.x | Data visualization chart library |
| [Marked](https://marked.js.org/) | 11.x | Markdown parser |
| [Highlight.js](https://highlightjs.org/) | 11.x | Code syntax highlighting |

### Backend

| Technology | Version | Description |
|------------|---------|-------------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.109.x | High-performance Python Web Framework |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0.x | Python SQL Toolkit and ORM |
| [PostgreSQL](https://www.postgresql.org/) | - | Open-source relational database |
| [Redis](https://redis.io/) | - | In-memory data structure store |
| [Pydantic](https://pydantic-docs.helpmanual.io/) | 2.5.x | Data validation and settings management |
| [Python-JOSE](https://github.com/mpdavis/python-jose) | 3.3.x | JWT token handling |
| [Uvicorn](https://www.uvicorn.org/) | 0.27.x | ASGI server |

---

## Local Development

### Prerequisites

- **Node.js** >= 18.0
- **Python** >= 3.11
- **PostgreSQL** >= 14 (or use SQLite for development)
- **Git**

### Clone the Repository

```bash
# Clone the repository
git clone https://github.com/sxchou/futuristic-blog.git
cd futuristic-blog
```

### Backend Setup

1. **Create Python Virtual Environment**

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Environment Variables**

Create a `.env` file:

```bash
# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///./futuristic_blog.db

# PostgreSQL for production
# DATABASE_URL=postgresql://user:password@localhost:5432/futuristic_blog

# Security Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Account
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# Frontend URL
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Timezone
TIMEZONE=Asia/Shanghai

# Email Configuration (Optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com

# Resend Email Service (Optional)
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=resend
```

4. **Start Backend Server**

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will run at `http://127.0.0.1:8000`, API docs at `http://127.0.0.1:8000/api/docs`

### Frontend Setup

1. **Install Dependencies**

```bash
cd frontend
npm install
```

2. **Configure Environment Variables**

Create a `.env` file:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

3. **Start Development Server**

```bash
npm run dev
```

Frontend will run at `http://localhost:3000`.

### Troubleshooting

<details>
<summary><b>🔧 Database Connection Failed</b></summary>

Ensure PostgreSQL is running and check the `DATABASE_URL` in `.env`. For development, you can use SQLite:

```bash
DATABASE_URL=sqlite:///./futuristic_blog.db
```

</details>

<details>
<summary><b>🔧 Frontend Cannot Connect to Backend</b></summary>

1. Verify backend server is running
2. Check CORS configuration includes frontend URL
3. Check proxy configuration in `vite.config.ts`

</details>

<details>
<summary><b>🔧 Email Sending Failed</b></summary>

Email functionality requires proper SMTP or Resend configuration. For testing, you can skip email configuration - related features will gracefully degrade.

</details>

---

## Railway Deployment

Railway offers free PostgreSQL database and application hosting, perfect for deploying this project.

### Deployment Advantages

- ✅ **Generous Free Tier** - $5/month free credits, sufficient for personal blogs
- ✅ **Automatic HTTPS** - Free SSL certificates
- ✅ **PostgreSQL Support** - Built-in PostgreSQL database
- ✅ **Auto Deploy** - GitHub integration for automatic deployment
- ✅ **Environment Variables** - Easy environment variable management

### Deployment Steps

#### 1. Fork the Repository

Click the **Fork** button on GitHub to fork the project to your account.

#### 2. Create Railway Account

Visit [Railway.app](https://railway.app/) and sign in with your GitHub account.

#### 3. Create New Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your forked `futuristic-blog` repository

#### 4. Add PostgreSQL Database

1. Click **Add Service** in the project
2. Select **Database** → **PostgreSQL**
3. Railway will automatically create the database and generate connection string

#### 5. Configure Backend Service

Create backend service:

1. Click **Add Service** → **GitHub Repo**
2. Select `backend` directory as root
3. Configure environment variables:

```bash
# Database (Railway provides automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security (Please modify)
SECRET_KEY=your-production-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Account (Please modify)
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=your-email@example.com

# Frontend URL (Update after deployment)
FRONTEND_URL=https://your-frontend.railway.app
CORS_ORIGINS=["https://your-frontend.railway.app"]

# Timezone
TIMEZONE=Asia/Shanghai

# Email Configuration (Optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
```

#### 6. Configure Frontend Service

Create frontend service:

1. Click **Add Service** → **GitHub Repo**
2. Select `frontend` directory as root
3. Configure environment variables:

```bash
VITE_API_BASE_URL=https://your-backend.railway.app
```

#### 7. Configure Custom Domain (Optional)

In Railway project settings, you can configure custom domains:

1. Go to service settings → **Domains**
2. Add custom domain
3. Configure DNS records as instructed

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | Database connection string | Provided by Railway |
| `SECRET_KEY` | ✅ | JWT secret key | At least 32 random characters |
| `ADMIN_USERNAME` | ✅ | Admin username | admin |
| `ADMIN_PASSWORD` | ✅ | Admin password | Strong password |
| `ADMIN_EMAIL` | ✅ | Admin email | admin@example.com |
| `FRONTEND_URL` | ✅ | Frontend URL | https://your-domain.com |
| `CORS_ORIGINS` | ✅ | CORS allowed origins | JSON array format |
| `TIMEZONE` | ⬜ | Timezone setting | Asia/Shanghai |
| `SMTP_*` | ⬜ | SMTP email config | See above |
| `RESEND_*` | ⬜ | Resend email config | See above |

---

## Important Notes

### 📧 Email Functionality Requirements

Complete email functionality requires:

1. **SMTP Method**
   - Requires an available SMTP server
   - Supports common email providers (QQ Mail, 163 Mail, Gmail, etc.)
   - May need to enable "App-specific password"

2. **Resend Method (Recommended)**
   - Register at [Resend](https://resend.com/)
   - **Note**: Free tier only sends to your registered email
   - To send to other emails, domain verification is required

### 🔒 Security Recommendations

1. **Must Change in Production**:
   - `SECRET_KEY`: Use a strong random string
   - `ADMIN_PASSWORD`: Set a strong password
   - Database password

2. **HTTPS**:
   - Always enable HTTPS in production
   - Railway provides HTTPS automatically

3. **Sensitive Information**:
   - Never commit `.env` files to version control
   - Use environment variables for sensitive configuration

### ⚠️ Known Limitations

1. **Email Sending**
   - Resend free tier: 100 emails/day limit
   - Domain verification required for sending to arbitrary emails

2. **File Upload**
   - Default uses local filesystem storage
   - Production recommends cloud storage services

3. **Caching**
   - Redis is optional
   - Some caching features unavailable without Redis

---

## License

This project is open-sourced under the [MIT License](LICENSE).

---

<div align="center">

**⭐ If this project helps you, please give it a Star! ⭐**

Made with ❤️ by [sxchou](https://github.com/sxchou)

</div>
