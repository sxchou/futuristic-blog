export default async function handler(req: any, res: any) {
  try {
    const apiUrl = process.env.VITE_API_URL || ''
    const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')

    if (!baseUrl) {
      res.setHeader('Content-Type', 'text/plain')
      res.status(200).send('User-agent: *\nAllow: /')
      return
    }

    const response = await fetch(`${baseUrl}/robots.txt`)
    const content = await response.text()

    res.setHeader('Content-Type', 'text/plain')
    res.setHeader('Cache-Control', 'public, max-age=86400')
    res.status(200).send(content)
  } catch {
    res.status(500).send('Error fetching robots.txt')
  }
}
