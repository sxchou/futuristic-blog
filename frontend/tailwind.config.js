/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#00d4ff',
          50: '#e6fbff',
          100: '#ccf7ff',
          200: '#99efff',
          300: '#66e7ff',
          400: '#33dfff',
          500: '#00d4ff',
          600: '#00aacc',
          700: '#007f99',
          800: '#005566',
          900: '#002a33',
        },
        accent: {
          DEFAULT: '#7c3aed',
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#7c3aed',
          600: '#6d28d9',
          700: '#5b21b6',
          800: '#4c1d95',
          900: '#3b0764',
        },
        dark: {
          DEFAULT: '#000000',
          100: '#0a0a0a',
          200: '#141414',
          300: '#1f1f1f',
          400: '#2a2a2a',
          500: '#3a3a3a',
        },
        cyber: {
          cyan: '#00d4ff',
          violet: '#7c3aed',
          pink: '#ec4899',
          green: '#10b981',
          yellow: '#f59e0b',
        }
      },
      fontFamily: {
        sans: ['Geist', 'Geist Latin', 'Inter', 'system-ui', '-apple-system', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['JetBrains Mono', 'Geist Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'xs': ['var(--font-size-xs)', { lineHeight: '1rem' }],
        'sm': ['var(--font-size-sm)', { lineHeight: '1.25rem' }],
        'base': ['var(--font-size-base)', { lineHeight: '1.5rem' }],
        'lg': ['var(--font-size-lg)', { lineHeight: '1.75rem' }],
        'xl': ['var(--font-size-xl)', { lineHeight: '1.75rem' }],
        '2xl': ['var(--font-size-2xl)', { lineHeight: '2rem' }],
        '3xl': ['var(--font-size-3xl)', { lineHeight: '2.25rem' }],
        '4xl': ['var(--font-size-4xl)', { lineHeight: '2.5rem' }],
        '5xl': ['var(--font-size-5xl)', { lineHeight: '1' }],
      },
      /* Vercel/Linear 式多层柔和阴影 —— 精细的深度层次 */
      boxShadow: {
        'hairline': '0 0 0 1px rgba(0, 0, 0, 0.04)',
        'xs': '0 1px 2px rgba(0, 0, 0, 0.04)',
        'sm': '0 1px 2px rgba(0, 0, 0, 0.04), 0 2px 4px rgba(0, 0, 0, 0.03)',
        'md': '0 1px 2px rgba(0, 0, 0, 0.04), 0 4px 8px -2px rgba(0, 0, 0, 0.06), 0 12px 20px -6px rgba(0, 0, 0, 0.05)',
        'lg': '0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 16px -4px rgba(0, 0, 0, 0.08), 0 20px 32px -8px rgba(0, 0, 0, 0.06)',
        'xl': '0 1px 2px rgba(0, 0, 0, 0.04), 0 12px 24px -6px rgba(0, 0, 0, 0.10), 0 32px 48px -12px rgba(0, 0, 0, 0.10)',
        'glow': '0 0 0 1px rgba(0, 212, 255, 0.15), 0 4px 24px -4px rgba(0, 212, 255, 0.25)',
        'glow-lg': '0 0 0 1px rgba(0, 212, 255, 0.2), 0 8px 40px -4px rgba(0, 212, 255, 0.35)',
      },
      /* 现代缓动曲线 */
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'out-back': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'spring': 'cubic-bezier(0.34, 1.3, 0.64, 1)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 8s ease infinite',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slideDown 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'fade-in': 'fadeIn 0.5s ease-out',
        'reveal-up': 'revealUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both',
        'aurora': 'aurora 14s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #00d4ff, 0 0 10px #00d4ff, 0 0 15px #00d4ff' },
          '100%': { boxShadow: '0 0 10px #00d4ff, 0 0 20px #00d4ff, 0 0 30px #00d4ff' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        revealUp: {
          '0%': { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        aurora: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: '0.7' },
          '50%': { transform: 'translate(4%, -3%) scale(1.08)', opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'cyber-grid': 'linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px)',
        'dot-grid': 'radial-gradient(circle, rgba(0, 0, 0, 0.08) 1px, transparent 1px)',
      },
      backgroundSize: {
        'dot-grid': '24px 24px',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
