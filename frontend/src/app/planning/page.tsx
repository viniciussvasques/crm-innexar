'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Textarea from '@/components/Textarea'
import Select from '@/components/Select'

interface QuoteRequest {
  id: number
  project_id: number
  project_name: string
  seller_id: number
  seller_name: string
  requested_by_id?: number
  requested_by_name?: string
  status: 'pending' | 'in_progress' | 'completed'
  technical_specs: string | null
  technical_details?: string | null // Alias para technical_specs
  technologies: string[] | string | null
  deadlines?: string | null
  stages: string | null
  estimated_hours: number | null
  created_at: string
  completed_at: string | null
}

export default function PlanningPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [quoteRequests, setQuoteRequests] = useState<QuoteRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRequest, setSelectedRequest] = useState<QuoteRequest | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    technical_details: '',
    technologies: '',
    deadlines: '',
    stages: '',
    estimated_hours: ''
  })

  const loadQuoteRequests = useCallback(async () => {
    try {
      const response = await api.get('/api/quote-requests/')
      setQuoteRequests(response.data)
    } catch (error) {
      console.error('Erro ao carregar solicitações:', error)
      toast.error('Erro ao carregar solicitações')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
    loadQuoteRequests()
  }, [router, loadQuoteRequests])

  const [generatingAI, setGeneratingAI] = useState(false)

  const handleFillQuote = (request: QuoteRequest) => {
    setSelectedRequest(request)
    setFormData({
      technical_details: request.technical_specs || request.technical_details || '',
      technologies: Array.isArray(request.technologies) ? request.technologies.join(', ') : (request.technologies || ''),
      deadlines: request.deadlines || '',
      stages: request.stages || '',
      estimated_hours: request.estimated_hours?.toString() || ''
    })
    setShowForm(true)
  }

  const handleGenerateWithAI = async () => {
    if (!selectedRequest) return
    
    setGeneratingAI(true)
    try {
      const response = await api.post(`/api/quote-requests/${selectedRequest.id}/generate-with-ai`)
      const data = response.data
      
      // Preencher formulário com dados gerados pela IA
      setFormData({
        technical_details: data.technical_specs || '',
        technologies: Array.isArray(data.technologies) ? data.technologies.join(', ') : (data.technologies || ''),
        deadlines: data.deadlines || '',
        stages: data.stages || '',
        estimated_hours: data.estimated_hours?.toString() || ''
      })
      
      toast.success(t('planning.aiGenerated'))
      loadQuoteRequests() // Recarregar para atualizar status
    } catch (error) {
      console.error('Erro ao gerar com IA:', error)
      toast.error(t('planning.aiError'))
    } finally {
      setGeneratingAI(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRequest) return

    try {
      await api.put(`/api/quote-requests/${selectedRequest.id}/complete`, {
        technical_details: formData.technical_details,
        technologies: formData.technologies,
        deadlines: formData.deadlines,
        stages: formData.stages,
        estimated_hours: formData.estimated_hours ? parseInt(formData.estimated_hours) : null
      })
      setShowForm(false)
      setSelectedRequest(null)
      loadQuoteRequests()
      toast.success(t('planning.completed'))
    } catch (error) {
      console.error('Erro ao completar orçamento:', error)
      toast.error('Erro ao completar orçamento')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return t('planning.completed')
      case 'in_progress': return t('planning.inProgress')
      default: return t('planning.pending')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">{t('planning.title')}</h2>
        <p className="mt-2 text-gray-600">{t('planning.quoteRequests')}</p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('projects.title')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {quoteRequests.map((request) => (
              <tr key={request.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {request.project_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {request.seller_name || request.requested_by_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                    {getStatusLabel(request.status)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(request.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {request.status !== 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFillQuote(request)}
                    >
                      {t('planning.fillQuote')}
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {quoteRequests.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {t('planning.noRequests')}
          </div>
        )}
      </div>

      {/* Modal de Preenchimento */}
      <Modal
        isOpen={showForm}
        onClose={() => {
          setShowForm(false)
          setSelectedRequest(null)
        }}
        title={t('planning.fillQuote')}
        size="xl"
      >
        {selectedRequest && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-blue-900">{t('projects.title')}: {selectedRequest.project_name}</p>
              <p className="text-sm text-blue-700">{t('common.name')}: {selectedRequest.seller_name || selectedRequest.requested_by_name}</p>
            </div>

            <Textarea
              label={t('planning.technicalDetails')}
              value={formData.technical_details}
              onChange={(e) => setFormData({ ...formData, technical_details: e.target.value })}
              rows={4}
            />

            <Input
              label={t('planning.technologies')}
              type="text"
              value={formData.technologies}
              onChange={(e) => setFormData({ ...formData, technologies: e.target.value })}
              placeholder={t('planning.technologiesPlaceholder')}
            />

            <Textarea
              label={t('planning.deadlines')}
              value={formData.deadlines}
              onChange={(e) => setFormData({ ...formData, deadlines: e.target.value })}
              rows={3}
              placeholder={t('planning.deadlinesPlaceholder')}
            />

            <Textarea
              label={t('planning.stages')}
              value={formData.stages}
              onChange={(e) => setFormData({ ...formData, stages: e.target.value })}
              rows={3}
            />

            <Input
              label={t('planning.estimatedHours')}
              type="number"
              value={formData.estimated_hours}
              onChange={(e) => setFormData({ ...formData, estimated_hours: e.target.value })}
            />

            <div className="flex justify-between items-center mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={handleGenerateWithAI}
                disabled={generatingAI}
                className="flex items-center gap-2"
              >
                {generatingAI ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                    {t('planning.generatingAI')}
                  </>
                ) : (
                  <>
                    🤖 {t('planning.generateWithAI')}
                  </>
                )}
              </Button>
              
              <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowForm(false)
                  setSelectedRequest(null)
                }}
              >
                {t('common.cancel')}
              </Button>
                <Button type="submit">
                  {t('planning.complete')}
                </Button>
              </div>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}

