import { Check } from 'lucide-react'

const benefits = [
  'Experiência comprovada no mercado',
  'Equipe altamente qualificada',
  'Atendimento personalizado',
  'Resultados mensuráveis',
  'Suporte contínuo',
  'Preços competitivos'
]

export default function Benefits() {
  return (
    <section className="section-padding bg-gray-50">
      <div className="container-custom">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Benefícios Exclusivos
            </h2>
            <p className="text-xl text-gray-600">
              Tudo que você precisa para alcançar seus objetivos
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-start bg-white p-6 rounded-lg shadow-sm">
                <Check className="text-primary mr-4 mt-1 flex-shrink-0" size={24} />
                <p className="text-lg text-gray-700">{benefit}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
