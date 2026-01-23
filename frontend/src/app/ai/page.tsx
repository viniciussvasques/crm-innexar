'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles, Send, User, Bot, Zap, MessageSquare,
  Lightbulb, CheckCircle, Loader2
} from 'lucide-react'

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
          user_role: 'vendedor',
          conversation_history: messages.slice(-5)
        }
      })

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        role: 'assistant',
        timestamp: response.data.timestamp
      }

      setMessages(prev => [...prev, aiMessage])

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
    { icon: User, text: 'Crie um contato para João Silva, email joao@empresa.com' },
    { icon: Zap, text: 'Crie uma oportunidade de R$ 50.000 para o cliente XYZ' },
    { icon: Lightbulb, text: 'Analise minha performance de vendas deste mês' },
    { icon: CheckCircle, text: 'Crie uma tarefa para ligar para o cliente amanhã' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 h-screen flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-400" />
            Helena - IA
          </h1>
          <p className="text-slate-400 mt-1">{t('ai.description') || 'Your intelligent CRM assistant'}</p>
        </div>

        <div className="flex-1 flex gap-6 overflow-hidden">
          {/* Chat Area */}
          <div className="flex-1 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex flex-col overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-5xl font-bold shadow-lg shadow-purple-500/25 mb-6"
                  >
                    H
                  </motion.div>
                  <h3 className="text-xl font-semibold text-white mb-2">{t('ai.welcome') || 'Olá! Eu sou Helena'}</h3>
                  <p className="text-slate-400 max-w-md mx-auto">{t('ai.welcomeMessage') || 'Sua assistente de CRM inteligente. Como posso ajudar você hoje?'}</p>
                </div>
              )}

              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25">
                          <Bot className="w-5 h-5 text-white" />
                        </div>
                      </div>
                    )}
                    <div
                      className={`max-w-xs lg:max-w-lg px-4 py-3 rounded-2xl ${message.role === 'user'
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-sm'
                          : 'bg-white/10 text-white border border-white/10 rounded-bl-sm'
                        }`}
                    >
                      <p className="whitespace-pre-wrap text-sm lg:text-base">{message.content}</p>
                      <p className="text-xs opacity-60 mt-2">
                        {new Date(message.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    {message.role === 'user' && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-medium">
                          {user?.name?.charAt(0).toUpperCase() || 'U'}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {loading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-3"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center animate-pulse shadow-lg shadow-purple-500/25">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div className="bg-white/10 border border-white/10 px-4 py-3 rounded-2xl rounded-bl-sm">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                      <span className="text-sm text-slate-400">{t('ai.thinking') || 'Helena está pensando...'}</span>
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-white/10 p-4">
              <div className="flex gap-3">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={t('ai.placeholder') || 'Digite sua pergunta ou peça para criar algo...'}
                  className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 resize-none transition-colors"
                  rows={2}
                  disabled={loading}
                />
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-purple-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  {t('ai.send') || 'Enviar'}
                </motion.button>
              </div>
            </div>
          </div>

          {/* Sidebar - Hidden on mobile */}
          <div className="hidden lg:block w-80 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 overflow-y-auto">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-400" />
              {t('ai.quickPrompts') || 'Sugestões Rápidas'}
            </h3>
            <div className="space-y-2">
              {quickPrompts.map((prompt, index) => (
                <motion.button
                  key={index}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setInput(prompt.text)}
                  className="w-full text-left p-3 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:border-purple-500/30 transition-all text-sm text-slate-300 flex items-start gap-3"
                  disabled={loading}
                >
                  <prompt.icon className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
                  <span>{prompt.text}</span>
                </motion.button>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t border-white/10">
              <h4 className="font-medium text-white mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                {t('ai.capabilities') || 'O que posso fazer'}
              </h4>
              <ul className="text-sm text-slate-400 space-y-2">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
                  Criar e gerenciar contatos
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                  Criar oportunidades e tarefas
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></div>
                  Analisar performance de vendas
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-amber-400 rounded-full"></div>
                  Gerar propostas comerciais
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
