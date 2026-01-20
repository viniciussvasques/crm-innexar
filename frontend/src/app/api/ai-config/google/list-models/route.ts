import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader) {
      return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const apiKey = searchParams.get('api_key')

    if (!apiKey) {
      return NextResponse.json({ error: 'API key é necessária' }, { status: 400 })
    }

    const response = await fetch(`${BACKEND_URL}/api/ai-config/google/list-models?api_key=${encodeURIComponent(apiKey)}`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: 'Erro ao listar modelos', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('Erro na API Route GET /api/ai-config/google/list-models:', error)
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    )
  }
}

