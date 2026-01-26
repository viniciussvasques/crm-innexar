import { ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface ServiceCardProps {
  service: {
    title: string
    description: string
  }
}

export default function ServiceCard({ service }: ServiceCardProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition-shadow">
      <h3 className="text-2xl font-bold mb-3 text-gray-900">
        {service.title}
      </h3>
      <p className="text-gray-600 mb-4">
        {service.description}
      </p>
      <Link href="/contato" className="text-primary font-semibold hover:underline inline-flex items-center">
        Saiba Mais
        <ArrowRight className="ml-1" size={18} />
      </Link>
    </div>
  )
}
