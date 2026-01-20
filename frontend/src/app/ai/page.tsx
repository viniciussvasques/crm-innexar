'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import { useLanguage } from '@/contexts/LanguageContext'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
}

export default function AIPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    if (!token) {
      router.push('/login')
      return
    }
    if (userStr) {
      try {
        setUser(JSON.parse(userStr))
      } catch (error) {
        console.error('Erro ao parsear usuário:', error)
      }
    }
    // Carregar histórico do chat
    loadChatHistory()
  }, [router])

  const loadChatHistory = async () => {
    try {
      const response = await api.get('/api/ai/chat/history?limit=50')
      if (response.data && response.data.length > 0) {
        setMessages(response.data.map((msg: any) => ({
          id: msg.id.toString(),
          content: msg.content,
          role: msg.role,
          timestamp: msg.created_at
        })))
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      // Não mostrar erro, apenas continuar sem histórico
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.post('/api/ai/chat', {
        prompt: input,
        context: {
          user_role: 'vendedor', // TODO: pegar do contexto do usuário
          conversation_history: messages.slice(-5) // últimos 5 mensagens para contexto
        }
      })

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        role: 'assistant',
        timestamp: response.data.timestamp
      }

      setMessages(prev => [...prev, aiMessage])

      // Se uma ação foi executada, mostrar notificação
      if (response.data.action_executed) {
        toast.success(t('ai.actionExecuted'))
      }

    } catch (error) {
      console.error('Erro no chat com IA:', error)
      toast.error(t('ai.error'))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const quickPrompts = [
    'Crie um contato para João Silva, email joao@empresa.com',
    'Crie uma oportunidade de R$ 50.000 para o cliente XYZ',
    'Analise minha performance de vendas deste mês',
    'Sugira estratégias para converter mais leads',
    'Crie uma tarefa para ligar para o cliente amanhã'
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">{t('ai.title')}</h2>
        <p className="text-gray-600 mt-2">{t('ai.description')}</p>
      </div>

      <div className="flex-1 flex gap-6">
        {/* Área de Chat */}
        <div className="flex-1 bg-white rounded-lg shadow flex flex-col">
          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-8">
                <div className="mb-4">
                  <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-5xl font-bold shadow-lg">
                    H
                  </div>
                </div>
                <h3 className="text-lg font-medium mb-2">{t('ai.welcome')}</h3>
                <p>{t('ai.welcomeMessage')}</p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start gap-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-sm font-bold flex items-center justify-center shadow-md">
                      H
                    </div>
                  </div>
                )}
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-8 h-8 rounded-full bg-primary text-white text-sm font-bold flex items-center justify-center">
                      {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-start gap-2 justify-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-sm font-bold flex items-center justify-center shadow-md animate-pulse">
                    H
                  </div>
                </div>
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                    <span className="text-sm text-gray-600">{t('ai.thinking')}</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={t('ai.placeholder')}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none"
                rows={2}
                disabled={loading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={loading || !input.trim()}
                className="px-6"
              >
                {t('ai.send')}
              </Button>
            </div>
          </div>
        </div>

        {/* Painel Lateral */}
        <div className="w-80 bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">{t('ai.quickPrompts')}</h3>
          <div className="space-y-2">
            {quickPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => setInput(prompt)}
                className="w-full text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors text-sm"
                disabled={loading}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t">
            <h4 className="font-medium mb-3">{t('ai.capabilities')}</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• {t('ai.capability1')}</li>
              <li>• {t('ai.capability2')}</li>
              <li>• {t('ai.capability3')}</li>
              <li>• {t('ai.capability4')}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
