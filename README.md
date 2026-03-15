<div align="center">

# 🚀 Futuristic Blog

**A modern, futuristic personal blog system built with Vue 3, FastAPI, and PostgreSQL**

[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)

---

## 🌐 Language / 语言

**[English](#-english-documentation)** | **[中文文档](#-中文文档)**

---

</div>

---

# 📚 English Documentation

## 📖 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Local Development Setup](#-local-development-setup)
- [Railway Deployment](#-railway-deployment)
- [Environment Variables](#-environment-variables)
- [Important Notes](#-important-notes)
- [License](#-license)

---

## 🌟 Project Overview

**Futuristic Blog** is a full-stack personal blog system designed for developers and content creators who want a modern, visually appealing platform to share their thoughts and knowledge. The system features a futuristic dark theme with smooth animations, particle backgrounds, and a comprehensive admin dashboard.

### Target Audience
- Personal bloggers and developers
- Content creators who want a modern platform
- Anyone interested in full-stack Vue.js + FastAPI development

### Key Highlights
- 🎨 Futuristic dark theme with particle effects
- 📝 Markdown support with syntax highlighting
- 💬 Real-time comment system with nested replies
- 📊 Admin dashboard with analytics
- 📧 Email notifications (comment replies, pending approvals)
- 🔐 JWT-based authentication
- 📱 Fully responsive design

---

## ✨ Features

### 📝 Content Management

#### Articles
- Create, edit, and delete articles with Markdown support
- Automatic reading time calculation
- Cover image support
- Draft/Published status management
- Featured articles highlighting
- Category and tag organization
- SEO-friendly slugs

#### Categories & Tags
- Hierarchical content organization
- Color-coded categories
- Tag-based filtering
- Article count tracking

#### Resources
- Resource link management
- Category organization
- Click tracking
- Icon support

### 💬 Comment System

#### User Features
- Nested comment replies
- Reply to specific users
- Edit and delete own comments
- Real-time comment updates
- Markdown support in comments

#### Admin Features
- Comment moderation (approve/reject)
- Batch approval operations
- Audit log tracking
- Soft delete with record keeping
- Permanent delete option

### 📧 Email Notifications

- New comment notifications (admin)
- Comment reply notifications (users)
- Pending comment approval notifications
- Comment approval notifications
- Configurable email provider (SMTP/Resend)

### 🎛️ Admin Dashboard

#### Analytics
- Article views and trends
- Comment statistics
- User registration trends
- Access logs visualization
- Popular content tracking

#### User Management
- User list and roles
- Admin promotion/demotion
- Account verification status
- Profile management

#### System Settings
- Site configuration
- Email settings
- Notification preferences
- SEO settings

### 🔐 Authentication & Security

- JWT token-based authentication
- Password hashing with bcrypt
- Token refresh mechanism
- Role-based access control
- CORS protection
- Input validation and sanitization

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Vue 3 | Frontend framework (Composition API) |
| TypeScript | Type safety |
| Vite | Build tool |
| TailwindCSS | Styling |
| Pinia | State management |
| Vue Router | Routing |
| Axios | HTTP client |
| Marked | Markdown parsing |
| Highlight.js | Code syntax highlighting |
| ECharts | Data visualization |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| PostgreSQL | Primary database |
| Pydantic | Data validation |
| Python-JOSE | JWT handling |
| Passlib | Password hashing |
| Uvicorn | ASGI server |

---

## 🚀 Local Development Setup

### Prerequisites

Ensure you have the following installed:

- **Node.js** >= 18.x ([Download](https://nodejs.org/))
- **Python** >= 3.11 ([Download](https://www.python.org/))
- **PostgreSQL** >= 14.x (optional, SQLite works for development)
- **Git** ([Download](https://git-scm.com/))

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/futuristic-blog.git
cd futuristic-blog
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Edit `backend/.env` with your configuration:

```env
# Database (SQLite for development)
DATABASE_URL=sqlite:///./futuristic_blog.db

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Email (optional for development)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# Resend API (alternative email provider)
RESEND_API_KEY=
RESEND_FROM_EMAIL=
EMAIL_PROVIDER=resend
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=/api/v1
```

### Step 4: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Admin Panel**: http://localhost:3000/admin

### Default Admin Credentials

```
Username: admin
Password: admin123
```

⚠️ **Important**: Change the default admin password immediately after first login!

### Troubleshooting

#### Database Issues
```bash
# Reset database (development only)
rm backend/futuristic_blog.db
# Restart backend to recreate database
```

#### Port Already in Use
```bash
# Find and kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :8000
kill -9 <PID>
```

#### Node Modules Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🚂 Railway Deployment

Railway provides an easy deployment experience with automatic builds and PostgreSQL integration.

### Step 1: Create Railway Account

1. Go to [Railway.app](https://railway.app/)
2. Sign up with your GitHub account
3. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `futuristic-blog` repository
4. Railway will auto-detect the configuration

### Step 3: Add PostgreSQL Database

1. In your project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create a database and provide connection details

### Step 4: Set Environment Variables

In Railway dashboard, go to your backend service → **Variables**:

```env
# Database (auto-linked from PostgreSQL addon)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security - Generate a strong secret key
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters

# Admin credentials
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=your-email@example.com

# Frontend URL (your Railway frontend URL)
FRONTEND_URL=https://your-frontend.railway.app

# CORS
CORS_ORIGINS=["https://your-frontend.railway.app"]

# Email Configuration (choose one)

# Option 1: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=smtp

# Option 2: Resend (recommended)
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=resend

# Timezone
TIMEZONE=Asia/Shanghai
```

### Step 5: Deploy

1. Push changes to your GitHub repository
2. Railway will automatically deploy
3. Check deployment logs for any errors

---

## ⚙️ Environment Variables

### Backend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Database connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Yes | JWT secret key (32+ chars) | `your-super-secret-key...` |
| `ADMIN_USERNAME` | Yes | Default admin username | `admin` |
| `ADMIN_PASSWORD` | Yes | Default admin password | `SecurePass123!` |
| `ADMIN_EMAIL` | Yes | Admin email address | `admin@example.com` |
| `FRONTEND_URL` | Yes | Frontend URL for CORS | `https://blog.example.com` |
| `CORS_ORIGINS` | Yes | Allowed origins (JSON array) | `["https://example.com"]` |
| `TIMEZONE` | No | Application timezone | `Asia/Shanghai` |
| `SMTP_HOST` | Conditional | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | Conditional | SMTP server port | `587` |
| `SMTP_USER` | Conditional | SMTP username | `user@gmail.com` |
| `SMTP_PASSWORD` | Conditional | SMTP password | `app-password` |
| `SMTP_FROM_EMAIL` | Conditional | Sender email address | `noreply@example.com` |
| `RESEND_API_KEY` | Conditional | Resend API key | `re_xxxxxxxxxx` |
| `RESEND_FROM_EMAIL` | Conditional | Resend sender email | `noreply@yourdomain.com` |
| `EMAIL_PROVIDER` | No | Email provider | `smtp` or `resend` |

---

## ⚠️ Important Notes

### Email Functionality Requirements

For full email functionality, you need:

#### Option 1: SMTP (Gmail Example)
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: Google Account → Security → App passwords
3. Use the app password as `SMTP_PASSWORD`

#### Option 2: Resend (Recommended)
1. Sign up at [Resend.com](https://resend.com/)
2. Verify your domain ownership
3. Generate an API key
4. **Note**: Free tier only allows sending to your verified email address
5. For production, verify a domain to send to any recipient

### Domain Ownership for Email

To send emails from a custom domain (e.g., `noreply@yourdomain.com`):

1. **Own the domain** - Purchase from a registrar (Namecheap, GoDaddy, etc.)
2. **Add DNS records** - Configure SPF, DKIM, and DMARC records
3. **Verify with email provider** - Complete domain verification process

### Security Considerations

1. **Secret Key**: Use a strong, random secret key (32+ characters)
2. **Admin Password**: Change default password immediately
3. **CORS**: Only allow your actual frontend domain
4. **Database**: Use PostgreSQL in production (not SQLite)
5. **HTTPS**: Always use HTTPS in production
6. **Environment Variables**: Never commit `.env` files

### Known Limitations

1. **Email Testing**: Resend free tier only sends to verified emails
2. **File Uploads**: Large files may require additional configuration
3. **Rate Limiting**: Not implemented (consider adding for production)
4. **Image Optimization**: Manual optimization recommended

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">

**[⬆ Back to Top](#-futuristic-blog)**

</div>

---

# 📚 中文文档

## 📖 目录

- [项目概述](#-项目概述)
- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [本地开发环境搭建](#-本地开发环境搭建)
- [Railway 部署指南](#-railway-部署指南)
- [环境变量配置](#-环境变量配置)
- [重要说明](#-重要说明)
- [许可证](#-许可证)

---

## 🌟 项目概述

**Futuristic Blog** 是一个全栈个人博客系统，专为开发者和内容创作者设计，提供现代化、视觉吸引力强的平台来分享思想和知识。系统采用未来感深色主题，配有流畅动画、粒子背景和完整的后台管理面板。

### 目标用户
- 个人博主和开发者
- 希望拥有现代化平台的内容创作者
- 对 Vue.js + FastAPI 全栈开发感兴趣的学习者

### 核心亮点
- 🎨 未来感深色主题与粒子特效
- 📝 Markdown 支持与代码高亮
- 💬 实时评论系统与嵌套回复
- 📊 数据分析后台管理面板
- 📧 邮件通知（评论回复、待审核通知）
- 🔐 基于 JWT 的身份认证
- 📱 完全响应式设计

---

## ✨ 功能特性

### 📝 内容管理

#### 文章管理
- 使用 Markdown 创建、编辑和删除文章
- 自动计算阅读时间
- 封面图片支持
- 草稿/发布状态管理
- 精选文章功能
- 分类和标签组织
- SEO 友好的 URL Slug

#### 分类与标签
- 层级化内容组织
- 彩色分类标识
- 基于标签的筛选
- 文章计数统计

#### 资源管理
- 资源链接管理
- 分类组织
- 点击统计
- 图标支持

### 💬 评论系统

#### 用户功能
- 嵌套评论回复
- 回复指定用户
- 编辑和删除自己的评论
- 实时评论更新
- 评论支持 Markdown

#### 管理员功能
- 评论审核（通过/拒绝）
- 批量审核操作
- 审核日志追踪
- 软删除保留记录
- 永久删除选项

### 📧 邮件通知

- 新评论通知（管理员）
- 评论回复通知（用户）
- 待审核评论通知
- 评论审核通过通知
- 可配置邮件服务商（SMTP/Resend）

### 🎛️ 后台管理面板

#### 数据分析
- 文章浏览量和趋势
- 评论统计
- 用户注册趋势
- 访问日志可视化
- 热门内容追踪

#### 用户管理
- 用户列表和角色
- 管理员权限设置
- 账户验证状态
- 个人资料管理

#### 系统设置
- 网站配置
- 邮件设置
- 通知偏好
- SEO 设置

### 🔐 身份认证与安全

- 基于 JWT Token 的身份认证
- 使用 bcrypt 进行密码哈希
- Token 刷新机制
- 基于角色的访问控制
- CORS 保护
- 输入验证和清理

---

## 🛠️ 技术栈

### 前端
| 技术 | 用途 |
|------------|---------|
| Vue 3 | 前端框架（Composition API） |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| TailwindCSS | 样式框架 |
| Pinia | 状态管理 |
| Vue Router | 路由管理 |
| Axios | HTTP 客户端 |
| Marked | Markdown 解析 |
| Highlight.js | 代码语法高亮 |
| ECharts | 数据可视化 |

### 后端
| 技术 | 用途 |
|------------|---------|
| FastAPI | REST API 框架 |
| SQLAlchemy | ORM |
| PostgreSQL | 主数据库 |
| Pydantic | 数据验证 |
| Python-JOSE | JWT 处理 |
| Passlib | 密码哈希 |
| Uvicorn | ASGI 服务器 |

---

## 🚀 本地开发环境搭建

### 环境要求

确保已安装以下软件：

- **Node.js** >= 18.x ([下载](https://nodejs.org/))
- **Python** >= 3.11 ([下载](https://www.python.org/))
- **PostgreSQL** >= 14.x（可选，开发环境可使用 SQLite）
- **Git** ([下载](https://git-scm.com/))

### 步骤 1：Fork 并克隆仓库

```bash
# 在 GitHub 上 Fork 仓库，然后克隆你的 Fork
git clone https://github.com/YOUR_USERNAME/futuristic-blog.git
cd futuristic-blog
```

### 步骤 2：后端配置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建环境配置文件
cp .env.example .env
```

编辑 `backend/.env` 配置文件：

```env
# 数据库（开发环境使用 SQLite）
DATABASE_URL=sqlite:///./futuristic_blog.db

# 安全密钥
SECRET_KEY=your-super-secret-key-change-in-production

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# 前端地址
FRONTEND_URL=http://localhost:3000

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 邮件配置（开发环境可选）
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# Resend API（备用邮件服务商）
RESEND_API_KEY=
RESEND_FROM_EMAIL=
EMAIL_PROVIDER=resend
```

### 步骤 3：前端配置

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 创建环境配置文件
cp .env.example .env
```

编辑 `frontend/.env`：

```env
VITE_API_BASE_URL=/api/v1
```

### 步骤 4：启动应用

**终端 1 - 后端：**
```bash
cd backend
source venv/bin/activate  # Windows 使用 venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

### 步骤 5：访问应用

- **前端页面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **后台管理**: http://localhost:3000/admin

### 默认管理员账户

```
用户名: admin
密码: admin123
```

⚠️ **重要提示**：首次登录后请立即修改默认管理员密码！

### 常见问题排查

#### 数据库问题
```bash
# 重置数据库（仅限开发环境）
rm backend/futuristic_blog.db
# 重启后端以重新创建数据库
```

#### 端口被占用
```bash
# 查找并终止占用 8000 端口的进程
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :8000
kill -9 <PID>
```

#### Node 模块问题
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🚂 Railway 部署指南

Railway 提供简单的部署体验，支持自动构建和 PostgreSQL 集成。

### 步骤 1：创建 Railway 账户

1. 访问 [Railway.app](https://railway.app/)
2. 使用 GitHub 账户注册
3. 授权 Railway 访问你的仓库

### 步骤 2：创建新项目

1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 选择你的 `futuristic-blog` 仓库
4. Railway 将自动检测配置

### 步骤 3：添加 PostgreSQL 数据库

1. 在项目中点击 **"+ New"**
2. 选择 **"Database"** → **"PostgreSQL"**
3. Railway 将创建数据库并提供连接信息

### 步骤 4：设置环境变量

在 Railway 控制面板中，进入后端服务 → **Variables**：

```env
# 数据库（自动关联 PostgreSQL 插件）
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 安全密钥 - 生成一个强密钥
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters

# 管理员账户
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=your-email@example.com

# 前端地址（你的 Railway 前端 URL）
FRONTEND_URL=https://your-frontend.railway.app

# CORS 配置
CORS_ORIGINS=["https://your-frontend.railway.app"]

# 邮件配置（选择一种）

# 方式 1: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=smtp

# 方式 2: Resend（推荐）
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=resend

# 时区
TIMEZONE=Asia/Shanghai
```

### 步骤 5：部署

1. 推送更改到 GitHub 仓库
2. Railway 将自动部署
3. 检查部署日志是否有错误

---

## ⚙️ 环境变量配置

### 后端变量

| 变量 | 必需 | 描述 | 示例 |
|----------|----------|-------------|---------|
| `DATABASE_URL` | 是 | 数据库连接字符串 | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | 是 | JWT 密钥（32+ 字符） | `your-super-secret-key...` |
| `ADMIN_USERNAME` | 是 | 默认管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 是 | 默认管理员密码 | `SecurePass123!` |
| `ADMIN_EMAIL` | 是 | 管理员邮箱地址 | `admin@example.com` |
| `FRONTEND_URL` | 是 | 前端 URL（用于 CORS） | `https://blog.example.com` |
| `CORS_ORIGINS` | 是 | 允许的来源（JSON 数组） | `["https://example.com"]` |
| `TIMEZONE` | 否 | 应用时区 | `Asia/Shanghai` |
| `SMTP_HOST` | 条件 | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | 条件 | SMTP 服务器端口 | `587` |
| `SMTP_USER` | 条件 | SMTP 用户名 | `user@gmail.com` |
| `SMTP_PASSWORD` | 条件 | SMTP 密码 | `app-password` |
| `SMTP_FROM_EMAIL` | 条件 | 发件人邮箱地址 | `noreply@example.com` |
| `RESEND_API_KEY` | 条件 | Resend API 密钥 | `re_xxxxxxxxxx` |
| `RESEND_FROM_EMAIL` | 条件 | Resend 发件人邮箱 | `noreply@yourdomain.com` |
| `EMAIL_PROVIDER` | 否 | 邮件服务商 | `smtp` 或 `resend` |

---

## ⚠️ 重要说明

### 邮件功能要求

要使用完整的邮件功能，你需要：

#### 方式 1：SMTP（以 Gmail 为例）
1. 在 Google 账户上启用两步验证
2. 生成应用密码：Google 账户 → 安全性 → 应用密码
3. 将应用密码用作 `SMTP_PASSWORD`

#### 方式 2：Resend（推荐）
1. 在 [Resend.com](https://resend.com/) 注册
2. 验证你的域名所有权
3. 生成 API 密钥
4. **注意**：免费版只能发送到已验证的邮箱地址
5. 生产环境需要验证域名才能发送给任意收件人

### 邮件域名要求

要从自定义域名发送邮件（如 `noreply@yourdomain.com`）：

1. **拥有域名** - 从域名注册商购买（Namecheap、GoDaddy 等）
2. **添加 DNS 记录** - 配置 SPF、DKIM 和 DMARC 记录
3. **验证域名** - 完成邮件服务商的域名验证流程

### 安全注意事项

1. **密钥安全**：使用强随机密钥（32+ 字符）
2. **管理员密码**：立即修改默认密码
3. **CORS 配置**：只允许你的实际前端域名
4. **数据库**：生产环境使用 PostgreSQL（不要用 SQLite）
5. **HTTPS**：生产环境始终使用 HTTPS
6. **环境变量**：永远不要提交 `.env` 文件

### 已知限制

1. **邮件测试**：Resend 免费版只能发送到已验证邮箱
2. **文件上传**：大文件可能需要额外配置
3. **速率限制**：未实现（建议生产环境添加）
4. **图片优化**：建议手动优化

---

## 📄 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献指南

欢迎贡献代码！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

<div align="center">

**[⬆ 返回顶部](#-futuristic-blog)**

Made with ❤️ by [sxchou](https://github.com/sxchou)

</div>
