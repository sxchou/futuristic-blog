# 免费部署指南

本文档介绍如何将博客系统部署到完全免费的平台。

## 部署架构

```
┌─────────────────────────────────────────────┐
│  前端：Vercel + Cloudflare CDN（免费）       │
│  后端：Render（免费，会休眠）                │
│  数据库：Neon（免费 PostgreSQL）             │
│  存储：Supabase Storage（免费 1GB）          │
│  防休眠：UptimeRobot（免费）                 │
└─────────────────────────────────────────────┘
```

## 第一步：创建 Neon 数据库

1. 访问 [neon.tech](https://neon.tech)
2. 使用 GitHub 账号登录
3. 点击 "Create a project"
4. 填写项目名称，选择区域（推荐：Singapore）
5. 创建完成后，复制连接字符串
   ```
   postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
6. 保存这个连接字符串，后面会用到

## 第二步：创建 Supabase 存储服务

1. 访问 [supabase.com](https://supabase.com)
2. 使用 GitHub 账号登录
3. 点击 "New Project"
4. 填写项目名称和数据库密码
5. 选择区域（推荐：Singapore）
6. 等待项目创建完成（约 2 分钟）

### 创建存储桶

1. 进入项目后，点击左侧 "Storage"
2. 点击 "Create a new bucket"
3. 填写 bucket 名称（如：`blog-files`）
4. 勾选 "Public bucket"（公开访问）
5. 点击 "Create bucket"

### 获取 API 密钥

1. 点击左侧 "Settings" → "API"
2. 复制以下信息：
   - **Project URL**（如：`https://xxx.supabase.co`）
   - **anon public key**（公开密钥）
   - **Bucket Name**（你创建的存储桶名称）

## 第三步：部署后端到 Render

1. 访问 [render.com](https://render.com)
2. 使用 GitHub 账号登录
3. 点击 "New" → "Web Service"
4. 连接你的 GitHub 仓库
5. 填写配置：
   - Name: `futuristic-blog-backend`
   - Region: Singapore
   - Branch: main
   - Root Directory: `backend`
   - Runtime: Docker
   - Instance Type: Free

6. 添加环境变量：

### 必填变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DATABASE_URL` | Neon 连接字符串 | 数据库连接 |
| `SECRET_KEY` | 随机字符串 | JWT 密钥（至少 32 位） |
| `ALLOWED_ORIGINS` | `https://你的前端域名.vercel.app` | CORS 允许的域名 |
| `FRONTEND_URL` | `https://你的前端域名.vercel.app` | 前端地址 |

### 可选变量（有默认值）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ALGORITHM` | `HS256` | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | Token 过期时间（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | 刷新 Token 过期天数 |
| `ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `ADMIN_PASSWORD` | `admin123` | 管理员密码（**建议修改**） |
| `ADMIN_EMAIL` | `admin@futuristic-blog.com` | 管理员邮箱 |
| `SITE_URL` | `https://zhouzhouya.top` | 网站地址 |
| `TIMEZONE` | `Asia/Shanghai` | 时区 |
| `UPLOAD_DIR` | `uploads` | 上传目录 |

### 邮件服务变量（可选）

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `EMAIL_PROVIDER` | `resend` 或 `smtp` | 邮件提供商 |
| `RESEND_API_KEY` | API Key | Resend 邮件服务 |
| `RESEND_FROM_EMAIL` | 发件人邮箱 | Resend 发件人 |
| `SMTP_HOST` | SMTP 服务器 | SMTP 主机 |
| `SMTP_PORT` | `587` | SMTP 端口 |
| `SMTP_USER` | 用户名 | SMTP 用户 |
| `SMTP_PASSWORD` | 密码 | SMTP 密码 |
| `SMTP_FROM_EMAIL` | 发件人邮箱 | SMTP 发件人 |

### 其他变量（可选）

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `BAIDU_PUSH_TOKEN` | Token | 百度搜索推送 |
| `REDIS_URL` | Redis 连接 | 缓存服务（Render 免费版不支持） |

### Supabase 存储变量（使用云存储时填写）

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `USE_SUPABASE_STORAGE` | `true` | 启用 Supabase 存储 |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Supabase 项目 URL |
| `SUPABASE_KEY` | `anon public key` | Supabase 公开密钥 |
| `SUPABASE_BUCKET` | `blog-files` | 存储桶名称 |

7. 点击 "Create Web Service"
8. 等待部署完成，记录后端 URL（如：`https://futuristic-blog-backend.onrender.com`）

## 第四步：部署前端到 Vercel

1. 访问 [vercel.com](https://vercel.com)
2. 使用 GitHub 账号登录
3. 点击 "Add New" → "Project"
4. 选择你的 GitHub 仓库
5. 配置项目：
   - Framework Preset: Vue.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

6. 添加环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `VITE_API_URL` | `https://你的后端地址.onrender.com/api/v1` | 后端 API 地址 |

7. 点击 "Deploy"
8. 等待部署完成

## 第五步：配置 UptimeRobot 防止休眠

1. 访问 [uptimerobot.com](https://uptimerobot.com)
2. 注册账号
3. 点击 "+ Add New Monitor"
4. 配置：
   - Monitor Type: HTTP(s)
   - Friendly Name: 博客后端
   - URL: `https://你的后端地址.onrender.com/api/health`
   - Monitoring Interval: 5 minutes
5. 点击 "Create Monitor"

## 第六步：绑定自定义域名 + Cloudflare CDN 加速（推荐）

> **重要**：Vercel 默认域名 `vercel.app` 在中国无法访问，必须绑定自定义域名并使用 Cloudflare CDN 加速。

### 6.1 Vercel 绑定域名

1. 进入 Vercel 项目 → Settings → Domains
2. 输入你的域名（如 `www.example.com` 和 `example.com`）
3. 点击 "Add" 添加域名
4. 记录 Vercel 提供的 DNS 配置信息

### 6.2 Cloudflare 配置

#### 将域名托管到 Cloudflare

1. 访问 [dash.cloudflare.com](https://dash.cloudflare.com)
2. 使用 GitHub 账号登录
3. 点击 "Add a site" 添加你的域名
4. 选择 **Free** 免费计划
5. Cloudflare 会扫描现有 DNS 记录
6. 记录 Cloudflare 提供的两个 NS 服务器地址（如 `bob.ns.cloudflare.com` 和 `coco.ns.cloudflare.com`）
7. 前往你的域名注册商（如阿里云、腾讯云、GoDaddy），修改域名的 NS 服务器为 Cloudflare 提供的地址
8. 等待 NS 生效（通常 24 小时内，最快几分钟）

#### 添加 DNS 记录

在 Cloudflare 控制台 → 选择你的域名 → DNS → Records 中添加以下记录：

| 类型 | 名称 | 内容 | 代理状态 | TTL |
|------|------|------|----------|-----|
| CNAME | `www` | `cname-china.vercel-dns.com` | ✅ 已代理（橙色云朵） | 自动 |
| CNAME | `@` | `cname-china.vercel-dns.com` | ✅ 已代理（橙色云朵） | 自动 |

**操作步骤：**
1. 点击 "Add Record"
2. 选择类型为 `CNAME`
3. 名称填写 `www` 或 `@`（@ 代表根域名）
4. 目标填写 `cname-china.vercel-dns.com`
5. 确保代理状态开关打开（显示橙色云朵图标）
6. 点击 "Save"

> **重要**：使用 `cname-china.vercel-dns.com` 而非 Vercel 默认提供的地址，这是专门为中国优化的 CNAME。

#### SSL/TLS 配置

1. 进入 SSL/TLS → 概述
2. 加密模式选择 **完全（严格）**
3. 确保 "始终使用 HTTPS" 已开启
4. 可选：开启 "自动 HTTPS 重写"

> **说明**：Vercel 已提供 SSL 证书，Cloudflare 需要设置为"完全（严格）"模式以避免证书错误。

#### 优化设置（可选）

在 **速度 → 优化** 中开启：
- **Auto Minify**：勾选 CSS、JavaScript、HTML（自动压缩代码）
- **Brotli**：开启（更好的压缩算法）
- **Early Hints**：开启（预加载提示，加快首屏加载）
- **Rocket Loader**：可选开启（异步加载 JavaScript）

#### 缓存配置（可选）

在 **缓存 → 配置** 中：
- 缓存级别：标准
- 浏览器缓存 TTL：4 小时或更长

### 6.3 更新后端 CORS 配置

在 Render 环境变量中更新 `ALLOWED_ORIGINS`：

```
https://你的域名.com,https://www.你的域名.com
```

### 6.4 更新前端环境变量

在 Vercel 环境变量中更新 `VITE_API_URL`：

```
https://你的后端地址.onrender.com/api/v1
```

> **注意**：后端不需要通过 Cloudflare 代理，直接使用 Render 地址即可。

### 6.5 验证配置

1. 等待 DNS 生效（通常 5-10 分钟）
2. 访问你的域名，确认网站正常加载
3. 检查 Cloudflare 控制台的流量统计

## 第七步：Render 后端绑定自定义域名（可选）

1. 进入 Render 项目设置
2. 点击 "Custom Domains"
3. 添加你的域名
4. 按提示配置 DNS 记录

## 免费额度汇总

| 服务 | 免费额度 | 说明 |
|------|----------|------|
| Vercel | 100GB 带宽/月 | 前端托管 |
| Cloudflare | 无限带宽 | CDN 加速 + DNS |
| Render | 750 小时/月 | 后端服务 |
| Neon | 0.5GB 数据库 | 永不过期 |
| Supabase | 1GB 存储 + 5GB 数据库 | 文件存储 |
| UptimeRobot | 50 个监控 | 防止休眠 |

## 常见问题

### Q: 网站在中国无法访问？
A: Vercel 默认域名 `vercel.app` 在中国被墙。解决方案：绑定自定义域名并使用 Cloudflare CDN 加速（参考第六步）。

### Q: Cloudflare CDN 配置后仍然无法访问？
A: 
1. 确认 DNS 记录使用的是 `cname.vercel-dns.com`
2. 确认代理状态（橙色云朵）已开启
3. 等待 DNS 生效（最多 48 小时，通常 5-10 分钟）
4. 清除浏览器缓存后重试

### Q: Render 服务休眠后首次访问很慢？
A: 这是正常现象，使用 UptimeRobot 每 5 分钟访问一次可以大幅减少休眠。

### Q: 数据库连接失败？
A: 检查 Neon 数据库是否处于活跃状态，免费版数据库一段时间不用会休眠。

### Q: 文件上传失败？
A: 检查 Supabase Storage 配置是否正确，确保 bucket 已设置为公开访问。

### Q: 如何查看日志？
A: 
- Vercel: 项目页面 → Deployments → 点击部署 → Functions
- Render: 项目页面 → Logs

## 维护建议

1. 定期备份数据库（Neon 支持自动备份）
2. 监控服务状态（UptimeRobot 会发送邮件通知）
3. 关注免费额度使用情况
4. 定期更新依赖包

## 升级建议

如果免费额度不够用，可以考虑：

| 服务 | 付费方案 | 价格 |
|------|----------|------|
| Vercel Pro | 更多带宽和功能 | $20/月 |
| Cloudflare Pro | 更多安全和性能功能 | $20/月 |
| Render Starter | 不休眠 | $7/月 |
| Neon Pro | 更大数据库 | $19/月 |
| Supabase Pro | 更大存储 | $25/月 |
