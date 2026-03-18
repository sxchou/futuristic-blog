"""
生成20篇高质量测试文章用于测试文章归档功能
时间范围：覆盖近2年（从当前日期向前推算24个月）
日期分布：均匀分布在不同月份，避免集中在单一时间段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import User, Category, Tag, Article
from app.utils.timezone import get_now


ARTICLES_DATA = [
    {
        "title": "深入理解 Vue 3 响应式原理",
        "slug": "deep-dive-vue3-reactivity-system",
        "summary": "探索 Vue 3 响应式系统的核心实现，包括 Proxy、Reflect 和依赖收集机制。",
        "content": """# 深入理解 Vue 3 响应式原理

## 引言

Vue 3 的响应式系统是其核心特性之一，相比 Vue 2 使用 Object.defineProperty，Vue 3 采用了更强大的 Proxy API。本文将深入探讨其实现原理。

## Proxy vs Object.defineProperty

Vue 2 的响应式实现存在一些局限性：

- 无法检测对象属性的添加或删除
- 无法监控数组索引和长度的变化
- 需要递归遍历对象的所有属性

Vue 3 使用 Proxy 解决了这些问题：

```javascript
const reactive = (target) => {
  return new Proxy(target, {
    get(target, key, receiver) {
      track(target, key)
      return Reflect.get(target, key, receiver)
    },
    set(target, key, value, receiver) {
      const result = Reflect.set(target, key, value, receiver)
      trigger(target, key)
      return result
    }
  })
}
```

## 依赖收集

Vue 3 使用 WeakMap 和 Set 进行依赖收集：

```javascript
const targetMap = new WeakMap()
let activeEffect = null

function track(target, key) {
  if (!activeEffect) return
  
  let depsMap = targetMap.get(target)
  if (!depsMap) {
    targetMap.set(target, (depsMap = new Map()))
  }
  
  let dep = depsMap.get(key)
  if (!dep) {
    depsMap.set(key, (dep = new Set()))
  }
  
  dep.add(activeEffect)
}

function trigger(target, key) {
  const depsMap = targetMap.get(target)
  if (!depsMap) return
  
  const dep = depsMap.get(key)
  if (dep) {
    dep.forEach(effect => effect())
  }
}
```

## 实际应用

```vue
<script setup>
import { ref, computed, watch } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

watch(doubled, (newVal) => {
  console.log('Doubled value:', newVal)
})
</script>
```

## 结论

Vue 3 的响应式系统通过 Proxy 实现了更完善的数据监听能力，配合 Composition API，让状态管理更加灵活和直观。理解其原理有助于我们更好地调试和优化应用。
""",
        "category_slug": "frontend-engineering",
        "tag_slugs": ["vue3", "typescript"],
        "reading_time": 8
    },
    {
        "title": "FastAPI 中间件与请求生命周期",
        "slug": "fastapi-middleware-request-lifecycle",
        "summary": "详解 FastAPI 的中间件机制，理解请求从进入到响应的完整生命周期。",
        "content": """# FastAPI 中间件与请求生命周期

## 引言

理解 FastAPI 的请求处理流程对于构建高性能 Web 应用至关重要。本文将深入探讨中间件机制和请求生命周期。

## 请求生命周期

FastAPI 的请求处理流程：

1. 请求到达 ASGI 服务器
2. 中间件预处理
3. 路由匹配
4. 依赖注入
5. 路径操作函数执行
6. 响应序列化
7. 中间件后处理
8. 返回客户端

## 中间件实现

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

## CORS 中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 自定义中间件类

```python
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api"):
            token = request.headers.get("Authorization")
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized"}
                )
        
        return await call_next(request)
```

## 结论

合理使用中间件可以实现横切关注点的统一处理，如认证、日志、性能监控等，是构建企业级应用的重要工具。
""",
        "category_slug": "backend-architecture",
        "tag_slugs": ["fastapi", "python", "api"],
        "reading_time": 6
    },
    {
        "title": "使用 RAG 构建企业知识库问答系统",
        "slug": "build-enterprise-knowledge-qa-with-rag",
        "summary": "基于 LangChain 和向量数据库，构建一个能够回答企业内部知识库问题的智能问答系统。",
        "content": """# 使用 RAG 构建企业知识库问答系统

## 引言

企业内部积累了大量的文档、手册和知识库，如何让员工快速找到需要的信息是一个挑战。RAG（检索增强生成）技术提供了解决方案。

## 技术架构

```
用户提问 → 向量检索 → 相关文档 → LLM 生成答案
```

## 实现步骤

### 1. 文档预处理

```python
from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = DirectoryLoader("./docs", glob="**/*.pdf", loader_cls=PyPDFLoader)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
texts = text_splitter.split_documents(documents)
```

### 2. 向量存储

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    texts,
    embeddings,
    persist_directory="./chroma_db"
)
```

### 3. 问答链

```python
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )
)

