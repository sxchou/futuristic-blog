# 免费部署指南

本文档介绍如何将博客系统部署到完全免费的平台。

## 部署架构

```
┌─────────────────────────────────────────────┐
│  前端：Vercel（免费，CDN 加速）              │
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

| 变量名 | 值 |
|--------|-----|
| `DATABASE_URL` | Neon 数据库连接字符串 |
| `SECRET_KEY` | 随机字符串（可用 `openssl rand -hex 32` 生成） |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `DEBUG` | `false` |
| `ALLOWED_ORIGINS` | `https://你的前端域名.vercel.app` |
| `FRONTEND_URL` | `https://你的前端域名.vercel.app` |
| `USE_SUPABASE_STORAGE` | `true` |
| `SUPABASE_URL` | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | 你的 anon public key |
| `SUPABASE_BUCKET` | `blog-files` |

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

| 变量名 | 值 |
|--------|-----|
| `VITE_API_URL` | `https://你的后端地址.onrender.com` |

7. 点击 "Deploy"
8. 等待部署完成

## 第五步：更新前端 API 代理

修改 `frontend/vercel.json`，将 `your-backend.onrender.com` 替换为你的实际后端地址：

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://你的后端地址.onrender.com/api/$1"
    }
  ]
}
```

## 第六步：配置 UptimeRobot 防止休眠

1. 访问 [uptimerobot.com](https://uptimerobot.com)
2. 注册账号
3. 点击 "+ Add New Monitor"
4. 配置：
   - Monitor Type: HTTP(s)
   - Friendly Name: 博客后端
   - URL: `https://你的后端地址.onrender.com/api/health`
   - Monitoring Interval: 5 minutes
5. 点击 "Create Monitor"

## 第七步：绑定自定义域名（可选）

### Vercel 绑定域名

1. 进入 Vercel 项目设置
2. 点击 "Domains"
3. 添加你的域名
4. 按提示配置 DNS 记录

### Render 绑定域名

1. 进入 Render 项目设置
2. 点击 "Custom Domains"
3. 添加你的域名
4. 按提示配置 DNS 记录

## 免费额度汇总

| 服务 | 免费额度 | 说明 |
|------|----------|------|
| Vercel | 100GB 带宽/月 | 前端托管 |
| Render | 750 小时/月 | 后端服务 |
| Neon | 0.5GB 数据库 | 永不过期 |
| Supabase | 1GB 存储 + 5GB 数据库 | 文件存储 |
| UptimeRobot | 50 个监控 | 防止休眠 |

## 常见问题

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
| Render Starter | 不休眠 | $7/月 |
| Neon Pro | 更大数据库 | $19/月 |
| Supabase Pro | 更大存储 | $25/月 |
