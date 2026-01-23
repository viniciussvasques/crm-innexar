import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Layout from '@/components/Layout'
import { LanguageProvider } from '@/contexts/LanguageContext'
import { ToastContainer } from '@/components/Toast'
import React, { Suspense } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Innexar Workspace',
  description: 'Internal workspace for Innexar team',
  icons: {
    icon: '/favicon.png',
  },
}

// Componente de Loading otimizado
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-800 rounded w-32 mx-auto animate-pulse"></div>
          <div className="h-3 bg-slate-900 rounded w-24 mx-auto animate-pulse"></div>
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
        <link rel="icon" type="image/png" href="/favicon.png" />
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
