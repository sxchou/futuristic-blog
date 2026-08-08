import type { Directive } from 'vue'

const MIN_COL_WIDTH = 60

/**
 * 表格列宽可调整指令
 * 在 <table> 上使用 v-resizable-table，自动为每列添加拖拽手柄
 * - 拖拽列边缘：手动调整列宽，当前列增宽时下一列减宽，保持总宽度不变
 * - 双击列边缘：自动调整到最佳宽度（像 Excel 一样），根据内容计算
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

    /**
     * 计算指定列的最佳宽度（适应所有内容）
     * 递归设置 white-space:nowrap + overflow:visible，确保 Range 测量不换行的自然宽度
     */
    const calcBestWidth = (colIndex: number): number => {
      let maxWidth = 0
      const cells = el.querySelectorAll<HTMLTableCellElement>(
        `tr > td:nth-child(${colIndex + 1}), tr > th:nth-child(${colIndex + 1})`
      )

      // 收集需要恢复的样式
      const restoreList: { el: HTMLElement; ws: string; ov: string; mw: string }[] = []

      cells.forEach((cell) => {
        // 递归设置单元格及所有子元素：nowrap + visible + 无 max-width 限制
        const all = [cell, ...Array.from(cell.querySelectorAll<HTMLElement>('*'))]
        all.forEach((e) => {
          restoreList.push({ el: e, ws: e.style.whiteSpace, ov: e.style.overflow, mw: e.style.maxWidth })
          e.style.whiteSpace = 'nowrap'
          e.style.overflow = 'visible'
          e.style.maxWidth = 'none'
        })

        // Range API 测量内容自然宽度（浮点精度）
        const range = document.createRange()
        range.selectNodeContents(cell)
        const rect = range.getBoundingClientRect()
        const computed = window.getComputedStyle(cell)
        const padding = parseFloat(computed.paddingLeft) + parseFloat(computed.paddingRight)
        const totalWidth = rect.width + padding
        if (totalWidth > maxWidth) maxWidth = totalWidth
      })

      // 恢复所有样式
      restoreList.forEach(({ el, ws, ov, mw }) => {
        el.style.whiteSpace = ws
        el.style.overflow = ov
        el.style.maxWidth = mw
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
        curStartWidth = cols[i].offsetWidth
        nextStartWidth = cols[i + 1].offsetWidth

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
      }

      /**
       * 双击手柄：自动调整到最佳宽度（类似 Excel）
       * 当前列设为最佳宽度，下一列相应调整，保持总宽度不变
       */
      const onDblClick = (e: MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        const bestWidth = calcBestWidth(i)
        if (bestWidth <= 0) return

        const oldWidth = cols[i].offsetWidth
        // 内容未溢出（最佳宽度 <= 当前列宽 + 1px 容差），不调整
        if (bestWidth <= oldWidth + 1) return
        const nextOldWidth = cols[i + 1].offsetWidth
        const delta = bestWidth - oldWidth
        const newNextWidth = nextOldWidth - delta

        if (newNextWidth < MIN_COL_WIDTH) {
          // 下一列空间不足，当前列最多扩展到下一列剩余空间
          const maxAllowed = oldWidth + (nextOldWidth - MIN_COL_WIDTH)
          cols[i].style.width = maxAllowed + 'px'
          cols[i + 1].style.width = MIN_COL_WIDTH + 'px'
        } else {
          cols[i].style.width = bestWidth + 'px'
          cols[i + 1].style.width = newNextWidth + 'px'
        }
      }

      handle.addEventListener('mousedown', onMouseDown)
      handle.addEventListener('dblclick', onDblClick)
    })
  },
}

export default resizableTable
