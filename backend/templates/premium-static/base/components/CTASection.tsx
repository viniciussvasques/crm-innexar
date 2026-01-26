import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function CTASection() {
  return (
    <section className="section-padding bg-primary text-white">
      <div className="container-custom text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Pronto para começar?</h2>
        <p className="text-xl mb-8 text-gray-100 max-w-2xl mx-auto">Entre em contato conosco hoje e descubra como podemos ajudar você</p>
        <Link href="/contato" className="bg-white text-primary px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center">
          {{CTA_TEXT}}
          <ArrowRight className="ml-2" size={20} />
        </Link>
      </div>
    </section>
  )
}
