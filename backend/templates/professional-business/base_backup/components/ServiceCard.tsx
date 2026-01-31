import { LucideIcon } from 'lucide-react'

interface ServiceProps {
    title: string
    description: string
    icon?: LucideIcon
}

export default function ServiceCard({ title, description, icon: Icon }: ServiceProps) {
    return (
        <div className="pt-6">
            <div className="flow-root bg-gray-50 rounded-lg px-6 pb-8">
                <div className="-mt-6">
                    <div>
                        <span className="inline-flex items-center justify-center p-3 bg-primary rounded-md shadow-lg">
                            {Icon ? <Icon className="h-6 w-6 text-white" /> : (
                                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            )}
                        </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">{title}</h3>
                    <p className="mt-5 text-base text-gray-500">
                        {description}
                    </p>
                </div>
            </div>
        </div>
    )
}
