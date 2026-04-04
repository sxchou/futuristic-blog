import type { Directive, DirectiveBinding } from 'vue'

interface LazyLoadElement extends HTMLElement {
  _lazyLoadObserver?: IntersectionObserver
  _lazyLoadSrc?: string
  _lazyLoadSrcset?: string
}

const defaultPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxIiBoZWlnaHQ9IjEiPjwvc3ZnPg=='

const loadImage = (el: LazyLoadElement) => {
  const src = el._lazyLoadSrc
  const srcset = el._lazyLoadSrcset
  
  if (!src) return
  
  const img = new Image()
  
  img.onload = () => {
    if (el.tagName === 'IMG') {
      const imgEl = el as HTMLImageElement
      if (srcset) {
        imgEl.setAttribute('srcset', srcset)
      }
      imgEl.src = src
    } else {
      el.style.backgroundImage = `url(${src})`
    }
    el.classList.add('lazy-loaded')
    el.classList.remove('lazy-loading')
  }
  
  img.onerror = () => {
    el.classList.remove('lazy-loading')
    el.classList.add('lazy-error')
  }
  
  img.src = src
}

const createObserver = (): IntersectionObserver => {
  return new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target as LazyLoadElement
          loadImage(el)
          el._lazyLoadObserver?.unobserve(el)
        }
      })
    },
    {
      rootMargin: '50px 0px',
      threshold: 0.01
    }
  )
}

let observer: IntersectionObserver | null = null

const lazyLoadDirective: Directive<LazyLoadElement> = {
  mounted(el: LazyLoadElement, binding: DirectiveBinding<string>) {
    if (!observer) {
      observer = createObserver()
    }
    
    const value = binding.value
    if (!value) return
    
    if (el.tagName === 'IMG') {
      el._lazyLoadSrc = value
      el._lazyLoadSrcset = el.getAttribute('data-srcset') || undefined
      ;(el as HTMLImageElement).src = defaultPlaceholder
    } else {
      el._lazyLoadSrc = value
      el.style.backgroundImage = `url(${defaultPlaceholder})`
    }
    
    el.classList.add('lazy-loading')
    el._lazyLoadObserver = observer
    observer.observe(el)
  },
  
  updated(el: LazyLoadElement, binding: DirectiveBinding<string>) {
    if (binding.value !== binding.oldValue) {
      el._lazyLoadSrc = binding.value
      
      if (el.tagName === 'IMG') {
        ;(el as HTMLImageElement).src = defaultPlaceholder
      }
      
      el.classList.remove('lazy-loaded', 'lazy-error')
      el.classList.add('lazy-loading')
      
      if (!observer) {
        observer = createObserver()
      }
      el._lazyLoadObserver = observer
      observer.observe(el)
    }
  },
  
  unmounted(el: LazyLoadElement) {
    if (el._lazyLoadObserver) {
      el._lazyLoadObserver.unobserve(el)
    }
  }
}

export const setupLazyLoad = (app: ReturnType<typeof import('vue').createApp>) => {
  app.directive('lazy', lazyLoadDirective)
}

export default lazyLoadDirective
