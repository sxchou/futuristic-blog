<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import JSZip from 'jszip'
import * as XLSX from 'xlsx'
import mammoth from 'mammoth'

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.js`

const props = defineProps<{
  fileId: number
  filename: string
  mimeType: string
  fileUrl: string
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(true)
const error = ref('')
const previewType = computed(() => {
  const { mimeType, filename } = props
  
  if (mimeType.includes('pdf')) return 'pdf'
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('text/') || 
      mimeType.includes('json') || 
      mimeType.includes('javascript') ||
      mimeType.includes('xml') ||
      mimeType.includes('markdown') ||
      filename.endsWith('.txt') ||
      filename.endsWith('.md') ||
      filename.endsWith('.json') ||
      filename.endsWith('.js') ||
      filename.endsWith('.css') ||
      filename.endsWith('.html') ||
      filename.endsWith('.xml')) return 'text'
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet') || 
      mimeType.includes('sheet') || filename.endsWith('.xlsx') || 
      filename.endsWith('.xls') || filename.endsWith('.csv')) return 'excel'
  if (mimeType.includes('word') || mimeType.includes('document') ||
      filename.endsWith('.docx')) return 'word'
  if (mimeType.includes('powerpoint') || mimeType.includes('presentation') ||
      filename.endsWith('.pptx')) return 'powerpoint'
  if (mimeType.includes('zip') || mimeType.includes('rar') || 
      mimeType.includes('7z') || mimeType.includes('compressed') ||
      mimeType.includes('tar') || mimeType.includes('gzip')) return 'archive'
  
  return 'unsupported'
})

const textContent = ref('')
const textEncoding = ref('UTF-8')
const pdfDoc = ref<pdfjsLib.PDFDocumentProxy | null>(null)
const currentPage = ref(1)
const totalPages = ref(0)
const pdfScale = ref(1.5)
const excelData = ref<string[][]>([])
const excelSheets = ref<string[]>([])
const currentSheet = ref(0)
const archiveFiles = ref<{ name: string; size: number; type: string }[]>([])
const wordHtml = ref('')
const pptSlides = ref<string[]>([])
const currentSlide = ref(0)

const imageUrl = computed(() => props.fileUrl)

const detectEncoding = (buffer: ArrayBuffer): string => {
  const uint8Array = new Uint8Array(buffer)
  
  if (uint8Array[0] === 0xEF && uint8Array[1] === 0xBB && uint8Array[2] === 0xBF) {
    return 'UTF-8'
  }
  if (uint8Array[0] === 0xFF && uint8Array[1] === 0xFE) {
    return 'UTF-16LE'
  }
  if (uint8Array[0] === 0xFE && uint8Array[1] === 0xFF) {
    return 'UTF-16BE'
  }
  
  let isUtf8 = true
  for (let i = 0; i < buffer.byteLength && i < 10000; i++) {
    const byte = uint8Array[i]
    if (byte > 127) {
      if (byte >= 0xC0 && byte <= 0xDF) {
        if (i + 1 >= buffer.byteLength || (uint8Array[i + 1] & 0xC0) !== 0x80) {
          isUtf8 = false
          break
        }
        i++
      } else if (byte >= 0xE0 && byte <= 0xEF) {
        if (i + 2 >= buffer.byteLength || 
            (uint8Array[i + 1] & 0xC0) !== 0x80 ||
            (uint8Array[i + 2] & 0xC0) !== 0x80) {
          isUtf8 = false
          break
        }
        i += 2
      } else if (byte >= 0xF0 && byte <= 0xF7) {
        if (i + 3 >= buffer.byteLength ||
            (uint8Array[i + 1] & 0xC0) !== 0x80 ||
            (uint8Array[i + 2] & 0xC0) !== 0x80 ||
            (uint8Array[i + 3] & 0xC0) !== 0x80) {
          isUtf8 = false
          break
        }
        i += 3
      } else {
        isUtf8 = false
        break
      }
    }
  }
  
  if (isUtf8) return 'UTF-8'
  
  const gbkCommonChars = new Set()
  for (let i = 0x81; i <= 0xFE; i++) {
    for (let j = 0x40; j <= 0xFE; j++) {
      if (j !== 0x7F) {
        gbkCommonChars.add((i << 8) | j)
      }
    }
  }
  
  let gbkScore = 0
  for (let i = 0; i < buffer.byteLength - 1 && i < 10000; i++) {
    const byte1 = uint8Array[i]
    const byte2 = uint8Array[i + 1]
    if (byte1 >= 0x81 && byte1 <= 0xFE && byte2 >= 0x40 && byte2 <= 0xFE && byte2 !== 0x7F) {
      gbkScore++
    }
  }
  
  if (gbkScore > 10) return 'GBK'
  
  return 'UTF-8'
}

const decodeBuffer = (buffer: ArrayBuffer, encoding: string): string => {
  try {
    const decoder = new TextDecoder(encoding)
    return decoder.decode(buffer)
  } catch {
    const decoder = new TextDecoder('UTF-8')
    return decoder.decode(buffer)
  }
}

const loadPreview = async () => {
  loading.value = true
  error.value = ''
  
  try {
    switch (previewType.value) {
      case 'pdf':
        await loadPdf()
        break
      case 'text':
        await loadText()
        break
      case 'excel':
        await loadExcel()
        break
      case 'archive':
        await loadArchive()
        break
      case 'word':
        await loadWord()
        break
      case 'powerpoint':
        await loadPowerPoint()
        break
      case 'image':
        break
      default:
        error.value = '此文件类型暂不支持预览，请下载后查看'
        break
    }
  } catch (err) {
    console.error('Preview error:', err)
    error.value = '文件预览失败，请尝试下载后查看'
  } finally {
    loading.value = false
  }
}

const loadPdf = async () => {
  const loadingTask = pdfjsLib.getDocument({
    url: props.fileUrl,
    cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/',
    cMapPacked: true,
  })
  pdfDoc.value = await loadingTask.promise
  totalPages.value = pdfDoc.value.numPages
  currentPage.value = 1
  await nextTick()
  await renderPdfPage(1)
}

const renderPdfPage = async (pageNum: number) => {
  if (!pdfDoc.value) return
  
  const page = await pdfDoc.value.getPage(pageNum)
  const viewport = page.getViewport({ scale: pdfScale.value })
  
  const canvas = document.getElementById('pdf-canvas') as HTMLCanvasElement
  if (!canvas) return
  
  const context = canvas.getContext('2d')
  canvas.height = viewport.height
  canvas.width = viewport.width
  
  await page.render({
    canvasContext: context!,
    viewport: viewport,
    canvas: canvas
  }).promise
}

const prevPage = async () => {
  if (currentPage.value > 1) {
    currentPage.value--
    await renderPdfPage(currentPage.value)
  }
}

const nextPage = async () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    await renderPdfPage(currentPage.value)
  }
}

const loadText = async () => {
  const response = await fetch(props.fileUrl)
  const buffer = await response.arrayBuffer()
  
  const encoding = detectEncoding(buffer)
  textEncoding.value = encoding
  
  textContent.value = decodeBuffer(buffer, encoding)
}

const loadExcel = async () => {
  const response = await fetch(props.fileUrl)
  const arrayBuffer = await response.arrayBuffer()
  
  const isCsv = props.filename.toLowerCase().endsWith('.csv')
  
  let workbook: XLSX.WorkBook
  if (isCsv) {
    const decoder = new TextDecoder('utf-8')
    const text = decoder.decode(arrayBuffer)
    workbook = XLSX.read(text, { type: 'string' })
  } else {
    workbook = XLSX.read(arrayBuffer, { type: 'array' })
  }
  
  excelSheets.value = workbook.SheetNames
  currentSheet.value = 0
  
  loadSheet(workbook, 0)
}

const loadSheet = (workbook: XLSX.WorkBook, sheetIndex: number) => {
  const sheetName = workbook.SheetNames[sheetIndex]
  const worksheet = workbook.Sheets[sheetName]
  const data = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' }) as string[][]
  excelData.value = data
}

const loadArchive = async () => {
  const response = await fetch(props.fileUrl)
  const arrayBuffer = await response.arrayBuffer()
  const zip = await JSZip.loadAsync(arrayBuffer)
  
  const files: { name: string; size: number; type: string }[] = []
  
  const promises: Promise<void>[] = []
  
  zip.forEach((relativePath, file) => {
    if (file.dir) {
      files.push({
        name: relativePath,
        size: 0,
        type: 'directory'
      })
    } else {
      const promise = file.async('uint8array').then(data => {
        files.push({
          name: relativePath,
          size: data.length,
          type: 'file'
        })
      })
      promises.push(promise)
    }
  })
  
  await Promise.all(promises)
  
  archiveFiles.value = files.sort((a, b) => {
    if (a.type === 'directory' && b.type !== 'directory') return -1
    if (a.type !== 'directory' && b.type === 'directory') return 1
    return a.name.localeCompare(b.name)
  })
}

const loadWord = async () => {
  const response = await fetch(props.fileUrl)
  const arrayBuffer = await response.arrayBuffer()
  const result = await mammoth.convertToHtml({ arrayBuffer })
  wordHtml.value = result.value || '<p>文档内容为空或无法解析</p>'
}

const loadPowerPoint = async () => {
  const response = await fetch(props.fileUrl)
  const arrayBuffer = await response.arrayBuffer()
  const zip = await JSZip.loadAsync(arrayBuffer)
  
  const slides: string[] = []
  
  const slideFiles: string[] = []
  zip.forEach((relativePath) => {
    if (relativePath.match(/ppt\/slides\/slide\d+\.xml$/)) {
      slideFiles.push(relativePath)
    }
  })
  
  slideFiles.sort((a, b) => {
    const numA = parseInt(a.match(/slide(\d+)\.xml$/)?.[1] || '0')
    const numB = parseInt(b.match(/slide(\d+)\.xml$/)?.[1] || '0')
    return numA - numB
  })
  
  for (const slideFile of slideFiles) {
    const content = await zip.file(slideFile)?.async('string')
    if (content) {
      const textMatches = content.match(/<a:t>([^<]*)<\/a:t>/g)
      if (textMatches) {
        const texts = textMatches.map(m => m.replace(/<a:t>|<\/a:t>/g, '')).join(' ')
        slides.push(texts)
      } else {
        slides.push('')
      }
    }
  }
  
  pptSlides.value = slides
  currentSlide.value = 0
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const downloadFile = () => {
  const link = document.createElement('a')
  link.href = props.fileUrl
  link.download = props.filename
  link.click()
}

watch(() => props.fileId, () => {
  loadPreview()
})

onMounted(() => {
  loadPreview()
})
</script>

<template>
  <div class="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" @click.self="emit('close')">
    <div class="bg-white dark:bg-dark-200 rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
      <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-white/10">
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate max-w-md">
            {{ filename }}
          </h3>
          <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 rounded">
            {{ mimeType }}
          </span>
          <span v-if="textEncoding !== 'UTF-8'" class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded">
            {{ textEncoding }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="downloadFile"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载
          </button>
          <button
            @click="emit('close')"
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="flex-1 overflow-auto p-4">
        <div v-if="loading" class="flex items-center justify-center h-64">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        
        <div v-else-if="error" class="flex flex-col items-center justify-center h-64 text-red-500">
          <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p>{{ error }}</p>
          <button
            @click="downloadFile"
            class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            下载文件
          </button>
        </div>
        
        <template v-else>
          <div v-if="previewType === 'pdf'" class="flex flex-col items-center">
            <div v-if="totalPages > 1" class="sticky top-0 z-10 bg-white dark:bg-dark-200 py-2 mb-4 flex items-center justify-center gap-4">
              <button
                @click="prevPage"
                :disabled="currentPage <= 1"
                class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100 disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-dark-50"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span class="text-sm text-gray-600 dark:text-gray-400 min-w-[80px] text-center">
                {{ currentPage }} / {{ totalPages }}
              </span>
              <button
                @click="nextPage"
                :disabled="currentPage >= totalPages"
                class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100 disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-dark-50"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
            <canvas id="pdf-canvas" class="max-w-full h-auto shadow-lg rounded-lg"></canvas>
          </div>
          
          <div v-else-if="previewType === 'image'" class="flex items-center justify-center">
            <img :src="imageUrl" :alt="filename" class="max-w-full max-h-[70vh] object-contain" />
          </div>
          
          <div v-else-if="previewType === 'text'" class="bg-gray-50 dark:bg-dark-100 rounded-lg p-4 overflow-auto max-h-[70vh]">
            <pre class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono break-all">{{ textContent }}</pre>
          </div>
          
          <div v-else-if="previewType === 'excel'" class="overflow-auto max-h-[70vh]">
            <div v-if="excelSheets.length > 1" class="flex gap-2 mb-4 flex-wrap">
              <button
                v-for="(sheet, index) in excelSheets"
                :key="sheet"
                @click="currentSheet = index"
                :class="[
                  'px-3 py-1 rounded-lg text-sm transition-colors',
                  currentSheet === index
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-50'
                ]"
              >
                {{ sheet }}
              </button>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full border-collapse">
                <tbody>
                  <tr v-for="(row, rowIndex) in excelData" :key="rowIndex" class="border-b border-gray-200 dark:border-white/10">
                    <td class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-dark-100 w-10 text-center sticky left-0">
                      {{ rowIndex + 1 }}
                    </td>
                    <td
                      v-for="(cell, cellIndex) in row"
                      :key="cellIndex"
                      class="px-3 py-2 text-sm text-gray-800 dark:text-gray-200 border-r border-gray-200 dark:border-white/10 last:border-r-0 whitespace-nowrap"
                    >
                      {{ cell }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div v-else-if="previewType === 'word'" class="bg-white dark:bg-dark-100 rounded-lg p-6 overflow-auto max-h-[70vh] prose dark:prose-invert max-w-none">
            <div v-html="wordHtml"></div>
          </div>
          
          <div v-else-if="previewType === 'powerpoint'" class="max-h-[70vh] overflow-auto">
            <div v-if="pptSlides.length > 1" class="sticky top-0 z-10 bg-white dark:bg-dark-200 py-2 mb-4 flex items-center justify-center gap-4">
              <button
                @click="currentSlide = Math.max(0, currentSlide - 1)"
                :disabled="currentSlide <= 0"
                class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100 disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-dark-50"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span class="text-sm text-gray-600 dark:text-gray-400 min-w-[80px] text-center">
                {{ currentSlide + 1 }} / {{ pptSlides.length }}
              </span>
              <button
                @click="currentSlide = Math.min(pptSlides.length - 1, currentSlide + 1)"
                :disabled="currentSlide >= pptSlides.length - 1"
                class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100 disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-dark-50"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
            <div class="bg-gray-50 dark:bg-dark-100 rounded-lg p-6 min-h-[300px]">
              <p class="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{{ pptSlides[currentSlide] || '此幻灯片无文本内容' }}</p>
            </div>
          </div>
          
          <div v-else-if="previewType === 'archive'" class="max-h-[70vh] overflow-auto">
            <div class="space-y-1">
              <div
                v-for="file in archiveFiles"
                :key="file.name"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-100"
              >
                <svg v-if="file.type === 'directory'" class="w-5 h-5 text-yellow-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
                </svg>
                <svg v-else class="w-5 h-5 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4z" />
                </svg>
                <span class="flex-1 text-sm text-gray-800 dark:text-gray-200 truncate">{{ file.name }}</span>
                <span v-if="file.type !== 'directory'" class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                  {{ formatFileSize(file.size) }}
                </span>
              </div>
            </div>
          </div>
          
          <div v-else class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="mb-4">此文件类型暂不支持在线预览</p>
            <button
              @click="downloadFile"
              class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              下载文件
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose {
  line-height: 1.7;
}
.prose :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}
.prose :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.prose :deep(p) {
  margin-bottom: 0.75rem;
}
.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}
.prose :deep(th),
.prose :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem;
}
.prose :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>