answer = qa.run("公司的报销流程是什么？")
```

## 优化策略

- **混合检索**：结合关键词和向量检索
- **重排序**：使用 Cross-Encoder 对检索结果重排序
- **引用溯源**：在回答中标注信息来源

## 结论

RAG 技术让企业能够快速构建智能问答系统，提升知识管理效率。
""",
        "category_slug": "ai-practice",
        "tag_slugs": ["langchain", "rag", "llm"],
        "reading_time": 7
    },
    {
        "title": "Kubernetes 集群监控最佳实践",
        "slug": "kubernetes-cluster-monitoring-best-practices",
        "summary": "介绍 Kubernetes 集群监控的完整方案，包括 Prometheus、Grafana 和告警配置。",
        "content": """# Kubernetes 集群监控最佳实践

## 引言

在生产环境中运行 Kubernetes 集群，完善的监控系统是必不可少的。本文将介绍如何构建完整的监控体系。

## Prometheus 架构

Prometheus 是 Kubernetes 监控的核心组件：

- **Prometheus Server**：数据采集和存储
- **Alertmanager**：告警处理和通知
- **Pushgateway**：短期任务指标推送
- **Exporters**：暴露各种服务的指标

## 部署 Prometheus Stack

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
```

## 关键指标

### 集群级别

- 节点 CPU/内存使用率
- Pod 调度延迟
- 网络流量

### 应用级别

- 请求 QPS
- 响应延迟
- 错误率

## Grafana 仪表盘

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.0.0
        ports:
        - containerPort: 3000
```

## 告警规则

```yaml
groups:
- name: node-alerts
  rules:
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
```

## 结论

完善的监控体系是保障 Kubernetes 集群稳定运行的基础。
""",
        "category_slug": "devops-notes",
        "tag_slugs": ["python", "最佳实践"],
        "reading_time": 8
    },
    {
        "title": "TypeScript 高级类型体操指南",
        "slug": "typescript-advanced-type-gymnastics",
        "summary": "深入 TypeScript 类型系统，掌握条件类型、映射类型和模板字面量类型等高级技巧。",
        "content": """# TypeScript 高级类型体操指南

## 引言

TypeScript 的类型系统是图灵完备的，这意味着我们可以用类型来进行复杂的计算。本文将介绍一些高级类型技巧。

## 条件类型

```typescript
type IsString = T extends string ? true : false;

type A = IsString<string>; // true
type B = IsString<number>; // false
```

## 映射类型

```typescript
type Readonly = {
  readonly [P in keyof T]: T[P];
};

type Partial = {
  [P in keyof T]?: T[P];
};

interface User {
  id: number;
  name: string;
}

type ReadonlyUser = Readonly<User>;
type PartialUser = Partial<User>;
```

## 模板字面量类型

```typescript
type EventName = `on${Capitalize}`;

type MouseEvents = EventName<'click' | 'mousedown' | 'mouseup'>;
// "onClick" | "onMousedown" | "onMouseup"
```

## 实用工具类型

### DeepReadonly

```typescript
type DeepReadonly = {
  readonly [P in keyof T]: T[P] extends object 
    ? DeepReadonly<T[P]> 
    : T[P];
};
```

### UnionToIntersection

```typescript
type UnionToIntersection = (
  T extends any ? (x: T) => any : never
) extends (x: infer R) => any 
  ? R 
  : never;
```

### RequiredKeys

```typescript
type RequiredKeys = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K;
}[keyof T];
```

## 实战案例

### API 响应类型

```typescript
type ApiResponse = {
  code: number;
  message: string;
  data: T;
};

type UserResponse = ApiResponse<{
  id: number;
  name: string;
  email: string;
}>;
```

## 结论

掌握 TypeScript 高级类型技巧，可以让我们写出更安全、更优雅的代码。
""",
        "category_slug": "frontend-engineering",
        "tag_slugs": ["typescript", "最佳实践"],
        "reading_time": 10
    },
    {
        "title": "PostgreSQL 性能优化实战",
        "slug": "postgresql-performance-optimization",
        "summary": "从索引设计到查询优化，全面介绍 PostgreSQL 数据库性能调优的方法。",
        "content": """# PostgreSQL 性能优化实战

## 引言

PostgreSQL 是一款功能强大的开源数据库，但不当的使用方式会导致性能问题。本文将介绍常见的优化技巧。

## 索引优化

### 选择合适的索引类型

```sql
-- B-tree 索引（默认）
CREATE INDEX idx_users_email ON users(email);

-- GIN 索引（用于全文搜索）
CREATE INDEX idx_articles_content ON articles USING gin(to_tsvector('english', content));

-- 部分索引
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- 表达式索引
CREATE INDEX idx_lower_email ON users(lower(email));
```

### 索引使用分析

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

## 查询优化

### 避免 SELECT *

```sql
-- 不推荐
SELECT * FROM articles;

