import Link from 'next/link'
import { Phone, Mail, MapPin, Facebook, Instagram, Linkedin, Youtube } from 'lucide-react'

export default function Footer() {
    return (
        <footer className="bg-gray-900 text-white">
            <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div>
                        <h3 className="text-2xl font-bold mb-4">{{ BUSINESS_NAME }}</h3>
                        <p className="text-gray-400 max-w-xs">
                            {{ BUSINESS_DESCRIPTION }}
                        </p>
                        <div className="mt-6 flex space-x-4">
                            {{ #SOCIAL_FACEBOOK}}
                            <a href="{{SOCIAL_FACEBOOK}}" className="text-gray-400 hover:text-white">
                                <Facebook className="h-6 w-6" />
                            </a>
                            {{/ SOCIAL_FACEBOOK}}
                            {{ #SOCIAL_INSTAGRAM}}
                            <a href="{{SOCIAL_INSTAGRAM}}" className="text-gray-400 hover:text-white">
                                <Instagram className="h-6 w-6" />
                            </a>
                            {{/ SOCIAL_INSTAGRAM}}
                            {{ #SOCIAL_LINKEDIN}}
                            <a href="{{SOCIAL_LINKEDIN}}" className="text-gray-400 hover:text-white">
                                <Linkedin className="h-6 w-6" />
                            </a>
                            {{/ SOCIAL_LINKEDIN}}
                        </div>
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold mb-4">Links Rápidos</h3>
                        <ul className="space-y-2">
                            <li><Link href="/" className="text-gray-400 hover:text-white">Início</Link></li>
                            <li><Link href="/sobre" className="text-gray-400 hover:text-white">Sobre Nós</Link></li>
                            <li><Link href="/servicos" className="text-gray-400 hover:text-white">Nossos Serviços</Link></li>
                            <li><Link href="/contato" className="text-gray-400 hover:text-white">Fale Conosco</Link></li>
                            <li><Link href="/privacidade" className="text-gray-400 hover:text-white">Política de Privacidade</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold mb-4">Contato</h3>
                        <ul className="space-y-4">
                            <li className="flex items-start">
                                <MapPin className="h-6 w-6 text-primary mr-2 flex-shrink-0" />
                                <span className="text-gray-400">{{ BUSINESS_ADDRESS }}</span>
                            </li>
                            <li className="flex items-center">
                                <Phone className="h-6 w-6 text-primary mr-2 flex-shrink-0" />
                                <span className="text-gray-400">{{ BUSINESS_PHONE }}</span>
                            </li>
                            <li className="flex items-center">
                                <Mail className="h-6 w-6 text-primary mr-2 flex-shrink-0" />
                                <span className="text-gray-400">{{ BUSINESS_EMAIL }}</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="mt-12 border-t border-gray-800 pt-8 text-center text-gray-400 text-sm">
                    <p>&copy; {new Date().getFullYear()} {{ BUSINESS_NAME }}. Todos os direitos reservados.</p>
                </div>
            </div>
        </footer>
    )
}
