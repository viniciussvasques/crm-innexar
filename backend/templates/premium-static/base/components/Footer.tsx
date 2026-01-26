import Link from 'next/link'
import { Mail, Phone, MapPin, Facebook, Instagram } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="container-custom section-padding">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-xl font-bold mb-4">{{BUSINESS_NAME}}</h3>
            <p className="text-gray-400">{{BUSINESS_DESCRIPTION}}</p>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-4">Links Rápidos</h4>
            <ul className="space-y-2">
              <li><Link href="/sobre" className="text-gray-400 hover:text-white transition-colors">Sobre Nós</Link></li>
              <li><Link href="/servicos" className="text-gray-400 hover:text-white transition-colors">Serviços</Link></li>
              <li><Link href="/contato" className="text-gray-400 hover:text-white transition-colors">Contato</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-4">Contato</h4>
            <ul className="space-y-3">
              <li className="flex items-center space-x-2 text-gray-400">
                <Phone size={18} />
                <a href="tel:{{BUSINESS_PHONE}}" className="hover:text-white">{{BUSINESS_PHONE}}</a>
              </li>
              <li className="flex items-center space-x-2 text-gray-400">
                <Mail size={18} />
                <a href="mailto:{{BUSINESS_EMAIL}}" className="hover:text-white">{{BUSINESS_EMAIL}}</a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; {new Date().getFullYear()} {{BUSINESS_NAME}}. Todos os direitos reservados.</p>
        </div>
      </div>
    </footer>
  )
}
