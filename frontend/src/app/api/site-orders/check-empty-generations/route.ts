import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = 'http://backend:8000';

export async function GET(request: NextRequest) {
    console.log('[check-empty-generations] Route handler called');
    try {
        // Try multiple header names
        const authHeader = request.headers.get('authorization') || 
                          request.headers.get('Authorization') ||
                          request.headers.get('AUTHORIZATION');
        
        console.log('[check-empty-generations] Auth header present:', !!authHeader);
        console.log('[check-empty-generations] All headers:', Object.fromEntries(request.headers.entries()));
        
        if (!authHeader) {
            console.log('[check-empty-generations] No auth header found');
            return NextResponse.json({ error: 'Token não fornecido' }, { status: 401 });
        }

        console.log('[check-empty-generations] Calling backend:', `${BACKEND_URL}/api/site-orders/check-empty-generations`);
        const response = await fetch(`${BACKEND_URL}/api/site-orders/check-empty-generations`, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        });

        console.log('[check-empty-generations] Backend response status:', response.status);
        console.log('[check-empty-generations] Backend response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorData = await response.text();
            console.error('[check-empty-generations] Backend error:', response.status, errorData);
            try {
                const errorJson = JSON.parse(errorData);
                // Extract error message from various formats
                let errorMessage = errorJson.detail || errorJson.error || 'Erro ao verificar gerações vazias';
                
                // Handle validation errors (422)
                if (response.status === 422) {
                    if (errorJson.errors && Array.isArray(errorJson.errors) && errorJson.errors.length > 0) {
                        const firstError = errorJson.errors[0];
                        errorMessage = firstError.msg || firstError.message || errorMessage;
                    }
                    // If it's an auth-related 422, provide helpful message
                    if (errorMessage.includes('authorization') || errorMessage.includes('credentials') || errorMessage.includes('Token')) {
                        errorMessage = 'Token de autenticação inválido ou ausente. Faça login novamente.';
                    }
                }
                
                return NextResponse.json(
                    { error: errorMessage, details: errorData },
                    { status: response.status }
                );
            } catch {
                return NextResponse.json(
                    { error: 'Erro ao verificar gerações vazias', details: errorData },
                    { status: response.status }
                );
            }
        }

        const data = await response.json();
        console.log('[check-empty-generations] Success, returning data');
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('[check-empty-generations] Exception:', error);
        return NextResponse.json(
            { error: 'Erro interno do servidor', details: error.message },
            { status: 500 }
        );
    }
}
