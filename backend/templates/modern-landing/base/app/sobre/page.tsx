import { Building2, Users, Award } from 'lucide-react'

export default function SobrePage() {
  return (
    <div className="section-padding">
      <div className="container-custom">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold text-center mb-4">
            Sobre a {{BUSINESS_NAME}}
          </h1>
          <p className="text-xl text-gray-600 text-center mb-12">
            {{BUSINESS_TAGLINE}}
          </p>
          
          <div className="prose prose-lg max-w-none mb-12">
            <p className="text-lg text-gray-700 leading-relaxed">
              {{ABOUT_FULL_TEXT}}
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center">
              <div className="bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Building2 className="text-primary" size={32} />
              </div>
              <h3 className="font-bold text-xl mb-2">Experiência</h3>
              <p className="text-gray-600">
                {{YEARS_IN_BUSINESS}} anos de experiência no mercado
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="text-primary" size={32} />
              </div>
              <h3 className="font-bold text-xl mb-2">Clientes Satisfeitos</h3>
              <p className="text-gray-600">
                Centenas de clientes atendidos com excelência
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Award className="text-primary" size={32} />
              </div>
              <h3 className="font-bold text-xl mb-2">Qualidade</h3>
              <p className="text-gray-600">
                Compromisso com a excelência em cada projeto
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
