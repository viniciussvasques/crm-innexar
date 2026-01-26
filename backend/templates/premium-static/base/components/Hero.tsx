'use client'

import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function Hero() {
  return (
    <section className="relative bg-gradient-to-br from-primary to-secondary text-white">
      <div className="container-custom section-padding">
        <div className="max-w-3xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-4xl md:text-6xl font-bold mb-6"
          >
            {{HERO_TITLE}}
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl md:text-2xl mb-8 text-gray-100"
          >
            {{HERO_SUBTITLE}}
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link href="/contato" className="btn-primary inline-flex items-center justify-center">
              {{CTA_TEXT}}
              <ArrowRight className="ml-2" size={20} />
            </Link>
            <Link href="/sobre" className="bg-white text-primary px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center justify-center">
              Saiba Mais
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
