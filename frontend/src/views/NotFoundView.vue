<script setup lang="ts">
import { ref, onMounted } from 'vue'

const glitchText = ref('404')
const showCursor = ref(true)

onMounted(() => {
  setInterval(() => {
    showCursor.value = !showCursor.value
  }, 500)
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center pb-20">
    <div class="container mx-auto px-4">
      <div class="max-w-2xl mx-auto text-center">
        <div class="mb-8">
          <h1 class="text-8xl md:text-9xl font-bold mb-4 relative">
            <span class="gradient-text glitch" data-text="404">{{ glitchText }}</span>
          </h1>
          <div class="w-24 h-1 bg-gradient-to-r from-primary to-accent mx-auto mb-8" />
        </div>

        <h2 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4">
          你似乎进入了代码的无人区
        </h2>
        
        <p class="text-gray-500 dark:text-gray-400 text-lg mb-8">
          这个页面可能已经被移动、删除，或者从未存在过。<br>
          就像代码中的 Bug 一样，有时候事情就是这样发生的。
        </p>

        <div class="glass-card p-6 mb-8 text-left">
          <div class="flex items-center gap-2 mb-4">
            <div class="w-3 h-3 rounded-full bg-red-500" />
            <div class="w-3 h-3 rounded-full bg-yellow-500" />
            <div class="w-3 h-3 rounded-full bg-green-500" />
            <span class="text-gray-500 text-sm ml-2">terminal</span>
          </div>
          <pre class="text-sm font-mono"><code><span class="text-primary">$</span> navigate --to /page
<span class="text-red-400">Error:</span> PageNotFoundException: The requested page could not be found
<span class="text-gray-500">  at Router.resolve (/app/router/index.ts:42:15)</span>
<span class="text-gray-500">  at async Server.handleRequest (/app/server.ts:128:9)</span>

<span class="text-primary">$</span> <span class="text-accent">suggested_actions</span><span class="text-white">:</span>
<span class="text-cyber-green">  →</span> Check the URL for typos
<span class="text-cyber-green">  →</span> Return to homepage
<span class="text-cyber-green">  →</span> Use the navigation menu
<span class="text-primary">$</span> <span :class="{ 'opacity-0': !showCursor }">_</span></code></pre>
        </div>

        <div class="flex flex-wrap justify-center gap-4">
          <router-link to="/" class="btn-primary">
            <span class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              返回首页
            </span>
          </router-link>
          <button @click="$router.back()" class="btn-secondary">
            <span class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              返回上页
            </span>
          </button>
        </div>

        <div class="mt-12 flex justify-center gap-8 text-gray-500">
          <router-link to="/categories" class="hover:text-primary transition-colors">浏览分类</router-link>
          <router-link to="/tags" class="hover:text-primary transition-colors">查看标签</router-link>
          <router-link to="/about" class="hover:text-primary transition-colors">关于我</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.glitch {
  position: relative;
  animation: glitch 1s infinite;
}

.glitch::before,
.glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.glitch::before {
  animation: glitch-1 0.3s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
  transform: translate(-2px, -2px);
  opacity: 0.8;
}

.glitch::after {
  animation: glitch-2 0.3s infinite;
  clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
  transform: translate(2px, 2px);
  opacity: 0.8;
}

@keyframes glitch {
  0%, 100% {
    text-shadow: -2px 0 #00d4ff, 2px 0 #7c3aed;
  }
  50% {
    text-shadow: 2px 0 #00d4ff, -2px 0 #7c3aed;
  }
}

@keyframes glitch-1 {
  0%, 100% {
    transform: translate(-2px, -2px);
  }
  50% {
    transform: translate(2px, 2px);
  }
}

@keyframes glitch-2 {
  0%, 100% {
    transform: translate(2px, 2px);
  }
  50% {
    transform: translate(-2px, -2px);
  }
}
</style>
