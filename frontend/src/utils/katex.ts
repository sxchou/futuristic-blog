import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'

/**
 * KaTeX marked 扩展配置
 *
 * output: 'htmlAndMathml' — HTML 层负责视觉渲染，MathML 层负责无障碍访问（屏幕阅读器）
 * throwOnError: false — 公式语法错误不抛异常，降级显示原始 LaTeX 文本
 * trust: true — 允许 \href 等命令（DOMPurify 会做安全过滤）
 */
export const katexExtension = markedKatex({
  throwOnError: false,
  output: 'htmlAndMathml',
  strict: false,
  trust: true,
  macros: {
    '\\R': '\\mathbb{R}',
    '\\N': '\\mathbb{N}',
    '\\Z': '\\mathbb{Z}',
    '\\Q': '\\mathbb{Q}',
    '\\C': '\\mathbb{C}'
  }
})

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
