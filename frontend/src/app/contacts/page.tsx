'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Contact } from '@/types'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ContactsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [selectedContactId, setSelectedContactId] = useState<number | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [analyses, setAnalyses] = useState<Record<number, any>>({})
  const [opportunitiesCreated, setOpportunitiesCreated] = useState<Set<number>>(new Set())
  const [showCreateOpportunity, setShowCreateOpportunity] = useState(false)
  const [opportunityFormData, setOpportunityFormData] = useState({
    name: '',
    value: '',
    stage: 'qualificacao',
    probability: 50
  })
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    status: 'lead',
    project_type: '',
    budget_range: '',
    timeline: '',
    website: '',
    linkedin: '',
    position: '',
    industry: '',
    company_size: '',
    source: 'manual'
  })

  const loadContacts = useCallback(async () => {
    try {
      const response = await api.get<Contact[]>('/api/contacts/')
      setContacts(response.data)
      
      // Carregar análises para leads (apenas se existirem)
      const leadContacts = response.data.filter(c => c.status === 'lead')
      const analysesData: Record<number, any> = {}
      for (const contact of leadContacts) {
        try {
          const analysisResponse = await api.get(`/api/lead-analysis/${contact.id}`)
          if (analysisResponse.data && analysisResponse.data.analysis_status) {
            analysesData[contact.id] = analysisResponse.data
          }
        } catch (error: any) {
          // Análise não existe ainda (404) ou outro erro - ignorar silenciosamente
          if (error.response?.status !== 404) {
            console.warn(`Erro ao carregar análise para contato ${contact.id}:`, error)
          }
        }
      }
      setAnalyses(analysesData)
    } catch (error) {
      console.error('Erro ao carregar contatos:', error)
      toast.error(t('contacts.errorLoad'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
    loadContacts()
  }, [router, loadContacts])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/contacts/', formData)
      setShowForm(false)
      const wasLead = formData.status === 'lead'
      setFormData({ 
        name: '', 
        email: '', 
        phone: '', 
        company: '', 
        status: 'lead',
        project_type: '',
        budget_range: '',
        timeline: '',
        website: '',
        linkedin: '',
        position: '',
        industry: '',
        company_size: '',
        source: 'manual'
      })
      
      // Recarregar contatos (a análise será iniciada automaticamente pelo backend se for lead)
      await loadContacts()
      
      if (wasLead) {
        toast.success(t('contacts.created') + ' ' + t('contacts.analysisWillStart'))
      } else {
        toast.success(t('contacts.created'))
      }
    } catch (error) {
      console.error('Erro ao criar contato:', error)
      toast.error(t('contacts.errorCreate'))
    }
  }

  const handleViewAnalysis = async (contactId: number) => {
    setSelectedContactId(contactId)
    setLoadingAnalysis(true)
    setShowAnalysis(true)
    try {
      const response = await api.get(`/api/lead-analysis/${contactId}`)
      setAnalysis(response.data)
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Análise não existe, tentar iniciar
        try {
          await api.post(`/api/lead-analysis/${contactId}`)
          toast.success(t('contacts.analysisStarted'))
          // Aguardar um pouco e tentar novamente
          setTimeout(async () => {
            try {
              const retryResponse = await api.get(`/api/lead-analysis/${contactId}`)
              setAnalysis(retryResponse.data)
            } catch (retryError) {
              setAnalysis({ analysis_status: 'pending', message: t('contacts.analysisPending') })
            }
          }, 2000)
        } catch (startError) {
          toast.error(t('contacts.analysisError'))
          setAnalysis(null)
        }
      } else {
        console.error('Erro ao carregar análise:', error)
        toast.error(t('contacts.analysisError'))
        setAnalysis(null)
      }
    } finally {
      setLoadingAnalysis(false)
    }
  }

  // Filtros e busca
  const filteredContacts = useMemo(() => {
    return contacts.filter(contact => {
      const matchesSearch = !searchTerm || 
        contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (contact.email && contact.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (contact.company && contact.company.toLowerCase().includes(searchTerm.toLowerCase()))
      
      const matchesStatus = statusFilter === 'all' || contact.status === statusFilter
      
      return matchesSearch && matchesStatus
    })
  }, [contacts, searchTerm, statusFilter])

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
        <h2 className="text-3xl font-bold text-gray-900">{t('contacts.title')}</h2>
        <Button onClick={() => setShowForm(true)}>
          + {t('contacts.new')}
        </Button>
      </div>

      {/* Cards de Análise Disponível */}
      {contacts.filter(c => 
        c.status === 'lead' && 
        analyses[c.id]?.analysis_status === 'completed' &&
        !opportunitiesCreated.has(c.id)
      ).length > 0 && (
        <div className="mb-6 space-y-3">
          {contacts
            .filter(c => 
              c.status === 'lead' && 
              analyses[c.id]?.analysis_status === 'completed' &&
              !opportunitiesCreated.has(c.id)
            )
            .map(contact => (
              <div
                key={contact.id}
                className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg p-4 text-white animate-pulse cursor-pointer hover:shadow-xl transition-all transform hover:scale-[1.02]"
                onClick={() => handleViewAnalysis(contact.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">📊</span>
                      <h3 className="font-bold text-lg">{t('contacts.analysisReady')} - {contact.name}</h3>
                    </div>
                    <p className="text-blue-100 text-sm">{contact.company || contact.email}</p>
                    {analyses[contact.id]?.opportunity_score && (
                      <div className="mt-2 flex items-center gap-4">
                        <span className="text-sm">
                          {t('contacts.opportunityScore')}: <span className="font-bold text-xl">{analyses[contact.id].opportunity_score}/100</span>
                        </span>
                        {analyses[contact.id]?.analysis_metadata?.potential_value && (
                          <span className="text-sm">
                            {t('contacts.potentialValue')}: <span className="font-bold">R$ {Number(analyses[contact.id].analysis_metadata.potential_value).toLocaleString('pt-BR')}</span>
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button variant="secondary" size="sm" onClick={() => handleViewAnalysis(contact.id)}>
                      {t('contacts.viewFullAnalysis')}
                    </Button>
                    <Button variant="primary" size="sm" onClick={() => {
                      setSelectedContactId(contact.id)
                      setOpportunityFormData({
                        name: `${contact.company || contact.name} - Oportunidade`,
                        value: analyses[contact.id]?.analysis_metadata?.potential_value?.toString() || '',
                        stage: 'qualificacao',
                        probability: analyses[contact.id]?.opportunity_score || 50
                      })
                      setShowCreateOpportunity(true)
                    }}>
                      + {t('contacts.createOpportunity')}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Busca e Filtros */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.search')}</label>
            <input
              type="text"
              placeholder={`${t('common.name')}, ${t('common.email')} ou ${t('common.company')}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.status')}</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">{t('common.all')}</option>
              <option value="lead">{t('contacts.lead')}</option>
              <option value="prospect">{t('contacts.prospect')}</option>
              <option value="client">{t('contacts.client')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Modal de Criação */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={t('contacts.new')}
        size="md"
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
            <Input
              label={t('common.email')}
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Input
              label={t('common.phone')}
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
          <Input
            label={t('common.company')}
            type="text"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          />
          <Select
            label={t('common.status')}
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            options={[
              { value: 'lead', label: t('contacts.lead') },
              { value: 'prospect', label: t('contacts.prospect') },
              { value: 'client', label: t('contacts.client') }
            ]}
          />
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

      {/* Lista de Contatos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.email')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.phone')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.company')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredContacts.map((contact) => (
              <tr key={contact.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {contact.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contact.email || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contact.phone || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contact.company || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${
                    contact.status === 'lead' ? 'bg-blue-100 text-blue-800' :
                    contact.status === 'prospect' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {contact.status === 'lead' ? t('contacts.lead') :
                     contact.status === 'prospect' ? t('contacts.prospect') :
                     t('contacts.client')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    {contact.status === 'lead' && (
                      <>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleViewAnalysis(contact.id)}
                        >
                          {analyses[contact.id]?.analysis_status === 'completed' ? '📊 ' : ''}
                          {t('contacts.viewAnalysis')}
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            setSelectedContactId(contact.id)
                            setOpportunityFormData({
                              name: `${contact.company || contact.name} - Oportunidade`,
                              value: analyses[contact.id]?.analysis_metadata?.potential_value?.toString() || '',
                              stage: 'qualificacao',
                              probability: analyses[contact.id]?.opportunity_score || 50
                            })
                            setShowCreateOpportunity(true)
                          }}
                        >
                          + {t('contacts.createOpportunity')}
                        </Button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredContacts.length === 0 && contacts.length > 0 && (
          <div className="p-8 text-center text-gray-500">
            {t('contacts.noFiltered')}
          </div>
        )}
        {contacts.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {t('contacts.noContacts')}
          </div>
        )}
      </div>

      {/* Modal de Análise */}
      <Modal
        isOpen={showAnalysis}
        onClose={() => {
          setShowAnalysis(false)
          setAnalysis(null)
          setSelectedContactId(null)
        }}
        title={t('contacts.leadAnalysis')}
        size="lg"
      >
        {loadingAnalysis ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">{t('contacts.loadingAnalysis')}</p>
          </div>
        ) : analysis ? (
          <div className="space-y-6">
            {analysis.analysis_status === 'pending' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">{t('contacts.analysisPending')}</p>
              </div>
            )}
            {analysis.analysis_status === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{t('contacts.analysisError')}</p>
              </div>
            )}
            {analysis.analysis_status === 'completed' && (
              <>
                {analysis.opportunity_score !== null && (
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-lg">{t('contacts.opportunityScore')}</span>
                      <span className="text-4xl font-bold">{analysis.opportunity_score}/100</span>
                    </div>
                    {analysis.analysis_metadata?.potential_value && (
                      <div className="mt-2 text-blue-100">
                        {t('contacts.potentialValue')}: <span className="font-bold text-white">R$ {Number(analysis.analysis_metadata.potential_value).toLocaleString('pt-BR')}</span>
                      </div>
                    )}
                  </div>
                )}
                {analysis.company_info && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.companyInfo')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.company_info}</p>
                  </div>
                )}
                {analysis.analysis_metadata?.digital_presence && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.digitalPresence')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.analysis_metadata.digital_presence}</p>
                  </div>
                )}
                {analysis.market_analysis && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.marketAnalysis')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.market_analysis}</p>
                  </div>
                )}
                {analysis.financial_insights && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.financialInsights')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.financial_insights}</p>
                  </div>
                )}
                {analysis.analysis_metadata?.lead_profile && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.leadProfile')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.analysis_metadata.lead_profile}</p>
                  </div>
                )}
                {analysis.analysis_metadata?.business_potential && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.businessPotential')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.analysis_metadata.business_potential}</p>
                  </div>
                )}
                {analysis.recommendations && (
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <h3 className="font-semibold text-green-900 mb-2 text-lg">{t('contacts.recommendations')}</h3>
                    <p className="text-green-800 whitespace-pre-wrap leading-relaxed">{analysis.recommendations}</p>
                  </div>
                )}
                {analysis.risk_assessment && (
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <h3 className="font-semibold text-yellow-900 mb-2 text-lg">{t('contacts.riskAssessment')}</h3>
                    <p className="text-yellow-800 whitespace-pre-wrap leading-relaxed">{analysis.risk_assessment}</p>
                  </div>
                )}
                {analysis.analysis_metadata?.sources && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">{t('contacts.sources')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{analysis.analysis_metadata.sources}</p>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>{t('contacts.noAnalysis')}</p>
            {selectedContactId && (
              <Button
                className="mt-4"
                onClick={() => handleViewAnalysis(selectedContactId)}
              >
                {t('contacts.startAnalysis')}
              </Button>
            )}
          </div>
        )}
      </Modal>

      {/* Modal de Criar Oportunidade */}
      <Modal
        isOpen={showCreateOpportunity}
        onClose={() => {
          setShowCreateOpportunity(false)
          setSelectedContactId(null)
        }}
        title={t('contacts.createOpportunity')}
        size="md"
      >
        <form onSubmit={async (e) => {
          e.preventDefault()
          try {
            if (!selectedContactId) return
            
            await api.post('/api/opportunities/', {
              name: opportunityFormData.name,
              contact_id: selectedContactId,
              value: opportunityFormData.value ? parseFloat(opportunityFormData.value) : null,
              stage: opportunityFormData.stage,
              probability: opportunityFormData.probability
            })
            
            toast.success(t('contacts.opportunityCreated'))
            
            // Marcar que oportunidade foi criada para este contato
            if (selectedContactId) {
              setOpportunitiesCreated(prev => new Set([...prev, selectedContactId]))
            }
            
            setShowCreateOpportunity(false)
            router.push('/opportunities')
          } catch (error) {
            console.error('Erro ao criar oportunidade:', error)
            toast.error(t('contacts.opportunityError'))
          }
        }} className="space-y-4">
          <Input
            label={t('common.name')}
            type="text"
            required
            value={opportunityFormData.name}
            onChange={(e) => setOpportunityFormData({ ...opportunityFormData, name: e.target.value })}
          />
          <Input
            label={t('common.value')}
            type="number"
            value={opportunityFormData.value}
            onChange={(e) => setOpportunityFormData({ ...opportunityFormData, value: e.target.value })}
            placeholder="R$ 0,00"
          />
          <Select
            label={t('common.stage')}
            value={opportunityFormData.stage}
            onChange={(e) => setOpportunityFormData({ ...opportunityFormData, stage: e.target.value })}
            options={[
              { value: 'qualificacao', label: t('opportunities.qualificacao') },
              { value: 'proposta', label: t('opportunities.proposta') },
              { value: 'negociacao', label: t('opportunities.negociacao') },
              { value: 'fechado', label: t('opportunities.fechado') }
            ]}
          />
          <Input
            label={t('opportunities.probability')}
            type="number"
            min="0"
            max="100"
            value={opportunityFormData.probability}
            onChange={(e) => setOpportunityFormData({ ...opportunityFormData, probability: parseInt(e.target.value) || 0 })}
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCreateOpportunity(false)}
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
