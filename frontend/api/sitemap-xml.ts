export default async function handler(_req: any, res: any) {
  try {
    const apiUrl = process.env.VITE_API_URL || ''
    const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')

    if (!baseUrl) {
      res.setHeader('Content-Type', 'application/xml')
      res.status(200).send(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
      )
      return
    }

    const response = await fetch(`${baseUrl}/sitemap.xml`)
    const content = await response.text()

    res.setHeader('Content-Type', 'application/xml')
    res.setHeader('Cache-Control', 'public, max-age=86400')
    res.status(200).send(content)
  } catch {
    res.status(500).send('Error fetching sitemap')
  }
}
