# Futuristic Blog 免费部署指南：从零到上线的完整攻略

> 本文将详细介绍如何使用 Vercel + Render + Neon + Supabase 这套免费技术栈，将 Futuristic Blog 部署到云端，实现零成本上线。

## 前言

作为一名开发者，拥有一个个人博客是展示技术能力和分享知识的重要窗口。然而，服务器费用、域名成本、运维压力往往让人望而却步。本文将分享一套完全免费的部署方案，让你零成本搭建一个功能完整的个人博客系统。

## 为什么选择这套技术栈？

### 各组件优势对比

| 组件 | 平台 | 特点 | 免费额度 |
|------|------|------|----------|
| 前端 | Vercel | 自动部署、CDN | 无限带宽 |
| 后端 | Render | Docker 支持 | 750h/月 |
| 数据库 | Neon | Serverless | 0.5GB |
| 存储 | Supabase | S3 兼容 | 5GB |
| 邮件 | Gmail SMTP | 稳定可靠 | 100封/天 |

### 架构优势

1. **零成本**：所有组件都有免费额度，个人博客完全够用
2. **高可用**：全球 CDN 加速，访问速度快
3. **易维护**：自动部署，无需运维知识
4. **可扩展**：随时升级付费计划，平滑迁移

## 部署准备

在开始部署之前，请确保你拥有以下条件：

- 一个 GitHub 账户
- 一个 Gmail 邮箱（用于 SMTP 邮件服务）
- 基本的 Git 操作知识
- 大约 30 分钟的时间

## 第一步：部署数据库（Neon）

Neon 是一个 Serverless PostgreSQL 数据库服务，免费版提供 0.5GB 存储空间，对于个人博客完全够用。

### 1.1 注册 Neon 账户

