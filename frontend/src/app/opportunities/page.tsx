'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Opportunity, Contact, LeadAnalysis } from '@/types'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Target, Search, Plus, LayoutGrid, LayoutList, DollarSign,
  TrendingUp, Calendar, GripVertical, ChevronRight, BarChart3
} from 'lucide-react'

export default function OpportunitiesPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'table' | 'pipeline'>('pipeline')
  const [searchTerm, setSearchTerm] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null)
  const [editingOpportunity, setEditingOpportunity] = useState<Opportunity | null>(null)
  const [leadAnalysis, setLeadAnalysis] = useState<any>(null)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [draggedItem, setDraggedItem] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '', contact_id: '', value: '', stage: 'qualificacao', probability: 0, expected_close_date: ''
  })
  const [editFormData, setEditFormData] = useState({
    name: '', contact_id: '', value: '', stage: 'qualificacao', probability: 0, expected_close_date: ''
  })

  const stages = [
    { value: 'qualificacao', label: t('opportunity.stage.qualificacao'), color: 'from-blue-500 to-blue-600', bgColor: 'bg-blue-500/20', textColor: 'text-blue-300', borderColor: 'border-blue-500/30' },
    { value: 'proposta', label: t('opportunity.stage.proposta'), color: 'from-amber-500 to-amber-600', bgColor: 'bg-amber-500/20', textColor: 'text-amber-300', borderColor: 'border-amber-500/30' },
    { value: 'negociacao', label: t('opportunity.stage.negociacao'), color: 'from-orange-500 to-orange-600', bgColor: 'bg-orange-500/20', textColor: 'text-orange-300', borderColor: 'border-orange-500/30' },
    { value: 'fechado', label: t('opportunity.stage.fechado'), color: 'from-emerald-500 to-emerald-600', bgColor: 'bg-emerald-500/20', textColor: 'text-emerald-300', borderColor: 'border-emerald-500/30' },
    { value: 'perdido', label: t('opportunity.stage.perdido'), color: 'from-red-500 to-red-600', bgColor: 'bg-red-500/20', textColor: 'text-red-300', borderColor: 'border-red-500/30' }
  ]

  const loadLeadAnalysis = async (contactId: number) => {
    setLoadingAnalysis(true)
    try {
      const response = await api.get<LeadAnalysis>(`/api/lead-analysis/${contactId}`)
      setLeadAnalysis(response.data)
    } catch (error: any) {
      if (error.response?.status !== 404) console.error('Erro ao carregar análise:', error)
      setLeadAnalysis(null)
    } finally {
      setLoadingAnalysis(false)
    }
  }

  const loadData = useCallback(async () => {
    try {
      const [oppsRes, contactsRes] = await Promise.all([
        api.get<Opportunity[]>('/api/opportunities/'),
        api.get<Contact[]>('/api/contacts/')
      ])
      setOpportunities(oppsRes.data)
      setContacts(contactsRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      toast.error(t('opportunities.errorLoad'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadData()
  }, [router, loadData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/opportunities/', {
        ...formData,
        contact_id: parseInt(formData.contact_id),
        value: formData.value ? parseFloat(formData.value) : null,
        probability: parseInt(formData.probability.toString())
      })
      setShowForm(false)
      setFormData({ name: '', contact_id: '', value: '', stage: 'qualificacao', probability: 0, expected_close_date: '' })
      loadData()
      toast.success(t('opportunities.created'))
    } catch (error) {
      console.error('Erro ao criar oportunidade:', error)
      toast.error(t('opportunities.errorCreate'))
    }
  }

  const updateStage = async (id: number, newStage: string) => {
    try {
      await api.put(`/api/opportunities/${id}`, { stage: newStage })
      loadData()
      toast.success(t('opportunities.updated'))
    } catch (error) {
      console.error('Erro ao atualizar estágio:', error)
      toast.error(t('opportunities.errorUpdate'))
    }
  }

  const handleEdit = (opp: Opportunity) => {
    setEditingOpportunity(opp)
    setEditFormData({
      name: opp.name, contact_id: opp.contact_id.toString(), value: opp.value ? opp.value.toString() : '',
      stage: opp.stage, probability: opp.probability, expected_close_date: opp.expected_close_date ? opp.expected_close_date.split('T')[0] : ''
    })
    setShowEditModal(true)
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingOpportunity) return
    try {
      await api.put(`/api/opportunities/${editingOpportunity.id}`, {
        name: editFormData.name, contact_id: parseInt(editFormData.contact_id),
        value: editFormData.value ? parseFloat(editFormData.value) : null,
        stage: editFormData.stage, probability: editFormData.probability,
        expected_close_date: editFormData.expected_close_date || null
      })
      setShowEditModal(false)
      setEditingOpportunity(null)
      loadData()
      toast.success(t('opportunities.updated'))
    } catch (error) {
      console.error('Erro ao atualizar oportunidade:', error)
      toast.error(t('opportunities.errorUpdate'))
    }
  }

  const handleDragStart = (e: React.DragEvent, opportunityId: number) => {
    setDraggedItem(opportunityId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = async (e: React.DragEvent, targetStage: string) => {
    e.preventDefault()
    if (!draggedItem) return
    const opportunity = opportunities.find(opp => opp.id === draggedItem)
    if (opportunity && opportunity.stage !== targetStage) {
      await updateStage(draggedItem, targetStage)
    }
    setDraggedItem(null)
  }

  const filteredOpportunities = useMemo(() => {
    return opportunities.filter(opp => {
      const matchesSearch = !searchTerm || opp.name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStage = stageFilter === 'all' || opp.stage === stageFilter
      return matchesSearch && matchesStage
    })
  }, [opportunities, searchTerm, stageFilter])

  const opportunitiesByStage = useMemo(() => {
    const grouped: Record<string, Opportunity[]> = {}
    stages.forEach(stage => { grouped[stage.value] = filteredOpportunities.filter(opp => opp.stage === stage.value) })
    return grouped
  }, [filteredOpportunities, stages])

  // Stats
  const stats = useMemo(() => ({
    total: opportunities.length,
    totalValue: opportunities.reduce((sum, o) => sum + (o.value || 0), 0),
    avgProbability: opportunities.length > 0 ? Math.round(opportunities.reduce((sum, o) => sum + o.probability, 0) / opportunities.length) : 0,
    closedValue: opportunities.filter(o => o.stage === 'fechado').reduce((sum, o) => sum + (o.value || 0), 0)
  }), [opportunities])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (<div key={i} className="h-24 bg-white/5 rounded-xl"></div>))}
          </div>
          <div className="h-96 bg-white/5 rounded-xl"></div>
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
              <Target className="w-8 h-8 text-purple-400" />
              {t('opportunities.title')}
            </h1>
            <p className="text-slate-400 mt-1">Sales Pipeline Management</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="flex bg-white/5 border border-white/10 rounded-lg p-1">
              <button
                onClick={() => setViewMode('pipeline')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'pipeline' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                  }`}
              >
                <LayoutGrid className="w-4 h-4" />
                Pipeline
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'table' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                  }`}
              >
                <LayoutList className="w-4 h-4" />
                Table
              </button>
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
            >
              <Plus className="w-5 h-5" />
              {t('opportunities.new')}
            </motion.button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Opportunities', value: stats.total, icon: Target, color: 'purple' },
            { label: 'Pipeline Value', value: `R$ ${stats.totalValue.toLocaleString('pt-BR')}`, icon: DollarSign, color: 'blue' },
            { label: 'Avg. Probability', value: `${stats.avgProbability}%`, icon: TrendingUp, color: 'amber' },
            { label: 'Closed Value', value: `R$ ${stats.closedValue.toLocaleString('pt-BR')}`, icon: BarChart3, color: 'emerald' }
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/[0.08] transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">{stat.label}</p>
                  <p className="text-xl lg:text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Search */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder={`${t('common.search')} opportunities...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
          </div>
        </div>

        {/* Pipeline View */}
        {viewMode === 'pipeline' && (
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-4 min-w-max">
              {stages.map((stage) => {
                const stageOpps = opportunitiesByStage[stage.value] || []
                const stageValue = stageOpps.reduce((sum, o) => sum + (o.value || 0), 0)
                return (
                  <div
                    key={stage.value}
                    className={`flex-1 min-w-[280px] bg-white/5 backdrop-blur-sm rounded-xl border ${stage.borderColor} p-4`}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, stage.value)}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${stage.bgColor} ${stage.textColor}`}>
                          {stage.label}
                        </span>
                        <span className="text-xs text-slate-500">{stageOpps.length}</span>
                      </div>
                      <span className="text-xs text-slate-400">R$ {stageValue.toLocaleString('pt-BR')}</span>
                    </div>
                    <div className="space-y-3 min-h-[200px]">
                      <AnimatePresence>
                        {stageOpps.map((opp) => (
                          <motion.div
                            key={opp.id}
                            layout
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            draggable
                            onDragStart={(e: any) => handleDragStart(e, opp.id)}
                            className={`bg-slate-800/50 border border-white/10 rounded-lg p-4 cursor-move hover:border-white/20 transition-all ${draggedItem === opp.id ? 'opacity-50 scale-95' : ''
                              }`}
                          >
                            <div className="flex items-start justify-between mb-2">
                              <GripVertical className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" />
                              <h4 className="font-medium text-white text-sm flex-1 ml-2">{opp.name}</h4>
                            </div>
                            {opp.value && (
                              <p className="text-emerald-400 font-semibold text-sm mb-2">
                                R$ {Number(opp.value).toLocaleString('pt-BR')}
                              </p>
                            )}
                            <div className="flex items-center justify-between text-xs text-slate-400">
                              <span>{opp.probability}% probability</span>
                              {opp.expected_close_date && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="w-3 h-3" />
                                  {new Date(opp.expected_close_date).toLocaleDateString('pt-BR')}
                                </span>
                              )}
                            </div>
                            <div className="mt-3 pt-3 border-t border-white/5 flex gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedOpportunity(opp)
                                  setShowDetailModal(true)
                                  loadLeadAnalysis(opp.contact_id)
                                }}
                                className="flex-1 text-xs px-3 py-1.5 bg-white/10 text-white rounded-md hover:bg-white/20 transition-colors"
                              >
                                {t('common.details')}
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleEdit(opp) }}
                                className="flex-1 text-xs px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:opacity-90 transition-opacity"
                              >
                                {t('common.edit')}
                              </button>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                      {stageOpps.length === 0 && (
                        <div className="text-center text-slate-500 text-sm py-8 border-2 border-dashed border-white/10 rounded-lg">
                          {t('opportunities.dragHere')}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Table View */}
        {viewMode === 'table' && (
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.value')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('opportunities.stage')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Probability</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Close Date</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredOpportunities.map((opp, i) => {
                    const stageInfo = stages.find(s => s.value === opp.stage) || stages[0]
                    return (
                      <motion.tr
                        key={opp.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.03 }}
                        className="hover:bg-white/[0.03] transition-colors"
                      >
                        <td className="px-6 py-4">
                          <span className="text-white font-medium">{opp.name}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-emerald-400 font-semibold">
                            {opp.value ? `R$ ${Number(opp.value).toLocaleString('pt-BR')}` : '-'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={opp.stage}
                            onChange={(e) => updateStage(opp.id, e.target.value)}
                            className={`text-xs font-medium rounded-full px-3 py-1 border cursor-pointer transition-colors ${stageInfo.bgColor} ${stageInfo.textColor} ${stageInfo.borderColor} bg-transparent`}
                          >
                            {stages.map((stage) => (
                              <option key={stage.value} value={stage.value} className="bg-slate-900">{stage.label}</option>
                            ))}
                          </select>
                        </td>
                        <td className="px-6 py-4 text-slate-400">{opp.probability}%</td>
                        <td className="px-6 py-4 text-slate-400">
                          {opp.expected_close_date ? new Date(opp.expected_close_date).toLocaleDateString('pt-BR') : '-'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setSelectedOpportunity(opp)
                                setShowDetailModal(true)
                                loadLeadAnalysis(opp.contact_id)
                              }}
                              className="px-3 py-1 text-xs bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors"
                            >
                              {t('common.details')}
                            </button>
                            <button
                              onClick={() => handleEdit(opp)}
                              className="px-3 py-1 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                            >
                              {t('common.edit')}
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {filteredOpportunities.length === 0 && (
              <div className="p-12 text-center">
                <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No opportunities found</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={t('opportunities.new')} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label={t('common.name')} type="text" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <Select label={t('opportunities.contact')} required value={formData.contact_id} onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              options={[{ value: '', label: t('common.none') }, ...contacts.map((c) => ({ value: c.id.toString(), label: `${c.name}${c.company ? ` - ${c.company}` : ''}` }))]} />
            <Input label={t('common.value')} type="number" step="0.01" value={formData.value} onChange={(e) => setFormData({ ...formData, value: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select label={t('opportunities.stage')} value={formData.stage} onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
              options={stages.map((s) => ({ value: s.value, label: s.label }))} />
            <Input label={`${t('opportunities.probability')} (%)`} type="number" min="0" max="100" value={formData.probability}
              onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) || 0 })} />
            <Input label={t('opportunities.expectedCloseDate')} type="date" value={formData.expected_close_date}
              onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })} />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>{t('common.cancel')}</Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showEditModal} onClose={() => { setShowEditModal(false); setEditingOpportunity(null) }} title={t('opportunities.edit')} size="lg">
        <form onSubmit={handleUpdate} className="space-y-4">
          <Input label={t('common.name')} type="text" required value={editFormData.name} onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <Select label={t('opportunities.contact')} required value={editFormData.contact_id} onChange={(e) => setEditFormData({ ...editFormData, contact_id: e.target.value })}
              options={[{ value: '', label: t('common.none') }, ...contacts.map((c) => ({ value: c.id.toString(), label: `${c.name}${c.company ? ` - ${c.company}` : ''}` }))]} />
            <Input label={t('common.value')} type="number" step="0.01" value={editFormData.value} onChange={(e) => setEditFormData({ ...editFormData, value: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select label={t('opportunities.stage')} value={editFormData.stage} onChange={(e) => setEditFormData({ ...editFormData, stage: e.target.value })}
              options={stages.map((s) => ({ value: s.value, label: s.label }))} />
            <Input label={`${t('opportunities.probability')} (%)`} type="number" min="0" max="100" value={editFormData.probability}
              onChange={(e) => setEditFormData({ ...editFormData, probability: parseInt(e.target.value) || 0 })} />
            <Input label={t('opportunities.expectedCloseDate')} type="date" value={editFormData.expected_close_date}
              onChange={(e) => setEditFormData({ ...editFormData, expected_close_date: e.target.value })} />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => { setShowEditModal(false); setEditingOpportunity(null) }}>{t('common.cancel')}</Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showDetailModal} onClose={() => { setShowDetailModal(false); setSelectedOpportunity(null); setLeadAnalysis(null) }}
        title={selectedOpportunity ? `${selectedOpportunity.name}` : 'Details'} size="lg">
        {selectedOpportunity && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('opportunities.contact')}</p>
                <p className="text-white font-medium">{contacts.find(c => c.id === selectedOpportunity.contact_id)?.name || '-'}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('common.value')}</p>
                <p className="text-emerald-400 font-semibold">{selectedOpportunity.value ? `R$ ${Number(selectedOpportunity.value).toLocaleString('pt-BR')}` : '-'}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('common.stage')}</p>
                <p className="text-white font-medium">{t(`opportunity.stage.${selectedOpportunity.stage}`)}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('opportunities.probability')}</p>
                <p className="text-white font-medium">{selectedOpportunity.probability}%</p>
              </div>
            </div>

            {loadingAnalysis ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
              </div>
            ) : leadAnalysis && leadAnalysis.analysis_status === 'completed' && (
              <div className="border-t border-white/10 pt-6">
                <h3 className="font-bold text-white mb-4">{t('contacts.leadAnalysis')}</h3>
                {leadAnalysis.opportunity_score !== null && (
                  <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">{t('contacts.opportunityScore')}</span>
                      <span className="text-3xl font-bold text-white">{leadAnalysis.opportunity_score}/100</span>
                    </div>
                  </div>
                )}
                {leadAnalysis.recommendations && (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                    <h4 className="font-semibold text-emerald-300 mb-2">{t('contacts.recommendations')}</h4>
                    <p className="text-emerald-200 text-sm whitespace-pre-wrap">{leadAnalysis.recommendations}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
