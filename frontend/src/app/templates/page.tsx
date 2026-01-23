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
import { FileText, Copy, Download, Sparkles, Code, FileCode } from 'lucide-react'

interface TemplateType {
  id: string
  name: string
  description: string
  variables: string[]
}

interface GeneratedTemplate {
  template_type: string
  content: string
  language: string
  generated_at: string
  variables_used: Record<string, any>
}

export default function TemplatesPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [templates, setTemplates] = useState<TemplateType[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateType | null>(null)
  const [showGenerator, setShowGenerator] = useState(false)
  const [showResult, setShowResult] = useState(false)
  const [generatedTemplate, setGeneratedTemplate] = useState<GeneratedTemplate | null>(null)
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [language, setLanguage] = useState('pt')

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadTemplates()
  }, [router])

  const loadTemplates = async () => {
    try {
      const response = await api.get('/api/templates/')
      setTemplates(response.data.types)
    } catch (error) {
      console.error('Erro ao carregar templates:', error)
      toast.error('Erro ao carregar templates')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!selectedTemplate) return
    try {
      const response = await api.post('/api/templates/generate', { template_type: selectedTemplate.id, data: formData, language })
      setGeneratedTemplate(response.data)
      setShowResult(true)
      toast.success('Template gerado com sucesso!')
    } catch (error) {
      console.error('Erro ao gerar template:', error)
      toast.error('Erro ao gerar template')
    }
  }

  const copyToClipboard = async () => {
    if (!generatedTemplate) return
    try {
      await navigator.clipboard.writeText(generatedTemplate.content)
      toast.success('Conteúdo copiado!')
    } catch (error) {
      toast.error('Erro ao copiar')
    }
  }

  const downloadAsText = () => {
    if (!generatedTemplate) return
    const blob = new Blob([generatedTemplate.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${generatedTemplate.template_type}_${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (<div key={i} className="h-48 bg-white/5 rounded-xl"></div>))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
            <FileCode className="w-8 h-8 text-pink-400" />
            {t('templates.title')}
          </h1>
          <p className="text-slate-400 mt-1">{t('templates.description')}</p>
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template, i) => (
            <motion.div key={template.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/[0.08] transition-colors">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{template.name}</h3>
                  <p className="text-slate-400 text-sm">{template.description}</p>
                </div>
              </div>
              <div className="mb-4">
                <p className="text-xs font-medium text-slate-500 mb-2">{t('templates.variables')}:</p>
                <div className="flex flex-wrap gap-1">
                  {template.variables.map((variable) => (
                    <span key={variable} className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded-full">{variable}</span>
                  ))}
                </div>
              </div>
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => { setSelectedTemplate(template); setFormData({}); setShowGenerator(true) }}
                className="w-full py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg hover:shadow-pink-500/25 transition-shadow flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" />
                {t('templates.useTemplate')}
              </motion.button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Generator Modal */}
      <Modal isOpen={showGenerator} onClose={() => { setShowGenerator(false); setSelectedTemplate(null); setFormData({}) }} title={selectedTemplate?.name || t('templates.generate')} size="lg">
        {selectedTemplate && (
          <div className="space-y-6">
            <Select label={t('common.language')} value={language} onChange={(e) => setLanguage(e.target.value)}
              options={[{ value: 'pt', label: 'Português' }, { value: 'en', label: 'English' }, { value: 'es', label: 'Español' }]} />
            <div className="space-y-4">
              <h4 className="font-medium text-white">{t('templates.fillVariables')}</h4>
              {selectedTemplate.variables.map((variable) => (
                <Input key={variable} label={variable.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} value={formData[variable] || ''}
                  onChange={(e) => setFormData({ ...formData, [variable]: e.target.value })} placeholder={`${t('templates.enterVariable').replace('{variable}', variable)}`} />
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowGenerator(false)}>{t('common.cancel')}</Button>
              <Button onClick={handleGenerate}>{t('templates.generate')}</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Result Modal */}
      <Modal isOpen={showResult} onClose={() => { setShowResult(false); setGeneratedTemplate(null) }} title={t('templates.generatedDocument')} size="xl">
        {generatedTemplate && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-slate-400">{t('templates.generatedAt')}: {new Date(generatedTemplate.generated_at).toLocaleString()}</p>
                <p className="text-sm text-slate-400">{t('common.language')}: {generatedTemplate.language.toUpperCase()}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={copyToClipboard} className="px-3 py-1.5 text-xs bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors flex items-center gap-1"><Copy className="w-4 h-4" />{t('templates.copy')}</button>
                <button onClick={downloadAsText} className="px-3 py-1.5 text-xs bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors flex items-center gap-1"><Download className="w-4 h-4" />{t('templates.download')}</button>
              </div>
            </div>
            <div className="border border-white/10 rounded-lg p-4 bg-white/5 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono text-slate-300">{generatedTemplate.content}</pre>
            </div>
            <div className="flex justify-end"><Button onClick={() => setShowResult(false)}>{t('common.close')}</Button></div>
          </div>
        )}
      </Modal>
    </div>
  )
}
