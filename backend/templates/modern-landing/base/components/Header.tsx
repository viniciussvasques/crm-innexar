'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  
  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-2xl font-bold text-primary">
            {{BUSINESS_NAME}}
          </Link>
          
          <nav className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-700 hover:text-primary transition-colors">
              Início
            </Link>
            <Link href="/sobre" className="text-gray-700 hover:text-primary transition-colors">
              Sobre
            </Link>
            <Link href="/servicos" className="text-gray-700 hover:text-primary transition-colors">
              Serviços
            </Link>
            <Link href="/contato" className="btn-primary">
              {{CTA_TEXT}}
            </Link>
          </nav>
          
          <button
            className="md:hidden text-gray-700"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
        
        {mobileMenuOpen && (
          <nav className="md:hidden py-4 border-t">
            <div className="flex flex-col space-y-4">
              <Link href="/" className="text-gray-700 hover:text-primary">
                Início
              </Link>
              <Link href="/sobre" className="text-gray-700 hover:text-primary">
                Sobre
              </Link>
              <Link href="/servicos" className="text-gray-700 hover:text-primary">
                Serviços
              </Link>
              <Link href="/contato" className="btn-primary text-center">
                {{CTA_TEXT}}
              </Link>
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
