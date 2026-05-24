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

  await Promise.all(
    unrendered.map(async (el, i) => {
      const htmlEl = el as HTMLElement
      htmlEl.setAttribute('data-rendered', 'true')

      const id = `mermaid-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`

      try {
        const { svg } = await m.render(id, htmlEl.textContent || '')
        htmlEl.innerHTML = svg
      } catch {
        const errorEl = document.getElementById('d' + id) || document.getElementById(id)
        if (errorEl) {
          htmlEl.innerHTML = ''
          htmlEl.appendChild(errorEl)
          errorEl.style.display = 'block'
        } else {
          htmlEl.innerHTML = `<div style="color:#ef4444;font-size:12px;padding:8px;">Mermaid 语法错误</div>`
        }
      }
    })
  )
}

export const rerenderMermaidOnThemeChange = async (
  container: HTMLElement,
  selector: string,
  isDark: boolean
) => {
  const m = await initMermaid(isDark)
  const mermaidElements = container.querySelectorAll(selector)

  if (mermaidElements.length === 0) return

  await Promise.all(
    Array.from(mermaidElements).map(async (el) => {
      const pre = el as HTMLElement
      const encodedCode = pre.getAttribute('data-mermaid-code')

      if (encodedCode) {
        const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

        try {
          const { svg } = await m.render(id, decodeURIComponent(encodedCode))
          pre.innerHTML = svg
        } catch {
          const errorEl = document.getElementById('d' + id) || document.getElementById(id)
          if (errorEl) {
            pre.innerHTML = ''
            pre.appendChild(errorEl)
            errorEl.style.display = 'block'
          } else {
            pre.innerHTML = `<div style="color:#ef4444;font-size:12px;padding:8px;">Mermaid 语法错误</div>`
          }
        }
      }
    })
  )
}

export const debounce = <T extends (...args: unknown[]) => void>(fn: T, delay: number) => {
  let timer: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}
