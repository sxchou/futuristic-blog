from app.core.database import SessionLocal, engine
from app.core.config import settings
from app.models import User, Category, Tag, Article, Resource, SiteConfig, OAuthProvider
from app.utils import get_password_hash
from app.utils.timezone import get_now
from datetime import datetime
from sqlalchemy import text
import sqlite3


def run_database_migrations():
    try:
        db_url = str(engine.url)
        print(f"Running migrations for database: {db_url[:50]}...")
        
        if "sqlite" in db_url:
            db_path = db_url.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(comments)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'deleted_by' not in columns:
                cursor.execute("ALTER TABLE comments ADD COLUMN deleted_by VARCHAR(20)")
                conn.commit()
                print("Migration: Added 'deleted_by' column to comments table")
            
            cursor.execute("PRAGMA table_info(article_likes)")
            like_columns = [column[1] for column in cursor.fetchall()]
            
            if like_columns:
                cursor.execute("SELECT * FROM pragma_table_info('article_likes') WHERE name='user_id'")
                result = cursor.fetchone()
                if result and result[3] == 1:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS article_likes_new (
                            id INTEGER PRIMARY KEY,
                            article_id INTEGER NOT NULL,
                            user_id INTEGER,
                            ip_address TEXT,
                            created_at TEXT,
                            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    ''')
                    cursor.execute('INSERT INTO article_likes_new SELECT * FROM article_likes')
                    cursor.execute('DROP TABLE article_likes')
                    cursor.execute('ALTER TABLE article_likes_new RENAME TO article_likes')
                    cursor.execute('CREATE INDEX IF NOT EXISTS ix_article_likes_id ON article_likes(id)')
                    conn.commit()
                    print("Migration: Updated article_likes table to allow NULL user_id for anonymous likes")
            
            conn.close()
        elif "postgresql" in db_url:
            db = SessionLocal()
            try:
                result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'deleted_by'"))
                if not result.fetchone():
                    db.execute(text("ALTER TABLE comments ADD COLUMN deleted_by VARCHAR(20)"))
                    db.commit()
                    print("Migration: Added 'deleted_by' column to comments table")
                else:
                    print("Migration: 'deleted_by' column already exists")
                
                result = db.execute(text("SELECT is_nullable FROM information_schema.columns WHERE table_name = 'article_likes' AND column_name = 'user_id'"))
                row = result.fetchone()
                if row and row[0] == 'NO':
                    db.execute(text("ALTER TABLE article_likes ALTER COLUMN user_id DROP NOT NULL"))
                    db.commit()
                    print("Migration: Updated article_likes table to allow NULL user_id for anonymous likes")
            except Exception as e:
                print(f"PostgreSQL migration error: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print(f"Migration: Unknown database type, skipping migrations")
    except Exception as e:
        print(f"Migration warning: {e}")


def init_database():
    run_database_migrations()
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_verified=True,
                bio="Full Stack Engineer | AI Explorer | Open Source Contributor",
                avatar="/avatars/admin.jpg"
            )
            db.add(admin)
            db.commit()
            print(f"Created admin user: {settings.ADMIN_USERNAME}")
        else:
            if not admin.is_verified:
                admin.is_verified = True
                db.commit()
                print(f"Updated admin user verification status: {settings.ADMIN_USERNAME}")
        
        categories_data = [
            {"name": "前端工程化", "slug": "frontend-engineering", "description": "前端架构、工程化最佳实践", "icon": "code", "color": "#00d4ff", "order": 1},
            {"name": "后端架构", "slug": "backend-architecture", "description": "后端服务设计与架构模式", "icon": "server", "color": "#7c3aed", "order": 2},
            {"name": "AI 实战", "slug": "ai-practice", "description": "人工智能应用开发实战", "icon": "brain", "color": "#f59e0b", "order": 3},
            {"name": "DevOps 笔记", "slug": "devops-notes", "description": "运维自动化与CI/CD实践", "icon": "cogs", "color": "#10b981", "order": 4},
        ]
        
        for cat_data in categories_data:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)
        
        db.commit()
        
        tags_data = [
            {"name": "FastAPI", "slug": "fastapi", "color": "#009688"},
            {"name": "Python", "slug": "python", "color": "#3776ab"},
            {"name": "API", "slug": "api", "color": "#00d4ff"},
            {"name": "高性能", "slug": "high-performance", "color": "#ff5722"},
            {"name": "Vue3", "slug": "vue3", "color": "#42b883"},
            {"name": "TypeScript", "slug": "typescript", "color": "#3178c6"},
            {"name": "Vite", "slug": "vite", "color": "#646cff"},
            {"name": "最佳实践", "slug": "best-practices", "color": "#10b981"},
            {"name": "LangChain", "slug": "langchain", "color": "#1c3c3c"},
            {"name": "LLM", "slug": "llm", "color": "#8b5cf6"},
            {"name": "OpenAI", "slug": "openai", "color": "#00a67e"},
            {"name": "RAG", "slug": "rag", "color": "#f59e0b"},
        ]
        
        for tag_data in tags_data:
            existing = db.query(Tag).filter(Tag.slug == tag_data["slug"]).first()
            if not existing:
                tag = Tag(**tag_data)
                db.add(tag)
        
        db.commit()
        
        resources_data = [
            {"title": "MDN Web Docs", "description": "Mozilla开发者网络文档", "url": "https://developer.mozilla.org", "icon": "book", "category": "学习网站", "order": 1},
            {"title": "Vue.js 官方文档", "description": "Vue 3 官方中文文档", "url": "https://cn.vuejs.org", "icon": "vuejs", "category": "学习网站", "order": 2},
            {"title": "FastAPI 官方文档", "description": "FastAPI 官方文档", "url": "https://fastapi.tiangolo.com", "icon": "python", "category": "学习网站", "order": 3},
            {"title": "VS Code", "description": "强大的代码编辑器", "url": "https://code.visualstudio.com", "icon": "code", "category": "开发工具", "order": 1},
            {"title": "GitHub", "description": "代码托管平台", "url": "https://github.com", "icon": "github", "category": "开发工具", "order": 2},
            {"title": "Dribbble", "description": "设计师作品展示平台", "url": "https://dribbble.com", "icon": "palette", "category": "设计灵感", "order": 1},
            {"title": "OpenAI API", "description": "OpenAI API文档", "url": "https://platform.openai.com", "icon": "robot", "category": "API服务", "order": 1},
        ]
        
        for res_data in resources_data:
            existing = db.query(Resource).filter(Resource.url == res_data["url"]).first()
            if not existing:
                resource = Resource(**res_data)
                db.add(resource)
        
        db.commit()
        
        articles_data = [
            {
                "title": "深入浅出 FastAPI：构建高性能 Python Web 服务",
                "slug": "fastapi-high-performance-python-web-service",
                "summary": "从基础路由到依赖注入和异步任务，全面解析 FastAPI 的核心特性与最佳实践。",
                "content": """# 深入浅出 FastAPI：构建高性能 Python Web 服务

## 为什么选择 FastAPI？

FastAPI 是一个现代、高性能的 Python Web 框架，基于 Starlette 和 Pydantic 构建。它具有以下优势：

- **高性能**：与 NodeJS 和 Go 相当的性能表现
- **快速开发**：开发效率提升约 200%-300%
- **更少的 Bug**：减少约 40% 的人为错误
- **直观易用**：强大的编辑器支持，自动补全
- **简单易学**：设计简洁，易于上手

## FastAPI vs Flask vs Django

| 特性 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 异步支持 | ✅ | ❌ | ✅ (3.0+) |
| 类型提示 | ✅ | ❌ | ❌ |
| 自动文档 | ✅ | ❌ | ❌ |
| 学习曲线 | 低 | 低 | 高 |

## 核心特性

### 1. 自动 API 文档

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.post("/items/")
async def create_item(item: Item):
    return {"item": item, "message": "Item created successfully"}
```

访问 `/docs` 即可看到自动生成的 Swagger UI 文档。

### 2. 依赖注入

```python
from fastapi import Depends, HTTPException

def get_current_user(token: str):
    # 验证 token 并返回用户
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@app.get("/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user
```

### 3. 异步支持

```python
import httpx

@app.get("/external-data")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

## 生产部署

推荐使用 Gunicorn + Uvicorn：

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 总结

FastAPI 是构建现代 Python Web 服务的最佳选择之一。它结合了高性能、开发效率和优秀的开发体验，非常适合构建 RESTful API 和微服务架构。
""",
                "category_slug": "backend-architecture",
                "tag_slugs": ["fastapi", "python", "api", "高性能"],
                "is_published": True,
                "is_featured": True
            },
            {
                "title": "Vue 3 + TypeScript + Vite：下一代前端开发体验",
                "slug": "vue3-typescript-vite-next-gen-frontend",
                "summary": "探讨如何利用 Vue 3 的组合式 API (Composition API) 和 TypeScript 提升大型应用的可维护性与开发效率。",
                "content": """# Vue 3 + TypeScript + Vite：下一代前端开发体验

## 技术栈概览

- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: JavaScript 的超集，提供静态类型检查
- **Vite**: 下一代前端构建工具

## Composition API 详解

### `<script setup>` 语法糖

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<{
  (e: 'update', value: number): void
}>()

const localCount = ref(props.count)

const doubledCount = computed(() => localCount.value * 2)

const increment = () => {
  localCount.value++
  emit('update', localCount.value)
}

onMounted(() => {
  console.log('Component mounted!')
})
</script>

<template>
  <div class="counter">
    <h2>{{ title }}</h2>
    <p>Count: {{ localCount }}</p>
    <p>Doubled: {{ doubledCount }}</p>
    <button @click="increment">Increment</button>
  </div>
</template>
```

## Pinia 状态管理

```typescript
// stores/user.ts
import { defineStore } from 'pinia'

interface User {
  id: number
  name: string
  email: string
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    isAuthenticated: false
  }),
  
  getters: {
    userName: (state) => state.user?.name ?? 'Guest'
  },
  
  actions: {
    async login(credentials: { email: string; password: string }) {
      const response = await api.login(credentials)
      this.user = response.user
      this.isAuthenticated = true
    },
    
    logout() {
      this.user = null
      this.isAuthenticated = false
    }
  }
})
```

## Vite 配置优化

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'ui': ['element-plus']
        }
      }
    }
  }
})
```

## 总结

Vue 3 + TypeScript + Vite 组合提供了卓越的开发体验，是构建现代前端应用的最佳选择。
""",
                "category_slug": "frontend-engineering",
                "tag_slugs": ["vue3", "typescript", "vite", "最佳实践"],
                "is_published": True,
                "is_featured": True
            },
            {
                "title": "LangChain 入门：构建你的第一个 AI 应用",
                "slug": "langchain-build-your-first-ai-app",
                "summary": "一篇为开发者准备的 LangChain 快速上手指南，通过实例讲解如何连接大语言模型，并构建一个简单的问答机器人。",
                "content": """# LangChain 入门：构建你的第一个 AI 应用

## 什么是 LangChain？

LangChain 是一个强大的框架，用于开发由语言模型驱动的应用程序。它提供了：

- **模型 I/O**: 与各种 LLM 的统一接口
- **Chains**: 将多个组件串联成复杂工作流
- **Agents**: 让 LLM 自主决策和执行操作
- **Memory**: 为对话提供上下文记忆
- **Retrieval**: 集成向量数据库实现 RAG

## 快速开始

### 安装依赖

```bash
pip install langchain langchain-openai chromadb
```

### 基础示例

```python
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 初始化模型
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7
)

# 发送消息
response = llm.invoke([
    SystemMessage(content="你是一个专业的 Python 开发者"),
    HumanMessage(content="请解释什么是装饰器？")
])

print(response.content)
```

## RAG (检索增强生成)

RAG 是将外部知识库与 LLM 结合的技术，让模型能够回答它训练数据中没有的信息。

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 1. 加载文档
loader = TextLoader("docs/knowledge.txt")
documents = loader.load()

# 2. 分割文档
text_splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
texts = text_splitter.split_documents(documents)

# 3. 创建向量存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    texts,
    embeddings,
    persist_directory="./chroma_db"
)

# 4. 创建问答链
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# 5. 提问
answer = qa.run("什么是 FastAPI 的核心特性？")
print(answer)
```

## Agent 示例

```python
from langchain.agents import initialize_agent, Tool
from langchain.tools import DuckDuckGoSearchRun

# 定义工具
search = DuckDuckGoSearchRun()

tools = [
    Tool(
        name="Search",
        func=search.run,
        description="用于搜索最新信息"
    )
]

# 初始化 Agent
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

# 运行
result = agent.run("2024年最新的 AI 技术趋势是什么？")
print(result)
```

## 总结

LangChain 大大简化了 AI 应用的开发流程，让开发者能够快速构建复杂的 LLM 应用。结合 RAG 技术，可以构建出具有专业领域知识的智能助手。
""",
                "category_slug": "ai-practice",
                "tag_slugs": ["langchain", "llm", "openai", "rag"],
                "is_published": True,
                "is_featured": False
            },
            {
                "title": "Docker 容器化部署：从开发到生产的完整指南",
                "slug": "docker-containerization-complete-guide",
                "summary": "全面介绍 Docker 容器化技术，包括镜像构建、容器编排、网络配置以及生产环境最佳实践。",
                "content": """# Docker 容器化部署：从开发到生产的完整指南

## 为什么选择 Docker？

Docker 彻底改变了软件交付的方式：

- **一致性**：开发、测试、生产环境完全一致
- **隔离性**：应用之间互不干扰
- **可移植性**：一次构建，到处运行
- **效率**：快速部署和扩展

## Dockerfile 最佳实践

### 多阶段构建

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Python 应用示例

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose 编排

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      - db
      - redis
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

## 生产环境优化

### 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

## 常用命令

```bash
# 构建镜像
docker build -t myapp:v1.0 .

# 运行容器
docker run -d -p 8000:8000 --name myapp myapp:v1.0

# 查看日志
docker logs -f myapp

# 进入容器
docker exec -it myapp /bin/sh

# 清理资源
docker system prune -a
```

## 总结

Docker 是现代 DevOps 的基石，掌握容器化技术对于构建可扩展、可维护的应用至关重要。
""",
                "category_slug": "devops-notes",
                "tag_slugs": ["python", "最佳实践"],
                "is_published": True,
                "is_featured": False
            },
            {
                "title": "Tailwind CSS 实战：打造未来感 UI 设计",
                "slug": "tailwind-css-futuristic-ui-design",
                "summary": "探索 Tailwind CSS 的高级用法，学习如何创建具有科技感的现代界面，包括玻璃态、渐变、动画等效果。",
                "content": """# Tailwind CSS 实战：打造未来感 UI 设计

## Tailwind CSS 简介

Tailwind CSS 是一个功能类优先的 CSS 框架，让你可以快速构建现代网站。

## 核心配置

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00d4ff',
        secondary: '#7c3aed',
        accent: '#f59e0b',
        dark: {
          50: '#f8fafc',
          100: '#1e293b',
          200: '#0f172a',
          300: '#020617',
        }
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #00d4ff, 0 0 10px #00d4ff' },
          '100%': { boxShadow: '0 0 20px #00d4ff, 0 0 30px #00d4ff' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}
```

## 玻璃态效果 (Glassmorphism)

```html
<div class="backdrop-blur-md bg-white/10 border border-white/20 rounded-2xl shadow-xl">
  <h2 class="text-white text-2xl font-bold">玻璃态卡片</h2>
  <p class="text-white/70">半透明背景 + 模糊效果</p>
</div>
```

## 渐变边框

```html
<div class="relative p-[2px] rounded-lg bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500">
  <div class="bg-dark-200 rounded-lg p-6">
    <h3 class="text-white">渐变边框卡片</h3>
  </div>
</div>
```

## 发光按钮

```html
<button class="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold rounded-lg 
               hover:shadow-[0_0_20px_rgba(0,212,255,0.5)] transition-all duration-300 
               hover:scale-105 active:scale-95">
  发光按钮
</button>
```

## 粒子背景效果

```html
<div class="fixed inset-0 overflow-hidden pointer-events-none">
  <div class="absolute w-2 h-2 bg-primary/30 rounded-full animate-float" 
       style="top: 20%; left: 10%; animation-delay: 0s;"></div>
  <div class="absolute w-3 h-3 bg-secondary/30 rounded-full animate-float" 
       style="top: 40%; left: 30%; animation-delay: 1s;"></div>
  <div class="absolute w-1 h-1 bg-accent/30 rounded-full animate-float" 
       style="top: 60%; left: 50%; animation-delay: 2s;"></div>
</div>
```

## 响应式设计

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div class="p-4 bg-dark-100 rounded-xl">卡片 1</div>
  <div class="p-4 bg-dark-100 rounded-xl">卡片 2</div>
  <div class="p-4 bg-dark-100 rounded-xl">卡片 3</div>
</div>
```

## 暗色模式

```html
<div class="bg-white dark:bg-dark-200 text-gray-900 dark:text-white">
  自动适配暗色模式
</div>
```

## 总结

Tailwind CSS 让我们能够快速构建具有未来感的 UI，通过组合各种功能类，实现复杂的设计效果。
""",
                "category_slug": "frontend-engineering",
                "tag_slugs": ["vue3", "typescript", "最佳实践"],
                "is_published": True,
                "is_featured": False
            },
            {
                "title": "PostgreSQL 性能优化：从索引到查询调优",
                "slug": "postgresql-performance-optimization",
                "summary": "深入探讨 PostgreSQL 数据库性能优化策略，包括索引设计、查询计划分析、连接池配置等核心主题。",
                "content": """# PostgreSQL 性能优化：从索引到查询调优

## 索引优化

### B-Tree 索引

```sql
-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_articles_created_at ON articles(created_at DESC);

-- 复合索引
CREATE INDEX idx_articles_category_status ON articles(category_id, status);
```

### 部分索引

```sql
-- 只索引已发布的文章
CREATE INDEX idx_published_articles ON articles(created_at) 
WHERE status = 'published';
```

### 全文搜索索引

```sql
-- 创建 GIN 索引用于全文搜索
CREATE INDEX idx_articles_content_search ON articles 
USING gin(to_tsvector('english', title || ' ' || content));

-- 搜索示例
SELECT * FROM articles 
WHERE to_tsvector('english', title || ' ' || content) @@ 
      to_tsquery('english', 'fastapi & python');
```

## 查询计划分析

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT a.*, c.name as category_name
FROM articles a
JOIN categories c ON a.category_id = c.id
WHERE a.status = 'published'
ORDER BY a.created_at DESC
LIMIT 10;
```

### 常见问题

1. **Seq Scan** - 全表扫描，考虑添加索引
2. **Nested Loop** - 大表连接效率低，考虑使用 Hash Join
3. **Filter** - 过滤条件未使用索引

## 连接池配置

### PgBouncer

```ini
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

## PostgreSQL 配置优化

```ini
# postgresql.conf

# 内存配置
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接配置
max_connections = 200

# WAL 配置
wal_buffers = 8MB
checkpoint_completion_target = 0.9

# 查询优化
random_page_cost = 1.1
effective_io_concurrency = 200
```

## 监控查询

```sql
-- 查看活跃连接
SELECT pid, usename, application_name, state, query_start
FROM pg_stat_activity
WHERE state = 'active';

-- 查看表统计信息
SELECT relname, n_live_tup, n_dead_tup, 
       last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- 查看索引使用情况
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

## 总结

PostgreSQL 性能优化需要从索引设计、查询优化、配置调优等多个维度综合考虑，持续监控和优化是保持数据库高性能的关键。
""",
                "category_slug": "backend-architecture",
                "tag_slugs": ["python", "api", "高性能"],
                "is_published": True,
                "is_featured": False
            },
            {
                "title": "OpenAI API 深度解析：GPT-4 与 Embeddings 实战",
                "slug": "openai-api-gpt4-embeddings-guide",
                "summary": "详细介绍 OpenAI API 的使用方法，包括 Chat Completions、Embeddings、Function Calling 等核心功能。",
                "content": """# OpenAI API 深度解析：GPT-4 与 Embeddings 实战

## API 基础

### 安装 SDK

```bash
pip install openai
```

### 初始化客户端

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")
```

## Chat Completions

### 基础对话

```python
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "你是一个专业的技术顾问"},
        {"role": "user", "content": "解释什么是微服务架构？"}
    ],
    temperature=0.7,
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### 流式输出

```python
stream = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[{"role": "user", "content": "写一首关于代码的诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools
)

# 处理函数调用
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    # 执行函数并返回结果
```

## Embeddings

### 生成向量

```python
def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\\n", " ")
    return client.embeddings.create(
        input=[text],
        model=model
    ).data[0].embedding

# 批量生成
texts = ["FastAPI 是一个现代 Web 框架", "Vue 3 是一个前端框架"]
embeddings = client.embeddings.create(
    input=texts,
    model="text-embedding-3-small"
)
```

### 相似度计算

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 比较文本相似度
emb1 = get_embedding("Python 是一门编程语言")
emb2 = get_embedding("JavaScript 是一门编程语言")
similarity = cosine_similarity(emb1, emb2)
print(f"相似度: {similarity:.4f}")
```

## 成本优化

### Token 计数

```python
import tiktoken

def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

text = "这是一段需要计算 token 数量的文本"
print(f"Token 数量: {count_tokens(text)}")
```

## 最佳实践

1. **使用 system prompt** 设定角色和行为约束
2. **控制 temperature** 平衡创造性和一致性
3. **设置 max_tokens** 控制成本
4. **使用流式输出** 提升用户体验
5. **缓存常见查询** 减少 API 调用

## 总结

OpenAI API 为开发者提供了强大的 AI 能力，合理使用可以构建出智能化的应用程序。
""",
                "category_slug": "ai-practice",
                "tag_slugs": ["openai", "llm", "api"],
                "is_published": True,
                "is_featured": False
            }
        ]
        
        for article_data in articles_data:
            existing = db.query(Article).filter(Article.slug == article_data["slug"]).first()
            if not existing:
                category = db.query(Category).filter(Category.slug == article_data["category_slug"]).first()
                tags = db.query(Tag).filter(Tag.slug.in_(article_data["tag_slugs"])).all()
                
                content = article_data["content"]
                words = len(content.split())
                reading_time = max(1, words // 200)
                
                article = Article(
                    title=article_data["title"],
                    slug=article_data["slug"],
                    summary=article_data["summary"],
                    content=content,
                    is_published=article_data["is_published"],
                    is_featured=article_data["is_featured"],
                    category_id=category.id if category else None,
                    author_id=admin.id,
                    reading_time=reading_time,
                    published_at=get_now() if article_data["is_published"] else None
                )
                article.tags = tags
                db.add(article)
        
        db.commit()
        
        site_configs_data = [
            {"key": "site_name", "value": "Futuristic Blog", "description": "网站名称"},
            {"key": "site_description", "value": "探索前沿技术，分享工程实践", "description": "网站描述"},
            {"key": "site_keywords", "value": "技术博客,全栈开发,AI,前端,后端", "description": "网站关键词"},
        ]
        
        for config_data in site_configs_data:
            existing = db.query(SiteConfig).filter(SiteConfig.key == config_data["key"]).first()
            if not existing:
                config = SiteConfig(**config_data)
                db.add(config)
        
        db.commit()
        
        oauth_providers_data = [
            {
                "name": "google",
                "display_name": "Google",
                "icon": "google",
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile",
                "order": 1
            },
            {
                "name": "github",
                "display_name": "GitHub",
                "icon": "github",
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user",
                "scope": "user:email read:user",
                "order": 2
            },
            {
                "name": "x",
                "display_name": "X (Twitter)",
                "icon": "twitter",
                "authorize_url": "https://twitter.com/i/oauth2/authorize",
                "token_url": "https://api.twitter.com/2/oauth2/token",
                "userinfo_url": "https://api.twitter.com/2/users/me",
                "scope": "users.read tweet.read offline.access",
                "order": 3
            },
            {
                "name": "wechat",
                "display_name": "微信",
                "icon": "wechat",
                "authorize_url": "https://open.weixin.qq.com/connect/qrconnect",
                "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
                "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
                "scope": "snsapi_userinfo",
                "order": 4
            },
            {
                "name": "qq",
                "display_name": "QQ",
                "icon": "qq",
                "authorize_url": "https://graph.qq.com/oauth2.0/authorize",
                "token_url": "https://graph.qq.com/oauth2.0/token",
                "userinfo_url": "https://graph.qq.com/user/get_user_info",
                "scope": "get_user_info,get_email",
                "order": 5
            }
        ]
        
        for provider_data in oauth_providers_data:
            existing = db.query(OAuthProvider).filter(OAuthProvider.name == provider_data["name"]).first()
            if not existing:
                provider = OAuthProvider(**provider_data)
                db.add(provider)
        
        db.commit()
        print("Database initialized with sample data!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
