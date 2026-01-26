import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function AboutPreview() {
  return (
    <section className="section-padding">
      <div className="container-custom">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">Sobre Nós</h2>
            <p className="text-lg text-gray-600 mb-4">{{ABOUT_PREVIEW_TEXT}}</p>
            <Link href="/sobre" className="inline-flex items-center text-primary font-semibold hover:underline">
              Conheça mais sobre nós
              <ArrowRight className="ml-2" size={20} />
            </Link>
          </div>
          <div className="bg-gray-200 rounded-lg aspect-video flex items-center justify-center">
            <span className="text-gray-400">Imagem sobre a empresa</span>
          </div>
        </div>
      </div>
    </section>
  )
}
