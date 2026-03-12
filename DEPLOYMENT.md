# Futuristic Blog 部署指南

## Railway 全栈部署（推荐）

### 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                     Railway 项目                         │
│                                                         │
│  ┌─────────────────┐     ┌─────────────────┐           │
│  │   Frontend      │     │    Backend      │           │
│  │   (Nginx)       │────▶│   (FastAPI)     │           │
│  │   Port: 80      │     │   Port: 8000    │           │
│  └─────────────────┘     └─────────────────┘           │
│          │                       │                      │
│          │                       │                      │
│          │              ┌────────┴────────┐            │
│          │              │                 │            │
│          │              │   PostgreSQL    │            │
│          │              │   (内置数据库)   │            │
│          │              │                 │            │
│          │              └─────────────────┘            │
│          │                                              │
│          ▼                                              │
│    静态文件 (Vue 3)                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 费用预估

| 服务 | 配置 | 预估费用/月 |
|------|------|-------------|
| Frontend | 0.25 vCPU, 256MB | ~$1 |
| Backend | 0.5 vCPU, 512MB | ~$2 |
| PostgreSQL | 0.25 vCPU, 256MB, 500MB存储 | ~$1 |
| **总计** | - | **~$4-5** |

✅ **$5/月 免费额度完全够用**

---

## 部署步骤

### 1. 准备 GitHub 仓库

```bash
# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Futuristic Blog"

# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/futuristic-blog.git

# 推送到 GitHub
git push -u origin main
```

### 2. 创建 Railway 项目

1. 注册 Railway: https://railway.app
2. 点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 授权 GitHub 并选择 `futuristic-blog` 仓库

### 3. 添加 PostgreSQL 数据库

1. 在项目中点击 **"+ New"**
2. 选择 **"Database"** → **"PostgreSQL"**
3. 数据库会自动创建并连接

### 4. 配置后端服务

1. 在项目中点击 **"+ New"**
2. 选择 **"GitHub Repo"** → 选择仓库
3. 设置 **Root Directory** 为 `backend`
4. 添加环境变量:

| 变量名 | 值 |
|--------|-----|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (自动引用) |
| `SECRET_KEY` | 随机字符串 (如: `openssl rand -hex 32`) |
| `CORS_ORIGINS` | `["https://your-frontend.railway.app"]` |
| `FRONTEND_URL` | `https://your-frontend.railway.app` |
| `TIMEZONE` | `Asia/Shanghai` |

### 5. 配置前端服务

1. 在项目中点击 **"+ New"**
2. 选择 **"GitHub Repo"** → 选择仓库
3. 设置 **Root Directory** 为 `frontend`
4. 添加环境变量:

| 变量名 | 值 |
|--------|-----|
| `BACKEND_URL` | `https://your-backend.railway.app` |

### 6. 配置自定义域名（可选）

1. 进入服务设置
2. 点击 **"Domains"**
3. 添加自定义域名
4. 配置 DNS 解析

---

## 环境变量配置

### 后端环境变量

```bash
# 数据库 (Railway 自动提供)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 安全密钥
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@futuristic-blog.com

# CORS 配置
CORS_ORIGINS=["https://your-frontend.railway.app"]

# 前端 URL
FRONTEND_URL=https://your-frontend.railway.app

# 时区
TIMEZONE=Asia/Shanghai

# 邮件配置 (可选)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Futuristic Blog
```

### 前端环境变量

```bash
# 后端 API 地址
BACKEND_URL=https://your-backend.railway.app
```

---

## 项目文件结构

```
futuristic-blog/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── Dockerfile
│   ├── railway.toml
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   └── main.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── railway.toml
│   └── package.json
├── railway.json
├── .gitignore
└── DEPLOYMENT.md
```

---

## 常见问题

### Q: 数据库连接失败?

检查 `DATABASE_URL` 是否正确引用:
```
${{Postgres.DATABASE_URL}}
```

### Q: CORS 错误?

确保 `CORS_ORIGINS` 包含前端完整域名:
```bash
CORS_ORIGINS=["https://your-frontend.railway.app"]
```

### Q: 前端无法访问后端 API?

检查 nginx 配置中的 `BACKEND_URL` 环境变量是否正确设置。

### Q: 如何查看日志?

Railway 控制台 → 选择服务 → 点击 "Logs" 标签

### Q: 如何重启服务?

Railway 控制台 → 选择服务 → 点击 "Redeploy"

---

## 部署检查清单

- [ ] GitHub 仓库已创建
- [ ] Railway 项目已创建
- [ ] PostgreSQL 数据库已添加
- [ ] 后端服务已部署
- [ ] 前端服务已部署
- [ ] 环境变量已配置
- [ ] 数据库迁移已执行
- [ ] 管理员账户已创建
- [ ] 前端页面正常加载
- [ ] API 接口可访问
- [ ] 登录功能正常

---

## Railway 常用命令

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 链接项目
railway link

# 部署
railway up

# 查看日志
railway logs

# 打开控制台
railway open
```

---

## 备份与监控

### 数据库备份

Railway 自动备份 PostgreSQL 数据库，也可以手动导出:

```bash
# 使用 pg_dump 备份
pg_dump $DATABASE_URL > backup.sql
```

### 监控

Railway 提供内置监控:
- CPU 使用率
- 内存使用率
- 网络流量
- 请求日志

---

## 扩展阅读

- [Railway 官方文档](https://docs.railway.app/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Vue.js 生产部署](https://vuejs.org/guide/best-practices/production-deployment.html)
