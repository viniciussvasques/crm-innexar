import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

/**
 * Preview endpoint - serves generated site files
 * This is a simple file server that serves the generated site
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params
        const { searchParams } = new URL(request.url)
        const filePath = searchParams.get('path') || 'index.html'

        const authHeader = request.headers.get('authorization')
        if (!authHeader) {
            // For preview, we might want to allow public access
            // But for now, require auth
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 })
        }

        // Get file content from backend
        const response = await fetch(`${BACKEND_URL}/api/projects/${id}/files/content?path=${encodeURIComponent(filePath)}`, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            // If file not found, try index.html
            if (response.status === 404 && filePath !== 'index.html') {
                const indexResponse = await fetch(`${BACKEND_URL}/api/projects/${id}/files/content?path=index.html`, {
                    method: 'GET',
                    headers: {
                        'Authorization': authHeader,
                        'Content-Type': 'application/json',
                    },
                })
                if (indexResponse.ok) {
                    const indexData = await indexResponse.json()
                    return new NextResponse(indexData.content, {
                        headers: { 'Content-Type': 'text/html' },
                    })
                }
            }
            return NextResponse.json(
                { error: 'Arquivo não encontrado' },
                { status: 404 }
            )
        }

        const data = await response.json()
        
        // Determine content type based on file extension
        let contentType = 'text/plain'
        if (filePath.endsWith('.html')) contentType = 'text/html'
        else if (filePath.endsWith('.css')) contentType = 'text/css'
        else if (filePath.endsWith('.js')) contentType = 'application/javascript'
        else if (filePath.endsWith('.json')) contentType = 'application/json'
        else if (filePath.endsWith('.png')) contentType = 'image/png'
        else if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) contentType = 'image/jpeg'
        else if (filePath.endsWith('.svg')) contentType = 'image/svg+xml'

        return new NextResponse(data.content, {
            headers: { 'Content-Type': contentType },
        })

    } catch (error: any) {
        console.error('Erro na API Route GET /api/projects/[id]/preview:', error)
        return NextResponse.json(
            { error: 'Erro interno do servidor' },
            { status: 500 }
        )
    }
}
