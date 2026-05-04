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

export const prefetchCategoriesData = async () => {
  if (dataPrefetch.has('categories')) return

  try {
    const { resourceCategoryApi } = await import('@/api')
    const data = await resourceCategoryApi.getCategories()
    dataPrefetch.set('categories', data)
  } catch {
    // Prefetch failures are silent
  }
}

export const prefetchAllData = () => {
  requestIdleCallback(() => {
    prefetchArchiveData().then(() => {
      requestIdleCallback(() => {
        Promise.all([prefetchResourcesData(), prefetchCategoriesData()])
      }, { timeout: 2000 })
    })
  }, { timeout: 2000 })
}
