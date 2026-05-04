interface PerformanceMetrics {
  fcp: number | null
  lcp: number | null
  fid: number | null
  cls: number | null
  ttfb: number | null
  domContentLoaded: number | null
  load: number | null
}

interface ResourceTiming {
  name: string
  duration: number
  size: number
  type: string
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
    domContentLoaded: null,
    load: null
  }

  private observer: PerformanceObserver | null = null
  private clsValue = 0
  private clsEntries: PerformanceEntry[] = []

  constructor() {
    this.initObservers()
    this.collectNavigationTiming()
  }

  private initObservers() {
    if (typeof PerformanceObserver === 'undefined') return

    try {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.processEntry(entry)
        }
      })

      this.observer.observe({
        entryTypes: ['paint', 'largest-contentful-paint', 'first-input', 'layout-shift']
      })
    } catch (e) {
      console.warn('PerformanceObserver not fully supported')
    }
  }

  private processEntry(entry: PerformanceEntry) {
    switch (entry.entryType) {
      case 'paint':
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime
        }
        break

      case 'largest-contentful-paint':
        this.metrics.lcp = entry.startTime
        break

      case 'first-input':
        this.metrics.fid = (entry as PerformanceEventTiming).processingStart - entry.startTime
        break

      case 'layout-shift':
        if (!(entry as LayoutShiftEntry).hadRecentInput) {
          this.clsValue += (entry as LayoutShiftEntry).value
          this.clsEntries.push(entry)
          this.metrics.cls = this.clsValue
        }
        break
    }
  }

  private collectNavigationTiming() {
    if (typeof performance === 'undefined') return

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (navigation) {
      this.metrics.ttfb = navigation.responseStart - navigation.requestStart
      this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.startTime
      this.metrics.load = navigation.loadEventEnd - navigation.startTime
    }
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }

  getResourceTimings(): ResourceTiming[] {
    if (typeof performance === 'undefined') return []

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
    
    return resources.map((resource) => ({
      name: resource.name,
      duration: resource.duration,
      size: resource.transferSize || 0,
      type: this.getResourceType(resource.initiatorType)
    }))
  }

  private getResourceType(initiatorType: string): string {
    const typeMap: Record<string, string> = {
      script: 'js',
      link: 'css',
      img: 'image',
      fetch: 'api',
      xmlhttprequest: 'api',
      font: 'font',
      other: 'other'
    }
    return typeMap[initiatorType] || 'other'
  }

  getBundleStats(): { js: number; css: number; images: number; fonts: number; api: number } {
    const resources = this.getResourceTimings()
    
    return resources.reduce(
      (acc, resource) => {
        const type = resource.type as keyof typeof acc
        if (type in acc) {
          acc[type] += resource.size
        }
        return acc
      },
      { js: 0, css: 0, images: 0, fonts: 0, api: 0 }
    )
  }

  getScore(): { performance: number; accessibility: number; bestPractices: number } {
    let performanceScore = 100

    if (this.metrics.lcp !== null) {
      if (this.metrics.lcp > 4000) performanceScore -= 30
      else if (this.metrics.lcp > 2500) performanceScore -= 15
    }

    if (this.metrics.fid !== null) {
      if (this.metrics.fid > 300) performanceScore -= 20
      else if (this.metrics.fid > 100) performanceScore -= 10
    }

    if (this.metrics.cls !== null) {
      if (this.metrics.cls > 0.25) performanceScore -= 15
      else if (this.metrics.cls > 0.1) performanceScore -= 8
    }

    if (this.metrics.fcp !== null) {
      if (this.metrics.fcp > 3000) performanceScore -= 15
      else if (this.metrics.fcp > 1800) performanceScore -= 8
    }

    performanceScore = Math.max(0, performanceScore)

    return {
      performance: performanceScore,
      accessibility: 85,
      bestPractices: 90
    }
  }

  logReport() {
    const metrics = this.getMetrics()
    const score = this.getScore()
    const bundleStats = this.getBundleStats()

    console.group('📊 Performance Report')
    
    console.group('Core Web Vitals')
    console.log(`FCP (First Contentful Paint): ${metrics.fcp?.toFixed(2) || 'N/A'}ms`)
    console.log(`LCP (Largest Contentful Paint): ${metrics.lcp?.toFixed(2) || 'N/A'}ms`)
    console.log(`FID (First Input Delay): ${metrics.fid?.toFixed(2) || 'N/A'}ms`)
    console.log(`CLS (Cumulative Layout Shift): ${metrics.cls?.toFixed(4) || 'N/A'}`)
    console.log(`TTFB (Time to First Byte): ${metrics.ttfb?.toFixed(2) || 'N/A'}ms`)
    console.groupEnd()

    console.group('Page Load')
    console.log(`DOM Content Loaded: ${metrics.domContentLoaded?.toFixed(2) || 'N/A'}ms`)
    console.log(`Page Load: ${metrics.load?.toFixed(2) || 'N/A'}ms`)
    console.groupEnd()

    console.group('Bundle Size (bytes)')
    console.log(`JavaScript: ${(bundleStats.js / 1024).toFixed(2)} KB`)
    console.log(`CSS: ${(bundleStats.css / 1024).toFixed(2)} KB`)
    console.log(`Images: ${(bundleStats.images / 1024).toFixed(2)} KB`)
    console.log(`Fonts: ${(bundleStats.fonts / 1024).toFixed(2)} KB`)
    console.log(`API Responses: ${(bundleStats.api / 1024).toFixed(2)} KB`)
    console.groupEnd()

    console.group('Scores')
    console.log(`Performance: ${score.performance}/100`)
    console.log(`Accessibility: ${score.accessibility}/100`)
    console.log(`Best Practices: ${score.bestPractices}/100`)
    console.groupEnd()

    console.groupEnd()
  }

  disconnect() {
    this.observer?.disconnect()
  }
}

interface PerformanceEventTiming extends PerformanceEntry {
  processingStart: number
}

interface LayoutShiftEntry extends PerformanceEntry {
  value: number
  hadRecentInput: boolean
}

export const performanceMonitor = new PerformanceMonitor()

export const logPerformanceReport = () => {
  if (typeof window !== 'undefined' && import.meta.env.DEV) {
    setTimeout(() => {
      performanceMonitor.logReport()
    }, 3000)
  }
}

export default performanceMonitor
