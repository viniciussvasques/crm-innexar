import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params
        const { searchParams } = new URL(request.url)
        const path = searchParams.get('path')

        const authHeader = request.headers.get('authorization')
        if (!authHeader) {
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
        }

        // Build URL
        let url = `${BACKEND_URL}/api/projects/${id}/files`
        if (path) {
            url += `/content?path=${encodeURIComponent(path)}`
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            const errorData = await response.text()
            return NextResponse.json(
                { error: 'Erro ao buscar arquivos', details: errorData },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error: any) {
        console.error('Erro na API Route GET /api/projects/[id]/files:', error)
        return NextResponse.json(
            { error: 'Erro interno do servidor' },
            { status: 500 }
        )
    }
}

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params
        const body = await request.json()

        const authHeader = request.headers.get('authorization')
        if (!authHeader) {
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
        }

        const response = await fetch(`${BACKEND_URL}/api/projects/${id}/files/content`, {
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
                { error: 'Erro ao salvar arquivo', details: errorData },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error: any) {
        console.error('Erro na API Route POST /api/projects/[id]/files:', error)
        return NextResponse.json(
            { error: 'Erro interno do servidor' },
            { status: 500 }
        )
    }
}
