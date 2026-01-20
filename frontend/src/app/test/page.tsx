'use client'

import React from 'react'
import { useLanguage } from '@/contexts/LanguageContext'

export default function TestPage() {
  const { t, language } = useLanguage()

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Página de Teste</h1>
      <p className="mb-4">Idioma atual: {language}</p>
      <p className="mb-4">Tradução de teste: {t('common.loading')}</p>
      <p className="mb-4">Dashboard title: {t('dashboard.title')}</p>
      <p className="mb-4">Nav dashboard: {t('nav.dashboard')}</p>

      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-2">Teste de Componentes</h2>
        <p>Se você consegue ver esta página, o frontend está funcionando!</p>
      </div>
    </div>
  )
}
