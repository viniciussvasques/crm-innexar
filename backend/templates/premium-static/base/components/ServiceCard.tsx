import { CheckCircle } from 'lucide-react'

interface ServiceCardProps {
  title: string
  description: string
  icon?: string
}

export default function ServiceCard({ title, description }: ServiceCardProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <CheckCircle className="text-primary" size={32} />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
          <p className="text-gray-600">{description}</p>
        </div>
      </div>
    </div>
  )
}
