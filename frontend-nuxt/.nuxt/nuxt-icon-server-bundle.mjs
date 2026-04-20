import { createRequire } from 'module'
const require = createRequire(import.meta.url)
export const collections = {
  'heroicons': () => require('@iconify-json/heroicons/icons.json'),
}