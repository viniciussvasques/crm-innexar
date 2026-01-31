'use client'

import { useState } from 'react'
import Section from '@/components/Section'
import { Phone, Mail, MapPin } from 'lucide-react'

export default function Contact() {
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        // Simulate form submission
        setStatus('success')
    }

    return (
        <>
            <div className="bg-primary py-20 text-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl font-extrabold sm:text-5xl lg:text-6xl">Entre em Contato</h1>
                    <p className="mt-4 text-xl text-primary-light max-w-2xl mx-auto">
                        Estamos prontos para atender você.
                    </p>
                </div>
            </div>

            <Section>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    {/* Contact Info */}
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-6">Informações de Contato</h2>
                        <p className="text-gray-600 mb-8">
                            Preencha o formulário ao lado ou utilize um dos nossos canais de atendimento direto.
                        </p>

                        <div className="space-y-6">
                            <div className="flex items-start">
                                <MapPin className="h-6 w-6 text-primary mt-1 mr-4" />
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">Endereço</h3>
                                    <p className="text-gray-600">{{ BUSINESS_ADDRESS }}</p>
                                </div>
                            </div>

                            <div className="flex items-start">
                                <Phone className="h-6 w-6 text-primary mt-1 mr-4" />
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">Telefone</h3>
                                    <p className="text-gray-600">{{ BUSINESS_PHONE }}</p>
                                </div>
                            </div>

                            <div className="flex items-start">
                                <Mail className="h-6 w-6 text-primary mt-1 mr-4" />
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">Email</h3>
                                    <p className="text-gray-600">{{ BUSINESS_EMAIL }}</p>
                                </div>
                            </div>
                        </div>

                        <div className="mt-12">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Horário de Atendimento</h3>
                            <p className="text-gray-600 whitespace-pre-line">{{ BUSINESS_HOURS }}</p>
                        </div>
                    </div>

                    {/* Contact Form */}
                    <div className="bg-gray-50 p-8 rounded-lg shadow-sm">
                        {status === 'success' ? (
                            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                                <strong className="font-bold">Mensagem enviada!</strong>
                                <span className="block sm:inline"> Entraremos em contato em breve.</span>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div>
                                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">Nome</label>
                                    <input
                                        type="text"
                                        name="name"
                                        id="name"
                                        required
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary h-10 px-3 border"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                                    <input
                                        type="email"
                                        name="email"
                                        id="email"
                                        required
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary h-10 px-3 border"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700">Telefone</label>
                                    <input
                                        type="tel"
                                        name="phone"
                                        id="phone"
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary h-10 px-3 border"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="message" className="block text-sm font-medium text-gray-700">Mensagem</label>
                                    <textarea
                                        id="message"
                                        name="message"
                                        rows={4}
                                        required
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary p-3 border"
                                    ></textarea>
                                </div>

                                <button
                                    type="submit"
                                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-colors"
                                >
                                    Enviar Mensagem
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </Section>
        </>
    )
}
