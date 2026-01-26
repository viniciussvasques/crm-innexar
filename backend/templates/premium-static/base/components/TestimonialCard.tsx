import { Star } from 'lucide-react'

interface TestimonialCardProps {
  name: string
  text: string
  rating: number
}

export default function TestimonialCard({ name, text, rating }: TestimonialCardProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center mb-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            className={i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}
            size={20}
          />
        ))}
      </div>
      <p className="text-gray-600 mb-4 italic">"{text}"</p>
      <p className="font-semibold text-gray-900">— {name}</p>
    </div>
  )
}
