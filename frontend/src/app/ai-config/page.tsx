'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import Modal from '@/components/Modal'
import { useLanguage } from '@/contexts/LanguageContext'

interface AIConfig {
  id: number
  name: string
  provider: string
  model_name: string
  base_url?: string
  is_active: boolean
  is_default: boolean
  status: string
  priority: number
  config?: any
  created_at: string
  updated_at: string
  last_tested_at?: string
  last_error?: string
}

interface AvailableModels {
  [provider: string]: Array<{ name: string; display: string }>
}

export default function AIConfigPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [configs, setConfigs] = useState<AIConfig[]>([])
  const [availableModels, setAvailableModels] = useState<AvailableModels>({})
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<AIConfig | null>(null)
  const [testingId, setTestingId] = useState<number | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    provider: 'grok',
    model_name: '',
    api_key: '',
    base_url: '',
    is_active: false,
    is_default: false,
    priority: 0
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    if (!token) {
      router.push('/login')
      return
    }
    if (userStr) {
      const user = JSON.parse(userStr)
      if (user.role !== 'admin') {
        router.push('/dashboard')
        return
      }
    }
    loadConfigs()
    loadAvailableModels()
  }, [router])

  const loadConfigs = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/ai-config')
      setConfigs(response.data)
    } catch (error) {
      console.error('Erro ao carregar configurações:', error)
      toast.error('Erro ao carregar configurações')
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const response = await api.get('/api/ai-config/models')
      setAvailableModels(response.data)
    } catch (error) {
      console.error('Erro ao carregar modelos:', error)
    }
  }

  const handleOpenModal = (config?: AIConfig) => {
    if (config) {
      setEditingConfig(config)
      setFormData({
        name: config.name,
        provider: config.provider,
        model_name: config.model_name,
        api_key: '', // Não mostrar API key existente por segurança
        base_url: config.base_url || '',
        is_active: config.is_active,
        is_default: config.is_default,
        priority: config.priority
      })
    } else {
      setEditingConfig(null)
      setFormData({
        name: '',
        provider: 'grok',
        model_name: '',
        api_key: '',
        base_url: '',
        is_active: false,
        is_default: false,
        priority: 0
      })
    }
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingConfig) {
        await api.put(`/api/ai-config/${editingConfig.id}`, formData)
        toast.success('Configuração atualizada com sucesso!')
      } else {
        await api.post('/api/ai-config', formData)
        toast.success('Configuração criada com sucesso!')
      }
      setShowModal(false)
      loadConfigs()
    } catch (error: any) {
      console.error('Erro ao salvar configuração:', error)
      toast.error(error.response?.data?.detail || 'Erro ao salvar configuração')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja deletar esta configuração?')) return

    try {
      await api.delete(`/api/ai-config/${id}`)
      toast.success('Configuração deletada com sucesso!')
      loadConfigs()
    } catch (error) {
      console.error('Erro ao deletar configuração:', error)
      toast.error('Erro ao deletar configuração')
    }
  }

  const handleTest = async (id: number) => {
    try {
      setTestingId(id)
      const response = await api.post(`/api/ai-config/${id}/test`)
      if (response.data.success) {
        toast.success('Teste bem-sucedido!')
      } else {
        toast.error(`Erro no teste: ${response.data.error}`)
      }
      loadConfigs()
    } catch (error: any) {
      console.error('Erro ao testar configuração:', error)
      toast.error(error.response?.data?.detail || 'Erro ao testar configuração')
    } finally {
      setTestingId(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'error': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getProviderDisplay = (provider: string) => {
    const providers: { [key: string]: string } = {
      grok: 'Grok (xAI)',
      openai: 'OpenAI',
      anthropic: 'Anthropic (Claude)',
      ollama: 'Ollama (Local)',
      google: 'Google (Gemini)',
      mistral: 'Mistral AI',
      cohere: 'Cohere',
      cloudflare: 'Cloudflare Workers AI'
    }
    return providers[provider] || provider
  }

  const providerOptions = [
    { value: 'grok', label: 'Grok (xAI)' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic (Claude)' },
    { value: 'ollama', label: 'Ollama (Local)' },
    { value: 'google', label: 'Google (Gemini)' },
    { value: 'mistral', label: 'Mistral AI' },
    { value: 'cohere', label: 'Cohere' },
    { value: 'cloudflare', label: 'Cloudflare Workers AI' }
  ]

  const modelOptions = availableModels[formData.provider]?.map(m => ({
    value: m.name,
    label: m.display
  })) || []

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Configuração de IA</h2>
          <p className="text-gray-600 mt-2">Gerencie os modelos de IA disponíveis para o sistema</p>
        </div>
        <Button onClick={() => handleOpenModal()}>
          + Nova Configuração
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando configurações...</p>
        </div>
      ) : configs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">⚙️</div>
          <h3 className="text-xl font-semibold mb-2">Nenhuma configuração encontrada</h3>
          <p className="text-gray-600 mb-6">Comece criando sua primeira configuração de IA</p>
          <Button onClick={() => handleOpenModal()}>
            Criar Primeira Configuração
          </Button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modelo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Padrão</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {configs.map((config) => (
                <tr key={config.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{config.name}</div>
                    {config.last_error && (
                      <div className="text-xs text-red-600 mt-1">{config.last_error.substring(0, 50)}...</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{getProviderDisplay(config.provider)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{config.model_name}</div>
                    {config.base_url && (
                      <div className="text-xs text-gray-500">{config.base_url}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(config.status)}`}>
                      {config.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {config.is_default ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        Padrão
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleTest(config.id)}
                      disabled={testingId === config.id}
                      className="text-primary hover:text-primary-dark disabled:opacity-50"
                    >
                      {testingId === config.id ? 'Testando...' : 'Testar'}
                    </button>
                    <button
                      onClick={() => handleOpenModal(config)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(config.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Deletar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingConfig ? 'Editar Configuração' : 'Nova Configuração'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nome"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="Ex: Helena - Grok"
          />

          <Select
            label="Provider"
            value={formData.provider}
            onChange={(e) => {
              setFormData({ ...formData, provider: e.target.value, model_name: '' })
              loadAvailableModels()
            }}
            options={providerOptions}
            required
          />

          <div>
            <div>
              {formData.provider === 'ollama' ? (
                <div>
                  <Input
                    label="Modelo"
                    value={formData.model_name}
                    onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                    required
                    placeholder="Ex: llama3.1, mistral, neural-chat"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    💡 Digite o nome exato do modelo instalado no Ollama (use 'ollama list' para ver os modelos disponíveis)
                  </p>
                </div>
              ) : (
                <Select
                  label="Modelo"
                  value={formData.model_name}
                  onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                  options={modelOptions}
                  required
                  disabled={!formData.provider}
                />
              )}
              {formData.provider === 'google' && formData.api_key && formData.api_key.trim().startsWith('AIza') && (
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      const response = await api.get(`/api/ai-config/google/list-models?api_key=${encodeURIComponent(formData.api_key.trim())}`)
                      if (response.data.models && response.data.models.length > 0) {
                        const googleModels = response.data.models.map((m: any) => ({
                          value: m.name,
                          label: m.display
                        }))
                        setAvailableModels({ ...availableModels, google: googleModels })
                        toast.success(`Encontrados ${googleModels.length} modelos disponíveis!`)
                      }
                    } catch (error: any) {
                      console.error('Erro ao listar modelos:', error)
                      toast.error('Erro ao listar modelos. Use os modelos padrão.')
                    }
                  }}
                  className="mt-2 text-sm text-primary hover:underline"
                >
                  🔍 Buscar modelos disponíveis na API
                </button>
              )}
            </div>
            {formData.provider === 'google' && formData.api_key && formData.api_key.trim().startsWith('AIza') && (
              <button
                type="button"
                onClick={async () => {
                  try {
                    const response = await api.get(`/api/ai-config/google/list-models?api_key=${encodeURIComponent(formData.api_key.trim())}`)
                    if (response.data.models && response.data.models.length > 0) {
                      const googleModels = response.data.models.map((m: any) => ({
                        value: m.name,
                        label: m.display
                      }))
                      setAvailableModels({ ...availableModels, google: googleModels })
                      toast.success(`Encontrados ${googleModels.length} modelos disponíveis!`)
                    }
                  } catch (error: any) {
                    console.error('Erro ao listar modelos:', error)
                    toast.error('Erro ao listar modelos. Use os modelos padrão.')
                  }
                }}
                className="mt-2 text-sm text-primary hover:underline"
              >
                🔍 Buscar modelos disponíveis na API
              </button>
            )}
          </div>

          <div>
            <Input
              label="API Key"
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value.trim() })}
              placeholder={formData.provider === 'ollama' ? 'Opcional para Ollama local' : formData.provider === 'google' ? 'AIza... (começa com AIza)' : formData.provider === 'cloudflare' ? 'Token do Workers AI' : 'Obrigatório'}
              required={formData.provider !== 'ollama'}
            />
            {formData.provider === 'google' && (
              <p className="mt-1 text-sm text-gray-500">
                💡 A chave do Google Gemini deve começar com "AIza" e ter aproximadamente 39 caracteres.
                Obtenha em: <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Google AI Studio</a>
              </p>
            )}
            {formData.provider === 'cloudflare' && (
              <p className="mt-1 text-sm text-gray-500">
                💡 Obtenha o token em <a href="https://dash.cloudflare.com/?to=/:account/ai/workers-ai" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Cloudflare Dashboard → Workers AI</a> → Use REST API → Create API Token
              </p>
            )}
          </div>

          {formData.provider === 'cloudflare' ? (
            <div>
              <Input
                label="Account ID"
                value={formData.base_url.replace('https://api.cloudflare.com/client/v4/accounts/', '').replace('/ai/run', '')}
                onChange={(e) => {
                  const accountId = e.target.value.trim()
                  setFormData({
                    ...formData,
                    base_url: accountId ? `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run` : ''
                  })
                }}
                placeholder="Ex: 5af4777bad39954734e3e99d96f9cb8c"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                💡 O Account ID está em Cloudflare Dashboard → Workers AI → Use REST API → Get Account ID
              </p>
              {formData.base_url && (
                <p className="mt-2 text-xs text-green-600 bg-green-50 p-2 rounded">
                  ✅ URL Final: {formData.base_url}/{formData.model_name || '{modelo}'}
                </p>
              )}
            </div>
          ) : (
            <Input
              label="URL Base (opcional)"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              placeholder={formData.provider === 'ollama' ? 'http://localhost:11434' : 'Deixe vazio para usar padrão'}
            />
          )}

          <div className="flex items-center space-x-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="ml-2 text-sm text-gray-700">Ativo</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="ml-2 text-sm text-gray-700">Padrão</span>
            </label>
          </div>

          <Input
            label="Prioridade"
            type="number"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
            min="0"
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowModal(false)}
            >
              Cancelar
            </Button>
            <Button type="submit">
              {editingConfig ? 'Atualizar' : 'Criar'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

