// 文章页 SEO/OG 元数据服务端注入
//
// 背景：SPA 的 index.html 中标题与 OG 标签写死，QQ/微信/Telegram 等聊天工具的
// 爬虫不执行 JS，抓到的永远是默认标题。此函数在服务端并行拉取静态 index.html
// 与后端文章数据，将动态元数据注入 HTML 后返回，确保爬虫在首次响应中即可
// 读取到文章标题、摘要、封面图等 OG 信息。
//
// 兜底策略：后端异常或文章不存在时仍返回 SPA 外壳，由前端正常渲染，
// 不影响真实用户访问。

const FETCH_TIMEOUT_MS = 5000
const DEFAULT_SITE_NAME = 'Futuristic Blog'
const DEFAULT_DESCRIPTION = 'Code for Future, Share for Growth'

interface PageMeta {
  title: string
  siteName: string
  description: string
  keywords: string
  url: string
  image: string
  type: string
  publishedTime: string
}

function escapeHtmlAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\r?\n/g, ' ')
    .trim()
}

// 从 markdown/HTML 混合内容提取纯文本摘要
function makeExcerpt(content: string, maxLength = 150): string {
  const text = (content || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[#>*_~|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text
}

// 封面图存储为 /uploads/... 相对路径（由后端域名提供服务），需转为绝对 URL
function resolveImageUrl(path: string | null | undefined, backendBase: string): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  if (path.startsWith('/')) return `${backendBase}${path}`
  return path
}

// 替换已有 meta 标签；不存在则收集，稍后统一插入 </head> 前
function replaceOrDeferMeta(
  html: string,
  attr: 'name' | 'property',
  key: string,
  content: string,
  deferred: string[]
): string {
  const tag = `<meta ${attr}="${key}" content="${escapeHtmlAttr(content)}" />`
  const pattern = new RegExp(`<meta\\s+${attr}="${key}"\\s+content="[^"]*"\\s*/?>`)
  if (pattern.test(html)) {
    // 使用函数替换，避免内容中含 $& 等特殊序列时被误解析
    return html.replace(pattern, () => tag)
  }
  deferred.push(tag)
  return html
}

function injectMeta(html: string, m: PageMeta): string {
  const deferred: string[] = []
  const fullTitle = m.siteName ? `${m.title} | ${m.siteName}` : m.title

  html = html.replace(/<title>[\s\S]*?<\/title>/, () => `<title>${escapeHtmlAttr(fullTitle)}</title>`)

  html = replaceOrDeferMeta(html, 'name', 'description', m.description, deferred)
  html = replaceOrDeferMeta(html, 'name', 'keywords', m.keywords, deferred)
  html = replaceOrDeferMeta(html, 'property', 'og:title', m.title, deferred)
  html = replaceOrDeferMeta(html, 'property', 'og:description', m.description, deferred)
  html = replaceOrDeferMeta(html, 'property', 'og:type', m.type, deferred)
  html = replaceOrDeferMeta(html, 'property', 'og:url', m.url, deferred)
  html = replaceOrDeferMeta(html, 'property', 'og:site_name', m.siteName, deferred)
  html = replaceOrDeferMeta(html, 'name', 'twitter:card', m.image ? 'summary_large_image' : 'summary', deferred)
  html = replaceOrDeferMeta(html, 'name', 'twitter:title', m.title, deferred)
  html = replaceOrDeferMeta(html, 'name', 'twitter:description', m.description, deferred)
  if (m.image) {
    html = replaceOrDeferMeta(html, 'property', 'og:image', m.image, deferred)
    html = replaceOrDeferMeta(html, 'name', 'twitter:image', m.image, deferred)
  }
  if (m.publishedTime) {
    html = replaceOrDeferMeta(html, 'property', 'article:published_time', m.publishedTime, deferred)
  }

  if (deferred.length) {
    const block = `    ${deferred.join('\n    ')}\n  `
    html = html.replace(/<\/head>/, () => `${block}</head>`)
  }
  return html
}

function serveHtml(res: any, html: string, status: number, cacheControl: string): void {
  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  res.setHeader('Cache-Control', cacheControl)
  res.status(status).send(html)
}

export default async function handler(req: any, res: any): Promise<void> {
  try {
    const slug = String(req.query?.slug || '').trim()
    const apiUrl = (process.env.VITE_API_URL || '').replace(/\/+$/, '')
    const backendBase = apiUrl.replace(/\/api\/v1$/i, '')
    const host = String(req.headers.host || '')
    const proto = String(req.headers['x-forwarded-proto'] || 'https').split(',')[0].trim() || 'https'
    const origin = `${proto}://${host}`

    // 拉取静态 SPA 外壳（同一部署的静态资源，走边缘缓存）
    let shell = ''
    try {
      const shellRes = await fetch(`${origin}/index.html`, {
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      })
      if (shellRes.ok) shell = await shellRes.text()
    } catch {
      // 静态资源获取失败时继续，走最后的 503 兜底
    }

    if (!shell) {
      res.status(503).send('Service temporarily unavailable')
      return
    }

    if (!slug || !apiUrl) {
      // 本地开发未配置 VITE_API_URL：返回原始外壳，SPA 正常工作
      serveHtml(res, shell, 200, 'public, max-age=30')
      return
    }

    // 并行拉取文章数据与站点配置
    const [articleRes, configRes] = await Promise.all([
      fetch(`${apiUrl}/articles/${encodeURIComponent(slug)}?track_view=false`, {
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      }).catch(() => null),
      fetch(`${apiUrl}/site-config`, {
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      }).catch(() => null),
    ])

    let siteName = ''
    let siteDescription = ''
    let siteKeywords = ''
    if (configRes && configRes.ok) {
      try {
        const configs: Array<{ key?: string; value?: string }> = await configRes.json()
        const find = (k: string) =>
          configs.find((c) => c && c.key === k && c.value)?.value || ''
        siteName = find('site_name')
        siteDescription = find('site_description')
        siteKeywords = find('site_keywords')
      } catch {
        // 配置解析失败则使用默认值
      }
    }

    let article: any = null
    if (articleRes && articleRes.ok) {
      article = await articleRes.json().catch(() => null)
    }

    if (article && article.title) {
      const tags: string[] = Array.isArray(article.tags)
        ? article.tags.map((t: any) => t?.name).filter(Boolean)
        : []
      const keywords = [article.category?.name, ...tags].filter(Boolean).join(',')
      const description =
        article.summary || makeExcerpt(article.content) || siteDescription || DEFAULT_DESCRIPTION
      const image = resolveImageUrl(article.cover_image, backendBase)

      const html = injectMeta(shell, {
        title: String(article.title),
        siteName: siteName || DEFAULT_SITE_NAME,
        description,
        keywords: keywords || siteKeywords,
        url: `${origin}/article/${slug}`,
        image,
        type: 'article',
        publishedTime: article.published_at || article.created_at || '',
      })
      serveHtml(res, html, 200, 'public, max-age=60, s-maxage=600, stale-while-revalidate=3600')
      return
    }

    if (articleRes && articleRes.status === 404) {
      // 文章不存在：返回外壳由前端渲染 404，状态码保持 404 供爬虫识别
      serveHtml(res, shell, 404, 'public, max-age=0, s-maxage=60')
      return
    }

    // 后端异常/超时：退回默认外壳，真实用户不受影响
    serveHtml(res, shell, 200, 'public, max-age=30')
  } catch {
    res.status(503).send('Service temporarily unavailable')
  }
}