-- 推荐
SELECT id, title, summary FROM articles;
```

### 使用 JOIN 替代子查询

```sql
-- 较慢
SELECT * FROM articles WHERE author_id IN (SELECT id FROM users WHERE is_active = true);

-- 较快
SELECT a.* FROM articles a
JOIN users u ON a.author_id = u.id
WHERE u.is_active = true;
```

## 连接池配置

```python
# SQLAlchemy 连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## VACUUM 和 ANALYZE

```sql
-- 手动执行 VACUUM
VACUUM ANALYZE articles;

-- 配置自动 VACUUM
ALTER TABLE articles SET (
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.1
);
```

## 结论

数据库优化是一个持续的过程，需要结合实际业务场景进行调整。
""",
        "category_slug": "backend-architecture",
        "tag_slugs": ["python", "高性能"],
        "reading_time": 9
    },
    {
        "title": "OpenAI API 高级应用技巧",
        "slug": "openai-api-advanced-techniques",
        "summary": "探索 OpenAI API 的高级用法，包括 Function Calling、流式响应和成本优化。",
        "content": """# OpenAI API 高级应用技巧

## 引言

OpenAI API 提供了强大的 AI 能力，但如何高效使用它需要一些技巧。本文将介绍高级应用方法。

## Function Calling

```python
from openai import OpenAI

client = OpenAI()

functions = [
    {
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
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    functions=functions
)
```

## 流式响应

```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "写一首关于春天的诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 成本优化

### 使用更便宜的模型

```python
# 简单任务使用 gpt-3.5-turbo
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "翻译成英文：你好"}]
)
```

### 控制输出长度

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "总结这篇文章"}],
    max_tokens=100
)
```

## 错误处理

```python
from openai import RateLimitError, APIError
import time

def call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            time.sleep(2 ** i)
        except APIError as e:
            if i == max_retries - 1:
                raise e
```

## 结论

合理使用 OpenAI API 可以在保证效果的同时控制成本。
""",
        "category_slug": "ai-practice",
        "tag_slugs": ["openai", "llm", "api"],
        "reading_time": 7
    },
    {
        "title": "CI/CD 流水线设计模式",
        "slug": "cicd-pipeline-design-patterns",
        "summary": "介绍现代软件开发中的 CI/CD 流水线设计模式，实现自动化构建、测试和部署。",
        "content": """# CI/CD 流水线设计模式

## 引言

持续集成和持续部署（CI/CD）是现代软件开发的核心实践。本文将介绍常见的流水线设计模式。

## GitHub Actions 实践

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=app tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t myapp:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker tag myapp:${{ github.sha }} registry.example.com/myapp:latest
        docker push registry.example.com/myapp:latest
```

## 部署策略

### 蓝绿部署

```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
  - name: Deploy to blue
    run: kubectl apply -f k8s/blue.yaml
  
  - name: Switch traffic
    run: kubectl patch service myapp -p '{"spec":{"selector":{"version":"blue"}}}'
  
  - name: Cleanup green
    run: kubectl delete -f k8s/green.yaml --ignore-not-found
```

### 金丝雀发布

```yaml
canary:
  runs-on: ubuntu-latest
  steps:
  - name: Deploy canary
    run: kubectl apply -f k8s/canary.yaml
  
  - name: Monitor metrics
    run: ./scripts/check-metrics.sh
  
  - name: Promote or rollback
    run: ./scripts/promote-or-rollback.sh
```

## 结论

设计良好的 CI/CD 流水线可以大大提高开发效率和代码质量。
""",
        "category_slug": "devops-notes",
        "tag_slugs": ["python", "最佳实践"],
        "reading_time": 8
    },
    {
        "title": "Vue 3 组件设计模式",
        "slug": "vue3-component-design-patterns",
        "summary": "探讨 Vue 3 中的组件设计模式，包括组合式函数、渲染函数和插槽的高级用法。",
        "content": """# Vue 3 组件设计模式

## 引言

良好的组件设计是构建可维护前端应用的关键。本文将介绍 Vue 3 中的几种常见设计模式。

## 组合式函数 (Composables)

```typescript
// composables/useFetch.ts
import { ref, watchEffect } from 'vue'

