import { SiteOrder, Step } from './types'

export const getProcessSteps = (order: SiteOrder): Step[] => {
    const deliverables = order.deliverables || []

    const steps: { id: string, title: string, description: string, requiredType: string, status: 'pending' }[] = [
        {
            id: 'strategy',
            title: 'Phase 1: Strategic Briefing',
            description: 'AI Consultant analyzes business model & target audience.',
            requiredType: 'briefing',
            status: 'pending'
        },
        {
            id: 'architecture',
            title: 'Phase 2: Information Architecture',
            description: 'Designing Sitemap & UX Journeys.',
            requiredType: 'sitemap',
            status: 'pending'
        },
        {
            id: 'code',
            title: 'Phase 3: Development',
            description: 'Generating Next.js Codebase & Tailwind Styles.',
            requiredType: 'code',
            status: 'pending'
        }
    ]

    return steps.map(step => {
        const deliverable = deliverables.find(d => d.type === step.requiredType)
        let status: 'pending' | 'active' | 'completed' = 'pending'
        let date = undefined

        if (deliverable) {
            if (deliverable.status === 'ready' || deliverable.status === 'approved') status = 'completed'
            else if (deliverable.status === 'generating') status = 'active'
            date = new Date(deliverable.created_at).toLocaleDateString()
        } else {
            // Heuristic for active state
            if (status === 'pending' && step.id === 'strategy' && (order.status === 'generating' || order.status === 'building')) {
                status = 'active'
            }
        }

        return {
            id: step.id,
            title: step.title,
            description: step.description,
            status,
            date
        }
    })
}