1. 访问 [Neon 官网](https://neon.tech/)
2. 点击 **Sign up** 使用 GitHub 账户登录
3. 授权 Neon 访问你的 GitHub 账户

### 1.2 创建数据库项目

1. 登录后点击 **Create a project**
2. 填写项目信息：
   - 项目名称：`futuristic-blog`
   - 区域选择：建议选择 `AWS Asia Pacific (Singapore)` 或离你用户最近的区域
3. 点击 **Create project**

### 1.3 获取数据库连接字符串

项目创建成功后，页面会显示数据库连接信息。复制 **Connection string**，格式如下：

```bash
postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> **小贴士**：Neon 免费版的数据库会在无活动时自动休眠，首次连接可能需要等待几秒钟唤醒。这是正常现象，不影响使用体验。

## 第二步：部署后端（Render）

Render 是一个现代化的云平台，支持多种编程语言和框架，免费版提供 750 小时/月的运行时间。

### 2.1 注册 Render 账户

1. 访问 [Render 官网](https://render.com/)
2. 点击 **Get Started** 使用 GitHub 账户登录
3. 授权 Render 访问你的 GitHub 仓库

### 2.2 创建 Web Service

1. 点击 **New** → **Web Service**
2. 连接 GitHub 仓库：
   - 点击 **Connect account** 授权访问
   - 选择你的 `futuristic-blog` 仓库
3. 配置服务参数：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Name | futuristic-blog-api | 服务名称 |
| Region | Singapore | 选择最近区域 |
| Branch | main | 部署分支 |
| Root Directory | backend | 后端目录 |
| Runtime | Python 3 | 运行时 |
| Instance Type | Free | 免费实例 |

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2.3 配置环境变量

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

# Gmail SMTP 邮件配置（推荐）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Resend 邮件服务（需要自定义域名）
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=smtp

# Supabase 文件存储（如需文件上传功能）
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=attachments
```

### 2.4 部署服务

1. 点击 **Create Web Service**
2. 等待构建完成（首次约 3-5 分钟）
3. 部署成功后会获得一个 `https://xxx.onrender.com` 的地址

> **注意事项**：Render 免费实例会在 15 分钟无请求后休眠，首次访问可能需要等待 30-60 秒唤醒。这是正常现象，可以通过定时 ping 服务来保持唤醒状态。

## 第三步：部署前端（Vercel）

Vercel 是前端部署的最佳选择，提供全球 CDN 加速，访问速度极快。

### 3.1 注册 Vercel 账户

1. 访问 [Vercel 官网](https://vercel.com/)
2. 点击 **Sign Up** 使用 GitHub 账户登录
3. 授权 Vercel 访问你的 GitHub 仓库

### 3.2 导入项目

1. 点击 **Add New** → **Project**
2. 在 **Import Git Repository** 中找到你的 `futuristic-blog` 仓库
3. 点击 **Import**

### 3.3 配置项目

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Framework | Vite | 自动检测 |
| Root Directory | frontend | 前端目录 |
| Output Directory | dist | 输出目录 |

**Build Command:** `npm run build`

**Install Command:** `npm install`

### 3.4 添加环境变量

在 **Environment Variables** 中添加：

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

> **提示**：将 `your-backend` 替换为你在 Render 上创建的后端服务名称。

### 3.5 部署项目

1. 点击 **Deploy**
2. 等待构建完成（约 1-2 分钟）
3. 部署成功后会获得一个 `https://xxx.vercel.app` 的地址

## 第四步：配置文件存储（Supabase）

如果你需要文章封面、附件上传功能，需要配置 Supabase Storage。

### 4.1 创建 Supabase 项目

1. 访问 [Supabase 官网](https://supabase.com/)
2. 点击 **Start your project** 使用 GitHub 登录
3. 创建新组织（如已有可跳过）
4. 点击 **New project** 创建项目：
   - 项目名称：`futuristic-blog-storage`
   - 区域：选择离用户最近的区域
   - 点击 **Create new project**

### 4.2 创建存储桶

1. 进入项目后，点击左侧 **Storage**
2. 点击 **New bucket** 创建以下存储桶：

| 名称 | 用途 | 公开 |
|------|------|------|
| avatars | 用户头像 | ✅ |
| covers | 文章封面 | ✅ |
| attachments | 文章附件 | ✅ |

### 4.3 配置公开访问

1. 点击每个存储桶 → **Configuration** → **Public bucket**
2. 开启 **Public bucket** 选项

### 4.4 获取 API 密钥

1. 点击左侧 **Settings** → **API**
2. 复制 **Project URL** 和 **anon public** 密钥

### 4.5 更新后端环境变量

回到 Render 后端服务，在环境变量中添加：

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET=attachments
```

## 第五步：更新 CORS 配置

前端部署完成后，需要更新后端的 CORS 配置，确保前后端能够正常通信。

1. 进入 Render 后端服务
2. 点击 **Environment**
3. 更新以下变量：

```bash
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

4. 点击 **Save Changes**，服务会自动重新部署

## 第六步：验证部署

1. 访问前端地址 `https://xxx.vercel.app`
2. 使用配置的管理员账户登录
3. 测试各项功能：
   - 发布文章
   - 上传图片
   - 发表评论
   - 邮件通知

## 避坑指南

### 问题一：数据库连接失败

**症状**：后端启动失败，日志显示数据库连接错误

**原因分析**：
- DATABASE_URL 格式错误
- Neon 数据库休眠，首次连接超时
- IP 白名单限制

**解决方案**：

```bash
# 确保 DATABASE_URL 格式正确
postgresql://username:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# Neon 免费版会自动休眠，首次访问可能需要等待几秒
# 如果持续失败，检查 Neon 控制台是否显示数据库正常
```

### 问题二：CORS 跨域错误

**症状**：前端请求后端 API 时控制台报 CORS 错误

**原因分析**：
- CORS_ORIGINS 配置错误
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

### 问题三：Render 服务休眠

**症状**：首次访问需要等待 30-60 秒

**原因分析**：Render 免费实例会在 15 分钟无请求后休眠

**解决方案**：
- 这是正常现象，免费服务都有此限制
- 可以使用 [UptimeRobot](https://uptimerobot.com/) 等监控服务定期 ping 保持唤醒
- 或升级到 Render 付费计划

### 问题四：前端构建失败

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

## 邮件配置避坑

### Gmail SMTP 配置（推荐）

Gmail SMTP 是最稳定的免费邮件发送方案，强烈推荐使用。

**配置步骤**：

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

> **重要提示**：不要使用 Gmail 账户密码，必须使用应用专用密码！

### Resend 邮件服务

**重要限制**：Resend 免费版只能发送邮件给自己注册时的邮箱！

**如需发送给任意邮箱**：
1. 必须拥有自定义域名
2. 在 Resend 中验证域名所有权
3. 配置 DNS 记录（MX、SPF、DKIM）
4. 使用域名邮箱作为发件人

**推荐方案**：
- 如果没有自定义域名，使用 Gmail SMTP
- 如果有自定义域名，Resend 是更好的选择

## 安全配置避坑

### SECRET_KEY 生成

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

### 管理员密码

首次部署后请立即修改默认管理员密码：
1. 登录管理后台
2. 进入个人设置
3. 修改密码

## 环境变量速查表

### 必须配置

| 变量 | 说明 | 示例 |
|------|------|------|
| DATABASE_URL | 数据库连接 | Neon 控制台获取 |
| SECRET_KEY | JWT 密钥 | 32位随机字符串 |
| ADMIN_USERNAME | 管理员用户名 | admin |
| ADMIN_PASSWORD | 管理员密码 | 强密码 |
| ADMIN_EMAIL | 管理员邮箱 | admin@example.com |
| FRONTEND_URL | 前端地址 | https://xxx.vercel.app |
| CORS_ORIGINS | CORS 配置 | ["https://xxx.vercel.app"] |

其他必须变量：
- `ALGORITHM`: `HS256`（固定值）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `30`（按需设置）

### 可选配置

| 变量 | 说明 | 用途 |
|------|------|------|
| TIMEZONE | 时区 | Asia/Shanghai |
| SMTP_HOST | SMTP 地址 | smtp.gmail.com |
| SMTP_PORT | SMTP 端口 | 587 |
| SMTP_USER | SMTP 用户 | your@gmail.com |
| SMTP_PASSWORD | SMTP 密码 | 应用专用密码 |
| SUPABASE_URL | 项目 URL | 文件存储 |
| SUPABASE_KEY | anon 密钥 | 文件存储 |
| SUPABASE_BUCKET | 存储桶 | attachments |

邮件服务可选：
- `RESEND_API_KEY`: Resend API 密钥
- `RESEND_FROM_EMAIL`: Resend 发件人
- `EMAIL_PROVIDER`: `smtp` 或 `resend`

## 总结

通过本文介绍的部署方案，你可以零成本搭建一个功能完整的个人博客系统。整个部署过程大约需要 30 分钟，主要步骤包括：

1. **Neon**：创建 Serverless PostgreSQL 数据库
2. **Render**：部署 FastAPI 后端服务
3. **Vercel**：部署 Vue 3 前端应用
4. **Supabase**：配置文件存储服务
5. **Gmail SMTP**：配置邮件发送服务

这套方案的优势在于：

- **零成本**：所有组件都有免费额度
- **高可用**：全球 CDN 加速，访问速度快
- **易维护**：自动部署，无需运维知识
- **可扩展**：随时升级付费计划

希望这篇教程对你有所帮助！如果你在部署过程中遇到任何问题，欢迎在评论区留言讨论。

---

> 本文首发于 [Futuristic Blog](https://github.com/sxchou/futuristic-blog)，转载请注明出处。
