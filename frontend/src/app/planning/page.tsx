'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Textarea from '@/components/Textarea'
import { motion } from 'framer-motion'
import { ClipboardList, Clock, CheckCircle, Sparkles, Loader2, FileText, Calendar } from 'lucide-react'

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
  technical_details?: string | null
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
  const [generatingAI, setGeneratingAI] = useState(false)
  const [formData, setFormData] = useState({
    technical_details: '', technologies: '', deadlines: '', stages: '', estimated_hours: ''
  })

  const statusConfig: Record<string, { label: string; color: string; bgColor: string; icon: React.ComponentType<any> }> = {
    pending: { label: t('planning.pending'), color: 'text-amber-300', bgColor: 'bg-amber-500/20', icon: Clock },
    in_progress: { label: t('planning.inProgress'), color: 'text-blue-300', bgColor: 'bg-blue-500/20', icon: ClipboardList },
    completed: { label: t('planning.completed'), color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', icon: CheckCircle }
  }

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
    if (!token) { router.push('/login'); return }
    loadQuoteRequests()
  }, [router, loadQuoteRequests])

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
      setFormData({
        technical_details: data.technical_specs || '',
        technologies: Array.isArray(data.technologies) ? data.technologies.join(', ') : (data.technologies || ''),
        deadlines: data.deadlines || '',
        stages: data.stages || '',
        estimated_hours: data.estimated_hours?.toString() || ''
      })
      toast.success(t('planning.aiGenerated'))
      loadQuoteRequests()
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

  // Stats
  const stats = useMemo(() => ({
    total: quoteRequests.length,
    pending: quoteRequests.filter(r => r.status === 'pending').length,
    inProgress: quoteRequests.filter(r => r.status === 'in_progress').length,
    completed: quoteRequests.filter(r => r.status === 'completed').length
  }), [quoteRequests])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (<div key={i} className="h-24 bg-white/5 rounded-xl"></div>))}
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
            <ClipboardList className="w-8 h-8 text-purple-400" />
            {t('planning.title')}
          </h1>
          <p className="text-slate-400 mt-1">{t('planning.quoteRequests')}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Requests', value: stats.total, icon: FileText, color: 'purple' },
            { label: 'Pending', value: stats.pending, icon: Clock, color: 'amber' },
            { label: 'In Progress', value: stats.inProgress, icon: ClipboardList, color: 'blue' },
            { label: 'Completed', value: stats.completed, icon: CheckCircle, color: 'emerald' }
          ].map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/[0.08] transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('projects.title')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.status')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.date')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {quoteRequests.map((request, i) => {
                  const status = statusConfig[request.status] || statusConfig.pending
                  return (
                    <motion.tr key={request.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                      className="hover:bg-white/[0.03] transition-colors">
                      <td className="px-6 py-4 text-white font-medium">{request.project_name}</td>
                      <td className="px-6 py-4 text-slate-400">{request.seller_name || request.requested_by_name}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${status.bgColor} ${status.color}`}>{status.label}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-400">{new Date(request.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4">
                        {request.status !== 'completed' && (
                          <button onClick={() => handleFillQuote(request)}
                            className="px-3 py-1.5 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity">
                            {t('planning.fillQuote')}
                          </button>
                        )}
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {quoteRequests.length === 0 && (
            <div className="p-12 text-center">
              <ClipboardList className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">{t('planning.noRequests')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setSelectedRequest(null) }} title={t('planning.fillQuote')} size="xl">
        {selectedRequest && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg">
              <p className="text-sm font-medium text-blue-300">{t('projects.title')}: {selectedRequest.project_name}</p>
              <p className="text-sm text-blue-200">{t('common.name')}: {selectedRequest.seller_name || selectedRequest.requested_by_name}</p>
            </div>
            <Textarea label={t('planning.technicalDetails')} value={formData.technical_details} onChange={(e) => setFormData({ ...formData, technical_details: e.target.value })} rows={4} />
            <Input label={t('planning.technologies')} type="text" value={formData.technologies} onChange={(e) => setFormData({ ...formData, technologies: e.target.value })} placeholder={t('planning.technologiesPlaceholder')} />
            <Textarea label={t('planning.deadlines')} value={formData.deadlines} onChange={(e) => setFormData({ ...formData, deadlines: e.target.value })} rows={3} />
            <Textarea label={t('planning.stages')} value={formData.stages} onChange={(e) => setFormData({ ...formData, stages: e.target.value })} rows={3} />
            <Input label={t('planning.estimatedHours')} type="number" value={formData.estimated_hours} onChange={(e) => setFormData({ ...formData, estimated_hours: e.target.value })} />
            <div className="flex justify-between items-center mt-6">
              <Button type="button" variant="outline" onClick={handleGenerateWithAI} disabled={generatingAI} className="flex items-center gap-2">
                {generatingAI ? (<><Loader2 className="w-4 h-4 animate-spin" />{t('planning.generatingAI')}</>) : (<><Sparkles className="w-4 h-4" />{t('planning.generateWithAI')}</>)}
              </Button>
              <div className="flex gap-3">
                <Button type="button" variant="outline" onClick={() => { setShowForm(false); setSelectedRequest(null) }}>{t('common.cancel')}</Button>
                <Button type="submit">{t('planning.complete')}</Button>
              </div>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
