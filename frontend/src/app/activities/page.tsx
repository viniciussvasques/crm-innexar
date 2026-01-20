'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import type { Activity, Contact, Opportunity } from '@/types';
import { toast } from '@/components/Toast';
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import Textarea from '@/components/Textarea'
import Calendar from '@/components/Calendar'
import { format } from 'date-fns'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ActivitiesPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [activities, setActivities] = useState<Activity[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list')
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [formData, setFormData] = useState({
    type: 'task',
    subject: '',
    description: '',
    due_date: '',
    due_time: '',
    status: 'pending',
    contact_id: '',
    opportunity_id: ''
  })

  const activityTypes = [
    { value: 'task', label: t('activities.task'), icon: '✓' },
    { value: 'call', label: t('activities.call'), icon: '📞' },
    { value: 'meeting', label: t('activities.meeting'), icon: '🤝' },
    { value: 'note', label: t('activities.note'), icon: '📝' }
  ]

  const loadData = useCallback(async () => {
    try {
      const [actsRes, contactsRes, oppsRes] = await Promise.all([
        api.get<Activity[]>('/api/activities/'),
        api.get<Contact[]>('/api/contacts/'),
        api.get<Opportunity[]>('/api/opportunities/')
      ])
      setActivities(actsRes.data)
      setContacts(contactsRes.data)
      setOpportunities(oppsRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      toast.error(t('activities.errorLoad'))
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
      await api.post('/api/activities/', {
        ...formData,
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
        opportunity_id: formData.opportunity_id ? parseInt(formData.opportunity_id) : null
      })
      setShowForm(false)
      setFormData({
        type: 'task',
        subject: '',
        description: '',
        due_date: '',
        due_time: '',
        status: 'pending',
        contact_id: '',
        opportunity_id: ''
      })
      loadData()
      toast.success(t('activities.created'))
    } catch (error) {
      console.error('Erro ao criar atividade:', error)
      toast.error(t('activities.errorCreate'))
    }
  }

  const updateStatus = async (id: number, newStatus: string) => {
    try {
      await api.put(`/api/activities/${id}`, { status: newStatus })
      loadData()
      toast.success(t('activities.statusUpdated'))
    } catch (error) {
      console.error('Erro ao atualizar status:', error)
      toast.error(t('activities.errorUpdate'))
    }
  }

  // Filtros e busca
  const filteredActivities = useMemo(() => {
    return activities.filter(activity => {
      const matchesSearch = !searchTerm || 
        activity.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (activity.description && activity.description.toLowerCase().includes(searchTerm.toLowerCase()))
      
      const matchesType = typeFilter === 'all' || activity.type === typeFilter
      const matchesStatus = statusFilter === 'all' || activity.status === statusFilter
      
      return matchesSearch && matchesType && matchesStatus
    })
  }, [activities, searchTerm, typeFilter, statusFilter])

  // Preparar eventos para o calendário
  const calendarEvents = useMemo(() => {
    return filteredActivities
      .filter(activity => activity.due_date)
      .map(activity => ({
        id: activity.id,
        date: activity.due_date!,
        time: activity.due_time || undefined,
        title: activity.subject,
        type: activity.type
      }))
  }, [filteredActivities])

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
        <h2 className="text-3xl font-bold text-gray-900">{t('activities.title')}</h2>
        <div className="flex gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t('activities.list')}
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'calendar'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t('activities.calendar')}
            </button>
          </div>
          <Button onClick={() => setShowForm(true)}>
            + {t('activities.new')}
          </Button>
        </div>
      </div>

      {/* Busca e Filtros */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.search')}</label>
            <input
              type="text"
              placeholder={`${t('activities.subject')} ou ${t('common.description')}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.type')}</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">{t('common.all')}</option>
              {activityTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.icon} {type.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.status')}</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">{t('common.all')}</option>
              <option value="pending">{t('activities.pending')}</option>
              <option value="completed">{t('activities.completed')}</option>
              <option value="cancelled">{t('activities.cancelled')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Modal de Criação */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={t('activities.new')}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('common.type')}
              required
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              options={activityTypes.map((type) => ({
                value: type.value,
                label: `${type.icon} ${type.label}`
              }))}
            />
            <Select
              label={t('common.status')}
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={[
                { value: 'pending', label: t('activities.pending') },
                { value: 'completed', label: t('activities.completed') },
                { value: 'cancelled', label: t('activities.cancelled') }
              ]}
            />
          </div>
          <Input
            label={t('activities.subject')}
            type="text"
            required
            value={formData.subject}
            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
          />
          <Textarea
            label={t('common.description')}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={3}
          />
          <div className="grid grid-cols-3 gap-4">
            <Input
              label={t('activities.dueDate')}
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            />
            <Input
              label={t('activities.dueTime')}
              type="time"
              value={formData.due_time}
              onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
            />
            <Select
              label={t('activities.contact')}
              value={formData.contact_id}
              onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              options={[
                { value: '', label: t('common.none') },
                ...contacts.map((contact) => ({
                  value: contact.id.toString(),
                  label: contact.name
                }))
              ]}
            />
          </div>
          <Select
            label={t('activities.opportunity')}
            value={formData.opportunity_id}
            onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
            options={[
              { value: '', label: t('common.none') },
              ...opportunities.map((opp) => ({
                value: opp.id.toString(),
                label: opp.name
              }))
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

      {/* Visualização Calendário */}
      {viewMode === 'calendar' && (
        <div className="mb-6">
          <Calendar
            events={calendarEvents}
            onDateClick={(date) => {
              setSelectedDate(date)
              setShowForm(true)
              setFormData(prev => ({
                ...prev,
                due_date: format(date, 'yyyy-MM-dd')
              }))
            }}
            onEventClick={(event) => {
              const activity = activities.find(a => a.id === event.id)
              if (activity) {
                // Poderia abrir modal de detalhes aqui
                toast.info(`Atividade: ${activity.subject}`)
              }
            }}
          />
        </div>
      )}

      {/* Lista de Atividades */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.type')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('activities.subject')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('activities.dueDate')}/{t('activities.dueTime')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.status')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredActivities.map((activity) => {
                const typeInfo = activityTypes.find(t => t.value === activity.type) || activityTypes[0]
                return (
                  <tr key={activity.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-xl">{typeInfo.icon}</span>
                      <span className="ml-2 text-sm text-gray-500">{typeInfo.label}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{activity.subject}</div>
                      {activity.description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">{activity.description}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {activity.due_date ? (
                        <>
                          {new Date(activity.due_date).toLocaleDateString('pt-BR')}
                          {activity.due_time && ` ${activity.due_time}`}
                        </>
                      ) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={activity.status}
                        onChange={(e) => updateStatus(activity.id, e.target.value)}
                        className={`text-xs font-medium rounded-full px-3 py-1 border-0 cursor-pointer transition-colors ${
                          activity.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : activity.status === 'cancelled'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        } hover:opacity-80`}
                      >
                        <option value="pending">{t('activities.pending')}</option>
                        <option value="completed">{t('activities.completed')}</option>
                        <option value="cancelled">{t('activities.cancelled')}</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-primary hover:text-primary-dark transition-colors">{t('common.edit')}</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {filteredActivities.length === 0 && activities.length > 0 && (
            <div className="p-8 text-center text-gray-500">
              {t('activities.noFiltered')}
            </div>
          )}
          {activities.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              {t('activities.noActivities')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