export function useFetch<T>(url: string) {
  const data = ref<T | null>(null)
  const error = ref<Error | null>(null)
  const loading = ref(true)

  watchEffect(async () => {
    try {
      loading.value = true
      const response = await fetch(url)
      data.value = await response.json()
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  })

  return { data, error, loading }
}
```

## 无渲染组件

```vue
<!-- Fetcher.vue -->
<script setup lang="ts">
import { ref, watchEffect } from 'vue'

const props = defineProps<{
  url: string
}>()

const data = ref(null)
const error = ref(null)
const loading = ref(true)

watchEffect(async () => {
  try {
    loading.value = true
    const response = await fetch(props.url)
    data.value = await response.json()
  } catch (e) {
    error.value = e
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <slot :data="data" :error="error" :loading="loading" />
</template>
```

## 使用示例

```vue
<template>
  <Fetcher :url="apiUrl" v-slot="{ data, loading, error }">
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <div v-else>
      <ArticleCard v-for="article in data" :key="article.id" :article="article" />
    </div>
  </Fetcher>
</template>
```

## 高阶组件

```typescript
// withLoading.ts
import { defineComponent, h } from 'vue'

export function withLoading(WrappedComponent: any) {
  return defineComponent({
    props: ['loading', ...WrappedComponent.props],
    setup(props, { slots }) {
      return () => {
        if (props.loading) {
          return h('div', { class: 'loading' }, 'Loading...')
        }
        return h(WrappedComponent, props, slots)
      }
    }
  })
}
```

## 结论

掌握这些设计模式可以帮助我们构建更加灵活和可复用的组件。
""",
        "category_slug": "frontend-engineering",
        "tag_slugs": ["vue3", "typescript", "最佳实践"],
        "reading_time": 9
    },
    {
        "title": "Redis 缓存策略与实践",
        "slug": "redis-caching-strategies",
        "summary": "深入探讨 Redis 缓存的各种策略，包括缓存穿透、击穿、雪崩的解决方案。",
        "content": """# Redis 缓存策略与实践

## 引言

Redis 是最流行的缓存解决方案之一，但不当的使用方式可能导致性能问题。本文将介绍缓存的最佳实践。

## 缓存策略

### Cache-Aside Pattern

```python
def get_user(user_id: int):
    # 1. 先查缓存
    cache_key = f"user:{user_id}"
    cached = redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # 2. 缓存未命中，查数据库
    user = db.query(User).get(user_id)
    
    # 3. 写入缓存
    redis.setex(cache_key, 3600, json.dumps(user.to_dict()))
    
    return user
```

### Write-Through Pattern

```python
def update_user(user_id: int, data: dict):
    # 1. 更新数据库
    user = db.query(User).get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    
    # 2. 同步更新缓存
    cache_key = f"user:{user_id}"
    redis.setex(cache_key, 3600, json.dumps(user.to_dict()))
    
    return user
```

## 常见问题解决

### 缓存穿透

```python
def get_user(user_id: int):
    cache_key = f"user:{user_id}"
    cached = redis.get(cache_key)
    
    if cached == "NULL":
        return None  # 防止穿透
    
    if cached:
        return json.loads(cached)
    
    user = db.query(User).get(user_id)
    
    if not user:
        # 缓存空值，设置较短过期时间
        redis.setex(cache_key, 60, "NULL")
        return None
    
    redis.setex(cache_key, 3600, json.dumps(user.to_dict()))
    return user
```

### 缓存击穿

```python
import threading

lock = threading.Lock()

def get_hot_data(key: str):
    cached = redis.get(key)
    if cached:
        return cached
    
    with lock:
        # 双重检查
        cached = redis.get(key)
        if cached:
            return cached
        
        data = db.query_hot_data()
        redis.setex(key, 3600, data)
        return data
```

### 缓存雪崩

```python
import random

def set_cache_with_jitter(key: str, value: str, base_ttl: int):
    # 添加随机偏移，避免同时过期
    jitter = random.randint(0, 300)
    redis.setex(key, base_ttl + jitter, value)
```

## 结论

合理使用缓存策略可以大幅提升系统性能，但需要注意处理各种边界情况。
""",
        "category_slug": "backend-architecture",
        "tag_slugs": ["python", "高性能", "api"],
        "reading_time": 8
    },
    {
        "title": "LLM Prompt 工程技巧",
        "slug": "llm-prompt-engineering-tips",
        "summary": "掌握大语言模型的提示工程技巧，让 AI 输出更准确、更有用的结果。",
        "content": """# LLM Prompt 工程技巧

## 引言

Prompt 工程是与大语言模型有效沟通的关键技能。本文将介绍一些实用的技巧。

## 基础原则

### 明确指令

```
请将以下英文翻译成中文，要求：
1. 保持原文的语气和风格
2. 专业术语保留英文
3. 输出格式为 Markdown

原文：[待翻译内容]
```

### 提供示例

```
任务：从文本中提取实体

示例：
输入：苹果公司 CEO 蒂姆·库克宣布新产品发布
输出：{"组织": "苹果公司", "人物": "蒂姆·库克", "事件": "新产品发布"}

输入：特斯拉在上海建设超级工厂
输出：
```

## 高级技巧

### Chain-of-Thought

```
问题：一个篮子里有 5 个苹果，拿走 2 个，又放进 3 个，请问篮子里现在有几个苹果？

让我们一步步思考：
1. 篮子里最初有 5 个苹果
2. 拿走 2 个后，剩下 5 - 2 = 3 个
3. 放进 3 个后，变成 3 + 3 = 6 个
4. 所以篮子里现在有 6 个苹果
```

### Few-Shot Learning

```
判断以下句子的情感：

句子：这部电影太精彩了！
情感：正面

句子：服务态度很差，不会再来了。
情感：负面

句子：产品质量一般，价格偏高。
情感：
```

### 角色扮演

```
你是一位资深的前端架构师，有 10 年以上的开发经验。请从以下角度分析这个技术方案：
1. 可维护性
2. 性能影响
3. 团队学习成本
4. 长期演进方向

技术方案：[待分析内容]
```

## 结构化输出

```
请分析以下文章，并以 JSON 格式输出：

{
  "title": "文章标题",
  "summary": "100字以内的摘要",
  "keywords": ["关键词1", "关键词2"],
  "sentiment": "positive/negative/neutral"
}

文章内容：[待分析内容]
```

## 结论

好的 Prompt 可以显著提升 LLM 的输出质量，是一项值得投入学习的技能。
""",
        "category_slug": "ai-practice",
        "tag_slugs": ["llm", "openai", "最佳实践"],
        "reading_time": 6
    },
    {
        "title": "Nginx 高性能配置指南",
        "slug": "nginx-high-performance-configuration",
        "summary": "从基础配置到高级优化，全面介绍 Nginx 的性能调优方法。",
        "content": """# Nginx 高性能配置指南

## 引言

Nginx 是高性能 Web 服务器和反向代理的首选。本文将介绍如何进行性能优化配置。

## 基础优化

```nginx
# nginx.conf
worker_processes auto;
worker_connections 10240;
multi_accept on;
use epoll;

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;
}
```

## 反向代理配置

```nginx
upstream backend {
    least_conn;
    server 127.0.0.1:8000 weight=3;
    server 127.0.0.1:8001 weight=2;
    server 127.0.0.1:8002 backup;
    
    keepalive 32;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 缓存配置

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

server {
    location /api/ {
        proxy_cache api_cache;
        proxy_cache_valid 200 10m;
        proxy_cache_key $scheme$request_method$host$request_uri;
        add_header X-Cache-Status $upstream_cache_status;
        
        proxy_pass http://backend;
    }
}
```

## SSL 优化

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

## 限流配置

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

## 结论

合理的 Nginx 配置可以大幅提升网站性能和安全性。
""",
        "category_slug": "devops-notes",
        "tag_slugs": ["高性能", "最佳实践"],
        "reading_time": 7
    },
    {
        "title": "前端状态管理方案对比",
        "slug": "frontend-state-management-comparison",
        "summary": "对比分析 Vuex、Pinia、Redux、Zustand 等主流状态管理方案的优缺点。",
        "content": """# 前端状态管理方案对比

## 引言

状态管理是前端应用的核心问题之一。本文将对比几种主流的状态管理方案。

## 方案对比

### Pinia (Vue 3 推荐)

```typescript
// stores/user.ts
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    token: ''
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.user?.name ?? 'Guest'
  },
  
  actions: {
    async login(credentials: LoginCredentials) {
      const { user, token } = await api.login(credentials)
      this.user = user
      this.token = token
    },
    
    logout() {
      this.user = null
      this.token = ''
    }
  }
})
```

**优点：**
- 完美支持 TypeScript
- 模块化设计，无需嵌套
- 支持 Vue DevTools
- 体积小

### Redux (React)

```typescript
// store.ts
import { configureStore, createSlice } from '@reduxjs/toolkit'

const userSlice = createSlice({
  name: 'user',
  initialState: { user: null, token: '' },
  reducers: {
    setUser: (state, action) => {
      state.user = action.payload
    },
    setToken: (state, action) => {
      state.token = action.payload
    },
    logout: (state) => {
      state.user = null
      state.token = ''
    }
  }
})

export const store = configureStore({
  reducer: {
    user: userSlice.reducer
  }
})
```

**优点：**
- 生态成熟，中间件丰富
- 时间旅行调试
- 社区资源丰富

### Zustand (React)

```typescript
// store.ts
import { create } from 'zustand'

interface UserStore {
  user: User | null
  token: string
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  token: '',
  login: async (credentials) => {
    const { user, token } = await api.login(credentials)
    set({ user, token })
  },
  logout: () => set({ user: null, token: '' })
}))
```

**优点：**
- 极简 API
- 无需 Provider
- 体积最小

## 选择建议

| 场景 | 推荐方案 |
|------|----------|
| Vue 3 项目 | Pinia |
| React 大型项目 | Redux Toolkit |
| React 中小型项目 | Zustand |
| 跨框架需求 | Jotai / Recoil |

## 结论

选择状态管理方案需要考虑项目规模、团队熟悉度和框架特性。
""",
        "category_slug": "frontend-engineering",
        "tag_slugs": ["vue3", "typescript", "最佳实践"],
        "reading_time": 8
    },
    {
        "title": "Python 异步编程深入解析",
        "slug": "python-async-programming-deep-dive",
        "summary": "深入理解 Python 的 asyncio 库，掌握协程、事件循环和异步上下文管理器。",
        "content": """# Python 异步编程深入解析

## 引言

Python 的异步编程能力是构建高性能应用的关键。本文将深入探讨 asyncio 的核心概念。

## 协程基础

```python
import asyncio

