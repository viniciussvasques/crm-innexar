'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Check } from 'lucide-react'
import Link from 'next/link'

export default function Hero() {
  return (
    <section className="relative bg-gradient-to-br from-primary via-primary-dark to-secondary text-white overflow-hidden">
      <div className="absolute inset-0 bg-black/10"></div>
      <div className="container-custom section-padding relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              {{HERO_TITLE}}
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-gray-100 max-w-2xl mx-auto">
              {{HERO_SUBTITLE}}
            </p>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          >
            <Link href="/contato" className="bg-white text-primary px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors inline-flex items-center justify-center">
              {{CTA_TEXT}}
              <ArrowRight className="ml-2" size={24} />
            </Link>
            <Link href="/sobre" className="border-2 border-white text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/10 transition-colors inline-flex items-center justify-center">
              Saiba Mais
            </Link>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap justify-center gap-6 text-sm md:text-base"
          >
            <div className="flex items-center">
              <Check className="mr-2" size={20} />
              <span>Qualidade Garantida</span>
            </div>
            <div className="flex items-center">
              <Check className="mr-2" size={20} />
              <span>Atendimento Personalizado</span>
            </div>
            <div className="flex items-center">
              <Check className="mr-2" size={20} />
              <span>Resultados Comprovados</span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
