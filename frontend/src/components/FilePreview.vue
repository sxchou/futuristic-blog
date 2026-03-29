<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import JSZip from 'jszip'

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
const previewMode = ref<'local' | 'online'>('online')

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
      filename.endsWith('.docx') || filename.endsWith('.doc')) return 'word'
  if (mimeType.includes('powerpoint') || mimeType.includes('presentation') ||
      filename.endsWith('.pptx') || filename.endsWith('.ppt')) return 'powerpoint'
  if (mimeType.includes('zip') || mimeType.includes('rar') || 
      mimeType.includes('7z') || mimeType.includes('compressed') ||
      mimeType.includes('tar') || mimeType.includes('gzip')) return 'archive'
  
  return 'unsupported'
})

const isOfficeFile = computed(() => {
  return ['word', 'excel', 'powerpoint'].includes(previewType.value)
})

const isProduction = computed(() => {
  const url = props.fileUrl
  return url.startsWith('https://') && 
         !url.includes('localhost') && 
         !url.includes('127.0.0.1') &&
         !url.includes('0.0.0.0')
})

const officeOnlineUrl = computed(() => {
  if (!isProduction.value) return null
  return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(props.fileUrl)}}`
})

const textContent = ref('')
const textEncoding = ref('UTF-8')
const pdfDoc = ref<pdfjsLib.PDFDocumentProxy | null>(null)
const currentPage = ref(1)
const totalPages = ref(0)
const pdfScale = ref(1.5)
const archiveFiles = ref<{ name: string; size: number; type: string }[]>([])

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
  
  if (isOfficeFile.value) {
    if (isProduction.value) {
      previewMode.value = 'online'
      loading.value = false
      return
    } else {
      error.value = 'Office 文件在线预览需要部署到公网环境（HTTPS）。\n本地开发环境请下载文件后查看。'
      loading.value = false
      return
    }
  }
  
  try {
    switch (previewType.value) {
      case 'pdf':
        await loadPdf()
        break
      case 'text':
        await loadText()
        break
      case 'archive':
        await loadArchive()
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

const openInNewTab = () => {
  if (officeOnlineUrl.value) {
    window.open(officeOnlineUrl.value, '_blank')
  }
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
            v-if="isOfficeFile && isProduction"
            @click="openInNewTab"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            新窗口打开
          </button>
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
        
        <div v-else-if="error" class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-center whitespace-pre-line mb-4">{{ error }}</p>
          <button
            @click="downloadFile"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            下载文件
          </button>
        </div>
        
        <template v-else>
          <div v-if="isOfficeFile && isProduction" class="h-full">
            <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center gap-2">
              <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-sm text-blue-700 dark:text-blue-300">
                使用微软 Office Online 预览，如需完整功能请点击"新窗口打开"
              </span>
            </div>
            <iframe
              :src="officeOnlineUrl!"
              class="w-full h-[65vh] border-0 rounded-lg bg-white"
              sandbox="allow-scripts allow-same-origin allow-popups"
            ></iframe>
          </div>
          
          <div v-else-if="previewType === 'pdf'" class="flex flex-col items-center">
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