async def fetch_data(url: str):
    print(f"Fetching {url}")
    await asyncio.sleep(1)  # 模拟 IO 操作
    return f"Data from {url}"

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

## 并发执行

```python
async def fetch_all():
    urls = [
        "https://api.example.com/1",
        "https://api.example.com/2",
        "https://api.example.com/3"
    ]
    
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

## 异步上下文管理器

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_database_connection():
    conn = await create_connection()
    try:
        yield conn
    finally:
        await conn.close()

async def query_data():
    async with async_database_connection() as conn:
        result = await conn.execute("SELECT * FROM users")
        return result
```

## 异步迭代器

```python
class AsyncRange:
    def __init__(self, count: int):
        self.count = count
    
    def __aiter__(self):
        self.index = 0
        return self
    
    async def __anext__(self):
        if self.index >= self.count:
            raise StopAsyncIteration
        
        await asyncio.sleep(0.1)
        value = self.index
        self.index += 1
        return value

async def iterate_async():
    async for i in AsyncRange(5):
        print(i)
```

## 异步与多进程结合

```python
import concurrent.futures

async def cpu_bound_task():
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, 
            heavy_computation, 
            data
        )
        return result
```

## FastAPI 异步最佳实践

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/external")
async def get_external():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

## 结论

掌握异步编程可以显著提升 Python 应用的并发处理能力。
""",
        "category_slug": "backend-architecture",
        "tag_slugs": ["python", "fastapi", "高性能"],
        "reading_time": 9
    },
    {
        "title": "向量数据库选型与实践",
        "slug": "vector-database-selection-and-practice",
        "summary": "对比 Pinecone、Milvus、Chroma 等向量数据库，帮助选择适合的向量存储方案。",
        "content": """# 向量数据库选型与实践

