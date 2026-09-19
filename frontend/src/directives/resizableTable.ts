import type { Directive } from 'vue'

const MIN_COL_WIDTH = 60
const STORAGE_PREFIX = 'resizable-table:'

/**
 * 表格列宽可调整指令
 * 在 <table> 上使用 v-resizable-table，自动为每列添加拖拽手柄
 * - 拖拽列边缘：手动调整列宽，当前列增宽时下一列减宽，保持总宽度不变
 * - 双击列边缘：自动调整到最佳宽度（像 Excel 一样，双向自适应：内容溢出则加宽、
 *   列宽超过内容则收窄；多次双击同一列结果稳定不变）
 * - 列宽持久化到 localStorage（key = 页面路径 + 表头签名），
 *   页面刷新或组件重新挂载后自动恢复
 */
const resizableTable: Directive<HTMLTableElement> = {
  mounted(el) {
    // 确保 table-fixed 布局，使 colgroup 的 col width 生效
    el.style.tableLayout = 'fixed'

    const ths = el.querySelectorAll<HTMLTableCellElement>('thead th')
    if (!ths.length) return

    // 创建 colgroup 并根据 th 当前宽度初始化 col
    const colgroup = document.createElement('colgroup')
    const cols: HTMLTableColElement[] = []

    ths.forEach((th) => {
      const col = document.createElement('col')
      const rect = th.getBoundingClientRect()
      const width = rect.width || th.offsetWidth
      col.style.width = width + 'px'
      colgroup.appendChild(col)
      cols.push(col)
    })

    el.insertBefore(colgroup, el.firstChild)

    // ---- 列宽持久化：同页多表格靠表头签名区分 ----
    const headersSignature = Array.from(ths)
      .map((t) => (t.textContent || '').trim())
      .join('>')
    const storageKey = `${STORAGE_PREFIX}${window.location.pathname}:${headersSignature}`

    // 读取列宽：以 col.style.width 为准（本指令写入的唯一事实来源）。
    // 不使用 col.offsetWidth：当各列 style 宽度之和小于表格实际宽度时（如 w-full
    // 表格），浏览器会按比例拉伸列，offsetWidth 返回拉伸后的渲染宽度，与
    // style.width 形成正反馈，导致反复双击时列宽持续增长
    const getColWidth = (idx: number): number => parseFloat(cols[idx].style.width) || 0

    const persistWidths = () => {
      try {
        localStorage.setItem(storageKey, JSON.stringify(cols.map((_, idx) => getColWidth(idx))))
      } catch {
        // localStorage 不可用（隐私模式等）时静默忽略
      }
    }

    const restoreWidths = () => {
      try {
        const raw = localStorage.getItem(storageKey)
        if (!raw) return
        const saved: unknown = JSON.parse(raw)
        if (!Array.isArray(saved) || saved.length !== cols.length) return
        saved.forEach((w, idx) => {
          if (typeof w === 'number' && w >= MIN_COL_WIDTH) {
            cols[idx].style.width = `${w}px`
          }
        })
      } catch {
        // 存储数据损坏时忽略，回退默认宽度
      }
    }
    restoreWidths()

    /**
     * 将单元格克隆到"自然宽度"测量容器中测量内容宽度
     *
     * 不在原单元格上直接测量（旧实现的问题）：
     * 1. 拖拽手柄是 th 内绝对定位元素（right:-3px 超出右边缘），
     *    计入测量会让"最佳宽度"永远比当前列宽大约 3px，
     *    导致反复双击同一列时列宽持续增长（本次修复的核心 Bug）
     * 2. 单元格内百分比宽度元素（w-full 等）的宽度跟随当前列宽，
     *    测量结果被当前列宽污染，导致双击无法收窄回最佳宽度
     *
     * 测量容器（position:absolute + width:max-content + nowrap）：
     * - 挂在原单元格内，完整继承字体、字距等环境样式
     * - 克隆体中的手柄已移除，不参与测量
     * - 以内联 width:auto / max-width:none / flex:none 覆盖克隆体中
     *   来自类名的固定与百分比宽度，让所有元素按内容自然宽度计算
     * - 同步添加、测量、移除，不触发浏览器绘制，无闪烁
     */
    const measureCell = (cell: HTMLTableCellElement): number => {
      const wrapper = document.createElement('div')
      wrapper.style.cssText =
        'position:absolute;visibility:hidden;white-space:nowrap;width:max-content;pointer-events:none;'

      const clone = cell.cloneNode(true) as HTMLTableCellElement
      clone.querySelectorAll('.col-resize-handle').forEach((h) => h.remove())
      clone.style.display = 'block'
      clone.style.width = 'auto'
      clone.style.maxWidth = 'none'
      clone.style.whiteSpace = 'nowrap'
      clone.querySelectorAll<HTMLElement>('*').forEach((e) => {
        e.style.width = 'auto'
        e.style.maxWidth = 'none'
        e.style.flex = 'none'
        e.style.whiteSpace = 'nowrap'
      })

      wrapper.appendChild(clone)
      cell.appendChild(wrapper)
      const width = clone.getBoundingClientRect().width
      wrapper.remove()
      return width
    }

    /** 计算指定列的最佳宽度（刚好容纳该列最宽内容，含内边距） */
    const calcBestWidth = (colIndex: number): number => {
      let maxWidth = 0
      const cells = el.querySelectorAll<HTMLTableCellElement>(
        `tr > td:nth-child(${colIndex + 1}), tr > th:nth-child(${colIndex + 1})`
      )
      cells.forEach((cell) => {
        const width = measureCell(cell)
        if (width > maxWidth) maxWidth = width
      })
      return Math.ceil(maxWidth)
    }

    // 为除最后一列外的每列添加拖拽手柄
    ths.forEach((th, i) => {
      if (i >= ths.length - 1) return

      th.style.position = 'relative'

      const handle = document.createElement('div')
      handle.className = 'col-resize-handle'
      th.appendChild(handle)

      let startX = 0
      let curStartWidth = 0
      let nextStartWidth = 0

      const onMouseDown = (e: MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        startX = e.clientX
        curStartWidth = getColWidth(i)
        nextStartWidth = getColWidth(i + 1)

        handle.classList.add('active')
        document.body.style.cursor = 'col-resize'
        document.body.style.userSelect = 'none'

        document.addEventListener('mousemove', onMouseMove)
        document.addEventListener('mouseup', onMouseUp)
      }

      const onMouseMove = (e: MouseEvent) => {
        const delta = e.clientX - startX
        const newCurWidth = curStartWidth + delta
        const newNextWidth = nextStartWidth - delta

        // 两列都不能小于最小宽度
        if (newCurWidth < MIN_COL_WIDTH || newNextWidth < MIN_COL_WIDTH) return

        cols[i].style.width = newCurWidth + 'px'
        cols[i + 1].style.width = newNextWidth + 'px'
      }

      const onMouseUp = () => {
        handle.classList.remove('active')
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        document.removeEventListener('mousemove', onMouseMove)
        document.removeEventListener('mouseup', onMouseUp)
        persistWidths()
      }

      /**
       * 双击手柄：自动调整到最佳宽度（类似 Excel，双向自适应）
       * 当前列与下一列互补增减，保持总宽度不变；多次双击结果稳定不变
       */
      const onDblClick = (e: MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        const natural = calcBestWidth(i)
        if (natural <= 0) return
        const bestWidth = Math.max(MIN_COL_WIDTH, natural)

        const oldWidth = getColWidth(i)
        const delta = bestWidth - oldWidth
        // 已处于最佳宽度（2px 容差吸收亚像素舍入误差），不调整
        if (Math.abs(delta) < 2) return

        const nextOldWidth = getColWidth(i + 1)
        const newNextWidth = nextOldWidth - delta

        if (newNextWidth < MIN_COL_WIDTH) {
          // 仅加宽方向可能发生：下一列剩余空间不足时，当前列最多扩展到该空间
          const maxAllowed = oldWidth + (nextOldWidth - MIN_COL_WIDTH)
          if (maxAllowed <= oldWidth + 1) return
          cols[i].style.width = maxAllowed + 'px'
          cols[i + 1].style.width = MIN_COL_WIDTH + 'px'
        } else {
          cols[i].style.width = bestWidth + 'px'
          cols[i + 1].style.width = newNextWidth + 'px'
        }
        persistWidths()
      }

      handle.addEventListener('mousedown', onMouseDown)
      handle.addEventListener('dblclick', onDblClick)
    })
  },
}

export default resizableTable
