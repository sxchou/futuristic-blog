<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationId: number | null = null

onMounted(() => {
  if (!canvasRef.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const particles: Array<{
    x: number
    y: number
    vx: number
    vy: number
    radius: number
    color: string
  }> = []

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }

  const createParticles = () => {
    const count = Math.floor((canvas.width * canvas.height) / 15000)
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 2 + 1,
        color: Math.random() > 0.5 ? '#00d4ff' : '#7c3aed'
      })
    }
  }

  const drawParticles = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    particles.forEach((p, i) => {
      p.x += p.vx
      p.y += p.vy

      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fillStyle = p.color
      ctx.globalAlpha = 0.6
      ctx.fill()

      particles.forEach((p2, j) => {
        if (i === j) return
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = p.color
          ctx.globalAlpha = 0.1 * (1 - dist / 150)
          ctx.stroke()
        }
      })
    })

    animationId = requestAnimationFrame(drawParticles)
  }

  resize()
  createParticles()
  drawParticles()

  window.addEventListener('resize', () => {
    resize()
    particles.length = 0
    createParticles()
  })
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<template>
  <div class="absolute inset-0 overflow-hidden">
    <canvas ref="canvasRef" class="absolute inset-0" />
    <div class="absolute inset-0 bg-gradient-to-b from-transparent via-white/30 dark:via-dark/50 to-white dark:to-dark" />
  </div>
</template>
