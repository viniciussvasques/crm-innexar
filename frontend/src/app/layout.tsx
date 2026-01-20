import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Layout from '@/components/Layout'
import { LanguageProvider } from '@/contexts/LanguageContext'
import { ToastContainer } from '@/components/Toast'
import React, { Suspense } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Innexar CRM',
  description: 'CRM interno da Innexar',
}

// Componente de Loading otimizado
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded w-32 mx-auto animate-pulse"></div>
          <div className="h-3 bg-gray-100 rounded w-24 mx-auto animate-pulse"></div>
        </div>
      </div>
    </div>
  )
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={inter.className}>
        <LanguageProvider>
          <Layout>{children}</Layout>
          <ToastContainer />
        </LanguageProvider>
      </body>
    </html>
  )
}
