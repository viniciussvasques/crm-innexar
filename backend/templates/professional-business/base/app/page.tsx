import Hero from '@/components/Hero'
import Section from '@/components/Section'
import ServiceCard from '@/components/ServiceCard'
import { CheckCircle } from 'lucide-react'

export default function Home() {
    const services = [
        {{ #SERVICES}}
    ];

return (
    <>
        <Hero />

        {/* Services Preview */}
        <Section id="servicos" light>
            <div className="text-center">
                <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                    Nossos Serviços
                </h2>
                <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
                    Soluções completas e profissionais para suas necessidades.
                </p>
            </div>

            <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                {services.map((service, index) => (
                    <ServiceCard
                        key={index}
                        title={service.title}
                        description={service.description}
                    />
                ))}
            </div>
        </Section>

        {/* About Preview */}
        <Section id="sobre">
            <div className="lg:grid lg:grid-cols-2 lg:gap-8 lg:items-center">
                <div>
                    <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        Sobre a {{ BUSINESS_NAME }}
                    </h2>
                    <p className="mt-3 max-w-3xl text-lg text-gray-500">
                        {{ ABOUT_PREVIEW_TEXT }}
                    </p>
                    <div className="mt-8 space-y-4">
                        <div className="flex items-center">
                            <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                            <span className="text-gray-600">Profissionais Experientes</span>
                        </div>
                        <div className="flex items-center">
                            <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                            <span className="text-gray-600">Atendimento Personalizado</span>
                        </div>
                        <div className="flex items-center">
                            <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                            <span className="text-gray-600">Qualidade Garantida</span>
                        </div>
                    </div>
                </div>
                <div className="mt-8 lg:mt-0 relative">
                    <div className="aspect-w-3 aspect-h-2 rounded-lg overflow-hidden shadow-lg">
                        <img
                            src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                            alt="Equipe trabalhando"
                            className="object-cover"
                        />
                    </div>
                </div>
            </div>
        </Section>
    </>
)
}
