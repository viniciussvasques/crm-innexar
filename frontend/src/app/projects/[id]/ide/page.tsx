'use client'

import React from 'react'
import VisualEditor from '@/components/VisualEditor'
import { useParams } from 'next/navigation'

export default function ProjectIDEPage() {
    const params = useParams()
    // Type coercion for ID, assuming generic route params
    const projectId = typeof params.id === 'string' ? parseInt(params.id) : 0

    if (!projectId) {
        return <div className="p-10 text-center text-white">Invalid Project ID</div>
    }

    return (
        <div className="h-full w-full">
            {/* Header could go here if not integrated in layout */}
            <VisualEditor projectId={projectId} />
        </div>
    )
}
