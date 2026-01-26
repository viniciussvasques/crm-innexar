'use client'

import { useState } from 'react'
import { Mail, Phone, MapPin, Send } from 'lucide-react'

export default function ContatoPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    message: ''
  })
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission
    alert('Mensagem enviada! Entraremos em contato em breve.')
  }
  
  return (
    <div className="section-padding">
      <div className="container-custom">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Entre em Contato
            </h1>
            <p className="text-xl text-gray-600">
              Estamos prontos para ajudar você
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="text-2xl font-bold mb-6">Informações de Contato</h2>
              
              <div className="space-y-6">
                <div className="flex items-start">
                  <Mail className="text-primary mr-4 mt-1" size={24} />
                  <div>
                    <h3 className="font-semibold mb-1">Email</h3>
                    <a href={`mailto:{{BUSINESS_EMAIL}}`} className="text-gray-600 hover:text-primary">
                      {{BUSINESS_EMAIL}}
                    </a>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <Phone className="text-primary mr-4 mt-1" size={24} />
                  <div>
                    <h3 className="font-semibold mb-1">Telefone</h3>
                    <a href={`tel:{{BUSINESS_PHONE}}`} className="text-gray-600 hover:text-primary">
                      {{BUSINESS_PHONE}}
                    </a>
                  </div>
                </div>
                
                {{#BUSINESS_ADDRESS}}
                <div className="flex items-start">
                  <MapPin className="text-primary mr-4 mt-1" size={24} />
                  <div>
                    <h3 className="font-semibold mb-1">Endereço</h3>
                    <p className="text-gray-600">
                      {{BUSINESS_ADDRESS}}
                    </p>
                  </div>
                </div>
                {{/BUSINESS_ADDRESS}}
              </div>
              
              {{#BUSINESS_HOURS}}
              <div className="mt-8">
                <h3 className="font-semibold mb-4">Horário de Funcionamento</h3>
                <div className="text-gray-600 whitespace-pre-line">
                  {{BUSINESS_HOURS}}
                </div>
              </div>
              {{/BUSINESS_HOURS}}
            </div>
            
            <div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium mb-2">
                    Nome
                  </label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label htmlFor="email" className="block text-sm font-medium mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium mb-2">
                    Telefone
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label htmlFor="message" className="block text-sm font-medium mb-2">
                    Mensagem
                  </label>
                  <textarea
                    id="message"
                    required
                    rows={5}
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                
                <button type="submit" className="btn-primary w-full flex items-center justify-center">
                  Enviar Mensagem
                  <Send className="ml-2" size={20} />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
