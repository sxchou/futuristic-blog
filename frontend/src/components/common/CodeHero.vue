<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 打字机操作序列：write 逐字写入 / backspace 回退 / pause 停顿
type Op =
  | { kind: 'write'; s: string }
  | { kind: 'backspace'; n: number }
  | { kind: 'pause'; ms: number }

const ops: Op[] = [
  { kind: 'write', s: '// Welcome to Futuristic Blog\n' },
  { kind: 'write', s: 'const blog = {\n' },
  { kind: 'write', s: '  name: "Blog' },
  { kind: 'pause', ms: 520 },
  { kind: 'backspace', n: 4 },
  { kind: 'pause', ms: 160 },
  { kind: 'write', s: 'Futuristic Blog",\n' },
  { kind: 'write', s: '  mission: "Code for Future, Share for Growth",\n' },
  { kind: 'write', s: '  stack: ["Vue 3", "React' },
  { kind: 'pause', ms: 480 },
  { kind: 'backspace', n: 5 },
  { kind: 'pause', ms: 150 },
  { kind: 'write', s: 'FastAPI", "TypeScript"],\n' },
  { kind: 'write', s: '  explore() {\n' },
  { kind: 'write', s: '    return "开启未来探索之旅"\n' },
  { kind: 'write', s: '  }\n' },
  { kind: 'write', s: '}\n\n' },
  { kind: 'write', s: 'export default blog' }
]

// 预计算最终代码（用于降级展示与完成态判断）
const finalCode = (() => {
  let s = ''
  for (const op of ops) {
    if (op.kind === 'write') s += op.s
    else if (op.kind === 'backspace') s = s.slice(0, -op.n)
  }
  return s
})()

type TokenType =
  | 'comment' | 'string' | 'number' | 'keyword'
  | 'function' | 'variable' | 'property' | 'punctuation' | 'plain'

const KEYWORDS = new Set([
  'const', 'let', 'var', 'function', 'return', 'export', 'default',
  'new', 'if', 'else', 'for', 'while', 'import', 'from', 'class',
  'async', 'await', 'typeof', 'of', 'in'
])

// 轻量级语法 tokenizer，支持不完整代码（打字过程中）
function tokenize(code: string): { text: string; type: TokenType }[] {
  const tokens: { text: string; type: TokenType }[] = []
  let i = 0
  const n = code.length
  const push = (text: string, type: TokenType) => { if (text) tokens.push({ text, type }) }

  while (i < n) {
    const ch = code[i]

    // 空白与换行
    if (ch === '\n' || ch === ' ' || ch === '\t') {
      let j = i + 1
      while (j < n && (code[j] === '\n' || code[j] === ' ' || code[j] === '\t')) j++
      push(code.slice(i, j), 'plain')
      i = j
      continue
    }

    // 行注释
    if (ch === '/' && code[i + 1] === '/') {
      let j = i + 2
      while (j < n && code[j] !== '\n') j++
      push(code.slice(i, j), 'comment')
      i = j
      continue
    }

    // 字符串
    if (ch === '"' || ch === "'" || ch === '`') {
      const quote = ch
      let j = i + 1
      while (j < n && code[j] !== quote) {
        if (code[j] === '\\') j++
        j++
      }
      j = Math.min(j + 1, n)
      push(code.slice(i, j), 'string')
      i = j
      continue
    }

    // 数字
    if (/[0-9]/.test(ch)) {
      let j = i + 1
      while (j < n && /[0-9.]/.test(code[j])) j++
      push(code.slice(i, j), 'number')
      i = j
      continue
    }

    // 标识符
    if (/[a-zA-Z_$]/.test(ch)) {
      let j = i + 1
      while (j < n && /[a-zA-Z0-9_$]/.test(code[j])) j++
      const word = code.slice(i, j)
      let k = j
      while (k < n && code[k] === ' ') k++
      let type: TokenType = 'plain'
      if (KEYWORDS.has(word)) type = 'keyword'
      else if (code[k] === '(') type = 'function'
      else if (code[k] === ':') type = 'property'
      else type = 'variable'
      push(word, type)
      i = j
      continue
    }

    // 标点
    if ('{}[]().,;:=<>+-*/'.includes(ch)) {
      push(ch, 'punctuation')
      i++
      continue
    }

    push(ch, 'plain')
    i++
  }

  return tokens
}

const tokenClassMap: Record<TokenType, string> = {
  comment: 'tok-comment',
  string: 'tok-string',
  number: 'tok-number',
  keyword: 'tok-keyword',
  function: 'tok-function',
  variable: 'tok-variable',
  property: 'tok-property',
  punctuation: 'tok-punctuation',
  plain: 'tok-plain'
}
const tokenClass = (t: TokenType) => tokenClassMap[t]

