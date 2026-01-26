import TestimonialCard from '@/components/TestimonialCard'

export const metadata = {
  title: 'Depoimentos - {{BUSINESS_NAME}}',
  description: 'Veja o que nossos clientes dizem sobre nós',
}

export default function DepoimentosPage() {
  const testimonials = [
    {{#TESTIMONIALS}}
    {
      name: '{{TESTIMONIAL_NAME}}',
      text: '{{TESTIMONIAL_TEXT}}',
      rating: {{TESTIMONIAL_RATING}},
    },
    {{/TESTIMONIALS}}
  ]

  return (
    <div className="section-padding">
      <div className="container-custom">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Depoimentos</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Veja o que nossos clientes têm a dizer sobre nossos serviços
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} {...testimonial} />
          ))}
        </div>
      </div>
    </div>
  )
}
