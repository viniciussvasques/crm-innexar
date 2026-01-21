import { NextRequest, NextResponse } from 'next/server'

// Backend URL
const BACKEND_URL = process.env.BACKEND_URL || 'http://crm-backend:8000'

export async function GET(request: NextRequest) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/system-config/public`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            const error = await response.text()
            return NextResponse.json(
                { error: 'Failed to fetch public config' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Error fetching public config:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}
