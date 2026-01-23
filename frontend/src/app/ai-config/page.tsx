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
import { motion } from 'framer-motion'
import { Bot, Plus, Zap, CheckCircle, AlertCircle, Settings, Play, Pencil, Trash2, Loader2 } from 'lucide-react'

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

interface AvailableModels { [provider: string]: Array<{ name: string; display: string }> }

const providerConfig: Record<string, { label: string; color: string; icon: string }> = {
  grok: { label: 'Grok (xAI)', color: 'blue', icon: '🤖' },
  openai: { label: 'OpenAI', color: 'emerald', icon: '🟢' },
  anthropic: { label: 'Anthropic (Claude)', color: 'purple', icon: '🟣' },
  ollama: { label: 'Ollama (Local)', color: 'orange', icon: '🦙' },
  google: { label: 'Google (Gemini)', color: 'yellow', icon: '✨' },
  mistral: { label: 'Mistral AI', color: 'cyan', icon: '🌊' },
  cohere: { label: 'Cohere', color: 'pink', icon: '💫' },
  cloudflare: { label: 'Cloudflare Workers AI', color: 'orange', icon: '☁️' }
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
  const [formData, setFormData] = useState({ name: '', provider: 'grok', model_name: '', api_key: '', base_url: '', is_active: false, is_default: false, priority: 0 })

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    if (!token) { router.push('/login'); return }
    if (userStr) { const user = JSON.parse(userStr); if (user.role !== 'admin') { router.push('/dashboard'); return } }
    loadConfigs()
    loadAvailableModels()
  }, [router])

  const loadConfigs = async () => {
    try { setLoading(true); const response = await api.get('/api/ai-config'); setConfigs(response.data) }
    catch (error) { console.error('Erro ao carregar configurações:', error); toast.error('Erro ao carregar configurações') }
    finally { setLoading(false) }
  }

  const loadAvailableModels = async () => {
    try { const response = await api.get('/api/ai-config/models'); setAvailableModels(response.data) }
    catch (error) { console.error('Erro ao carregar modelos:', error) }
  }

  const handleOpenModal = (config?: AIConfig) => {
    if (config) {
      setEditingConfig(config)
      setFormData({ name: config.name, provider: config.provider, model_name: config.model_name, api_key: '', base_url: config.base_url || '', is_active: config.is_active, is_default: config.is_default, priority: config.priority })
    } else {
      setEditingConfig(null)
      setFormData({ name: '', provider: 'grok', model_name: '', api_key: '', base_url: '', is_active: false, is_default: false, priority: 0 })
    }
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingConfig) { await api.put(`/api/ai-config/${editingConfig.id}`, formData); toast.success('Configuração atualizada!') }
      else { await api.post('/api/ai-config', formData); toast.success('Configuração criada!') }
      setShowModal(false); loadConfigs()
    } catch (error: any) { console.error('Erro ao salvar configuração:', error); toast.error(error.response?.data?.detail || 'Erro ao salvar') }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja deletar esta configuração?')) return
    try { await api.delete(`/api/ai-config/${id}`); toast.success('Configuração deletada!'); loadConfigs() }
    catch (error) { console.error('Erro ao deletar:', error); toast.error('Erro ao deletar') }
  }

  const handleTest = async (id: number) => {
    try { setTestingId(id); const response = await api.post(`/api/ai-config/${id}/test`); if (response.data.success) toast.success('Teste bem-sucedido!'); else toast.error(`Erro: ${response.data.error}`); loadConfigs() }
    catch (error: any) { console.error('Erro ao testar:', error); toast.error(error.response?.data?.detail || 'Erro ao testar') }
    finally { setTestingId(null) }
  }

  const providerOptions = Object.entries(providerConfig).map(([value, config]) => ({ value, label: config.label }))
  const modelOptions = availableModels[formData.provider]?.map(m => ({ value: m.name, label: m.display })) || []

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(i => (<div key={i} className="h-48 bg-white/5 rounded-xl"></div>))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <Bot className="w-8 h-8 text-purple-400" />
              Configuração de IA
            </h1>
            <p className="text-slate-400 mt-1">Gerencie os modelos de IA disponíveis para o sistema</p>
          </div>
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => handleOpenModal()}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow">
            <Plus className="w-5 h-5" />
            Nova Configuração
          </motion.button>
        </div>

        {/* Configs Grid */}
        {configs.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-12 text-center">
            <Bot className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Nenhuma configuração encontrada</h3>
            <p className="text-slate-400 mb-6">Comece criando sua primeira configuração de IA</p>
            <Button onClick={() => handleOpenModal()}>Criar Primeira Configuração</Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {configs.map((config, i) => {
              const provider = providerConfig[config.provider] || { label: config.provider, color: 'slate', icon: '🤖' }
              return (
                <motion.div key={config.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/[0.08] transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{provider.icon}</span>
                      <div>
                        <h3 className="font-semibold text-white">{config.name}</h3>
                        <p className="text-sm text-slate-500">{provider.label}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${config.status === 'active' ? 'bg-emerald-500/20 text-emerald-300' : config.status === 'error' ? 'bg-red-500/20 text-red-300' : 'bg-slate-500/20 text-slate-300'}`}>
                        {config.status}
                      </span>
                      {config.is_default && (<span className="px-2.5 py-1 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300">Padrão</span>)}
                    </div>
                  </div>
                  <div className="space-y-2 text-sm mb-4">
                    <p className="text-slate-400"><span className="text-slate-500">Modelo:</span> {config.model_name}</p>
                    {config.base_url && (<p className="text-slate-400 truncate"><span className="text-slate-500">URL:</span> {config.base_url}</p>)}
                    {config.last_error && (<p className="text-red-300 text-xs truncate">{config.last_error}</p>)}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleTest(config.id)} disabled={testingId === config.id}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20 transition-colors disabled:opacity-50">
                      {testingId === config.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                      Testar
                    </button>
                    <button onClick={() => handleOpenModal(config)} className="p-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(config.id)} className="p-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editingConfig ? 'Editar Configuração' : 'Nova Configuração'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required placeholder="Ex: Helena - Grok" />
          <Select label="Provider" value={formData.provider} onChange={(e) => { setFormData({ ...formData, provider: e.target.value, model_name: '' }); loadAvailableModels() }} options={providerOptions} required />
          {formData.provider === 'ollama' ? (
            <Input label="Modelo" value={formData.model_name} onChange={(e) => setFormData({ ...formData, model_name: e.target.value })} required placeholder="Ex: llama3.1, mistral" />
          ) : (
            <Select label="Modelo" value={formData.model_name} onChange={(e) => setFormData({ ...formData, model_name: e.target.value })} options={modelOptions} required disabled={!formData.provider} />
          )}
          <Input label="API Key" type="password" value={formData.api_key} onChange={(e) => setFormData({ ...formData, api_key: e.target.value.trim() })} placeholder={formData.provider === 'ollama' ? 'Opcional' : 'Obrigatório'} required={formData.provider !== 'ollama'} />
          <Input label="URL Base (opcional)" value={formData.base_url} onChange={(e) => setFormData({ ...formData, base_url: e.target.value })} placeholder={formData.provider === 'ollama' ? 'http://localhost:11434' : 'Deixe vazio para usar padrão'} />
          <div className="flex items-center space-x-6">
            <label className="flex items-center"><input type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="rounded border-white/20 bg-white/5 text-blue-600" /><span className="ml-2 text-sm text-white">Ativo</span></label>
            <label className="flex items-center"><input type="checkbox" checked={formData.is_default} onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })} className="rounded border-white/20 bg-white/5 text-blue-600" /><span className="ml-2 text-sm text-white">Padrão</span></label>
          </div>
          <Input label="Prioridade" type="number" value={formData.priority.toString()} onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })} />
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)}>Cancelar</Button>
            <Button type="submit">{editingConfig ? 'Atualizar' : 'Criar'}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
