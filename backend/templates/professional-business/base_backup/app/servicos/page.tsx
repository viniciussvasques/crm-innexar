import Section from '@/components/Section'
import ServiceCard from '@/components/ServiceCard'

export default function Services() {
    return (
        <>
            <div className="bg-gray-900 py-20 text-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl font-extrabold sm:text-5xl lg:text-6xl">Nossos Serviços</h1>
                    <p className="mt-4 text-xl text-gray-400 max-w-2xl mx-auto">
                        O que podemos fazer por você hoje.
                    </p>
                </div>
            </div>

            <Section>
                <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-3">
                    {{ #SERVICES}}
                    <div className="flex flex-col rounded-lg shadow-lg overflow-hidden bg-white border border-gray-100">
                        <div className="flex-1 p-6 flex flex-col justify-between">
                            <div className="flex-1">
                                <h3 className="text-xl font-semibold text-gray-900">
                                    {title}
                                </h3>
                                <p className="mt-3 text-base text-gray-500">
                                    {description}
                                </p>
                            </div>
                            <div className="mt-6">
                                <a href="/contato" className="text-base font-semibold text-primary hover:text-primary-dark">
                                    Solicitar este serviço <span aria-hidden="true">&rarr;</span>
                                </a>
                            </div>
                        </div>
                    </div>
                    {{/ SERVICES}}
                </div>
            </Section>
        </>
    )
}
