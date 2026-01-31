import Section from '@/components/Section'

export default function About() {
    return (
        <>
            <div className="bg-primary py-20 text-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl font-extrabold sm:text-5xl lg:text-6xl">Sobre Nós</h1>
                    <p className="mt-4 text-xl text-primary-light max-w-2xl mx-auto">
                        Conheça nossa história e nossa missão.
                    </p>
                </div>
            </div>

            <Section>
                <div className="prose prose-lg mx-auto text-gray-500">
                    <p className="lead text-2xl text-gray-700 font-semibold mb-8">
                        {{ ABOUT_PREVIEW_TEXT }}
                    </p>
                    <div className="space-y-6">
                        {{ ABOUT_FULL_TEXT }}
                    </div>
                </div>
            </Section>

            <Section light>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
                    <div className="p-6 bg-white rounded-lg shadow-md">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Missão</h3>
                        <p className="text-gray-600">Oferecer soluções de excelência que superem as expectativas dos nossos clientes.</p>
                    </div>
                    <div className="p-6 bg-white rounded-lg shadow-md">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Visão</h3>
                        <p className="text-gray-600">Ser referência em qualidade e inovação no nosso setor de atuação.</p>
                    </div>
                    <div className="p-6 bg-white rounded-lg shadow-md">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Valores</h3>
                        <p className="text-gray-600">Ética, comprometimento, transparência e foco no resultado.</p>
                    </div>
                </div>
            </Section>
        </>
    )
}
