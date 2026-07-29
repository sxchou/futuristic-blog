import type MermaidAPI from 'mermaid'
import type { MermaidConfig } from 'mermaid'

let mermaidInstance: typeof MermaidAPI | null = null
let loadingPromise: Promise<typeof MermaidAPI> | null = null

const getMermaidConfig = (isDark: boolean): MermaidConfig => ({
  startOnLoad: false,
  theme: isDark ? 'dark' : 'default',
  securityLevel: 'loose'
})

/**
 * 计算颜色相对亮度（WCAG，0~1）。
 * 支持 #rgb / #rrggbb / #rrggbbaa / rgb() / rgba()。
 * 无法解析时返回 -1。
 */
const getLuminance = (color: string): number => {
  const c = color.trim()
  let r = 0, g = 0, b = 0

  if (c.startsWith('#')) {
    let h = c.slice(1)
    if (h.length === 3) {
      h = h.split('').map(ch => ch + ch).join('')
    }
    if (h.length < 6) return -1
    r = parseInt(h.slice(0, 2), 16) / 255
    g = parseInt(h.slice(2, 4), 16) / 255
    b = parseInt(h.slice(4, 6), 16) / 255
  } else {
    const m = c.match(/rgba?\(([^)]+)\)/)
    if (!m) return -1
    const parts = m[1].split(',').map(p => parseFloat(p))
    if (parts.length < 3) return -1
    r = parts[0] / 255
    g = parts[1] / 255
    b = parts[2] / 255
  }

  const lin = (v: number) => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

/**
 * 夜间模式下，Mermaid 的 dark 主题会把节点文字设为浅色。
 * 当图表用 style/classDef 显式指定了「浅色 fill」却没有指定 color 时，
 * 会导致浅色文字落在浅色背景上而无法阅读。
 *
 * 本函数仅在夜间模式下，为这类「浅色填充 + 未指定文字色」的节点注入深色文字，
 * 使其在浅色填充上仍可阅读。日间模式原样返回，不做任何改动。
 */
const DARK_TEXT_ON_LIGHT_FILL = '#1f2937'
const preprocessMermaidCode = (code: string, isDark: boolean): string => {
  if (!isDark) return code
  return code.replace(/^(\s*(?:style|classDef)\s+\S+\s+)(.*)$/gim, (_line, prefix: string, props: string) => {
    if (/\bcolor\s*:/.test(props)) return _line
    const fillMatch = props.match(/fill\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))/)
    if (!fillMatch) return _line
    const lum = getLuminance(fillMatch[1])
    if (lum < 0 || lum < 0.5) return _line
    return `${prefix}${props.replace(/\s+$/, '')},color:${DARK_TEXT_ON_LIGHT_FILL}`
  })
}

const loadMermaid = async (): Promise<typeof MermaidAPI> => {
  if (mermaidInstance) return mermaidInstance
  if (loadingPromise) return loadingPromise

  loadingPromise = import('mermaid').then(mod => {
    mermaidInstance = mod.default
    return mermaidInstance
  })

  return loadingPromise
}

export const initMermaid = async (isDark: boolean) => {
  const m = await loadMermaid()
  m.initialize(getMermaidConfig(isDark))
  return m
}

const yieldToBrowser = () => new Promise<void>(resolve => requestAnimationFrame(() => resolve()))

const handleError = (htmlEl: HTMLElement, id: string) => {
  const errorEl = document.getElementById('d' + id) || document.getElementById(id)
  if (errorEl) {
    htmlEl.innerHTML = ''
    htmlEl.appendChild(errorEl)
    errorEl.style.display = 'block'
  } else {
    htmlEl.innerHTML = `<div style="color:#ef4444;font-size:12px;padding:8px;">Mermaid 语法错误</div>`
  }
}

export const renderMermaidDiagrams = async (
  container: HTMLElement,
  selector: string,
  isDark: boolean
) => {
  const m = await initMermaid(isDark)
  const mermaidElements = container.querySelectorAll(selector)
  const unrendered = Array.from(mermaidElements).filter(
    el => !(el as HTMLElement).hasAttribute('data-rendered')
  )

  if (unrendered.length === 0) return

  for (let i = 0; i < unrendered.length; i++) {
    const htmlEl = unrendered[i] as HTMLElement
    htmlEl.setAttribute('data-rendered', 'true')

    const id = `mermaid-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`

    try {
      const { svg } = await m.render(id, preprocessMermaidCode(htmlEl.textContent || '', isDark))
      htmlEl.innerHTML = svg
    } catch {
      handleError(htmlEl, id)
    }

    if (i < unrendered.length - 1) {
      await yieldToBrowser()
    }
  }
}

export const rerenderMermaidOnThemeChange = async (
  container: HTMLElement,
  selector: string,
  isDark: boolean
) => {
  const m = await initMermaid(isDark)
  const mermaidElements = container.querySelectorAll(selector)

  if (mermaidElements.length === 0) return

  for (let i = 0; i < mermaidElements.length; i++) {
    const pre = mermaidElements[i] as HTMLElement
    if (!document.contains(pre)) break

    const encodedCode = pre.getAttribute('data-mermaid-code')
    if (!encodedCode) continue

    const id = `mermaid-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`

    try {
      const { svg } = await m.render(id, preprocessMermaidCode(decodeURIComponent(encodedCode), isDark))
      pre.innerHTML = svg
    } catch {
      handleError(pre, id)
    }

    if (i < mermaidElements.length - 1) {
      await yieldToBrowser()
    }
  }
}

export const debounce = <T extends (...args: unknown[]) => void>(fn: T, delay: number) => {
  let timer: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}
