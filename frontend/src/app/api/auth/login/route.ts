import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validar dados de entrada
    if (!body.email || !body.password) {
      return NextResponse.json(
        { detail: 'Email e senha são obrigatórios' },
        { status: 400 }
      )
    }

    const backendUrl = `${BACKEND_URL}/api/auth/login`
    
    // Criar AbortController para timeout (30 segundos para dar mais tempo)
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 segundos
    
    let response: Response
    try {
      response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
    } catch (fetchError: any) {
      clearTimeout(timeoutId)
      
      // Erro de rede/conexão ou timeout
      console.error('Erro ao conectar com backend:', fetchError)
      
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          {
            detail: 'Timeout ao conectar com o servidor. Verifique se o backend está rodando.',
            backendUrl
          },
          { status: 504 }
        )
      }
      
      return NextResponse.json(
        {
          detail: 'Erro ao conectar com o servidor. Verifique se o backend está rodando.',
          error: fetchError.message,
          backendUrl
        },
        { status: 503 }
      )
    }

    if (!response.ok) {
      let errorMessage = 'Erro ao fazer login'
      
      try {
        const errorData = await response.text()
        try {
          const errorJson = JSON.parse(errorData)
          errorMessage = errorJson.detail || errorMessage
        } catch {
          errorMessage = errorData || errorMessage
        }
      } catch (parseError) {
        errorMessage = `Erro ${response.status}: ${response.statusText}`
      }

      return NextResponse.json(
        { detail: errorMessage },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error: any) {
    console.error('Erro na API Route POST /api/auth/login:', error)

    return NextResponse.json(
      { 
        detail: 'Erro interno do servidor',
        error: error?.message || String(error)
      },
      { status: 500 }
    )
  }
}
