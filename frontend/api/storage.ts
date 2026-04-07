export const config = {
  runtime: 'edge',
}

const SUPABASE_URL = process.env.SUPABASE_URL
const SUPABASE_BUCKET = process.env.SUPABASE_BUCKET || 'blog-files'

export default async function handler(request: Request) {
  if (!SUPABASE_URL) {
    return new Response(JSON.stringify({ error: 'SUPABASE_URL not configured' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  const url = new URL(request.url)
  const path = url.searchParams.get('path')
  
  if (!path) {
    return new Response(JSON.stringify({ error: 'Path parameter required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  const supabaseUrl = `${SUPABASE_URL}/storage/v1/object/public/${SUPABASE_BUCKET}/${path}`

  try {
    const response = await fetch(supabaseUrl, {
      method: request.method,
      headers: {
        'Accept': request.headers.get('Accept') || '*/*',
        'Accept-Encoding': 'identity',
      },
    })

    const headers = new Headers(response.headers)
    headers.set('Access-Control-Allow-Origin', '*')
    headers.set('Cache-Control', 'public, max-age=86400')
    headers.delete('Content-Encoding')

    return new Response(response.body, {
      status: response.status,
      headers
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to fetch from Supabase' }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}
