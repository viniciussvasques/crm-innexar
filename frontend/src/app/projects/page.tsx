'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Project, Contact, Opportunity, User } from '@/types'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import Textarea from '@/components/Textarea'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion } from 'framer-motion'
import {
  FolderKanban, Plus, Search, Filter, Code, Globe, Briefcase,
  Building2, CheckCircle, Clock, Rocket, AlertCircle, ExternalLink
} from 'lucide-react'

export default function ProjectsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [projects, setProjects] = useState<Project[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [formData, setFormData] = useState({
    name: '', description: '', contact_id: '', opportunity_id: '',
    project_type: 'custom_development' as Project['project_type'],
    estimated_value: '', technical_requirements: '', tech_stack: ''
  })

  const statusConfig: Record<string, { label: string; color: string; bgColor: string; borderColor: string; icon: React.ComponentType<any> }> = {
    lead: { label: t('projects.status.lead'), color: 'text-slate-300', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: AlertCircle },
    qualificacao: { label: t('projects.status.qualificacao'), color: 'text-blue-300', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Search },
    proposta: { label: t('projects.status.proposta'), color: 'text-amber-300', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/30', icon: Briefcase },
    aprovado: { label: t('projects.status.aprovado'), color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30', icon: CheckCircle },
    em_planejamento: { label: t('projects.status.em_planejamento'), color: 'text-purple-300', bgColor: 'bg-purple-500/20', borderColor: 'border-purple-500/30', icon: Clock },
    planejamento_concluido: { label: t('projects.status.planejamento_concluido'), color: 'text-indigo-300', bgColor: 'bg-indigo-500/20', borderColor: 'border-indigo-500/30', icon: CheckCircle },
    em_desenvolvimento: { label: t('projects.status.em_desenvolvimento'), color: 'text-orange-300', bgColor: 'bg-orange-500/20', borderColor: 'border-orange-500/30', icon: Code },
    em_revisao: { label: t('projects.status.em_revisao'), color: 'text-pink-300', bgColor: 'bg-pink-500/20', borderColor: 'border-pink-500/30', icon: Search },
    concluido: { label: t('projects.status.concluido'), color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30', icon: Rocket },
    cancelado: { label: t('projects.status.cancelado'), color: 'text-red-300', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30', icon: AlertCircle }
  }

  const loadProjects = useCallback(async () => {
    try {
      const [projectsRes, contactsRes, oppsRes, usersRes] = await Promise.all([
        api.get<Project[]>('/api/projects/'),
        api.get<Contact[]>('/api/contacts/'),
        api.get<Opportunity[]>('/api/opportunities/'),
        api.get<User[]>('/api/users/')
      ])
      setProjects(projectsRes.data)
      setContacts(contactsRes.data)
      setOpportunities(oppsRes.data)
      setUsers(usersRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadProjects()
  }, [router, loadProjects])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/projects/', {
        ...formData,
        contact_id: parseInt(formData.contact_id),
        opportunity_id: formData.opportunity_id ? parseInt(formData.opportunity_id) : null,
        estimated_value: formData.estimated_value || null,
        technical_requirements: formData.technical_requirements || null,
        tech_stack: formData.tech_stack || null
      })
      setShowForm(false)
      setFormData({ name: '', description: '', contact_id: '', opportunity_id: '', project_type: 'custom_development', estimated_value: '', technical_requirements: '', tech_stack: '' })
      loadProjects()
      toast.success(t('projects.created'))
    } catch (error) {
      console.error('Erro ao criar projeto:', error)
      toast.error(t('projects.errorCreate'))
    }
  }

  const handleSendToPlanning = async (projectId: number, planningOwnerId: number) => {
    try {
      await api.post(`/ api / projects / ${projectId}/send-to-planning?planning_owner_id=${planningOwnerId}`)
      loadProjects()
      toast.success(t('projects.sentToPlanning'))
    } catch (error) {
      console.error('Erro ao enviar para planejamento:', error)
      toast.error(t('projects.errorSendPlanning'))
    }
  }

  const handleSendToDev = async (projectId: number, devOwnerId: number) => {
    try {
      await api.post(`/api/projects/${projectId}/send-to-dev?dev_owner_id=${devOwnerId}`)
      loadProjects()
      toast.success(t('projects.sentToDev'))
    } catch (error) {
      console.error('Erro ao enviar para desenvolvimento:', error)
      toast.error(t('projects.errorSendDev'))
    }
  }

  const filteredProjects = useMemo(() => {
    return projects.filter(project => {
      const matchesSearch = !searchTerm ||
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (project.contact_name && project.contact_name.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesStatus = statusFilter === 'all' || project.status === statusFilter
      const matchesType = typeFilter === 'all' || project.project_type === typeFilter
      return matchesSearch && matchesStatus && matchesType
    })
  }, [projects, searchTerm, statusFilter, typeFilter])

  const currentUser = typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('user') || '{}') as User : null
  const isVendedor = currentUser?.role === 'vendedor'
  const isAdmin = currentUser?.role === 'admin'
  const isPlanejamento = currentUser?.role === 'planejamento'
  const planningUsers = users.filter(u => u.role === 'planejamento')
  const devUsers = users.filter(u => u.role === 'dev')

  // Stats
  const stats = useMemo(() => ({
    total: projects.length,
    inProgress: projects.filter(p => ['em_planejamento', 'em_desenvolvimento', 'em_revisao'].includes(p.status)).length,
    completed: projects.filter(p => p.status === 'concluido').length,
    pending: projects.filter(p => ['lead', 'qualificacao', 'proposta'].includes(p.status)).length
  }), [projects])

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
              <FolderKanban className="w-8 h-8 text-indigo-400" />
              {t('projects.title')}
            </h1>
            <p className="text-slate-400 mt-1">Manage development projects</p>
          </div>
          {(isVendedor || isAdmin) && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
            >
              <Plus className="w-5 h-5" />
              {t('projects.new')}
            </motion.button>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Projects', value: stats.total, icon: FolderKanban, color: 'indigo' },
            { label: 'Pending', value: stats.pending, icon: Clock, color: 'amber' },
            { label: 'In Progress', value: stats.inProgress, icon: Code, color: 'blue' },
            { label: 'Completed', value: stats.completed, icon: CheckCircle, color: 'emerald' }
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

        {/* Filters */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">{t('common.all')} Status</option>
              {Object.entries(statusConfig).map(([value, config]) => (
                <option key={value} value={value} className="bg-slate-900">{config.label}</option>
              ))}
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">{t('common.all')} Types</option>
              <option value="marketing_site" className="bg-slate-900">{t('projects.type.marketing_site')}</option>
              <option value="saas_platform" className="bg-slate-900">{t('projects.type.saas_platform')}</option>
              <option value="enterprise_software" className="bg-slate-900">{t('projects.type.enterprise_software')}</option>
              <option value="custom_development" className="bg-slate-900">{t('projects.type.custom_development')}</option>
              <option value="consulting" className="bg-slate-900">{t('projects.type.consulting')}</option>
            </select>
          </div>
        </div>

        {/* Projects Table */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.type')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.status')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Client</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Value</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredProjects.map((project, i) => {
                  const status = statusConfig[project.status] || statusConfig.lead
                  return (
                    <motion.tr
                      key={project.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="hover:bg-white/[0.03] transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-medium">
                            {project.name.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-white font-medium">{project.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400">{t(`projects.type.${project.project_type}`)}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${status.bgColor} ${status.color} border ${status.borderColor}`}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-400">{project.contact_name || '-'}</td>
                      <td className="px-6 py-4 text-emerald-400 font-semibold">{project.estimated_value || '-'}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => { setSelectedProject(project); setShowDetails(true) }}
                          className="px-3 py-1.5 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                        >
                          {t('common.view')}
                        </button>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {filteredProjects.length === 0 && (
            <div className="p-12 text-center">
              <FolderKanban className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">{projects.length === 0 ? t('projects.noProjects') : t('projects.noFiltered')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={t('projects.new')} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label={`${t('projects.title')} ${t('common.name')}`} type="text" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <Textarea label={t('common.description')} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} />
          <Select label={t('contacts.client')} required value={formData.contact_id} onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
            options={[{ value: '', label: t('projects.selectClient') }, ...contacts.map(c => ({ value: c.id.toString(), label: `${c.name}${c.company ? ` - ${c.company}` : ''}` }))]} />
          <Select label={`${t('opportunities.title')} (${t('common.optional')})`} value={formData.opportunity_id} onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
            options={[{ value: '', label: t('common.none') }, ...opportunities.filter(o => o.contact_id === parseInt(formData.contact_id) || !formData.contact_id).map(o => ({ value: o.id.toString(), label: `${o.name} - ${o.stage}` }))]} />
          <Select label={`${t('common.type')} ${t('projects.title')}`} value={formData.project_type} onChange={(e) => setFormData({ ...formData, project_type: e.target.value as Project['project_type'] })}
            options={[
              { value: 'marketing_site', label: t('projects.type.marketing_site') },
              { value: 'saas_platform', label: t('projects.type.saas_platform') },
              { value: 'enterprise_software', label: t('projects.type.enterprise_software') },
              { value: 'custom_development', label: t('projects.type.custom_development') },
              { value: 'consulting', label: t('projects.type.consulting') },
              { value: 'other', label: t('projects.type.other') }
            ]} />
          <Input label={t('projects.estimatedValue')} type="text" value={formData.estimated_value} onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })} placeholder={t('projects.placeholderValue')} />
          <Textarea label={t('projects.technicalRequirements')} value={formData.technical_requirements} onChange={(e) => setFormData({ ...formData, technical_requirements: e.target.value })} rows={4} />
          <Input label={`${t('projects.techStack')} (${t('common.optional')})`} type="text" value={formData.tech_stack} onChange={(e) => setFormData({ ...formData, tech_stack: e.target.value })} placeholder={t('projects.placeholderTech')} />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>{t('common.cancel')}</Button>
            <Button type="submit">{t('projects.create')}</Button>
          </div>
        </form>
      </Modal>

      {/* Details Modal */}
      <Modal isOpen={showDetails} onClose={() => { setShowDetails(false); setSelectedProject(null) }} title={selectedProject?.name || t('projects.projectDetails')} size="xl">
        {selectedProject && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('common.status')}</p>
                <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusConfig[selectedProject.status]?.bgColor} ${statusConfig[selectedProject.status]?.color}`}>
                  {statusConfig[selectedProject.status]?.label}
                </span>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">{t('common.type')}</p>
                <p className="text-white">{t(`projects.type.${selectedProject.project_type}`)}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">Client</p>
                <p className="text-white">{selectedProject.contact_name || '-'}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">Value</p>
                <p className="text-emerald-400 font-semibold">{selectedProject.estimated_value || '-'}</p>
              </div>
            </div>
            {selectedProject.description && (
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-2">{t('common.description')}</p>
                <p className="text-white whitespace-pre-wrap">{selectedProject.description}</p>
              </div>
            )}
            {selectedProject.technical_requirements && (
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-2">{t('projects.technicalRequirements')}</p>
                <p className="text-white whitespace-pre-wrap">{selectedProject.technical_requirements}</p>
              </div>
            )}
            {(selectedProject.repository_url || selectedProject.deployment_url || true) && (
              <div className="flex gap-3">
                <a href={`/projects/${selectedProject.id}/ide`} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors">
                  <Code className="w-4 h-4" /> Open Visual Editor
                </a>
                {selectedProject.repository_url && (
                  <a href={selectedProject.repository_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors">
                    <ExternalLink className="w-4 h-4" /> Repository
                  </a>
                )}
                {selectedProject.deployment_url && (
                  <a href={selectedProject.deployment_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors">
                    <Globe className="w-4 h-4" /> Deployment <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            )}
            {/* Actions */}
            <div className="border-t border-white/10 pt-4">
              <h4 className="font-medium text-white mb-3">{t('common.actions')}</h4>
              <div className="flex flex-wrap gap-2">
                {(isVendedor || isAdmin) && selectedProject.status === 'aprovado' && !selectedProject.planning_owner_id && (
                  <Select label={t('projects.sendToPlanning')} onChange={(e) => { if (e.target.value) { handleSendToPlanning(selectedProject.id, parseInt(e.target.value)); e.target.value = '' } }}
                    options={[{ value: '', label: t('projects.selectPlanner') }, ...planningUsers.map(u => ({ value: u.id.toString(), label: u.name }))]} />
                )}
                {(isPlanejamento || isAdmin) && selectedProject.status === 'planejamento_concluido' && !selectedProject.dev_owner_id && (
                  <Select label={t('projects.sendToDev')} onChange={(e) => { if (e.target.value) { handleSendToDev(selectedProject.id, parseInt(e.target.value)); e.target.value = '' } }}
                    options={[{ value: '', label: t('projects.selectDeveloper') }, ...devUsers.map(u => ({ value: u.id.toString(), label: u.name }))]} />
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
