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
    if (!token) {
      router.push('/login')
      return
    }
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
      const response = await api.post('/api/templates/generate', {
        template_type: selectedTemplate.id,
        data: formData,
        language
      })

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
      toast.success('Conteúdo copiado para a área de transferência!')
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
      <div className="flex items-center justify-center min-h-screen">
        <div className="space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">{t('templates.title')}</h2>
        <p className="text-gray-600 mt-2">{t('templates.description')}</p>
      </div>

      {/* Lista de Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">{template.name}</h3>
            <p className="text-gray-600 mb-4">{template.description}</p>

            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">{t('templates.variables')}:</p>
              <div className="flex flex-wrap gap-1">
                {template.variables.map((variable) => (
                  <span
                    key={variable}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                  >
                    {variable}
                  </span>
                ))}
              </div>
            </div>

            <Button
              onClick={() => {
                setSelectedTemplate(template)
                setFormData({})
                setShowGenerator(true)
              }}
              className="w-full"
            >
              {t('templates.useTemplate')}
            </Button>
          </div>
        ))}
      </div>

      {/* Modal de Geração */}
      <Modal
        isOpen={showGenerator}
        onClose={() => {
          setShowGenerator(false)
          setSelectedTemplate(null)
          setFormData({})
        }}
        title={selectedTemplate?.name || t('templates.generate')}
        size="lg"
      >
        {selectedTemplate && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('common.language')}
              </label>
              <Select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                options={[
                  { value: 'pt', label: 'Português' },
                  { value: 'en', label: 'English' },
                  { value: 'es', label: 'Español' }
                ]}
              />
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">{t('templates.fillVariables')}</h4>
              {selectedTemplate.variables.map((variable) => (
                <Input
                  key={variable}
                  label={variable.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  value={formData[variable] || ''}
                  onChange={(e) => setFormData({ ...formData, [variable]: e.target.value })}
                  placeholder={t('templates.enterVariable', { variable })}
                />
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => setShowGenerator(false)}
              >
                {t('common.cancel')}
              </Button>
              <Button onClick={handleGenerate}>
                {t('templates.generate')}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal de Resultado */}
      <Modal
        isOpen={showResult}
        onClose={() => {
          setShowResult(false)
          setGeneratedTemplate(null)
        }}
        title={t('templates.generatedDocument')}
        size="xl"
      >
        {generatedTemplate && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">
                  {t('templates.generatedAt')}: {new Date(generatedTemplate.generated_at).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">
                  {t('common.language')}: {generatedTemplate.language.toUpperCase()}
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={copyToClipboard}>
                  {t('templates.copy')}
                </Button>
                <Button variant="outline" size="sm" onClick={downloadAsText}>
                  {t('templates.download')}
                </Button>
              </div>
            </div>

            <div className="border rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono">
                {generatedTemplate.content}
              </pre>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setShowResult(false)}>
                {t('common.close')}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
