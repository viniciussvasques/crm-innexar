import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params
        
        // Reject non-numeric IDs to avoid catching static routes
        if (isNaN(Number(id))) {
            return NextResponse.json(
                { error: 'Invalid order ID' },
                { status: 404 }
            )
        }
        
        const authHeader = request.headers.get('authorization')
        if (!authHeader) {
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
        }

        const response = await fetch(`${BACKEND_URL}/api/site-orders/${id}/build`, {
            method: 'POST',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            const errorData = await response.text()
            return NextResponse.json(
                { error: 'Erro ao iniciar build', details: errorData },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error) {
        console.error('Erro na API Route POST /api/site-orders/[id]/build:', error)
        return NextResponse.json(
            { error: 'Erro interno do servidor' },
            { status: 500 }
        )
    }
}
