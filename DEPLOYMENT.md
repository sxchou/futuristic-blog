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
│                                  │                      │
│                                  ▼                      │
│                         ┌───────────────┐              │
│                         │  PostgreSQL   │              │
│                         │  (内置数据库)  │              │
│                         └───────────────┘              │
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

# 添加远程仓库 (替换 YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/futuristic-blog.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 2. 创建 Railway 项目

1. 注册 Railway: https://railway.app
2. 点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 授权 GitHub 并选择 `futuristic-blog` 仓库

### 3. 添加 PostgreSQL 数据库

1. 在项目中点击 **"+ New"**
2. 选择 **"Database"** → **"Add PostgreSQL"**
3. 数据库会自动创建

### 4. 部署后端服务

**方式一：通过 Railway 控制台**

1. 在项目中点击 **"+ New"**
2. 选择 **"GitHub Repo"** → 选择仓库
3. 设置 **Root Directory** 为 `backend`
4. Railway 会自动检测 Dockerfile 并构建

**方式二：使用 Dockerfile（推荐）**

后端使用 Dockerfile 部署，配置环境变量：

| 变量名 | 值 |
|--------|-----|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `SECRET_KEY` | 随机字符串 |
| `CORS_ORIGINS` | `["https://your-frontend.railway.app"]` |
| `FRONTEND_URL` | `https://your-frontend.railway.app` |
| `TIMEZONE` | `Asia/Shanghai` |

### 4.1 配置持久化存储（重要！）

**⚠️ 必须配置，否则用户上传的头像会在部署时丢失！**

Railway 默认每次部署会重新构建容器，导致本地文件丢失。需要配置 Volume 持久化存储：

**方式一：通过项目画布（推荐）**

1. 在 Railway 项目页面，**右键点击项目画布空白处**
2. 或使用快捷键 `Ctrl+K` (Windows) / `⌘K` (Mac) 打开命令面板
3. 选择 **"Create Volume"**
4. 配置 Volume：
   - **Name**: `avatar-storage`
   - **Mount Path**: `/app/uploads`
5. 选择要连接的服务：你的后端服务
6. 服务会自动重启并挂载 Volume

**方式二：使用 Railway CLI**

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 链接项目
railway link

# 创建 Volume 并挂载到后端服务
railway volume create --service backend --mount /app/uploads

# 部署
railway up
```

**Railway 自动提供的环境变量**

当 Volume 连接到服务后，Railway 会自动提供以下环境变量（无需手动配置）：
- `RAILWAY_VOLUME_NAME`: Volume 名称
- `RAILWAY_VOLUME_MOUNT_PATH`: 挂载路径（如 `/app/uploads`）

**验证 Volume 配置**

1. 在项目画布中确认 Volume 已连接到后端服务
2. 点击 Volume 查看详情，确认挂载路径为 `/app/uploads`
3. 上传测试头像后重新部署，验证头像是否保留

### 5. 部署前端服务

1. 在项目中点击 **"+ New"**
2. 选择 **"GitHub Repo"** → 选择仓库
3. 设置 **Root Directory** 为 `frontend`
4. Railway 会自动检测 Dockerfile 并构建

**注意：** 前端 nginx.conf 已配置使用 Railway 内部网络连接后端：
```
proxy_pass http://backend.railway.internal:8000;
```

### 6. 配置自定义域名（可选）

1. 进入服务设置
2. 点击 **"Settings"** → **"Domains"**
3. 点击 **"Generate Domain"** 获取免费域名
4. 或添加自定义域名

---

## 环境变量配置

### 后端环境变量

在 Railway 后端服务中添加：

```bash
# 数据库 (Railway 自动提供，使用引用)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 安全密钥 (必须修改)
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@futuristic-blog.com

# CORS 配置 (替换为你的前端域名)
CORS_ORIGINS=["https://your-frontend.railway.app"]

# 前端 URL
FRONTEND_URL=https://your-frontend.railway.app

# 时区
TIMEZONE=Asia/Shanghai

# 头像存储路径（可选）
# Railway Volume 会自动提供 RAILWAY_VOLUME_MOUNT_PATH 环境变量
# 无需手动配置 AVATAR_STORAGE_PATH，除非需要覆盖默认行为
# AVATAR_STORAGE_PATH=/app/uploads

# 邮件配置（可选）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Futuristic Blog
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
│   └── package.json
├── .gitignore
└── DEPLOYMENT.md
```

---

## 常见问题

### Q: 数据库连接失败?

检查 `DATABASE_URL` 是否正确引用：
```
${{Postgres.DATABASE_URL}}
```

### Q: CORS 错误?

确保 `CORS_ORIGINS` 包含前端完整域名：
```bash
CORS_ORIGINS=["https://your-frontend.railway.app"]
```

### Q: 前端无法访问后端 API?

检查：
1. 后端服务名称是否为 `backend`
2. 后端是否正常运行
3. 查看 Railway 日志排查问题

### Q: 用户上传的头像在部署后丢失?

**原因**: Railway 每次部署会重新构建容器，本地文件系统会被清空。

**解决方案**: 配置持久化 Volume 存储

1. 在项目画布中右键点击空白处
2. 选择 "Create Volume"
3. 配置挂载路径为 `/app/uploads`
4. 连接到后端服务

详见 [4.1 配置持久化存储](#41-配置持久化存储重要)

### Q: 如何查看日志?

Railway 控制台 → 选择服务 → 点击 "Logs" 标签

### Q: 如何重启服务?

Railway 控制台 → 选择服务 → 点击 "Redeploy"

### Q: 构建失败?

常见原因：
1. `requirements.txt` 依赖安装失败
2. `package.json` 依赖安装失败
3. Dockerfile 配置错误

查看构建日志定位具体问题。

---

## 部署检查清单

- [ ] GitHub 仓库已创建
- [ ] Railway 项目已创建
- [ ] PostgreSQL 数据库已添加
- [ ] 后端服务已部署
- [ ] **后端 Volume 已配置（重要！）**
- [ ] 前端服务已部署
- [ ] 环境变量已配置
- [ ] 前端页面正常加载
- [ ] API 接口可访问
- [ ] 登录功能正常
- [ ] 头像上传功能正常

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

Railway 自动备份 PostgreSQL 数据库，也可以手动导出：

```bash
# 使用 pg_dump 备份
pg_dump $DATABASE_URL > backup.sql
```

### 监控

Railway 提供内置监控：
- CPU 使用率
- 内存使用率
- 网络流量
- 请求日志

---

## 扩展阅读

- [Railway 官方文档](https://docs.railway.app/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Vue.js 生产部署](https://vuejs.org/guide/best-practices/production-deployment.html)
