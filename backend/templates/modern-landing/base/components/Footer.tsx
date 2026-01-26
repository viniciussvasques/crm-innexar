import Link from 'next/link'
import { Mail, Phone, MapPin, Facebook, Instagram } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container-custom section-padding">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-white text-xl font-bold mb-4">
              {{BUSINESS_NAME}}
            </h3>
            <p className="text-gray-400">
              {{BUSINESS_DESCRIPTION}}
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Links Rápidos</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/" className="hover:text-white transition-colors">
                  Início
                </Link>
              </li>
              <li>
                <Link href="/sobre" className="hover:text-white transition-colors">
                  Sobre
                </Link>
              </li>
              <li>
                <Link href="/servicos" className="hover:text-white transition-colors">
                  Serviços
                </Link>
              </li>
              <li>
                <Link href="/contato" className="hover:text-white transition-colors">
                  Contato
                </Link>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Contato</h4>
            <ul className="space-y-3">
              <li className="flex items-center">
                <Mail className="mr-2" size={18} />
                <a href={`mailto:{{BUSINESS_EMAIL}}`} className="hover:text-white">
                  {{BUSINESS_EMAIL}}
                </a>
              </li>
              <li className="flex items-center">
                <Phone className="mr-2" size={18} />
                <a href={`tel:{{BUSINESS_PHONE}}`} className="hover:text-white">
                  {{BUSINESS_PHONE}}
                </a>
              </li>
              {{#BUSINESS_ADDRESS}}
              <li className="flex items-start">
                <MapPin className="mr-2 mt-1" size={18} />
                <span>{{BUSINESS_ADDRESS}}</span>
              </li>
              {{/BUSINESS_ADDRESS}}
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Redes Sociais</h4>
            <div className="flex space-x-4">
              {{#SOCIAL_FACEBOOK}}
              <a href="{{SOCIAL_FACEBOOK}}" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                <Facebook size={24} />
              </a>
              {{/SOCIAL_FACEBOOK}}
              {{#SOCIAL_INSTAGRAM}}
              <a href="{{SOCIAL_INSTAGRAM}}" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                <Instagram size={24} />
              </a>
              {{/SOCIAL_INSTAGRAM}}
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; {new Date().getFullYear()} {{BUSINESS_NAME}}. Todos os direitos reservados.</p>
        </div>
      </div>
    </footer>
  )
}
