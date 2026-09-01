import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { compression } from 'vite-plugin-compression2'

export default defineConfig({
  plugins: [
    vue(),
    compression({
      algorithms: ['gzip'],
      threshold: 1024,
      deleteOriginalAssets: false
    }),
    compression({
      algorithms: ['brotliCompress'],
      threshold: 1024,
      deleteOriginalAssets: false
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/robots.txt': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/sitemap.xml': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    target: 'esnext',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
        passes: 2
      },
      format: {
        comments: false
      }
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) {
              return 'vue-vendor'
            }
            if (id.includes('echarts') || id.includes('zrender')) {
              return 'echarts'
            }
            if (id.includes('mermaid')) {
              return 'mermaid'
            }
            if (id.includes('marked') || id.includes('highlight.js') || id.includes('dompurify')) {
              return 'markdown'
            }
            if (id.includes('pdfjs')) {
              return 'pdfjs'
            }
            if (id.includes('xlsx') || id.includes('jszip')) {
              return 'xlsx'
            }
            if (id.includes('mammoth')) {
              return 'mammoth'
            }
            if (id.includes('axios')) {
              return 'axios'
            }
            if (id.includes('cropperjs')) {
              return 'cropperjs'
            }
            if (id.includes('particles.js')) {
              return 'particles'
            }
            if (id.includes('@vueuse')) {
              return 'vueuse'
            }
            return 'vendor'
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|avif|ico)$/i.test(assetInfo.name || '')) {
            return 'assets/images/[name]-[hash].[ext]'
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return 'assets/fonts/[name]-[hash].[ext]'
          }
          if (ext === 'css') {
            return 'assets/css/[name]-[hash].[ext]'
          }
          return 'assets/[ext]/[name]-[hash].[ext]'
        }
      }
    },
    // mermaid 库体积约 2.2MB（已单独分包且懒加载），无法再拆分，调高阈值消除误报警告
    chunkSizeWarningLimit: 2500,
    cssCodeSplit: true,
    sourcemap: false,
    reportCompressedSize: true,
    cssMinify: true
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'marked', 'dompurify', 'highlight.js'],
    exclude: ['@iconify/json']
  },
  css: {
    devSourcemap: false
  }
})
