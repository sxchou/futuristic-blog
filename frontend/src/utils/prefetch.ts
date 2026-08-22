interface CacheEntry<T> {
  data: T
  timestamp: number
}

const DEFAULT_TTL = 600000

const cache = new Map<string, CacheEntry<unknown>>()

export const dataPrefetch = {
  set<T>(key: string, data: T): void {
    cache.set(key, { data, timestamp: Date.now() })
  },

  get<T>(key: string, ttl: number = DEFAULT_TTL): T | null {
    const entry = cache.get(key)
    if (!entry) return null
    if (Date.now() - entry.timestamp > ttl) {
      cache.delete(key)
      return null
    }
    return entry.data as T
  },

  has(key: string, ttl: number = DEFAULT_TTL): boolean {
    return this.get(key, ttl) !== null
  },

  invalidate(key: string): void {
    cache.delete(key)
  },

  clear(): void {
    cache.clear()
  }
}

export const prefetchArchiveData = async () => {
  if (dataPrefetch.has('archive')) return

  try {
    const apiClient = (await import('@/api/client')).default
    const response = await apiClient.get('/articles/archive/list')
    dataPrefetch.set('archive', response.data)
  } catch {
    // Prefetch failures are silent
  }
}

export const prefetchResourcesData = async () => {
  if (dataPrefetch.has('resources')) return

  try {
    const { resourceApi } = await import('@/api')
    const data = await resourceApi.getResources()
    dataPrefetch.set('resources', data)
  } catch {
    // Prefetch failures are silent
  }
}

/**
 * 预取热门分类/标签的文章列表（第一页），预热 HTTP 缓存。
 * 用户随后切换到对应分类/标签时可直接命中缓存，实现秒开。
 */
export const prefetchFilterArticles = async (): Promise<void> => {
  try {
    const { articleApi, categoryApi, tagApi } = await import('@/api')
    const [categories, tags] = await Promise.all([
      categoryApi.getCategories().catch(() => []),
      tagApi.getTags().catch(() => [])
    ])

    if (categories.length === 0 && tags.length === 0) return

    // 与 usePageSize 保持一致，确保预取参数能命中真实请求的缓存键
    const pageSize = window.innerWidth >= 1280 ? 8 : 6

    // 按文章数量选取热门分类/标签
    const hotCategories = [...categories]
      .sort((a, b) => (b.article_count || 0) - (a.article_count || 0))
      .slice(0, 4)
    const hotTags = [...tags]
      .sort((a, b) => (b.article_count || 0) - (a.article_count || 0))
      .slice(0, 4)

    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

    // 逐个预取并间隔发送，避免请求集中触发服务端限流；
    // allowDuplicate 确保预取不会中断用户正在进行的请求
    for (const category of hotCategories) {
      await articleApi.getArticles(
        { page: 1, page_size: pageSize, category_id: category.id },
        { allowDuplicate: true }
      ).catch(() => {})
      await delay(200)
    }

    for (const tag of hotTags) {
      await articleApi.getArticles(
        { page: 1, page_size: pageSize, tag_id: tag.id },
        { allowDuplicate: true }
      ).catch(() => {})
      await delay(200)
    }
  } catch {
    // 预取失败静默处理，不影响正常功能
  }
}

export const prefetchAllData = () => {
  requestIdleCallback(() => {
    prefetchArchiveData().then(() => {
      requestIdleCallback(() => {
        prefetchResourcesData().then(() => {
          requestIdleCallback(() => {
            prefetchFilterArticles()
          }, { timeout: 3000 })
        })
      }, { timeout: 2000 })
    })
  }, { timeout: 2000 })
}
