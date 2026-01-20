import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(request: NextRequest) {
  try {
    // Verificar saúde do backend
    const backendHealth = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    }).catch(() => null)

    return NextResponse.json({
      status: 'ok',
      frontend: 'running',
      backend: backendHealth?.ok ? 'running' : 'unavailable',
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      frontend: 'running',
      backend: 'unavailable',
      error: error instanceof Error ? error.message : String(error),
      timestamp: new Date().toISOString()
    }, { status: 503 })
  }
}
