import { NextRequest, NextResponse } from 'next/server'

// URL interna do backend FastAPI dentro da rede Docker
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(request: NextRequest) {
  try {
    // Obter token do header Authorization
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader) {
      return NextResponse.json(
        { error: 'Token não fornecido' },
        { status: 401 }
      )
    }

    // Obter query params
    const { searchParams } = new URL(request.url)
    const skip = searchParams.get('skip') || '0'
    const limit = searchParams.get('limit') || '100'
    const status = searchParams.get('status') || null

    // Construir URL do backend com query params
    let backendUrl = `${BACKEND_URL}/api/activities/?skip=${skip}&limit=${limit}`
    if (status) {
      backendUrl += `&status=${status}`
    }

    // Fazer requisição interna para o backend FastAPI
    let response: Response
    try {
      response = await fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      })
    } catch (fetchError: any) {
      return NextResponse.json(
        { error: 'Erro ao conectar com o backend' },
        { status: 500 }
      )
    }

    if (!response.ok) {
      const errorData = await response.text().catch(() => 'Erro desconhecido')
      return NextResponse.json(
        { error: 'Erro ao buscar atividades', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error: any) {
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader) {
      return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
    }

    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/activities/`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: 'Erro ao criar atividade', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: 201 })

  } catch (error) {
    console.error('Erro na API Route POST /api/activities:', error)
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    )
  }
}

