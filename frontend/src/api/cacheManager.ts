interface CacheEntry {
  data: unknown
  timestamp: number
}

interface CacheConfig {
  ttl: number
  pattern: RegExp
}

class CacheManager {
  private cache: Map<string, CacheEntry>
  private config: Map<string, CacheConfig>
  
  constructor() {
    this.cache = new Map()
    this.config = new Map()
    this.initializeConfig()
  }
  
  private initializeConfig() {
    const configs: Record<string, { ttl: number; pattern: RegExp }> = {
      '/categories': { ttl: 1800000, pattern: /^\/categories(\?|\/|$)/ },
      '/tags': { ttl: 1800000, pattern: /^\/tags(\?|\/|$)/ },
      '/resources': { ttl: 900000, pattern: /^\/resources(\?|\/|$)/ },
      '/resource-categories': { ttl: 900000, pattern: /^\/resource-categories(\?|\/|$)/ },
      '/site-config': { ttl: 1800000, pattern: /^\/site-config(\?|\/|$)/ },
      '/profile': { ttl: 1800000, pattern: /^\/profile(\?|\/|$)/ },
      '/articles': { ttl: 300000, pattern: /^\/articles(\?|\/|$)/ },
      '/dashboard': { ttl: 120000, pattern: /^\/dashboard(\?|\/|$)/ },
      '/announcements': { ttl: 900000, pattern: /^\/announcements(\?|\/|$)/ },
      '/users': { ttl: 300000, pattern: /^\/users(\?|\/|$)/ },
      '/roles': { ttl: 600000, pattern: /^\/roles(\?|\/|$)/ },
      '/permissions': { ttl: 1800000, pattern: /^\/permissions(\?|\/|$)/ },
      '/logs/stats': { ttl: 60000, pattern: /^\/logs\/stats(\?|\/|$)/ },
      '/comments': { ttl: 180000, pattern: /^\/comments(\?|\/|$)/ }
    }
    
    Object.entries(configs).forEach(([key, value]) => {
      this.config.set(key, value)
    })
  }
  
  shouldCache(url: string | undefined): boolean {
    if (!url) return false
    for (const config of this.config.values()) {
      if (config.pattern.test(url)) {
        return true
      }
    }
    return false
  }
  
  getCacheTTL(url: string | undefined): number {
    if (!url) return 60000
    for (const config of this.config.values()) {
      if (config.pattern.test(url)) {
        return config.ttl
      }
    }
    return 60000
  }
  
  getCacheKey(method: string, url: string, params: unknown): string {
    return `${method}-${url}-${JSON.stringify(params)}`
  }
  
  get(key: string): unknown | null {
    const cached = this.cache.get(key)
    if (!cached) return null
    
    const ttl = this.getCacheTTLFromKey(key)
    if (Date.now() - cached.timestamp < ttl) {
      return cached.data
    }
    
    this.cache.delete(key)
    return null
  }
  
  set(key: string, data: unknown) {
    this.cache.set(key, { data, timestamp: Date.now() })
  }
  
  clear() {
    this.cache.clear()
  }
  
  clearByPattern(pattern: string) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }
  
  clearByEndpoint(endpoint: string) {
    const config = this.config.get(endpoint)
    if (!config) return
    
    for (const key of this.cache.keys()) {
      const urlMatch = key.match(/^[A-Z]+-(.+?)-\{/)
      if (urlMatch && config.pattern.test(urlMatch[1])) {
        this.cache.delete(key)
      }
    }
  }
  
  clearByRegex(regex: RegExp) {
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key)
      }
    }
  }
  
  private getCacheTTLFromKey(key: string): number {
    const urlMatch = key.match(/^[A-Z]+-(.+?)-\{/)
    if (urlMatch) {
      return this.getCacheTTL(urlMatch[1])
    }
    return 60000
  }
  
  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    }
  }
}

export const cacheManager = new CacheManager()
export type { CacheEntry, CacheConfig }
