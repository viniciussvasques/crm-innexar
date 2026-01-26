import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function CTASection() {
  return (
    <section className="section-padding bg-gradient-to-r from-primary to-secondary text-white">
      <div className="container-custom">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Pronto para Começar?
          </h2>
          <p className="text-xl mb-8 text-gray-100">
            Entre em contato hoje mesmo e descubra como podemos ajudar você a alcançar seus objetivos
          </p>
          <Link href="/contato" className="bg-white text-primary px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors inline-flex items-center">
            {{CTA_TEXT}}
            <ArrowRight className="ml-2" size={24} />
          </Link>
        </div>
      </div>
    </section>
  )
}
