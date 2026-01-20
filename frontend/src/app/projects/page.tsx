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
    name: '',
    description: '',
    contact_id: '',
    opportunity_id: '',
    project_type: 'custom_development' as Project['project_type'],
    estimated_value: '',
    technical_requirements: '',
    tech_stack: ''
  })

  const loadProjects = useCallback(async () => {
    try {
      const projectsRes = await api.get<Project[]>('/api/projects/')
      setProjects(projectsRes.data)

      const contactsRes = await api.get<Contact[]>('/api/contacts/')
      setContacts(contactsRes.data)

      const oppsRes = await api.get<Opportunity[]>('/api/opportunities/')
      setOpportunities(oppsRes.data)

      const usersRes = await api.get<User[]>('/api/users/')
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
    if (!token) {
      router.push('/login')
      return
    }
    loadProjects()
  }, [router, loadProjects])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        contact_id: parseInt(formData.contact_id),
        opportunity_id: formData.opportunity_id ? parseInt(formData.opportunity_id) : null,
        estimated_value: formData.estimated_value || null,
        technical_requirements: formData.technical_requirements || null,
        tech_stack: formData.tech_stack || null
      }
      await api.post('/api/projects/', payload)
      setShowForm(false)
      setFormData({
        name: '',
        description: '',
        contact_id: '',
        opportunity_id: '',
        project_type: 'custom_development',
        estimated_value: '',
        technical_requirements: '',
        tech_stack: ''
      })
      loadProjects()
      toast.success(t('projects.created'))
    } catch (error) {
      console.error('Erro ao criar projeto:', error)
      toast.error(t('projects.errorCreate'))
    }
  }

  const handleSendToPlanning = async (projectId: number, planningOwnerId: number) => {
    try {
      await api.post(`/api/projects/${projectId}/send-to-planning?planning_owner_id=${planningOwnerId}`)
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

  const handleRequestQuote = async (projectId: number) => {
    try {
      await api.post('/api/quote-requests/', { project_id: projectId })
      loadProjects()
      toast.success(t('projects.quoteRequested'))
    } catch (error) {
      console.error('Erro ao solicitar orçamento:', error)
      toast.error(t('projects.errorRequestQuote'))
    }
  }

  const getStatusColor = (status: Project['status']) => {
    const colors: Record<Project['status'], string> = {
      lead: 'bg-gray-100 text-gray-800',
      qualificacao: 'bg-blue-100 text-blue-800',
      proposta: 'bg-yellow-100 text-yellow-800',
      aprovado: 'bg-green-100 text-green-800',
      em_planejamento: 'bg-purple-100 text-purple-800',
      planejamento_concluido: 'bg-indigo-100 text-indigo-800',
      em_desenvolvimento: 'bg-orange-100 text-orange-800',
      em_revisao: 'bg-pink-100 text-pink-800',
      concluido: 'bg-green-200 text-green-900',
      cancelado: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: Project['status']) => {
    return t(`projects.status.${status}`) || status
  }

  const getProjectTypeLabel = (type: Project['project_type']) => {
    return t(`projects.type.${type}`) || type
  }

  // Filtros e busca
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
  const isDev = currentUser?.role === 'dev'

  const planningUsers = users.filter(u => u.role === 'planejamento')
  const devUsers = users.filter(u => u.role === 'dev')

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
        <h2 className="text-3xl font-bold text-gray-900">{t('projects.title')}</h2>
        {(isVendedor || isAdmin) && (
          <Button onClick={() => setShowForm(true)}>
            + {t('projects.new')}
          </Button>
        )}
      </div>

      {/* Busca e Filtros */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.search')}</label>
            <input
              type="text"
              placeholder={`${t('projects.title')} ou ${t('contacts.title')}...`}
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
              <option value="lead">{t('projects.status.lead')}</option>
              <option value="qualificacao">{t('projects.status.qualificacao')}</option>
              <option value="proposta">{t('projects.status.proposta')}</option>
              <option value="aprovado">{t('projects.status.aprovado')}</option>
              <option value="em_planejamento">{t('projects.status.em_planejamento')}</option>
              <option value="planejamento_concluido">{t('projects.status.planejamento_concluido')}</option>
              <option value="em_desenvolvimento">{t('projects.status.em_desenvolvimento')}</option>
              <option value="em_revisao">{t('projects.status.em_revisao')}</option>
              <option value="concluido">{t('projects.status.concluido')}</option>
              <option value="cancelado">{t('projects.status.cancelado')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.type')}</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">{t('common.all')}</option>
              <option value="marketing_site">{t('projects.type.marketing_site')}</option>
              <option value="saas_platform">{t('projects.type.saas_platform')}</option>
              <option value="enterprise_software">{t('projects.type.enterprise_software')}</option>
              <option value="custom_development">{t('projects.type.custom_development')}</option>
              <option value="consulting">{t('projects.type.consulting')}</option>
              <option value="other">{t('projects.type.other')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de Projetos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('common.name')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('common.type')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('common.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('contacts.client')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('projects.seller')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('projects.estimatedValue')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('common.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredProjects.map((project) => (
              <tr key={project.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{project.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{getProjectTypeLabel(project.project_type)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(project.status)}`}>
                    {getStatusLabel(project.status)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{project.contact_name || 'N/A'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{project.owner_name || 'N/A'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{project.estimated_value || 'N/A'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => {
                      setSelectedProject(project)
                      setShowDetails(true)
                    }}
                    className="text-primary hover:text-primary-dark mr-4"
                  >
                    {t('common.view')}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredProjects.length === 0 && projects.length > 0 && (
          <div className="p-8 text-center text-gray-500">
            {t('projects.noFiltered')}
          </div>
        )}
        {projects.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {t('projects.noProjects')}
          </div>
        )}
      </div>

      {/* Modal de Criação */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={t('projects.new')}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label={`${t('projects.title')} ${t('common.name')}`}
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <Textarea
              label={t('common.description')}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
            <Select
              label={t('contacts.client')}
              required
              value={formData.contact_id}
              onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              options={[
                { value: '', label: t('projects.selectClient') },
                ...contacts.map((contact) => ({
                  value: contact.id.toString(),
                  label: `${contact.name}${contact.company ? ` - ${contact.company}` : ''}`
                }))
              ]}
            />
            <Select
              label={`${t('opportunities.title')} (${t('common.optional')})`}
              value={formData.opportunity_id}
              onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
              options={[
                { value: '', label: t('common.none') },
                ...opportunities
                  .filter(opp => opp.contact_id === parseInt(formData.contact_id) || !formData.contact_id)
                  .map((opp) => ({
                    value: opp.id.toString(),
                    label: `${opp.name} - ${opp.stage}`
                  }))
              ]}
            />
            <Select
              label={`${t('common.type')} ${t('projects.title')}`}
              value={formData.project_type}
              onChange={(e) => setFormData({ ...formData, project_type: e.target.value as Project['project_type'] })}
              options={[
                { value: 'marketing_site', label: t('projects.type.marketing_site') },
                { value: 'saas_platform', label: t('projects.type.saas_platform') },
                { value: 'enterprise_software', label: t('projects.type.enterprise_software') },
                { value: 'custom_development', label: t('projects.type.custom_development') },
                { value: 'consulting', label: t('projects.type.consulting') },
                { value: 'other', label: t('projects.type.other') }
              ]}
            />
            <Input
              label={t('projects.estimatedValue')}
              type="text"
              value={formData.estimated_value}
              onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
              placeholder={t('projects.placeholderValue')}
            />
            <Textarea
              label={t('projects.technicalRequirements')}
              value={formData.technical_requirements}
              onChange={(e) => setFormData({ ...formData, technical_requirements: e.target.value })}
              rows={4}
            />
            <Input
              label={`${t('projects.techStack')} (${t('common.optional')})`}
              type="text"
              value={formData.tech_stack}
              onChange={(e) => setFormData({ ...formData, tech_stack: e.target.value })}
              placeholder={t('projects.placeholderTech')}
            />
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit">
              {t('projects.create')}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal de Detalhes */}
      <Modal
        isOpen={showDetails}
        onClose={() => {
          setShowDetails(false)
          setSelectedProject(null)
        }}
        title={selectedProject?.name || t('projects.projectDetails')}
        size="xl"
      >
        {selectedProject && (
          <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('common.status')}</label>
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(selectedProject.status)}`}>
                    {getStatusLabel(selectedProject.status)}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('common.type')}</label>
                  <div className="text-sm text-gray-900">{getProjectTypeLabel(selectedProject.project_type)}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('contacts.client')}</label>
                  <div className="text-sm text-gray-900">{selectedProject.contact_name || t('common.na')}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('projects.seller')}</label>
                  <div className="text-sm text-gray-900">{selectedProject.owner_name || t('common.na')}</div>
                </div>
                {selectedProject.planning_owner_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">{t('planning.title')}</label>
                    <div className="text-sm text-gray-900">{selectedProject.planning_owner_name}</div>
                  </div>
                )}
                {selectedProject.dev_owner_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">{t('projects.development')}</label>
                    <div className="text-sm text-gray-900">{selectedProject.dev_owner_name}</div>
                  </div>
                )}
                {selectedProject.estimated_value && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">{t('projects.estimatedValue')}</label>
                    <div className="text-sm text-gray-900">{selectedProject.estimated_value}</div>
                  </div>
                )}
                {selectedProject.approved_value && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">{t('projects.approvedValue')}</label>
                    <div className="text-sm text-gray-900">{selectedProject.approved_value}</div>
                  </div>
                )}
              </div>

              {selectedProject.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('common.description')}</label>
                  <div className="text-sm text-gray-900 whitespace-pre-wrap">{selectedProject.description}</div>
                </div>
              )}

              {selectedProject.technical_requirements && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('projects.technicalRequirements')}</label>
                  <div className="text-sm text-gray-900 whitespace-pre-wrap">{selectedProject.technical_requirements}</div>
                </div>
              )}

              {selectedProject.tech_stack && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('projects.techStack')}</label>
                  <div className="text-sm text-gray-900">{selectedProject.tech_stack}</div>
                </div>
              )}

              {selectedProject.repository_url && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('projects.repository')}</label>
                  <a href={selectedProject.repository_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                    {selectedProject.repository_url}
                  </a>
                </div>
              )}

              {selectedProject.deployment_url && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('projects.deployment')}</label>
                  <a href={selectedProject.deployment_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                    {selectedProject.deployment_url}
                  </a>
                </div>
              )}

              {/* Ações baseadas no status e role */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium mb-2">{t('common.actions')}</h4>
                <div className="flex flex-wrap gap-2">
                  {(isVendedor || isAdmin) && selectedProject.status === 'aprovado' && (
                    <Button
                      variant="outline"
                      onClick={() => handleRequestQuote(selectedProject.id)}
                    >
                      {t('projects.requestQuote')}
                    </Button>
                  )}
                  {(isVendedor || isAdmin) && selectedProject.status === 'aprovado' && !selectedProject.planning_owner_id && (
                    <div>
                      <Select
                        label={t('projects.sendToPlanning')}
                        onChange={(e) => {
                          if (e.target.value) {
                            handleSendToPlanning(selectedProject.id, parseInt(e.target.value))
                            e.target.value = ''
                          }
                        }}
                        options={[
                          { value: '', label: t('projects.selectPlanner') },
                          ...planningUsers.map((user) => ({
                            value: user.id.toString(),
                            label: user.name
                          }))
                        ]}
                      />
                    </div>
                  )}
                  {(isPlanejamento || isAdmin) && selectedProject.status === 'planejamento_concluido' && !selectedProject.dev_owner_id && (
                    <div>
                      <Select
                        label={t('projects.sendToDev')}
                        onChange={(e) => {
                          if (e.target.value) {
                            handleSendToDev(selectedProject.id, parseInt(e.target.value))
                            e.target.value = ''
                          }
                        }}
                        options={[
                          { value: '', label: t('projects.selectDeveloper') },
                          ...devUsers.map((user) => ({
                            value: user.id.toString(),
                            label: user.name
                          }))
                        ]}
                      />
                    </div>
                  )}
                </div>
              </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