const current = ref('')
const mode = ref<'type' | 'edit' | 'idle'>('type')

const tokens = computed(() => tokenize(current.value))

const lineCount = computed(() => Math.max((current.value.match(/\n/g)?.length || 0) + 1, 1))
// 行号文本：每行用 padStart 固定 2 字符宽度，避免位数变化导致偏移；
// 用 \n 分隔的纯文本交给 <pre> 渲染，与代码区使用相同的 inline formatting context，
// 从而消除 block-level 行号与 inline 代码之间因字体 metrics 导致的首行 0.5px 偏移与行距微差。
const gutterText = computed(() =>
  Array.from({ length: lineCount.value }, (_, i) => String(i + 1).padStart(2, ' ')).join('\n')
)
const cursorLn = computed(() => (current.value.slice(0, current.value.lastIndexOf('\n')).match(/\n/g)?.length || 0) + 1)
const cursorCol = computed(() => current.value.length - current.value.lastIndexOf('\n'))

const statusLabel = computed(() => mode.value === 'edit' ? 'Editing…' : mode.value === 'type' ? 'Typing…' : 'Ready')

let opIndex = 0
let charIndexInOp = 0
let timer: ReturnType<typeof setTimeout> | null = null
let restartTimer: ReturnType<typeof setTimeout> | null = null

const RESTART_DELAY = 7000

const tick = () => {
  if (opIndex >= ops.length) {
    mode.value = 'idle'
    restartTimer = setTimeout(() => {
      current.value = ''
      startTyping()
    }, RESTART_DELAY)
    return
  }

  const op = ops[opIndex]

  if (op.kind === 'write') {
    const typed = op.s[charIndexInOp]
    current.value += typed
    charIndexInOp++
    if (charIndexInOp >= op.s.length) { opIndex++; charIndexInOp = 0 }
    mode.value = 'type'

    let delay = 42 + Math.random() * 26
    if (typed === '\n') delay = 170
    else if (typed === ' ') delay = 22
    else if (',;:'.includes(typed)) delay = 78
    else if (/[^\x00-\x7F]/.test(typed)) delay = 95 + Math.random() * 35 // CJK 字符稍慢
    timer = setTimeout(tick, delay)
  } else if (op.kind === 'backspace') {
    current.value = current.value.slice(0, -1)
    charIndexInOp++
    mode.value = 'edit'
    if (charIndexInOp >= op.n) { opIndex++; charIndexInOp = 0 }
    timer = setTimeout(tick, 36)
  } else {
    opIndex++; charIndexInOp = 0
    timer = setTimeout(tick, op.ms)
  }
}

const startTyping = () => {
  opIndex = 0
  charIndexInOp = 0
  current.value = ''
  mode.value = 'type'
  tick()
}

const stopTimers = () => {
  if (timer) { clearTimeout(timer); timer = null }
  if (restartTimer) { clearTimeout(restartTimer); restartTimer = null }
}

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

const onVisibilityChange = () => {
  if (document.hidden) {
    stopTimers()
  } else if (!prefersReducedMotion()) {
    if (opIndex < ops.length && !timer && mode.value !== 'idle') {
      tick()
    } else if (opIndex >= ops.length && !restartTimer) {
      mode.value = 'idle'
      restartTimer = setTimeout(() => { current.value = ''; startTyping() }, 4000)
    }
  }
}