## 引言

向量数据库是 AI 应用的重要基础设施。本文将对比主流向量数据库并介绍实践方法。

## 方案对比

### Pinecone

**优点：**
- 完全托管，无需运维
- 高性能，低延迟
- 自动扩展

**缺点：**
- 价格较高
- 数据存储在云端

### Milvus

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

connections.connect("default", host="localhost", port="19530")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)
]

schema = CollectionSchema(fields, "文章向量存储")
collection = Collection("articles", schema)

index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}
collection.create_index("embedding", index_params)
```

**优点：**
- 开源免费
- 功能丰富
- 支持多种索引

### Chroma

```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

collection = client.create_collection("articles")

collection.add(
    embeddings=[[0.1, 0.2, ...]],
    documents=["文章内容"],
    metadatas=[{"source": "blog"}],
    ids=["article_1"]
)

results = collection.query(
    query_embeddings=[[0.1, 0.3, ...]],
    n_results=5
)
```

**优点：**
- 轻量级，易上手
- 本地开发友好
- 与 LangChain 集成好

## 性能对比

| 数据库 | 写入 QPS | 查询延迟 | 扩展性 |
|--------|----------|----------|--------|
| Pinecone | 高 | 低 | 自动 |
| Milvus | 高 | 中 | 手动 |
| Chroma | 中 | 中 | 单机 |

## 选择建议

- **快速原型**：Chroma
- **生产环境**：Milvus / Pinecone
- **成本敏感**：Milvus
- **运维能力弱**：Pinecone

## 结论

选择向量数据库需要权衡性能、成本和运维能力。
""",
        "category_slug": "ai-practice",
        "tag_slugs": ["langchain", "rag", "llm"],
        "reading_time": 7
    },
    {
        "title": "Git 高效工作流实践",
        "slug": "git-efficient-workflow-practice",
        "summary": "介绍 Git 分支管理策略、提交规范和团队协作最佳实践。",
        "content": """# Git 高效工作流实践

## 引言

良好的 Git 工作流是团队协作的基础。本文将介绍高效的工作流实践。

## 分支策略

### Git Flow

```
main (生产分支)
  └── develop (开发分支)
        ├── feature/xxx (功能分支)
        ├── feature/yyy
        └── release/1.0 (发布分支)
              └── hotfix/xxx (热修复分支)
```

### GitHub Flow

```
main (主分支)
  └── feature/xxx (功能分支)
        └── Pull Request → main
