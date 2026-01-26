import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = 'http://backend:8000';

export async function POST(request: NextRequest) {
    try {
        const authHeader = request.headers.get('authorization');
        if (!authHeader) {
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 });
        }

        const response = await fetch(`${BACKEND_URL}/api/site-orders/reset-empty-generations`, {
            method: 'POST',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const errorData = await response.text();
            try {
                const errorJson = JSON.parse(errorData);
                return NextResponse.json(
                    { error: errorJson.detail || 'Erro ao resetar gerações vazias', details: errorData },
                    { status: response.status }
                );
            } catch {
                return NextResponse.json(
                    { error: 'Erro ao resetar gerações vazias', details: errorData },
                    { status: response.status }
                );
            }
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Erro na API Route POST /api/site-orders/reset-empty-generations:', error);
        return NextResponse.json(
            { error: 'Erro interno do servidor', details: error.message },
            { status: 500 }
        );
    }
}
