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
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users, Search, Filter, Plus, BarChart3, Briefcase,
  Mail, Phone, Building2, ChevronRight, Sparkles, X
} from 'lucide-react'

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

      const leadContacts = response.data.filter(c => c.status === 'lead')
      const analysesData: Record<number, any> = {}
      for (const contact of leadContacts) {
        try {
          const analysisResponse = await api.get(`/api/lead-analysis/${contact.id}`)
          if (analysisResponse.data && analysisResponse.data.analysis_status) {
            analysesData[contact.id] = analysisResponse.data
          }
        } catch (error: any) {
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
        name: '', email: '', phone: '', company: '', status: 'lead',
        project_type: '', budget_range: '', timeline: '', website: '',
        linkedin: '', position: '', industry: '', company_size: '', source: 'manual'
      })

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
        try {
          await api.post(`/api/lead-analysis/${contactId}`)
          toast.success(t('contacts.analysisStarted'))
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

  // Stats
  const stats = useMemo(() => ({
    total: contacts.length,
    leads: contacts.filter(c => c.status === 'lead').length,
    prospects: contacts.filter(c => c.status === 'prospect').length,
    clients: contacts.filter(c => c.status === 'client').length
  }), [contacts])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-white/5 rounded-xl"></div>
            ))}
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
              <Users className="w-8 h-8 text-blue-400" />
              {t('contacts.title')}
            </h1>
            <p className="text-slate-400 mt-1">{t('contacts.subtitle') || 'Manage your contacts and leads'}</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
          >
            <Plus className="w-5 h-5" />
            {t('contacts.new')}
          </motion.button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: t('common.total'), value: stats.total, color: 'blue', icon: Users },
            { label: t('contacts.lead'), value: stats.leads, color: 'purple', icon: Sparkles },
            { label: t('contacts.prospect'), value: stats.prospects, color: 'amber', icon: BarChart3 },
            { label: t('contacts.client'), value: stats.clients, color: 'emerald', icon: Briefcase }
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
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Alert Cards for Analysis Ready */}
        <AnimatePresence>
          {contacts.filter(c =>
            c.status === 'lead' &&
            analyses[c.id]?.analysis_status === 'completed' &&
            !opportunitiesCreated.has(c.id)
          ).map(contact => (
            <motion.div
              key={contact.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-4 cursor-pointer hover:border-blue-500/50 transition-colors"
              onClick={() => handleViewAnalysis(contact.id)}
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{t('contacts.analysisReady')} - {contact.name}</h3>
                    <p className="text-sm text-slate-400">{contact.company || contact.email}</p>
                  </div>
                  {analyses[contact.id]?.opportunity_score && (
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm font-medium">
                      Score: {analyses[contact.id].opportunity_score}/100
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleViewAnalysis(contact.id) }}
                    className="px-3 py-1.5 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20 transition-colors"
                  >
                    {t('contacts.viewFullAnalysis')}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedContactId(contact.id)
                      setOpportunityFormData({
                        name: `${contact.company || contact.name} - Oportunidade`,
                        value: analyses[contact.id]?.analysis_metadata?.potential_value?.toString() || '',
                        stage: 'qualificacao',
                        probability: analyses[contact.id]?.opportunity_score || 50
                      })
                      setShowCreateOpportunity(true)
                    }}
                    className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm hover:opacity-90 transition-opacity"
                  >
                    + {t('contacts.createOpportunity')}
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Search and Filters */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder={`${t('common.search')}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
              >
                <option value="all" className="bg-slate-900">{t('common.all')}</option>
                <option value="lead" className="bg-slate-900">{t('contacts.lead')}</option>
                <option value="prospect" className="bg-slate-900">{t('contacts.prospect')}</option>
                <option value="client" className="bg-slate-900">{t('contacts.client')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* Contacts List */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          {/* Desktop Table */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.email')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.phone')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.company')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.status')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredContacts.map((contact, i) => (
                  <motion.tr
                    key={contact.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="hover:bg-white/[0.03] transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
                          {contact.name.charAt(0).toUpperCase()}
                        </div>
                        <span className="text-white font-medium">{contact.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">{contact.email || '-'}</td>
                    <td className="px-6 py-4 text-slate-400">{contact.phone || '-'}</td>
                    <td className="px-6 py-4 text-slate-400">{contact.company || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${contact.status === 'lead' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                          contact.status === 'prospect' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                            'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}>
                        {contact.status === 'lead' ? t('contacts.lead') :
                          contact.status === 'prospect' ? t('contacts.prospect') :
                            t('contacts.client')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {contact.status === 'lead' && (
                          <>
                            <button
                              onClick={() => handleViewAnalysis(contact.id)}
                              className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20 transition-colors"
                            >
                              <BarChart3 className="w-4 h-4" />
                              {t('contacts.viewAnalysis')}
                            </button>
                            <button
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
                              className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm hover:opacity-90 transition-opacity"
                            >
                              <Plus className="w-4 h-4" />
                              {t('contacts.createOpportunity')}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="lg:hidden divide-y divide-white/5">
            {filteredContacts.map((contact, i) => (
              <motion.div
                key={contact.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="p-4 hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-lg">
                      {contact.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-white font-medium">{contact.name}</h3>
                      <p className="text-slate-400 text-sm">{contact.company || 'No company'}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${contact.status === 'lead' ? 'bg-purple-500/20 text-purple-300' :
                      contact.status === 'prospect' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-emerald-500/20 text-emerald-300'
                    }`}>
                    {contact.status}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {contact.email && (
                    <div className="flex items-center gap-2 text-slate-400">
                      <Mail className="w-4 h-4" />
                      <span>{contact.email}</span>
                    </div>
                  )}
                  {contact.phone && (
                    <div className="flex items-center gap-2 text-slate-400">
                      <Phone className="w-4 h-4" />
                      <span>{contact.phone}</span>
                    </div>
                  )}
                </div>
                {contact.status === 'lead' && (
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleViewAnalysis(contact.id)}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-white/10 text-white rounded-lg text-sm"
                    >
                      <BarChart3 className="w-4 h-4" />
                      {t('contacts.viewAnalysis')}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedContactId(contact.id)
                        setShowCreateOpportunity(true)
                      }}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm"
                    >
                      <Plus className="w-4 h-4" />
                      Opportunity
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {/* Empty States */}
          {filteredContacts.length === 0 && contacts.length > 0 && (
            <div className="p-12 text-center">
              <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">{t('contacts.noFiltered')}</p>
            </div>
          )}
          {contacts.length === 0 && (
            <div className="p-12 text-center">
              <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 mb-4">{t('contacts.noContacts')}</p>
              <button
                onClick={() => setShowForm(true)}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg"
              >
                {t('contacts.new')}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
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
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
              {t('common.cancel')}
            </Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>

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
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-slate-400">{t('contacts.loadingAnalysis')}</p>
          </div>
        ) : analysis ? (
          <div className="space-y-6">
            {analysis.analysis_status === 'pending' && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                <p className="text-amber-300">{t('contacts.analysisPending')}</p>
              </div>
            )}
            {analysis.analysis_status === 'completed' && (
              <>
                {analysis.opportunity_score !== null && (
                  <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300 font-medium">{t('contacts.opportunityScore')}</span>
                      <span className="text-4xl font-bold text-white">{analysis.opportunity_score}/100</span>
                    </div>
                  </div>
                )}
                {analysis.company_info && (
                  <div className="bg-white/5 rounded-lg p-4">
                    <h3 className="font-semibold text-white mb-2">{t('contacts.companyInfo')}</h3>
                    <p className="text-slate-300 whitespace-pre-wrap">{analysis.company_info}</p>
                  </div>
                )}
                {analysis.recommendations && (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                    <h3 className="font-semibold text-emerald-300 mb-2">{t('contacts.recommendations')}</h3>
                    <p className="text-emerald-200 whitespace-pre-wrap">{analysis.recommendations}</p>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            <p>{t('contacts.noAnalysis')}</p>
          </div>
        )}
      </Modal>

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
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => setShowCreateOpportunity(false)}>
              {t('common.cancel')}
            </Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