```

## 提交规范

### Conventional Commits

```
feat: 添加用户登录功能
fix: 修复登录页面样式问题
docs: 更新 API 文档
style: 格式化代码
refactor: 重构用户模块
test: 添加单元测试
chore: 更新依赖版本
```

### Commit Template

```
# .git/commit-template
<type>(<scope>): <subject>

<body>

<footer>
```

## 常用别名配置

```bash
# ~/.gitconfig
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --graph --oneline --all
    amend = commit --amend --no-edit
```

## PR 审查清单

```markdown
## 代码审查清单

- [ ] 代码风格符合规范
- [ ] 单元测试覆盖新功能
- [ ] 无明显性能问题
- [ ] 文档已更新
- [ ] 无安全漏洞
```

## Git Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 运行 lint
npm run lint

# 运行测试
npm run test

# 检查提交信息
commitlint -E HUSKY_GIT_PARAMS
```

## 结论

规范的 Git 工作流可以提升团队协作效率和代码质量。
""",
        "category_slug": "devops-notes",
        "tag_slugs": ["最佳实践"],
        "reading_time": 6
    },
    {
        "title": "前端性能优化全攻略",
        "slug": "frontend-performance-optimization-guide",
        "summary": "从加载性能到运行时性能，全面介绍前端优化的方法和工具。",
        "content": """# 前端性能优化全攻略

## 引言

性能优化是前端开发的重要课题。本文将从多个维度介绍优化方法。

## 加载性能

### 代码分割

```typescript
// Vite 动态导入
const AdminPanel = () => import('./AdminPanel.vue')

// 路由级别分割
const routes = [
  {
    path: '/admin',
    component: () => import('./views/AdminView.vue')
  }
]
```

### 资源压缩

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['element-plus']
        }
      }
    }
  }
})
```

### 图片优化

```vue
<template>
  <img
    :src="imageUrl"
    loading="lazy"
    :srcset="`${imageUrl}?w=400 400w, ${imageUrl}?w=800 800w`"
    sizes="(max-width: 600px) 400px, 800px"
  />
</template>
```

## 运行时性能

### 虚拟列表

```vue
<script setup>
import { useVirtualList } from '@vueuse/core'

const { list, containerProps, wrapperProps } = useVirtualList(
  largeArray,
  { itemHeight: 50 }
)
</script>

<template>
  <div v-bind="containerProps" style="height: 500px; overflow: auto;">
    <div v-bind="wrapperProps">
      <div v-for="{ data, index } in list" :key="index" style="height: 50px;">
        {{ data }}
      </div>
    </div>
  </div>
</template>
```

### 防抖节流

```typescript
import { useDebounceFn, useThrottleFn } from '@vueuse/core'

const debouncedSearch = useDebounceFn((query) => {
  searchAPI(query)
}, 300)

const throttledScroll = useThrottleFn(() => {
  handleScroll()
}, 100)
```

## 缓存策略

### Service Worker

```javascript
// sw.js
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request)
    })
  )
})
```

## 性能监控

```typescript
// 使用 Performance API
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(entry.name, entry.duration)
  }
})

observer.observe({ entryTypes: ['measure', 'navigation'] })
```

## 结论

性能优化是一个持续的过程，需要结合实际场景选择合适的策略。
""",
        "category_slug": "frontend-engineering",
        "tag_slugs": ["vue3", "vite", "高性能"],
        "reading_time": 10
    },
    {
        "title": "API 安全最佳实践",
        "slug": "api-security-best-practices",
        "summary": "介绍 API 安全的关键措施，包括认证授权、输入验证、速率限制等。",
        "content": """# API 安全最佳实践

## 引言

API 安全是后端开发的核心关注点。本文将介绍常见的安全措施。

## 认证授权

### JWT 实现

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 权限控制

```python
from fastapi import Depends, HTTPException

def require_admin(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, admin = Depends(require_admin)):
    # 只有管理员可以删除用户
    pass
```

## 输入验证

```python
from pydantic import BaseModel, validator, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少3个字符')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8个字符')
        return v
```

## 速率限制

```python
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

@app.get("/api/data")
@limiter.limit("10/minute")
async def get_data(request: Request):
    return {"data": "sensitive"}
```

## CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

## 安全头

```python
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## 结论

API 安全需要多层防护，每个环节都不能忽视。
""",
        "category_slug": "backend-architecture",
        "tag_slugs": ["fastapi", "python", "api", "最佳实践"],
        "reading_time": 8
    },
    {
        "title": "LangChain Agent 开发实战",
        "slug": "langchain-agent-development",
        "summary": "使用 LangChain 构建能够自主决策和执行任务的智能 Agent。",
        "content": """# LangChain Agent 开发实战

## 引言

Agent 是 LangChain 中最强大的概念之一，它能让 LLM 自主决定使用哪些工具来完成任务。

## Agent 基础

