'use client'

import React, { useState } from 'react'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import Input from '@/components/Input'
import { useLanguage } from '@/contexts/LanguageContext'
import { CheckCircle, XCircle, Loader, Globe, CreditCard, Bell } from 'lucide-react'

export default function TestIntegrationsPage() {
  const { t } = useLanguage()
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [results, setResults] = useState<Record<string, any>>({})
  const [domain, setDomain] = useState('example.com')
  const [domains, setDomains] = useState('example.com,test.com')

  const setLoadingState = (key: string, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }))
  }

  const testDynadotConfig = async () => {
    setLoadingState('dynadot-config', true)
    try {
      const response = await api.get('/api/test-integrations/dynadot/config')
      setResults(prev => ({ ...prev, 'dynadot-config': response.data }))
      toast.success('Configuração Dynadot verificada')
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message}`)
      setResults(prev => ({ ...prev, 'dynadot-config': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('dynadot-config', false)
    }
  }

  const testDynadotDomain = async () => {
    if (!domain.trim()) {
      toast.error('Digite um domínio para testar')
      return
    }
    setLoadingState('dynadot-domain', true)
    try {
      const response = await api.post('/api/test-integrations/dynadot/check-domain', { domain: domain.trim() })
      setResults(prev => ({ ...prev, 'dynadot-domain': response.data }))
      toast.success('Domínio verificado')
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message}`)
      setResults(prev => ({ ...prev, 'dynadot-domain': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('dynadot-domain', false)
    }
  }

  const testDynadotMultiple = async () => {
    const domainList = domains.split(',').map(d => d.trim()).filter(d => d)
    if (domainList.length === 0) {
      toast.error('Digite pelo menos um domínio')
      return
    }
    setLoadingState('dynadot-multiple', true)
    try {
      const response = await api.post('/api/test-integrations/dynadot/check-multiple', domainList)
      setResults(prev => ({ ...prev, 'dynadot-multiple': response.data }))
      toast.success(`${domainList.length} domínios verificados`)
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message}`)
      setResults(prev => ({ ...prev, 'dynadot-multiple': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('dynadot-multiple', false)
    }
  }

  const testStripeConfig = async () => {
    setLoadingState('stripe-config', true)
    try {
      const response = await api.get('/api/test-integrations/stripe/config')
      setResults(prev => ({ ...prev, 'stripe-config': response.data }))
      toast.success('Configuração Stripe verificada')
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message }`)
      setResults(prev => ({ ...prev, 'stripe-config': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('stripe-config', false)
    }
  }

  const testStripeWebhook = async () => {
    setLoadingState('stripe-webhook', true)
    try {
      const response = await api.post('/api/test-integrations/stripe/test-webhook')
      setResults(prev => ({ ...prev, 'stripe-webhook': response.data }))
      toast.success('Teste de webhook executado')
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message}`)
      setResults(prev => ({ ...prev, 'stripe-webhook': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('stripe-webhook', false)
    }
  }

  const testNotifications = async () => {
    setLoadingState('notifications', true)
    try {
      const response = await api.post('/api/test-integrations/notifications/test')
      setResults(prev => ({ ...prev, 'notifications': response.data }))
      toast.success('Notificação de teste criada! Verifique o sino de notificações.')
    } catch (error: any) {
      toast.error(`Erro: ${error.response?.data?.detail || error.message}`)
      setResults(prev => ({ ...prev, 'notifications': { error: error.response?.data?.detail || error.message } }))
    } finally {
      setLoadingState('notifications', false)
    }
  }

  const renderResult = (key: string, title: string) => {
    const result = results[key]
    if (!result) return null

    return (
      <div className="mt-4 p-4 bg-slate-800 rounded-lg border border-white/10">
        <h4 className="text-sm font-semibold text-white mb-2">{title}</h4>
        <pre className="text-xs text-slate-300 overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Testes de Integrações</h1>
        <p className="text-slate-400">Teste as integrações com Dynadot, Stripe e sistema de notificações</p>
      </div>

      {/* Dynadot Tests */}
      <div className="bg-slate-900 rounded-lg p-6 mb-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-6 h-6 text-cyan-500" />
          <h2 className="text-xl font-semibold text-white">Dynadot</h2>
        </div>

        <div className="space-y-4">
          <div>
            <Button
              onClick={testDynadotConfig}
              disabled={loading['dynadot-config']}
              className="w-full sm:w-auto"
            >
              {loading['dynadot-config'] ? (
                <Loader className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Verificar Configuração
            </Button>
            {renderResult('dynadot-config', 'Configuração Dynadot')}
          </div>

          <div>
            <div className="flex gap-2 mb-2">
              <Input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="example.com"
                className="flex-1"
              />
              <Button
                onClick={testDynadotDomain}
                disabled={loading['dynadot-domain']}
              >
                {loading['dynadot-domain'] ? (
                  <Loader className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Globe className="w-4 h-4 mr-2" />
                )}
                Verificar Domínio
              </Button>
            </div>
            {renderResult('dynadot-domain', 'Resultado da Verificação')}
          </div>

          <div>
            <div className="flex gap-2 mb-2">
              <Input
                type="text"
                value={domains}
                onChange={(e) => setDomains(e.target.value)}
                placeholder="example.com,test.com,site.com"
                className="flex-1"
              />
              <Button
                onClick={testDynadotMultiple}
                disabled={loading['dynadot-multiple']}
              >
                {loading['dynadot-multiple'] ? (
                  <Loader className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Globe className="w-4 h-4 mr-2" />
                )}
                Verificar Múltiplos
              </Button>
            </div>
            {renderResult('dynadot-multiple', 'Resultado da Verificação Múltipla')}
          </div>
        </div>
      </div>

      {/* Stripe Tests */}
      <div className="bg-slate-900 rounded-lg p-6 mb-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <CreditCard className="w-6 h-6 text-green-500" />
          <h2 className="text-xl font-semibold text-white">Stripe</h2>
        </div>

        <div className="space-y-4">
          <div>
            <Button
              onClick={testStripeConfig}
              disabled={loading['stripe-config']}
              className="w-full sm:w-auto"
            >
              {loading['stripe-config'] ? (
                <Loader className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Verificar Configuração
            </Button>
            {renderResult('stripe-config', 'Configuração Stripe')}
          </div>

          <div>
            <Button
              onClick={testStripeWebhook}
              disabled={loading['stripe-webhook']}
              className="w-full sm:w-auto"
            >
              {loading['stripe-webhook'] ? (
                <Loader className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CreditCard className="w-4 h-4 mr-2" />
              )}
              Testar Webhook (Cria Notificação)
            </Button>
            {renderResult('stripe-webhook', 'Resultado do Teste')}
          </div>
        </div>
      </div>

      {/* Notifications Test */}
      <div className="bg-slate-900 rounded-lg p-6 mb-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-6 h-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Notificações</h2>
        </div>

        <div>
          <Button
            onClick={testNotifications}
            disabled={loading['notifications']}
            className="w-full sm:w-auto"
          >
            {loading['notifications'] ? (
              <Loader className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Bell className="w-4 h-4 mr-2" />
            )}
            Criar Notificação de Teste
          </Button>
          {renderResult('notifications', 'Resultado do Teste')}
        </div>
      </div>
    </div>
  )
}
