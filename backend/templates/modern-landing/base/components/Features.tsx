import { Zap, Shield, Heart } from 'lucide-react'

const features = [
  {
    icon: Zap,
    title: 'Rápido e Eficiente',
    description: 'Soluções que entregam resultados em tempo recorde'
  },
  {
    icon: Shield,
    title: 'Confiável e Seguro',
    description: 'Seus dados e projetos estão sempre protegidos'
  },
  {
    icon: Heart,
    title: 'Atendimento Dedicado',
    description: 'Equipe comprometida com seu sucesso'
  }
]

export default function Features() {
  return (
    <section className="section-padding bg-white">
      <div className="container-custom">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Por Que Escolher a {{BUSINESS_NAME}}?
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Oferecemos o melhor em qualidade, confiança e resultados
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div key={index} className="text-center p-6 rounded-lg hover:shadow-lg transition-shadow">
                <div className="bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Icon className="text-primary" size={40} />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
