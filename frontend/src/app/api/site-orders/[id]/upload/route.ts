import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: orderId } = await params
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader) {
      return NextResponse.json(
        { error: 'Token não fornecido' },
        { status: 401 }
      )
    }
    const formData = await request.formData()
    const backendUrl = `${BACKEND_URL}/api/site-orders/${orderId}/upload`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        // Não definir Content-Type, deixar o fetch definir com boundary
      },
      body: formData,
      cache: 'no-store',
    })

    if (!response.ok) {
      const errorData = await response.text().catch(() => 'Erro desconhecido')
      return NextResponse.json(
        { error: 'Erro ao fazer upload', details: errorData },
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
