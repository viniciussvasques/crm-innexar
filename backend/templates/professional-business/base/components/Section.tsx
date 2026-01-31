import { ReactNode } from 'react'

interface SectionProps {
    children: ReactNode
    className?: string
    id?: string
    light?: boolean
}

export default function Section({ children, className = '', id = '', light = false }: SectionProps) {
    return (
        <section
            id={id}
            className={`py-12 sm:py-16 lg:py-20 ${light ? 'bg-gray-50' : 'bg-white'} ${className}`}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {children}
            </div>
        </section>
    )
}
