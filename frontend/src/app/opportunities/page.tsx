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
    name: '',
    contact_id: '',
    value: '',
    stage: 'qualificacao',
    probability: 0,
    expected_close_date: ''
  })
  const [editFormData, setEditFormData] = useState({
    name: '',
    contact_id: '',
    value: '',
    stage: 'qualificacao',
    probability: 0,
    expected_close_date: ''
  })

  const stages = [
    { value: 'qualificacao', label: t('opportunity.stage.qualificacao'), color: 'bg-blue-100 text-blue-800', borderColor: 'border-blue-300' },
    { value: 'proposta', label: t('opportunity.stage.proposta'), color: 'bg-yellow-100 text-yellow-800', borderColor: 'border-yellow-300' },
    { value: 'negociacao', label: t('opportunity.stage.negociacao'), color: 'bg-orange-100 text-orange-800', borderColor: 'border-orange-300' },
    { value: 'fechado', label: t('opportunity.stage.fechado'), color: 'bg-green-100 text-green-800', borderColor: 'border-green-300' },
    { value: 'perdido', label: t('opportunity.stage.perdido'), color: 'bg-red-100 text-red-800', borderColor: 'border-red-300' }
  ]

  const loadLeadAnalysis = async (contactId: number) => {
    setLoadingAnalysis(true)
    try {
      const response = await api.get<LeadAnalysis>(`/api/lead-analysis/${contactId}`)
      setLeadAnalysis(response.data)
    } catch (error: any) {
      if (error.response?.status !== 404) {
        console.error('Erro ao carregar análise:', error)
      }
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
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
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
      setFormData({
        name: '',
        contact_id: '',
        value: '',
        stage: 'qualificacao',
        probability: 0,
        expected_close_date: ''
      })
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
      name: opp.name,
      contact_id: opp.contact_id.toString(),
      value: opp.value ? opp.value.toString() : '',
      stage: opp.stage,
      probability: opp.probability,
      expected_close_date: opp.expected_close_date ? opp.expected_close_date.split('T')[0] : ''
    })
    setShowEditModal(true)
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingOpportunity) return

    try {
      await api.put(`/api/opportunities/${editingOpportunity.id}`, {
        name: editFormData.name,
        contact_id: parseInt(editFormData.contact_id),
        value: editFormData.value ? parseFloat(editFormData.value) : null,
        stage: editFormData.stage,
        probability: editFormData.probability,
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

  // Drag and Drop handlers
  const handleDragStart = (e: React.DragEvent, opportunityId: number) => {
    setDraggedItem(opportunityId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/html', '')
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

  // Filtros e busca
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter(opp => {
      const matchesSearch = !searchTerm || 
        opp.name.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStage = stageFilter === 'all' || opp.stage === stageFilter
      
      return matchesSearch && matchesStage
    })
  }, [opportunities, searchTerm, stageFilter])

  // Agrupar por estágio para o pipeline
  const opportunitiesByStage = useMemo(() => {
    const grouped: Record<string, Opportunity[]> = {}
    stages.forEach(stage => {
      grouped[stage.value] = filteredOpportunities.filter(opp => opp.stage === stage.value)
    })
    return grouped
  }, [filteredOpportunities])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">{t('opportunities.title')}</h2>
        <div className="flex gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('pipeline')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'pipeline'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t('opportunities.viewPipeline')}
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'table'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t('opportunities.viewTable')}
            </button>
          </div>
          <Button onClick={() => setShowForm(true)}>
            + {t('opportunities.new')}
          </Button>
        </div>
      </div>

      {/* Busca e Filtros */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.search')}</label>
            <input
              type="text"
              placeholder={`${t('opportunities.title')}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          {viewMode === 'table' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('opportunities.stage')}</label>
              <select
                value={stageFilter}
                onChange={(e) => setStageFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">{t('common.all')}</option>
                {stages.map((stage) => (
                  <option key={stage.value} value={stage.value}>
                    {stage.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Criação */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={t('opportunities.new')}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label={t('common.name')}
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('opportunities.contact')}
              required
              value={formData.contact_id}
              onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              options={[
                { value: '', label: t('common.none') },
                ...contacts.map((contact) => ({
                  value: contact.id.toString(),
                  label: `${contact.name}${contact.company ? ` - ${contact.company}` : ''}`
                }))
              ]}
            />
            <Input
              label={t('common.value')}
              type="number"
              step="0.01"
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select
              label={t('opportunities.stage')}
              value={formData.stage}
              onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
              options={stages.map((stage) => ({
                value: stage.value,
                label: stage.label
              }))}
            />
            <Input
              label={`${t('opportunities.probability')} (%)`}
              type="number"
              min="0"
              max="100"
              value={formData.probability}
              onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) || 0 })}
            />
            <Input
              label={t('opportunities.expectedCloseDate')}
              type="date"
              value={formData.expected_close_date}
              onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit">
              {t('common.save')}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Visualização Pipeline (Kanban) */}
      {viewMode === 'pipeline' && (
        <div className="overflow-x-auto">
          <div className="flex gap-4 min-w-max pb-4">
            {stages.map((stage) => {
              const stageOpps = opportunitiesByStage[stage.value] || []
              return (
                <div
                  key={stage.value}
                  className={`flex-1 min-w-[280px] bg-gray-50 rounded-lg border-2 ${stage.borderColor} p-4`}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, stage.value)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className={`font-semibold text-sm px-3 py-1 rounded-full ${stage.color}`}>
                      {stage.label}
                    </h3>
                    <span className="text-sm text-gray-500 bg-white px-2 py-1 rounded-full">
                      {stageOpps.length}
                    </span>
                  </div>
                  <div className="space-y-3 min-h-[200px]">
                    {stageOpps.map((opp) => {
                      const isDragging = draggedItem === opp.id
                      return (
                        <div
                          key={opp.id}
                          draggable
                          onDragStart={(e) => handleDragStart(e, opp.id)}
                          className={`bg-white rounded-lg shadow-sm p-4 cursor-move hover:shadow-md transition-all ${
                            isDragging ? 'opacity-50' : ''
                          }`}
                        >
                          <div className="font-medium text-sm text-gray-900 mb-2">
                            {opp.name}
                          </div>
                          {opp.value && (
                            <div className="text-xs text-gray-600 mb-1">
                              {t('common.value')}: {Number(opp.value).toLocaleString('pt-BR', { minimumFractionDigits: 2, style: 'currency', currency: 'BRL' })}
                            </div>
                          )}
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-gray-500">
                              {opp.probability}%
                            </span>
                            {opp.expected_close_date && (
                              <span className="text-xs text-gray-500">
                                {new Date(opp.expected_close_date).toLocaleDateString('pt-BR')}
                              </span>
                            )}
                          </div>
                          <div className="mt-3 pt-3 border-t border-gray-200 flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setSelectedOpportunity(opp)
                                setShowDetailModal(true)
                                loadLeadAnalysis(opp.contact_id)
                              }}
                              className="flex-1 text-xs px-3 py-1.5 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors"
                            >
                              {t('common.details')}
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleEdit(opp)
                              }}
                              className="flex-1 text-xs px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                              {t('common.edit')}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                    {stageOpps.length === 0 && (
                      <div className="text-center text-gray-400 text-sm py-8">
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

      {/* Visualização Tabela */}
      {viewMode === 'table' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.name')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.value')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('opportunities.stage')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('opportunities.probability')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('opportunities.expectedCloseDate')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredOpportunities.map((opp) => {
                const stageInfo = stages.find(s => s.value === opp.stage) || stages[0]
                return (
                  <tr key={opp.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {opp.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {opp.value ? Number(opp.value).toLocaleString('pt-BR', { minimumFractionDigits: 2, style: 'currency', currency: 'BRL' }) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={opp.stage}
                        onChange={(e) => updateStage(opp.id, e.target.value)}
                        className={`text-xs font-medium rounded-full px-3 py-1 border-0 cursor-pointer transition-colors ${stageInfo.color} hover:opacity-80`}
                      >
                        {stages.map((stage) => (
                          <option key={stage.value} value={stage.value}>
                            {stage.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {opp.probability}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {opp.expected_close_date ? new Date(opp.expected_close_date).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => {
                            setSelectedOpportunity(opp)
                            setShowDetailModal(true)
                            loadLeadAnalysis(opp.contact_id)
                          }}
                          className="text-primary hover:text-primary-dark transition-colors"
                        >
                          {t('common.details')}
                        </button>
                        <button 
                          onClick={() => handleEdit(opp)}
                          className="text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          {t('common.edit')}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {filteredOpportunities.length === 0 && opportunities.length > 0 && (
            <div className="p-8 text-center text-gray-500">
              Nenhuma oportunidade encontrada com os filtros aplicados.
            </div>
          )}
          {opportunities.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              Nenhuma oportunidade encontrada. Crie sua primeira oportunidade!
            </div>
          )}
        </div>
      )}

      {/* Modal de Detalhes da Oportunidade */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false)
          setSelectedOpportunity(null)
          setLeadAnalysis(null)
        }}
        title={selectedOpportunity ? `${t('opportunities.details')} - ${selectedOpportunity.name}` : t('opportunities.details')}
        size="lg"
      >
        {selectedOpportunity && (
          <div className="space-y-6">
            {/* Informações Básicas */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('opportunities.contact')}</h4>
                <p className="text-gray-700">
                  {contacts.find(c => c.id === selectedOpportunity.contact_id)?.name || '-'}
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('common.value')}</h4>
                <p className="text-gray-700">
                  {selectedOpportunity.value ? Number(selectedOpportunity.value).toLocaleString('pt-BR', { minimumFractionDigits: 2, style: 'currency', currency: 'BRL' }) : '-'}
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('common.stage')}</h4>
                <p className="text-gray-700">{t(`opportunity.stage.${selectedOpportunity.stage}`)}</p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('opportunities.probability')}</h4>
                <p className="text-gray-700">{selectedOpportunity.probability}%</p>
              </div>
            </div>

            {/* Análise do Lead */}
            {loadingAnalysis ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                <p className="mt-2 text-sm text-gray-600">{t('contacts.loadingAnalysis')}</p>
              </div>
            ) : leadAnalysis && leadAnalysis.analysis_status === 'completed' ? (
              <div className="border-t pt-6">
                <h3 className="font-bold text-lg mb-4 text-gray-900">{t('contacts.leadAnalysis')}</h3>
                
                {leadAnalysis.opportunity_score !== null && (
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white mb-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-lg">{t('contacts.opportunityScore')}</span>
                      <span className="text-4xl font-bold">{leadAnalysis.opportunity_score}/100</span>
                    </div>
                    {leadAnalysis.analysis_metadata?.potential_value && (
                      <div className="mt-2 text-blue-100">
                        {t('contacts.potentialValue')}: <span className="font-bold text-white">R$ {Number(leadAnalysis.analysis_metadata.potential_value).toLocaleString('pt-BR')}</span>
                      </div>
                    )}
                  </div>
                )}

                {leadAnalysis.company_info && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">{t('contacts.companyInfo')}</h4>
                    <p className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">{leadAnalysis.company_info}</p>
                  </div>
                )}

                {leadAnalysis.market_analysis && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">{t('contacts.marketAnalysis')}</h4>
                    <p className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">{leadAnalysis.market_analysis}</p>
                  </div>
                )}

                {leadAnalysis.financial_insights && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">{t('contacts.financialInsights')}</h4>
                    <p className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">{leadAnalysis.financial_insights}</p>
                  </div>
                )}

                {leadAnalysis.recommendations && (
                  <div className="bg-green-50 rounded-lg p-4 mb-4 border border-green-200">
                    <h4 className="font-semibold text-green-900 mb-2">{t('contacts.recommendations')}</h4>
                    <p className="text-green-800 whitespace-pre-wrap text-sm leading-relaxed">{leadAnalysis.recommendations}</p>
                  </div>
                )}

                {leadAnalysis.risk_assessment && (
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <h4 className="font-semibold text-yellow-900 mb-2">{t('contacts.riskAssessment')}</h4>
                    <p className="text-yellow-800 whitespace-pre-wrap text-sm leading-relaxed">{leadAnalysis.risk_assessment}</p>
                  </div>
                )}
              </div>
            ) : leadAnalysis && leadAnalysis.analysis_status === 'pending' ? (
              <div className="border-t pt-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-800">{t('contacts.analysisPending')}</p>
                </div>
              </div>
            ) : (
              <div className="border-t pt-6">
                <p className="text-gray-500 text-sm">{t('contacts.noAnalysis')}</p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Modal de Edição */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingOpportunity(null)
        }}
        title={t('opportunities.edit')}
        size="lg"
      >
        <form onSubmit={handleUpdate} className="space-y-4">
          <Input
            label={t('common.name')}
            type="text"
            required
            value={editFormData.name}
            onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('opportunities.contact')}
              required
              value={editFormData.contact_id}
              onChange={(e) => setEditFormData({ ...editFormData, contact_id: e.target.value })}
              options={[
                { value: '', label: t('common.none') },
                ...contacts.map((contact) => ({
                  value: contact.id.toString(),
                  label: `${contact.name}${contact.company ? ` - ${contact.company}` : ''}`
                }))
              ]}
            />
            <Input
              label={t('common.value')}
              type="number"
              step="0.01"
              value={editFormData.value}
              onChange={(e) => setEditFormData({ ...editFormData, value: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select
              label={t('opportunities.stage')}
              value={editFormData.stage}
              onChange={(e) => setEditFormData({ ...editFormData, stage: e.target.value })}
              options={stages.map((stage) => ({
                value: stage.value,
                label: stage.label
              }))}
            />
            <Input
              label={`${t('opportunities.probability')} (%)`}
              type="number"
              min="0"
              max="100"
              value={editFormData.probability}
              onChange={(e) => setEditFormData({ ...editFormData, probability: parseInt(e.target.value) || 0 })}
            />
            <Input
              label={t('opportunities.expectedCloseDate')}
              type="date"
              value={editFormData.expected_close_date}
              onChange={(e) => setEditFormData({ ...editFormData, expected_close_date: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowEditModal(false)
                setEditingOpportunity(null)
              }}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit">
              {t('common.save')}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
