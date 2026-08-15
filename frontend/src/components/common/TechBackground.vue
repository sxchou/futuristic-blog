<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useThemeStore } from '@/stores'

interface Props {
  particleCount?: number
  speed?: number
  linkDistance?: number
  mouseInteraction?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  particleCount: 0,
  speed: 0.5,
  linkDistance: 120,
  mouseInteraction: true
})

const themeStore = useThemeStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)

let ctx: CanvasRenderingContext2D | null = null
let animationId: number | null = null
let particles: Particle[] = []
let mouseX = -1000
let mouseY = -1000
let dpr = 1
let width = 0
let height = 0

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  colorIdx: number
}

interface ColorScheme {
  particles: string[]
  linkRGB: string
  linkAlpha: number
}

const getColors = (): ColorScheme => {
  if (themeStore.isDark) {
    return {
      particles: ['#00d4ff', '#7c3aed'],
      linkRGB: '0, 212, 255',
      linkAlpha: 0.13
    }
  }
  return {
    particles: ['#0284c7', '#6d28d9'],
    linkRGB: '2, 132, 199',
    linkAlpha: 0.08
  }
}

let colors = getColors()

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

const calcParticleCount = () => {
  if (props.particleCount > 0) return props.particleCount
  const isMobile = width < 768
  const base = isMobile ? 25 : 50
  const extra = Math.floor((width * height) / 30000)
  return Math.min(isMobile ? 40 : 80, Math.max(15, base + extra))
}

const initParticles = () => {
  const count = calcParticleCount()
  particles = []
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * props.speed,
      vy: (Math.random() - 0.5) * props.speed,
      radius: Math.random() * 1.5 + 0.5,
      colorIdx: Math.random() > 0.5 ? 0 : 1
    })
  }
}

const resize = () => {
  if (!canvasRef.value) return
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = window.innerWidth
  height = window.innerHeight
  canvasRef.value.width = width * dpr
  canvasRef.value.height = height * dpr
  canvasRef.value.style.width = width + 'px'
  canvasRef.value.style.height = height + 'px'
  ctx = canvasRef.value.getContext('2d')
  if (ctx) ctx.scale(dpr, dpr)
  initParticles()
}

const draw = () => {
  if (!ctx) return

  ctx.clearRect(0, 0, width, height)

  // 更新粒子位置
  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 0 || p.x > width) p.vx *= -1
    if (p.y < 0 || p.y > height) p.vy *= -1
  }

  // 绘制连线
  const linkDist = props.linkDistance
  const linkDistSq = linkDist * linkDist
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const distSq = dx * dx + dy * dy
      if (distSq < linkDistSq) {
        const dist = Math.sqrt(distSq)
        const alpha = (1 - dist / linkDist) * colors.linkAlpha
        ctx.strokeStyle = `rgba(${colors.linkRGB}, ${alpha})`
        ctx.lineWidth = 0.5
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.stroke()
      }
    }
  }

  // 鼠标连线
  if (props.mouseInteraction && mouseX > 0) {
    const mouseDist = linkDist * 1.5
    const mouseDistSq = mouseDist * mouseDist
    for (const p of particles) {
      const dx = p.x - mouseX
      const dy = p.y - mouseY
      const distSq = dx * dx + dy * dy
      if (distSq < mouseDistSq) {
        const dist = Math.sqrt(distSq)
        const alpha = (1 - dist / mouseDist) * colors.linkAlpha * 1.5
        ctx.strokeStyle = `rgba(${colors.linkRGB}, ${alpha})`
        ctx.lineWidth = 0.8
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(mouseX, mouseY)
        ctx.stroke()
      }
    }
  }

  // 绘制粒子
  for (const p of particles) {
    ctx.fillStyle = colors.particles[p.colorIdx]
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fill()
  }

  animationId = requestAnimationFrame(draw)
}

const onMouseMove = (e: MouseEvent) => {
  mouseX = e.clientX
  mouseY = e.clientY
}

const onMouseLeave = () => {
  mouseX = -1000
  mouseY = -1000
}

const onVisibilityChange = () => {
  if (document.hidden) {
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
  } else if (!prefersReducedMotion()) {
    if (!animationId) draw()
  }
}

watch(() => themeStore.isDark, () => {
  colors = getColors()
})

onMounted(() => {
  if (prefersReducedMotion()) return
  resize()
  window.addEventListener('resize', resize)
  if (props.mouseInteraction) {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)
  }
  document.addEventListener('visibilitychange', onVisibilityChange)
  draw()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resize)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseleave', onMouseLeave)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div
    class="tech-bg"
    :class="themeStore.isDark ? 'tech-bg-dark' : 'tech-bg-light'"
  >
    <canvas
      ref="canvasRef"
      class="tech-canvas"
    />
  </div>
</template>

<style scoped>
.tech-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
  transition: background 0.4s ease;
}

.tech-bg-dark {
  background:
    radial-gradient(52% 38% at 18% -4%, rgba(0, 170, 204, 0.10) 0%, transparent 100%),
    radial-gradient(40% 32% at 82% 8%, rgba(124, 58, 237, 0.09) 0%, transparent 100%),
    radial-gradient(ellipse at 50% 120%, rgba(0, 212, 255, 0.05) 0%, transparent 60%),
    linear-gradient(180deg, #0b0f14 0%, #0a0a0a 45%, #000000 100%);
}

.tech-bg-light {
  background:
    radial-gradient(52% 38% at 18% -4%, rgba(0, 170, 204, 0.09) 0%, transparent 100%),
    radial-gradient(40% 32% at 82% 8%, rgba(109, 40, 217, 0.06) 0%, transparent 100%),
    radial-gradient(ellipse at 50% 120%, rgba(0, 212, 255, 0.04) 0%, transparent 60%),
    linear-gradient(180deg, #f4fafd 0%, #f2f7fb 45%, #f8fafc 100%);
}

.tech-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