onMounted(() => {
  if (prefersReducedMotion()) {
    current.value = finalCode
    mode.value = 'idle'
  } else {
    startTyping()
  }
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  stopTimers()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <section class="code-hero" aria-label="站点介绍">
    <div class="hero-grid">
      <!-- 代码编辑器窗口 -->
      <div class="editor-wrap">
        <div class="editor-window" role="img" :aria-label="`代码编辑器演示：${statusLabel}`">
          <div class="editor-titlebar">
            <span class="dot dot-red" />
            <span class="dot dot-yellow" />
            <span class="dot dot-green" />
            <span class="filename">future.ts</span>
            <span class="lang-tag">TS</span>
          </div>

          <div class="editor-body">
            <pre class="gutter" aria-hidden="true"><code>{{ gutterText }}</code></pre>
            <pre class="code-area"><code><template v-for="(tok, i) in tokens" :key="i"><span :class="tokenClass(tok.type)">{{ tok.text }}</span></template><span class="cursor" :class="mode" aria-hidden="true" /></code></pre>
          </div>

          <div class="editor-statusbar">
            <span class="status-item status-led-item">
              <span class="status-led" :class="mode" />
              <span class="status-label">{{ statusLabel }}</span>
            </span>
            <span class="status-right-group">
              <span class="status-item">TypeScript</span>
              <span class="status-item">UTF-8</span>
              <span class="status-item">Ln <span class="num-cell">{{ cursorLn }}</span>, Col <span class="num-cell">{{ cursorCol }}</span></span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.code-hero {
  position: relative;
  margin-bottom: 1.5rem;
}

/* minmax(0,1fr) 允许列宽收缩到 min-content 以下，防止移动端代码行撑破屏幕 */
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1.5rem;
  align-items: center;
}

/* —— 代码编辑器 —— */
.editor-wrap {
  position: relative;
  min-width: 0;
}

.editor-window {
  position: relative;
  border-radius: 0.9rem;
  overflow: hidden;
  background: var(--ed-bg);
  border: 1px solid var(--ed-border);
  box-shadow: var(--ed-shadow);

  /* 主题变量 —— 日间模式（默认） */
  --ed-bg: #ffffff;
  --ed-bg-alt: #f8fafc;
  --ed-bg-status: #f8fafc;
  --ed-border: rgba(15, 23, 42, 0.10);
  --ed-border-soft: rgba(15, 23, 42, 0.06);
  --ed-text: #1f2937;
  --ed-text-muted: #64748b;
  --ed-gutter: #94a3b8;
  --ed-accent: #00aacc;
  --ed-accent-soft: rgba(0, 170, 204, 0.12);
  --ed-accent-border: rgba(0, 170, 204, 0.35);
  --ed-shadow: 0 18px 40px -20px rgba(15, 23, 42, 0.22), 0 0 0 1px rgba(15, 23, 42, 0.02);
  --ed-scrollbar: rgba(15, 23, 42, 0.18);
  --ed-scrollbar-hover: rgba(15, 23, 42, 0.32);
  --tok-comment: #94a3b8;
  --tok-string: #15803d;
  --tok-number: #b45309;
  --tok-keyword: #7c3aed;
  --tok-function: #00aacc;
  --tok-variable: #be185d;
  --tok-property: #6d28d9;
  --tok-punctuation: #64748b;
  --tok-plain: #1f2937;
  --ed-cursor: #00aacc;
  --ed-cursor-glow: rgba(0, 170, 204, 0.45);
  --ed-cursor-edit: #b45309;
  --ed-cursor-edit-glow: rgba(180, 83, 9, 0.45);
  --ed-led: #00aacc;
  --ed-led-edit: #b45309;
  --ed-led-idle: #15803d;
  --ed-led-idle-glow: rgba(21, 128, 61, 0.4);
}

/* 暗黑模式覆盖 */
.dark .editor-window {
  --ed-bg: #0a0a0a;
  --ed-bg-alt: #141414;
  --ed-bg-status: #111111;
  --ed-border: rgba(255, 255, 255, 0.08);
  --ed-border-soft: rgba(255, 255, 255, 0.06);
  --ed-text: #d4d4d4;
  --ed-text-muted: #64748b;
  --ed-gutter: #3a3a3a;
  --ed-accent: #00d4ff;
  --ed-accent-soft: rgba(0, 212, 255, 0.1);
  --ed-accent-border: rgba(0, 212, 255, 0.25);
  --ed-shadow: 0 18px 40px -18px rgba(0, 0, 0, 0.45), 0 2px 0 0 rgba(0, 212, 255, 0.25) inset;
  --ed-scrollbar: rgba(0, 212, 255, 0.25);
  --ed-scrollbar-hover: rgba(0, 212, 255, 0.45);
  --tok-comment: #64748b;
  --tok-string: #10b981;
  --tok-number: #f59e0b;
  --tok-keyword: #a78bfa;
  --tok-function: #00d4ff;
  --tok-variable: #ec4899;
  --tok-property: #ddd6fe;
  --tok-punctuation: #64748b;
  --tok-plain: #d4d4d4;
  --ed-cursor: #00d4ff;
  --ed-cursor-glow: rgba(0, 212, 255, 0.65);
  --ed-cursor-edit: #f59e0b;
  --ed-cursor-edit-glow: rgba(245, 158, 11, 0.7);
  --ed-led: #00d4ff;
  --ed-led-edit: #f59e0b;
  --ed-led-idle: #10b981;
  --ed-led-idle-glow: rgba(16, 185, 129, 0.7);
}

.editor-titlebar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 0.85rem;
  background: var(--ed-bg-alt);
  border-bottom: 1px solid var(--ed-border-soft);
}

.dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-red { background: #ff5f57; }
.dot-yellow { background: #febc2e; }
.dot-green { background: #28c840; }

.filename {
  margin-left: 0.6rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: var(--ed-text-muted);
}

.lang-tag {
  margin-left: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--ed-accent);
  padding: 0.1rem 0.4rem;
  border-radius: 0.3rem;
  background: var(--ed-accent-soft);
  border: 1px solid var(--ed-accent-border);
}

.editor-body {
  display: flex;
  align-items: stretch;
  min-height: 300px;
  background: var(--ed-bg);
}

/* 行号区使用 <pre> 渲染：与代码区完全对称的 inline formatting context，
   共享相同的字体 metrics 与 line-box 高度，从根本上消除首行偏移与行距微差。
   视觉样式（颜色/padding/字号/右对齐/右边框）与原 flex 列实现一致。 */
.gutter {
  margin: 0;
  padding: 1rem 0.6rem 1rem 0.85rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--ed-gutter);
  text-align: right;
  user-select: none;
  /* 全局 pre 样式会注入 border-top/border-radius/background，这里显式重置，
     避免行号区出现圆角与背景污染，同时消除与代码区的 1px 垂直偏移 */
  border: none;
  border-right: 1px solid var(--ed-border-soft);
  border-radius: 0;
  background: transparent;
  flex-shrink: 0;
  white-space: pre;
}

.code-area {
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 1rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--tok-plain);
  white-space: pre;
  overflow-x: auto;
  background: transparent;
  border: none;
  tab-size: 2;
}

.code-area code,
.gutter code {
  font-family: inherit;
  background: transparent;
  white-space: pre;
}

/* 语法高亮配色 —— 与项目 hljs 体系一致 */
.tok-comment { color: var(--tok-comment); font-style: italic; }
.tok-string { color: var(--tok-string); }
.tok-number { color: var(--tok-number); }
.tok-keyword { color: var(--tok-keyword); }
.tok-function { color: var(--tok-function); }
.tok-variable { color: var(--tok-variable); }
.tok-property { color: var(--tok-property); }
.tok-punctuation { color: var(--tok-punctuation); }
.tok-plain { color: var(--tok-plain); }

/* 光标 */
.cursor {
  display: inline-block;
  width: 0.62ch;
  height: 1.15em;
  vertical-align: text-bottom;
  margin-left: 1px;
  background: var(--ed-cursor);
  box-shadow: 0 0 6px var(--ed-cursor-glow);
  animation: cursor-blink 1.05s steps(2) infinite;
  transform: translateY(2px);
}

.cursor.edit {
  background: var(--ed-cursor-edit);
  box-shadow: 0 0 6px var(--ed-cursor-edit-glow);
}

.cursor.idle {
  opacity: 0.85;
  animation: cursor-blink 1.2s steps(2) infinite;
}

@keyframes cursor-blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

/* 状态栏 —— 数字与标签均预留宽度，避免打字过程布局抖动 */
.editor-statusbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.4rem 0.85rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.7rem;
  color: var(--ed-text-muted);
  background: var(--ed-bg-status);
  border-top: 1px solid var(--ed-border-soft);
  font-variant-numeric: tabular-nums;
}

.status-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  white-space: nowrap;
}

.status-label {
  display: inline-block;
  min-width: 9ch;
}

.status-right-group {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 1rem;
}

.num-cell {
  display: inline-block;
  min-width: 2ch;
  text-align: right;
}

.status-led {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ed-led);
  box-shadow: 0 0 5px var(--ed-cursor-glow);
}

.status-led.edit {
  background: var(--ed-led-edit);
  box-shadow: 0 0 5px var(--ed-cursor-edit-glow);
}

.status-led.idle {
  background: var(--ed-led-idle);
  box-shadow: 0 0 5px var(--ed-led-idle-glow);
  animation: none;
}

.status-led-item .status-led {
  animation: led-pulse 1.4s ease-in-out infinite;
}

.status-led-item .status-led.idle {
  animation: none;
}

@keyframes led-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 小屏适配 —— 缩小字号与内边距，给代码区更多横向空间 */
@media (max-width: 640px) {
  .editor-body { min-height: 264px; }
  .code-area, .gutter { font-size: 0.72rem; line-height: 1.55; }
  .code-area { padding: 0.75rem 0.7rem; }
  .gutter { padding: 0.75rem 0.45rem 0.75rem 0.6rem; }
  .editor-titlebar { padding: 0.5rem 0.65rem; }
  .editor-statusbar { gap: 0.6rem; padding: 0.35rem 0.6rem; font-size: 0.64rem; }
  .status-right-group { gap: 0.6rem; }
  .status-label { min-width: 8ch; }
}

/* 滚动条 */
.code-area::-webkit-scrollbar { height: 6px; }
.code-area::-webkit-scrollbar-track { background: transparent; }
.code-area::-webkit-scrollbar-thumb {
  background: var(--ed-scrollbar);
  border-radius: 3px;
}
.code-area::-webkit-scrollbar-thumb:hover { background: var(--ed-scrollbar-hover); }
</style>
