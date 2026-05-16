# 🚀 Futuristic Blog

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/network/members)
[![GitHub license](https://img.shields.io/github/license/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/sxchou/futuristic-blog?style=for-the-badge)](https://github.com/sxchou/futuristic-blog/issues)

**A modern, futuristic personal blog system built with Vue 3, FastAPI, and PostgreSQL**

**一个基于 Vue 3、FastAPI 和 PostgreSQL 的现代化个人博客系统**

[🌐](https://zhouzhouya.top/) **[Live Preview / 在线预览](https://zhouzhouya.top/)**

***

**📖 Language / 语言选择**

[🇨🇳 中文文档](#-中文文档) | [🇺🇸 English Documentation](#-english-documentation)

</div>

***

# 📖 中文文档

## 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [本地开发](#本地开发)
- [生产部署](#-生产部署)
  - [方案一：Vercel + Render + Neon（推荐）](#方案一vercel--render--neon推荐)
  - [方案二：Netlify + Render + Neon](#方案二netlify--render--neon)
  - [配置文件存储](#配置文件存储supabase)
  - [环境变量说明](#环境变量完整说明)
  - [避坑指南](#-避坑指南)
- [重要说明](#重要说明)
- [许可证](#许可证)

***

## 项目概述

Futuristic Blog 是一个具有未来感设计风格的现代化个人博客系统，采用前后端分离架构，提供完整的博客管理功能和极佳的用户体验。

### 📸 项目截图

<div align="center">

| 首页 | 文章详情 |
|:---:|:---:|
| ![首页](screenshots/home.png) | ![文章详情](screenshots/article.png) |

| 管理后台 | 文章编辑 |
|:---:|:---:|
| ![管理后台](screenshots/admin.png) | ![文章编辑](screenshots/editor.png) |

| 暗黑模式 | 移动端适配 |
|:---:|:---:|
| ![暗黑模式](screenshots/dark.png) | ![移动端](screenshots/mobile.png) |

</div>

> 💡 **提示**：截图需要您手动添加。请将截图保存到 `screenshots/` 目录，然后更新 README 中的图片路径。

### 🎯 目标用户

- 个人博主和内容创作者
- 技术文章写作者
- 希望搭建个人品牌网站的开发者
- 学习全栈开发的开发者

### ✨ 核心亮点

- 🔐 **完整的用户认证系统** - 支持邮箱注册、OAuth 第三方登录（Google/GitHub/X/微信/QQ）
- 📝 **强大的文章管理** - Markdown 编辑、代码高亮、文件附件、自动别名生成
- 💬 **互动评论系统** - 支持 Markdown、嵌套回复、邮件通知、审核机制
- 🎨 **现代化 UI 设计** - 响应式布局、暗黑模式、玻璃态效果、流畅动画
- 📊 **数据可视化** - 访问统计、趋势图表、排行榜、实时数据展示
- 🛡️ **角色权限管理（RBAC）** - 细粒度权限控制、多角色支持、权限继承、操作审计
- 📜 **系统日志导出** - 操作日志/登录日志/访问日志导出 Excel、进度追踪、取消导出
- 🔧 **灵活的后台管理** - 内容管理、用户管理、系统配置、存储管理
- 📦 **文件存储管理** - Supabase 存储、文件预览、批量管理、存储统计
- 📢 **公告系统** - 多类型公告、优先级排序、启用/禁用控制

***

## 功能特性

### 📄 文章管理

| 功能           | 描述                       |
| ------------ | ------------------------ |
| Markdown 编辑器 | 支持 Markdown 语法，实时预览，代码高亮 |
| 文章发布         | 支持草稿/发布状态，精选文章标记         |
| 分类与标签        | 灵活的分类和标签系统，支持多标签         |
| 封面图片         | 支持文章封面图片上传和展示            |
| 文件附件         | 支持文章附件上传和下载              |
| 阅读统计         | 自动统计文章阅读量、点赞数、评论数        |
| 归档功能         | 按年月归档文章，方便查阅             |

### 💬 评论系统

| 功能   | 描述                |
| ---- | ----------------- |
| 嵌套回复 | 支持多级嵌套评论回复        |
| 审核机制 | 评论审核（待审核/已通过/已拒绝） |
| 邮件通知 | 评论回复邮件通知、审核结果通知   |
| 删除管理 | 用户删除和管理员删除，支持软删除  |
| 表情支持 | 内置表情选择器           |

### 👤 用户系统

| 功能         | 描述                                  |
| ------------ | ------------------------------------- |
| 用户注册/登录 | 支持用户名密码注册登录                |
| OAuth 登录   | 支持 Google/GitHub/X/微信/QQ 登录     |
| 邮箱验证     | 注册邮箱验证功能                      |
| JWT 认证     | 基于 JWT 的无状态认证                 |
| 权限管理     | 管理员/普通用户权限分离               |
| 个人资料     | 用户头像、简介等个人信息管理          |

### 📊 管理后台

| 功能     | 描述                       |
| -------- | -------------------------- |
| 数据仪表盘 | 文章、评论、用户数据统计可视化 |
| 文章管理   | 文章增删改查，发布状态管理     |
| 评论管理   | 评论审核、批量操作           |
| 分类标签   | 分类和标签的增删改查         |
| 用户管理   | 用户列表、权限管理           |
| 角色管理   | RBAC 角色权限管理           |
| 资源管理   | 文件资源管理               |
| 系统设置   | 站点配置、邮件设置         |
| 日志管理   | 操作日志、登录日志、访问日志 |
| 日志导出   | 日志导出 Excel、进度追踪    |
| 存储管理   | Supabase 文件存储管理      |
| 公告管理   | 公告创建、编辑、排序        |

### 🎨 前端特性

| 功能    | 描述          |
| ----- | ----------- |
| 粒子背景  | 首页动态粒子背景效果  |
| 暗黑模式  | 支持亮色/暗色主题切换 |
| 响应式设计 | 完美适配各种设备尺寸  |
| 阅读进度条 | 文章阅读进度指示    |
| 全局搜索  | 文章标题、内容全文搜索 |
| 平滑动画  | 页面切换和交互动画效果 |

***

## 技术栈

### 前端技术

| 技术                                            | 版本    | 描述                    |
| --------------------------------------------- | ----- | --------------------- |
| [Vue 3](https://vuejs.org/)                   | 3.4.x | 渐进式 JavaScript 框架     |
| [TypeScript](https://www.typescriptlang.org/) | 5.3.x | JavaScript 的超集，提供类型安全 |
| [Vite](https://vitejs.dev/)                   | 5.0.x | 下一代前端构建工具             |
| [Pinia](https://pinia.vuejs.org/)             | 2.1.x | Vue 3 官方状态管理库         |
| [Vue Router](https://router.vuejs.org/)       | 4.2.x | Vue.js 官方路由           |
| [Tailwind CSS](https://tailwindcss.com/)      | 3.4.x | 实用优先的 CSS 框架          |
| [ECharts](https://echarts.apache.org/)        | 6.0.x | 数据可视化图表库              |
| [Marked](https://marked.js.org/)              | 11.x  | Markdown 解析器          |
| [Highlight.js](https://highlightjs.org/)      | 11.x  | 代码语法高亮                |

### 后端技术

| 技术                                                    | 版本      | 描述                  |
| ----------------------------------------------------- | ------- | ------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)              | 0.109.x | 高性能 Python Web 框架   |
| [SQLAlchemy](https://www.sqlalchemy.org/)             | 2.0.x   | Python SQL 工具包和 ORM |
| [PostgreSQL](https://www.postgresql.org/)             | -       | 开源关系型数据库            |
| [Redis](https://redis.io/)                            | -       | 内存数据结构存储            |
| [Pydantic](https://pydantic-docs.helpmanual.io/)      | 2.5.x   | 数据验证和设置管理           |
| [Python-JOSE](https://github.com/mpdavis/python-jose) | 3.3.x   | JWT 令牌处理            |
| [Uvicorn](https://www.uvicorn.org/)                   | 0.27.x  | ASGI 服务器            |

***

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

1. **安装依赖**

```bash
pip install -r requirements.txt
```

1. **配置环境变量**

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

# Resend 邮件服务 (推荐)
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend

# SMTP 邮件配置 (备选)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
```

1. **启动后端服务**

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

1. **配置环境变量**

创建 `.env` 文件：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

1. **启动开发服务器**

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

***

## 🚀 生产部署

本项目推荐使用以下免费部署方案，稳定可靠，适合个人博客长期运行。

### 推荐部署架构

| 组件      | 推荐平台             | 特点               | 免费额度     |
| ------- | ---------------- | ---------------- | -------- |
| 🎨 前端   | Vercel / Netlify | 自动部署、全球 CDN 加速   | 无限带宽     |
| ⚙️ 后端   | Render           | 支持 Docker、自动休眠唤醒 | 750 小时/月 |
| 🗄️ 数据库 | Neon             | Serverless、自动扩容  | 0.5GB 存储 |
| 📦 存储   | Supabase         | CDN 加速、S3 兼容     | 5GB 存储   |
| 📧 邮件   | Resend           | 现代 API、高送达率      | 3000 封/月 |

***

### 方案一：Vercel + Render + Neon（推荐）

这是最推荐的部署方案，各组件免费额度充足，适合长期运行。

#### 第一步：部署数据库（Neon）

Neon 提供 Serverless PostgreSQL 数据库，免费版足够个人博客使用。

1. **注册 Neon 账户**
   - 访问 [Neon 官网](https://neon.tech/)
   - 点击 **Sign up** 使用 GitHub 账户登录
2. **创建数据库项目**
   - 点击 **Create a project**
   - 项目名称：`futuristic-blog`
   - 区域选择：建议选择 `AWS Asia Pacific (Singapore)` 或离用户最近的区域
   - 点击 **Create project**
3. **获取数据库连接字符串**
   - 项目创建后，会显示连接信息
   - 复制 **Connection string**，格式如下：

```bash
postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> 💡 **提示**：Neon 免费版提供 0.5GB 存储空间，对于个人博客完全够用。数据库会在无活动时自动休眠，首次连接可能需要几秒钟唤醒。

#### 第二步：部署后端（Render）

Render 提供免费的 Web Service，支持 Python 应用部署。

1. **注册 Render 账户**
   - 访问 [Render 官网](https://render.com/)
   - 点击 **Get Started** 使用 GitHub 账户登录
2. **创建 Web Service**
   - 点击 **New** → **Web Service**
   - 连接 GitHub 仓库，授权访问 `futuristic-blog` 仓库
   - 选择仓库后，配置服务：

| 配置项            | 值                                                  | 说明            |
| -------------- | -------------------------------------------------- | ------------- |
| Name           | `futuristic-blog-api`                              | 服务名称，影响默认域名   |
| Region         | `Singapore` 或 `Oregon`                             | 选择离用户最近的区域    |
| Branch         | `main`                                             | 部署分支          |
| Root Directory | `backend`                                          | **重要**：后端代码目录 |
| Runtime        | `Python 3`                                         | 运行时环境         |
| Build Command  | `pip install -r requirements.txt`                  | 安装依赖          |
| Start Command  | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | 启动命令          |
| Instance Type  | `Free`                                             | 免费实例          |

1. **添加环境变量**

在 **Advanced** → **Environment Variables** 中添加以下变量：

**必须配置的环境变量：**

```bash
# 数据库连接（从 Neon 复制）
DATABASE_URL=postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# JWT 安全密钥（请生成一个 32 位以上的随机字符串）
SECRET_KEY=your-super-secret-key-at-least-32-characters-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员账户（首次部署后自动创建，请修改密码）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourStrongPassword123!
ADMIN_EMAIL=your-email@example.com

# 前端地址（部署前端后更新）
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

**可选配置的环境变量：**

```bash
# 时区设置
TIMEZONE=Asia/Shanghai

# Resend 邮件服务（推荐）
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend

# Gmail SMTP 邮件配置（备选，配置复杂）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Supabase 文件存储（如需文件上传功能）
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=attachments
```

1. **部署服务**
   - 点击 **Create Web Service**
   - 等待构建完成（首次约 3-5 分钟）
   - 部署成功后会获得一个 `https://xxx.onrender.com` 的地址

> ⚠️ **注意**：Render 免费实例会在 15 分钟无请求后休眠，首次访问可能需要等待 30-60 秒唤醒。这是正常现象。

#### 第三步：部署前端（Vercel）

Vercel 是前端部署的最佳选择，全球 CDN 加速，访问速度快。

1. **注册 Vercel 账户**
   - 访问 [Vercel 官网](https://vercel.com/)
   - 点击 **Sign Up** 使用 GitHub 账户登录
2. **导入项目**
   - 点击 **Add New** → **Project**
   - 选择 `futuristic-blog` 仓库
   - 点击 **Import**
3. **配置项目**

| 配置项              | 值               | 说明            |
| ---------------- | --------------- | ------------- |
| Framework Preset | `Vite`          | 自动检测          |
| Root Directory   | `frontend`      | **重要**：前端代码目录 |
| Build Command    | `npm run build` | 构建命令          |
| Output Directory | `dist`          | 输出目录          |
| Install Command  | `npm install`   | 安装依赖          |

1. **添加环境变量**

在 **Environment Variables** 中添加：

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

> 💡 **提示**：将 `your-backend` 替换为你在 Render 上创建的后端服务名称。

1. **部署项目**
   - 点击 **Deploy**
   - 等待构建完成（约 1-2 分钟）
   - 部署成功后会获得一个 `https://xxx.vercel.app` 的地址

#### 第四步：配置文件存储（Supabase）

如需文章封面、附件上传功能，需要配置 Supabase Storage。

1. **创建 Supabase 项目**
   - 访问 [Supabase 官网](https://supabase.com/)
   - 点击 **Start your project** 使用 GitHub 登录
   - 创建新组织（如已有可跳过）
   - 点击 **New project**
   - 项目名称：`futuristic-blog-storage`
   - 区域：选择离用户最近的区域
   - 点击 **Create new project**
2. **创建存储桶**
   - 进入项目后，点击左侧 **Storage**
   - 点击 **New bucket** 创建存储桶：
     - 名称：`attachments`（或自定义名称）
     - 开启 **Public bucket** 选项
     - 点击 **Create bucket**

> 💡 **说明**：系统使用单一存储桶存储所有文件（头像、封面、附件），通过文件路径区分不同类型。

1. **获取 API 密钥**
   - 点击左侧 **Settings** → **API**
   - 复制 **Project URL** 和 **anon public** 密钥
2. **更新后端环境变量**
   - 回到 Render 后端服务
   - 在环境变量中添加：

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET=attachments
```

#### 第五步：更新 CORS 配置

前端部署完成后，需要更新后端的 CORS 配置：

1. 进入 Render 后端服务
2. 点击 **Environment**
3. 更新以下变量：

```bash
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

1. 点击 **Save Changes**，服务会自动重新部署

#### 第六步：验证部署

1. 访问前端地址 `https://xxx.vercel.app`
2. 使用配置的管理员账户登录
3. 测试各项功能是否正常

***

### 方案二：Netlify + Render + Neon

如果你更喜欢 Netlify，可以使用此方案。与方案一的区别仅在前端部署平台。

#### 部署步骤

1. **数据库和后端**：同方案一的 Neon 和 Render 部署步骤
2. **部署前端（Netlify）**
   - 访问 [Netlify 官网](https://www.netlify.com/)
   - 点击 **Sign up** 使用 GitHub 登录
   - 点击 **Add new site** → **Import an existing project**
   - 选择 `futuristic-blog` 仓库
   - 配置构建：

| 配置项               | 值               |
| ----------------- | --------------- |
| Base directory    | `frontend`      |
| Build command     | `npm run build` |
| Publish directory | `frontend/dist` |

1. **添加环境变量**：

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

1. 点击 **Deploy site** 完成部署

***

### 环境变量完整说明

#### 必须配置的环境变量

这些变量是系统运行的必要条件，缺少会导致功能异常。

| 变量名                           | 描述                  | 示例值                              | 获取方式      |
| ----------------------------- | ------------------- | -------------------------------- | --------- |
| `DATABASE_URL`                | PostgreSQL 数据库连接字符串 | `postgresql://user:pass@host/db` | Neon 控制台  |
| `SECRET_KEY`                  | JWT 令牌加密密钥          | 32 位以上随机字符串                      | 自行生成      |
| `ALGORITHM`                   | 加密算法                | `HS256`                          | 固定值       |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 令牌过期时间（分钟）          | `30`                             | 按需设置      |
| `ADMIN_USERNAME`              | 管理员用户名              | `admin`                          | 自定义       |
| `ADMIN_PASSWORD`              | 管理员密码               | `StrongPass123!`                 | 自定义强密码    |
| `ADMIN_EMAIL`                 | 管理员邮箱               | `admin@example.com`              | 自定义       |
| `FRONTEND_URL`                | 前端访问地址              | `https://blog.vercel.app`        | 部署后获取     |
| `CORS_ORIGINS`                | CORS 允许的源           | `["https://blog.vercel.app"]`    | JSON 数组格式 |

#### 可选配置的环境变量

这些变量用于增强功能，不配置不影响核心功能运行。

| 变量名                 | 描述               | 示例值                       | 用途       |
| ------------------- | ---------------- | ------------------------- | -------- |
| `TIMEZONE`          | 时区设置             | `Asia/Shanghai`           | 时间显示     |
| `RESEND_API_KEY`    | Resend API 密钥    | `re_xxx`                  | 邮件发送（推荐） |
| `RESEND_FROM_EMAIL` | Resend 发件人       | `onboarding@resend.dev`   | 邮件发送     |
| `EMAIL_PROVIDER`    | 邮件服务提供商          | `resend` 或 `smtp`         | 邮件发送     |
| `SMTP_HOST`         | SMTP 服务器地址       | `smtp.gmail.com`          | 邮件发送（备选） |
| `SMTP_PORT`         | SMTP 端口          | `587`                     | 邮件发送（备选） |
| `SMTP_USER`         | SMTP 用户名         | `your@gmail.com`          | 邮件发送（备选） |
| `SMTP_PASSWORD`     | SMTP 密码/应用密码     | `xxxx xxxx xxxx xxxx`     | 邮件发送（备选） |
| `SMTP_FROM_EMAIL`   | 发件人邮箱            | `your@gmail.com`          | 邮件发送（备选） |
| `SUPABASE_URL`      | Supabase 项目 URL  | `https://xxx.supabase.co` | 文件存储     |
| `SUPABASE_KEY`      | Supabase anon 密钥 | `eyJhbG...`               | 文件存储     |
| `SUPABASE_BUCKET`   | 存储桶名称            | `attachments`             | 文件存储     |

***

## 🚨 避坑指南

### 部署常见问题

#### 1. 数据库连接失败

**症状**：后端启动失败，日志显示数据库连接错误

**原因**：

- DATABASE\_URL 格式错误
- Neon 数据库休眠，首次连接超时
- IP 白名单限制

**解决方案**：

```bash
# 确保 DATABASE_URL 格式正确
postgresql://username:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# Neon 免费版会自动休眠，首次访问可能需要等待几秒
# 如果持续失败，检查 Neon 控制台是否显示数据库正常
```

#### 2. CORS 跨域错误

**症状**：前端请求后端 API 时控制台报 CORS 错误

**原因**：

- CORS\_ORIGINS 配置错误
- 前端地址与配置不匹配

**解决方案**：

```bash
# 确保 CORS_ORIGINS 格式正确（JSON 数组）
CORS_ORIGINS=["https://your-frontend.vercel.app"]

# 如果使用自定义域名，需要同时添加
CORS_ORIGINS=["https://your-frontend.vercel.app","https://yourdomain.com"]

# 本地开发时添加本地地址
CORS_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]
```

#### 3. Render 服务休眠

**症状**：首次访问需要等待 30-60 秒

**原因**：Render 免费实例会在 15 分钟无请求后休眠

**解决方案**：

- 这是正常现象，免费服务都有此限制
- 可以使用 [UptimeRobot](https://uptimerobot.com/) 等监控服务定期 ping 保持唤醒
- 或升级到 Render 付费计划

#### 4. 前端构建失败

**症状**：Vercel/Netlify 构建时报错

**常见原因及解决方案**：

```bash
# 原因1：Node.js 版本不兼容
# 在 package.json 中添加 engines 字段
"engines": {
  "node": ">=18.0.0"
}

# 原因2：依赖安装失败
# 确保 package-lock.json 存在并提交到仓库

# 原因3：环境变量未配置
# 确保 VITE_API_BASE_URL 已正确配置
```

### 邮件配置避坑

#### 1. Resend 邮件服务（强烈推荐）

Resend 是现代化的邮件 API 服务，免费版提供每月 3000 封邮件额度，完全满足个人博客需求。

**优势**：

- 🚀 现代 API，集成简单
- 📊 完善的发送日志和统计
- 🔒 高送达率，不易进垃圾箱
- 💰 免费额度充足（3000封/月）

**配置步骤**：

1. **注册 Resend 账户**
   - 访问 [Resend 官网](https://resend.com/)
   - 点击 **Sign Up** 使用 GitHub 账户登录
   - 验证邮箱地址
2. **获取 API 密钥**
   - 登录后点击 **API Keys**
   - 点击 **Create API Key**
   - 输入名称：`futuristic-blog`
   - 复制生成的 API 密钥（格式：`re_xxxxxxxxxxxx`）
3. **配置环境变量**：

```bash
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend
```

> **重要提示**：Resend 免费版默认使用 `onboarding@resend.dev` 作为发件人，只能发送给注册 Resend 账户时使用的邮箱地址。如需发送给任意邮箱，需要添加并验证自定义域名。

**如需发送给任意邮箱**：

1. 添加自定义域名
   - 在 Resend 控制台点击 **Domains**
   - 点击 **Add Domain** 添加你的域名
   - 配置 DNS 记录（MX、SPF、DKIM）
   - 等待验证通过
2. 更新环境变量：

```bash
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

#### 2. Gmail SMTP 配置（不推荐）

**重要限制**：Gmail SMTP 配置复杂，免费账户有严格限制！

**原因**：

- Google 于 2022 年 5 月关闭了"低安全性应用访问"功能
- 必须使用 OAuth 2.0 或应用专用密码（需开启两步验证）
- 免费 Gmail 账户每日发送限制约 100-500 封
- 送达率较低，容易进入垃圾箱

**如果坚持使用 Gmail SMTP**：

1. **开启两步验证**
   - 访问 [Google 账户安全设置](https://myaccount.google.com/security)
   - 开启 **两步验证**
2. **生成应用专用密码**
   - 在安全设置中找到 **应用专用密码**
   - 点击 **创建新密码**
   - 选择 **邮件** 和 **其他设备**
   - 复制生成的 16 位密码（格式：`xxxx xxxx xxxx xxxx`）
3. **配置环境变量**：

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_EMAIL=your-email@gmail.com
EMAIL_PROVIDER=smtp
```

**推荐方案**：

- ✅ 使用 Resend（免费、稳定、送达率高）
- ✅ 如有自定义域名，配置 Resend 域名验证

### 文件上传避坑

#### 1. Supabase 存储桶权限

**症状**：上传文件后无法访问

**解决方案**：

- 确保存储桶已开启 **Public bucket**
- 检查 SUPABASE\_KEY 是否为 anon public 密钥（非 service\_role）

#### 2. 文件大小限制

**限制说明**：

- Supabase 免费版单文件最大 50MB
- 建议上传前压缩图片

### 安全配置避坑

#### 1. SECRET\_KEY 生成

**错误做法**：

```bash
SECRET_KEY=admin
SECRET_KEY=123456
SECRET_KEY=password
```

**正确做法**：

```bash
# 方法1：使用 Python 生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2：使用 OpenSSL
openssl rand -hex 32

# 方法3：在线生成
# 访问 https://www.uuidgenerator.net/ 生成随机字符串
```

#### 2. 管理员密码

首次部署后请立即修改默认管理员密码：

1. 登录管理后台
2. 进入个人设置
3. 修改密码

***

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

***

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

***

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个 Star！⭐**

Made with ❤️ by [sxchou](https://github.com/sxchou)

</div>

***

# 📖 English Documentation

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
- [Production Deployment](#-production-deployment)
  - [Option 1: Vercel + Render + Neon (Recommended)](#option-1-vercel--render--neon-recommended)
  - [Option 2: Netlify + Render + Neon](#option-2-netlify--render--neon)
  - [Configure File Storage](#configure-file-storage-supabase)
  - [Environment Variables](#environment-variables-reference)
  - [Troubleshooting Guide](#-troubleshooting-guide)
- [Important Notes](#important-notes)
- [License](#license)

***

## Project Overview

Futuristic Blog is a modern personal blog system with a futuristic design aesthetic, built with a decoupled frontend-backend architecture, providing complete blog management functionality and an excellent user experience.

### 🎯 Target Audience

- Personal bloggers and content creators
- Technical article writers
- Developers looking to build personal brand websites
- Developers learning full-stack development

### ✨ Key Highlights

- 🔐 **Complete User Authentication** - Email registration, OAuth third-party login (Google/GitHub/X/WeChat/QQ)
- 📝 **Powerful Article Management** - Markdown editing, code highlighting, file attachments, auto alias generation
- 💬 **Interactive Comment System** - Markdown support, nested replies, email notifications, moderation
- 🎨 **Modern UI Design** - Responsive layout, dark mode, glassmorphism effects, smooth animations
- 📊 **Data Visualization** - Access statistics, trend charts, rankings, real-time data display
- 🛡️ **Role-Based Access Control (RBAC)** - Fine-grained permissions, multi-role support, permission inheritance, audit logs
- 📜 **System Log Export** - Operation/login/access logs export to Excel, progress tracking, cancel export
- 🔧 **Flexible Admin Panel** - Content management, user management, system configuration, storage management
- 📦 **File Storage Management** - Supabase storage, file preview, batch management, storage statistics
- 📢 **Announcement System** - Multiple types, priority sorting, enable/disable control

***

## Features

### 📄 Article Management

| Feature            | Description                                                          |
| ------------------ | -------------------------------------------------------------------- |
| Markdown Editor    | Markdown syntax support with real-time preview and code highlighting |
| Article Publishing | Draft/published status support, featured article marking             |
| Categories & Tags  | Flexible category and tag system with multi-tag support              |
| Cover Images       | Article cover image upload and display                               |
| File Attachments   | Article attachment upload and download                               |
| Reading Statistics | Automatic tracking of views, likes, and comments                     |
| Archive            | Articles organized by year and month                                 |

### 💬 Comment System

| Feature             | Description                                          |
| ------------------- | ---------------------------------------------------- |
| Nested Replies      | Multi-level nested comment support                   |
| Moderation          | Comment review (pending/approved/rejected)           |
| Email Notifications | Reply notifications, moderation result notifications |
| Delete Management   | User and admin deletion with soft delete support     |
| Emoji Support       | Built-in emoji picker                                |

### 👤 User System

| Feature               | Description                                           |
| --------------------- | ----------------------------------------------------- |
| Registration/Login    | Username/password registration and login              |
| OAuth Login           | Google/GitHub/X/WeChat/QQ login support               |
| Email Verification    | Registration email verification                       |
| JWT Authentication    | Stateless JWT-based authentication                    |
| Permission Management | Admin/user permission separation                      |
| Profile               | User avatar, bio, and personal information management |

### 📊 Admin Dashboard

| Feature             | Description                                     |
| ------------------- | ----------------------------------------------- |
| Data Dashboard      | Article, comment, user statistics visualization |
| Article Management  | Article CRUD, publish status management         |
| Comment Management  | Comment moderation, batch operations            |
| Categories & Tags   | Category and tag CRUD                           |
| User Management     | User list, permission management                |
| Role Management     | RBAC role and permission management             |
| Resource Management | File resource management                        |
| System Settings     | Site configuration, email settings              |
| Log Management      | Operation, login, and access logs               |
| Log Export          | Export logs to Excel, progress tracking         |
| Storage Management  | Supabase file storage management                |
| Announcement Mgmt   | Announcement creation, editing, sorting         |

### 🎨 Frontend Features

| Feature             | Description                                 |
| ------------------- | ------------------------------------------- |
| Particle Background | Dynamic particle background on homepage     |
| Dark Mode           | Light/dark theme switching                  |
| Responsive Design   | Perfect adaptation for all device sizes     |
| Reading Progress    | Article reading progress indicator          |
| Global Search       | Full-text search in titles and content      |
| Smooth Animations   | Page transitions and interaction animations |

***

## Tech Stack

### Frontend

| Technology                                    | Version | Description                          |
| --------------------------------------------- | ------- | ------------------------------------ |
| [Vue 3](https://vuejs.org/)                   | 3.4.x   | Progressive JavaScript Framework     |
| [TypeScript](https://www.typescriptlang.org/) | 5.3.x   | JavaScript superset with type safety |
| [Vite](https://vitejs.dev/)                   | 5.0.x   | Next-generation frontend build tool  |
| [Pinia](https://pinia.vuejs.org/)             | 2.1.x   | Official Vue 3 state management      |
| [Vue Router](https://router.vuejs.org/)       | 4.2.x   | Official Vue.js router               |
| [Tailwind CSS](https://tailwindcss.com/)      | 3.4.x   | Utility-first CSS framework          |
| [ECharts](https://echarts.apache.org/)        | 6.0.x   | Data visualization chart library     |
| [Marked](https://marked.js.org/)              | 11.x    | Markdown parser                      |
| [Highlight.js](https://highlightjs.org/)      | 11.x    | Code syntax highlighting             |

### Backend

| Technology                                            | Version | Description                             |
| ----------------------------------------------------- | ------- | --------------------------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)              | 0.109.x | High-performance Python Web Framework   |
| [SQLAlchemy](https://www.sqlalchemy.org/)             | 2.0.x   | Python SQL Toolkit and ORM              |
| [PostgreSQL](https://www.postgresql.org/)             | -       | Open-source relational database         |
| [Redis](https://redis.io/)                            | -       | In-memory data structure store          |
| [Pydantic](https://pydantic-docs.helpmanual.io/)      | 2.5.x   | Data validation and settings management |
| [Python-JOSE](https://github.com/mpdavis/python-jose) | 3.3.x   | JWT token handling                      |
| [Uvicorn](https://www.uvicorn.org/)                   | 0.27.x  | ASGI server                             |

***

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

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

1. **Configure Environment Variables**

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

# Resend Email Service (Recommended)
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend

# SMTP Email Configuration (Alternative)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
```

1. **Start Backend Server**

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

1. **Configure Environment Variables**

Create a `.env` file:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

1. **Start Development Server**

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

***

## 🚀 Production Deployment

This project recommends the following free deployment options, stable and reliable for long-term personal blog operation.

### Recommended Deployment Architecture

| Component    | Platform         | Features                        | Free Tier           |
| ------------ | ---------------- | ------------------------------- | ------------------- |
| 🎨 Frontend  | Vercel / Netlify | Auto-deploy, global CDN         | Unlimited bandwidth |
| ⚙️ Backend   | Render           | Docker support, auto-sleep/wake | 750 hours/month     |
| 🗄️ Database | Neon             | Serverless, auto-scaling        | 0.5GB storage       |
| 📦 Storage   | Supabase         | CDN acceleration, S3 compatible | 5GB storage         |
| 📧 Email     | Resend           | Modern API, high deliverability | 3000 emails/month   |

***

### Option 1: Vercel + Render + Neon (Recommended)

This is the most recommended deployment option with sufficient free quotas for long-term operation.

#### Step 1: Deploy Database (Neon)

Neon provides Serverless PostgreSQL database, free tier is sufficient for personal blogs.

1. **Register Neon Account**
   - Visit [Neon](https://neon.tech/)
   - Click **Sign up** to sign in with GitHub account
2. **Create Database Project**
   - Click **Create a project**
   - Project name: `futuristic-blog`
   - Region: Recommend `AWS Asia Pacific (Singapore)` or closest to your users
   - Click **Create project**
3. **Get Database Connection String**
   - After project creation, connection info will be displayed
   - Copy the **Connection string**, format as follows:

```bash
postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> 💡 **Tip**: Neon free tier provides 0.5GB storage, sufficient for personal blogs. Database auto-sleeps when inactive, first connection may take a few seconds to wake up.

#### Step 2: Deploy Backend (Render)

Render provides free Web Service supporting Python application deployment.

1. **Register Render Account**
   - Visit [Render](https://render.com/)
   - Click **Get Started** to sign in with GitHub account
2. **Create Web Service**
   - Click **New** → **Web Service**
   - Connect GitHub repository, authorize access to `futuristic-blog` repo
   - After selecting repository, configure service:

| Setting        | Value                                              | Description                           |
| -------------- | -------------------------------------------------- | ------------------------------------- |
| Name           | `futuristic-blog-api`                              | Service name, affects default domain  |
| Region         | `Singapore` or `Oregon`                            | Choose closest to your users          |
| Branch         | `main`                                             | Deployment branch                     |
| Root Directory | `backend`                                          | **Important**: Backend code directory |
| Runtime        | `Python 3`                                         | Runtime environment                   |
| Build Command  | `pip install -r requirements.txt`                  | Install dependencies                  |
| Start Command  | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | Start command                         |
| Instance Type  | `Free`                                             | Free instance                         |

1. **Add Environment Variables**

In **Advanced** → **Environment Variables**, add the following:

**Required Environment Variables:**

```bash
# Database connection (copy from Neon)
DATABASE_URL=postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# JWT security key (generate a random string of 32+ characters)
SECRET_KEY=your-super-secret-key-at-least-32-characters-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin account (auto-created on first deploy, please change password)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourStrongPassword123!
ADMIN_EMAIL=your-email@example.com

# Frontend URL (update after deploying frontend)
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

**Optional Environment Variables:**

```bash
# Timezone setting
TIMEZONE=Asia/Shanghai

# Resend email service (recommended)
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend

# Gmail SMTP email configuration (alternative, complex setup)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Supabase file storage (for file upload functionality)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=attachments
```

1. **Deploy Service**
   - Click **Create Web Service**
   - Wait for build to complete (first time \~3-5 minutes)
   - After successful deployment, you'll get a `https://xxx.onrender.com` address

> ⚠️ **Note**: Render free instances sleep after 15 minutes of inactivity, first access may take 30-60 seconds to wake up. This is normal behavior.

#### Step 3: Deploy Frontend (Vercel)

Vercel is the best choice for frontend deployment with global CDN acceleration.

1. **Register Vercel Account**
   - Visit [Vercel](https://vercel.com/)
   - Click **Sign Up** to sign in with GitHub account
2. **Import Project**
   - Click **Add New** → **Project**
   - Select `futuristic-blog` repository
   - Click **Import**
3. **Configure Project**

| Setting          | Value           | Description                            |
| ---------------- | --------------- | -------------------------------------- |
| Framework Preset | `Vite`          | Auto-detected                          |
| Root Directory   | `frontend`      | **Important**: Frontend code directory |
| Build Command    | `npm run build` | Build command                          |
| Output Directory | `dist`          | Output directory                       |
| Install Command  | `npm install`   | Install dependencies                   |

1. **Add Environment Variable**

In **Environment Variables**, add:

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

> 💡 **Tip**: Replace `your-backend` with your backend service name created on Render.

1. **Deploy Project**
   - Click **Deploy**
   - Wait for build to complete (\~1-2 minutes)
   - After successful deployment, you'll get a `https://xxx.vercel.app` address

#### Step 4: Configure File Storage (Supabase)

For article cover and attachment upload functionality, configure Supabase Storage.

1. **Create Supabase Project**
   - Visit [Supabase](https://supabase.com/)
   - Click **Start your project** to sign in with GitHub
   - Create new organization (skip if exists)
   - Click **New project**
   - Project name: `futuristic-blog-storage`
   - Region: Choose closest to your users
   - Click **Create new project**
2. **Create Storage Bucket**
   - After entering project, click **Storage** on the left
   - Click **New bucket** to create a bucket:
     - Name: `attachments` (or custom name)
     - Enable **Public bucket** option
     - Click **Create bucket**

> 💡 **Note**: The system uses a single bucket for all files (avatars, covers, attachments), differentiated by file path.

1. **Get API Keys**
   - Click **Settings** → **API** on the left
   - Copy **Project URL** and **anon public** key
2. **Update Backend Environment Variables**
   - Return to Render backend service
   - Add environment variables:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET=attachments
```

#### Step 5: Update CORS Configuration

After frontend deployment, update backend CORS configuration:

1. Enter Render backend service
2. Click **Environment**
3. Update the following variables:

```bash
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

1. Click **Save Changes**, service will auto-redeploy

#### Step 6: Verify Deployment

1. Visit frontend URL `https://xxx.vercel.app`
2. Login with configured admin account
3. Test all functionalities

***

### Option 2: Netlify + Render + Neon

If you prefer Netlify, use this option. The only difference is the frontend deployment platform.

#### Deployment Steps

1. **Database and Backend**: Same as Option 1 Neon and Render deployment steps
2. **Deploy Frontend (Netlify)**
   - Visit [Netlify](https://www.netlify.com/)
   - Click **Sign up** to sign in with GitHub
   - Click **Add new site** → **Import an existing project**
   - Select `futuristic-blog` repository
   - Configure build:

| Setting           | Value           |
| ----------------- | --------------- |
| Base directory    | `frontend`      |
| Build command     | `npm run build` |
| Publish directory | `frontend/dist` |

1. **Add Environment Variable**:

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

1. Click **Deploy site** to complete deployment

***

### Environment Variables Reference

#### Required Environment Variables

These variables are essential for system operation, missing will cause functionality issues.

| Variable                      | Description                  | Example                          | How to Get             |
| ----------------------------- | ---------------------------- | -------------------------------- | ---------------------- |
| `DATABASE_URL`                | PostgreSQL connection string | `postgresql://user:pass@host/db` | Neon console           |
| `SECRET_KEY`                  | JWT token encryption key     | 32+ character random string      | Generate yourself      |
| `ALGORITHM`                   | Encryption algorithm         | `HS256`                          | Fixed value            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration (minutes)   | `30`                             | Set as needed          |
| `ADMIN_USERNAME`              | Admin username               | `admin`                          | Custom                 |
| `ADMIN_PASSWORD`              | Admin password               | `StrongPass123!`                 | Custom strong password |
| `ADMIN_EMAIL`                 | Admin email                  | `admin@example.com`              | Custom                 |
| `FRONTEND_URL`                | Frontend access URL          | `https://blog.vercel.app`        | Get after deployment   |
| `CORS_ORIGINS`                | CORS allowed origins         | `["https://blog.vercel.app"]`    | JSON array format      |

#### Optional Environment Variables

These variables enhance functionality, not required for core features.

| Variable            | Description                | Example                   | Purpose                     |
| ------------------- | -------------------------- | ------------------------- | --------------------------- |
| `TIMEZONE`          | Timezone setting           | `Asia/Shanghai`           | Time display                |
| `RESEND_API_KEY`    | Resend API key             | `re_xxx`                  | Email sending (recommended) |
| `RESEND_FROM_EMAIL` | Resend sender              | `onboarding@resend.dev`   | Email sending               |
| `EMAIL_PROVIDER`    | Email service provider     | `resend` or `smtp`        | Email sending               |
| `SMTP_HOST`         | SMTP server address        | `smtp.gmail.com`          | Email sending (alternative) |
| `SMTP_PORT`         | SMTP port                  | `587`                     | Email sending (alternative) |
| `SMTP_USER`         | SMTP username              | `your@gmail.com`          | Email sending (alternative) |
| `SMTP_PASSWORD`     | SMTP password/app password | `xxxx xxxx xxxx xxxx`     | Email sending (alternative) |
| `SMTP_FROM_EMAIL`   | Sender email               | `your@gmail.com`          | Email sending (alternative) |
| `SUPABASE_URL`      | Supabase project URL       | `https://xxx.supabase.co` | File storage                |
| `SUPABASE_KEY`      | Supabase anon key          | `eyJhbG...`               | File storage                |
| `SUPABASE_BUCKET`   | Storage bucket name        | `attachments`             | File storage                |

***

## 🚨 Troubleshooting Guide

### Common Deployment Issues

#### 1. Database Connection Failed

**Symptoms**: Backend startup fails, logs show database connection error

**Causes**:

- Incorrect DATABASE\_URL format
- Neon database sleeping, first connection timeout
- IP whitelist restrictions

**Solution**:

```bash
# Ensure DATABASE_URL format is correct
postgresql://username:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# Neon free tier auto-sleeps, first access may take a few seconds
# If persistent failure, check Neon console for database status
```

#### 2. CORS Error

**Symptoms**: Frontend requests to backend API show CORS error in console

**Causes**:

- Incorrect CORS\_ORIGINS configuration
- Frontend URL doesn't match configuration

**Solution**:

```bash
# Ensure CORS_ORIGINS format is correct (JSON array)
CORS_ORIGINS=["https://your-frontend.vercel.app"]

# If using custom domain, add both
CORS_ORIGINS=["https://your-frontend.vercel.app","https://yourdomain.com"]

# For local development, add local address
CORS_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]
```

#### 3. Render Service Sleeping

**Symptoms**: First access takes 30-60 seconds

**Cause**: Render free instances sleep after 15 minutes of inactivity

**Solution**:

- This is normal behavior for free services
- Use monitoring services like [UptimeRobot](https://uptimerobot.com/) to ping periodically
- Or upgrade to Render paid plan

#### 4. Frontend Build Failed

**Symptoms**: Build errors on Vercel/Netlify

**Common Causes and Solutions**:

```bash
# Cause 1: Node.js version incompatible
# Add engines field in package.json
"engines": {
  "node": ">=18.0.0"
}

# Cause 2: Dependency installation failed
# Ensure package-lock.json exists and is committed to repo

# Cause 3: Environment variable not configured
# Ensure VITE_API_BASE_URL is correctly configured
```

### Email Configuration Troubleshooting

#### 1. Resend Email Service (Highly Recommended)

Resend is a modern email API service with a free tier of 3000 emails per month, fully sufficient for personal blogs.

**Advantages**:

- 🚀 Modern API, simple integration
- 📊 Complete sending logs and statistics
- 🔒 High deliverability, less likely to be marked as spam
- 💰 Generous free tier (3000 emails/month)

**Configuration Steps**:

1. **Register Resend Account**
   - Visit [Resend](https://resend.com/)
   - Click **Sign Up** to sign in with GitHub account
   - Verify email address
2. **Get API Key**
   - After login, click **API Keys**
   - Click **Create API Key**
   - Enter name: `futuristic-blog`
   - Copy generated API key (format: `re_xxxxxxxxxxxx`)
3. **Configure Environment Variables**:

```bash
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_PROVIDER=resend
```

> **Important**: Resend free tier uses `onboarding@resend.dev` as sender by default, and can only send to the email address used when registering Resend account. To send to any email, add and verify a custom domain.

**To Send to Any Email Address**:

1. Add Custom Domain
   - In Resend dashboard, click **Domains**
   - Click **Add Domain** to add your domain
   - Configure DNS records (MX, SPF, DKIM)
   - Wait for verification
2. Update Environment Variables:

```bash
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

#### 2. Gmail SMTP Configuration (Not Recommended)

**Important Limitation**: Gmail SMTP configuration is complex with strict free account limits!

**Reasons**:

- Google disabled "Less secure app access" in May 2022
- Must use OAuth 2.0 or app-specific password (requires 2FA)
- Free Gmail accounts have \~100-500 emails/day limit
- Low deliverability, easily marked as spam

**If You Must Use Gmail SMTP**:

1. **Enable Two-Factor Authentication**
   - Visit [Google Account Security](https://myaccount.google.com/security)
   - Enable **2-Step Verification**
2. **Generate App Password**
   - Find **App passwords** in security settings
   - Click **Create new password**
   - Select **Mail** and **Other device**
   - Copy the generated 16-character password (format: `xxxx xxxx xxxx xxxx`)
3. **Configure Environment Variables**:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_EMAIL=your-email@gmail.com
EMAIL_PROVIDER=smtp
```

**Recommended Approach**:

- ✅ Use Resend (free, stable, high deliverability)
- ✅ If you have a custom domain, configure Resend domain verification

### File Upload Troubleshooting

#### 1. Supabase Bucket Permissions

**Symptoms**: Uploaded files cannot be accessed

**Solution**:

- Ensure bucket has **Public bucket** enabled
- Check SUPABASE\_KEY is anon public key (not service\_role)

#### 2. File Size Limits

**Limitations**:

- Supabase free tier: 50MB max per file
- Recommend compressing images before upload

### Security Configuration Troubleshooting

#### 1. SECRET\_KEY Generation

**Wrong Approach**:

```bash
SECRET_KEY=admin
SECRET_KEY=123456
SECRET_KEY=password
```

**Correct Approach**:

```bash
# Method 1: Use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Use OpenSSL
openssl rand -hex 32

# Method 3: Online generation
# Visit https://www.uuidgenerator.net/ to generate random string
```

#### 2. Admin Password

Change default admin password immediately after first deployment:

1. Login to admin panel
2. Go to profile settings
3. Change password

***

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

***

## License

This project is open-sourced under the [MIT License](LICENSE).

***

<div align="center">

**⭐ If this project helps you, please give it a Star! ⭐**

Made with ❤️ by [sxchou](https://github.com/sxchou)

</div>
