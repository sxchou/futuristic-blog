import type MermaidAPI from 'mermaid'
import type { MermaidConfig } from 'mermaid'

let mermaidInstance: typeof MermaidAPI | null = null
let loadingPromise: Promise<typeof MermaidAPI> | null = null

const getMermaidConfig = (isDark: boolean): MermaidConfig => ({
  startOnLoad: false,
  theme: isDark ? 'dark' : 'default',
  securityLevel: 'loose'
})

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
      const { svg } = await m.render(id, htmlEl.textContent || '')
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
      const { svg } = await m.render(id, decodeURIComponent(encodedCode))
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