```python
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

tools = [
    Tool(
        name="Calculator",
        func=lambda x: eval(x),
        description="用于数学计算，输入数学表达式"
    ),
    Tool(
        name="Search",
        func=search_function,
        description="用于搜索最新信息"
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

result = agent.run("2024年世界杯冠军是谁？他们赢了几个球？")
```

## 自定义工具

```python
from langchain.tools import BaseTool
from typing import Optional

class WeatherTool(BaseTool):
    name = "weather"
    description = "获取指定城市的天气信息，输入城市名称"
    
    def _run(self, city: str) -> str:
        # 调用天气 API
        response = requests.get(f"https://api.weather.com/{city}")
        return response.json()
    
    async def _arun(self, city: str) -> str:
        # 异步版本
        pass
```

## ReAct Agent

```python
from langchain.agents import create_react_agent
from langchain import hub

prompt = hub.pull("hwchase17/react")

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)
```

## 记忆功能

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = initialize_agent(
    tools,
    llm,
    agent="conversational-react-description",
    memory=memory,
    verbose=True
)
```

## 实战案例：代码助手

```python
tools = [
    Tool(name="ReadFile", func=read_file, description="读取文件内容"),
    Tool(name="WriteFile", func=write_file, description="写入文件"),
    Tool(name="RunCode", func=run_code, description="执行代码"),
    Tool(name="SearchDocs", func=search_docs, description="搜索文档")
]

code_agent = initialize_agent(
    tools,
    llm,
    agent="structured-chat-zero-shot-react-description",
    verbose=True
)

code_agent.run("帮我创建一个 FastAPI 项目骨架")
```

## 结论

Agent 让 LLM 具备了自主行动能力，是构建复杂 AI 应用的关键组件。
""",
        "category_slug": "ai-practice",
        "tag_slugs": ["langchain", "llm", "openai"],
        "reading_time": 9
    }
]


def generate_date_distribution():
    """
    生成20篇文章的日期分布，覆盖近2年（24个月）
    确保文章均匀分布在不同月份
    """
    now = get_now()
    dates = []
    
    month_distribution = [
        (2024, 3), (2024, 4), (2024, 5), (2024, 6),
        (2024, 7), (2024, 8), (2024, 9), (2024, 10),
        (2024, 11), (2024, 12), (2025, 1), (2025, 2),
        (2025, 3), (2025, 4), (2025, 5), (2025, 6),
        (2025, 7), (2025, 8), (2025, 9), (2025, 10),
        (2025, 11), (2025, 12), (2026, 1), (2026, 2)
    ]
    
    selected_months = []
    for i in range(20):
        month_index = i * 24 // 20
        selected_months.append(month_distribution[month_index])
    
    for year, month in selected_months:
        day = random.randint(1, 28)
        hour = random.randint(8, 22)
        minute = random.randint(0, 59)
        
        date = datetime(year, month, day, hour, minute, 0)
        dates.append(date)
    
    dates.sort()
    
    return dates


def create_articles(db: Session):
    """创建测试文章"""
    admin = db.query(User).filter(User.is_admin == True).first()
    if not admin:
        print("Error: No admin user found. Please run init_database first.")
        return
    
    categories = {cat.slug: cat for cat in db.query(Category).all()}
    tags = {tag.slug: tag for tag in db.query(Tag).all()}
    
    dates = generate_date_distribution()
    
    created_count = 0
    
    for i, article_data in enumerate(ARTICLES_DATA):
        existing = db.query(Article).filter(Article.slug == article_data["slug"]).first()
        if existing:
            print(f"Article already exists: {article_data['title']}")
            continue
        
        category = categories.get(article_data["category_slug"])
        if not category:
            print(f"Warning: Category not found: {article_data['category_slug']}")
            continue
        
        article = Article(
            title=article_data["title"],
            slug=article_data["slug"],
            summary=article_data["summary"],
            content=article_data["content"],
            category_id=category.id,
            author_id=admin.id,
            is_published=True,
            is_featured=article_data.get("is_featured", False),
            reading_time=article_data.get("reading_time", 5),
            view_count=random.randint(50, 500),
            like_count=random.randint(5, 50),
            comment_count=random.randint(0, 10),
            created_at=dates[i],
            updated_at=dates[i],
            published_at=dates[i]
        )
        
        article_tags = []
        for tag_slug in article_data.get("tag_slugs", []):
            tag = tags.get(tag_slug)
            if tag:
                article_tags.append(tag)
        
        if article_tags:
            article.tags = article_tags
        
        db.add(article)
        created_count += 1
        print(f"Created article: {article_data['title']} ({dates[i].strftime('%Y-%m-%d')})")
    
    db.commit()
    print(f"\nSuccessfully created {created_count} articles!")
    print(f"Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")


def main():
    print("=" * 60)
    print("Generating 20 test articles for archive testing...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        create_articles(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
