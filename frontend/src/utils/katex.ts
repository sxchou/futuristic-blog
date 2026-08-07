import { marked } from 'marked'
import katex from 'katex'

const KATEX_OPTIONS = {
  throwOnError: true,
  output: 'htmlAndMathml' as const,
  strict: false,
  trust: true,
  macros: {
    '\\R': '\\mathbb{R}',
    '\\N': '\\mathbb{N}',
    '\\Z': '\\mathbb{Z}',
    '\\Q': '\\mathbb{Q}',
    '\\C': '\\mathbb{C}'
  }
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/**
 * 安全渲染 KaTeX：失败时降级显示原始 LaTeX 文本（而非红色错误信息）
 * 避免文章中 $ 符号被误识别为公式分隔符时出现刺眼的 ParseError
 */
function renderKatex(text: string, displayMode: boolean): string {
  try {
    return katex.renderToString(text, { ...KATEX_OPTIONS, displayMode })
  } catch {
    const escaped = escapeHtml(text)
    return displayMode
      ? `<span class="katex-fallback" style="display:block;padding:0.5em 0;font-family:monospace;">${escaped}</span>\n`
      : `<span class="katex-fallback" style="font-family:monospace;">${escaped}</span>`
  }
}

// 行内公式：$...$ 或 $$...$$
// 后置条件：闭合$后必须是标点/空格/行尾，字符类包含中英文标点（含顿号、分号、括号）
const inlineRule = /^(\${1,2})(?!\$)((?:\\.|[^\\\n])*?(?:\\.|[^\\\n\$]))\1(?=[\s?!\.,:？！。，：、；（）]|$)/
// 块级公式：$$...\n$$（需换行）
const blockRule = /^(\${1,2})\n((?:\\[^]|[^\\])+?)\n\1(?:\n|$)/

const katexExtension = {
  extensions: [
    {
      name: 'inlineKatex',
      level: 'inline' as const,
      start(src: string): number | undefined {
        let indexSrc = src
        while (indexSrc) {
          const index = indexSrc.indexOf('$')
          if (index === -1) return undefined
          // nonStandard 模式：任意位置的 $ 都尝试匹配（中文文本中 $ 前面常是中文标点）
          const possibleKatex = indexSrc.substring(index)
          if (possibleKatex.match(inlineRule)) return index
          indexSrc = indexSrc.substring(index + 1).replace(/^\$+/, '')
        }
        return undefined
      },
      tokenizer(src: string) {
        const match = src.match(inlineRule)
        if (match) {
          return {
            type: 'inlineKatex',
            raw: match[0],
            text: match[2].trim(),
            displayMode: match[1].length === 2,
          }
        }
        return undefined
      },
      renderer(token: { text: string; displayMode: boolean }) {
        return renderKatex(token.text, token.displayMode)
      },
    },
    {
      name: 'blockKatex',
      level: 'block' as const,
      tokenizer(src: string) {
        const match = src.match(blockRule)
        if (match) {
          return {
            type: 'blockKatex',
            raw: match[0],
            text: match[2].trim(),
            displayMode: match[1].length === 2,
          }
        }
        return undefined
      },
      renderer(token: { text: string; displayMode: boolean }) {
        return renderKatex(token.text, true) + '\n'
      },
    },
  ],
}

// 模块加载时注册到 marked 全局单例（ES 模块只执行一次，注册幂等安全）
marked.use(katexExtension)

// 重新导出 marked，便于统一入口（已注册 katex 扩展）
export { marked }

/**
 * KaTeX 输出可能用到的 MathML 标签白名单（供 DOMPurify ADD_TAGS 使用）
 * KaTeX htmlAndMathml 模式会同时输出 HTML span 层和 MathML 语义层
 */
export const KATEX_MATHML_TAGS = [
  'math', 'semantics', 'annotation', 'annotation-xml',
  'mrow', 'mi', 'mo', 'mn', 'ms', 'mtext', 'mspace',
  'mfrac', 'msqrt', 'mroot', 'msub', 'msup', 'msubsup',
  'munder', 'mover', 'munderover',
  'mmultiscripts', 'mprescripts', 'none',
  'mtable', 'mtr', 'mtd', 'maligngroup', 'malignmark',
  'maction', 'menclose', 'merror', 'mfenced', 'mphantom', 'mstyle'
]

/**
 * KaTeX 输出可能用到的属性白名单（供 DOMPurify ADD_ATTR 使用）
 * style: KaTeX HTML 层大量使用内联 style 定位字符
 * 其余: MathML 层语义属性
 */
export const KATEX_MATHML_ATTR = [
  'style', 'mathvariant', 'encoding', 'aria-hidden', 'xmlns',
  'stretchy', 'fence', 'separator', 'accent', 'accentunder',
  'columnalign', 'rowalign', 'columnspacing', 'rowspacing',
  'columnlines', 'rowlines', 'frame', 'framespacing',
  'equalcolumns', 'equalrows', 'displaystyle', 'scriptlevel',
  'lspace', 'rspace', 'height', 'depth', 'width',
  'voffset', 'fontstyle', 'fontweight', 'fontfamily',
  'linethickness', 'notation', 'actiontype', 'selection',
  'bevelled', 'open', 'close', 'separators'
]
