'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import type { Activity, Contact, Opportunity } from '@/types'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import Textarea from '@/components/Textarea'
import Calendar from '@/components/Calendar'
import { format } from 'date-fns'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CalendarDays, CheckCircle, Clock, List, Phone, FileText, Users, Plus,
  Search, Filter, LayoutList
} from 'lucide-react'

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
    type: 'task', subject: '', description: '', due_date: '', due_time: '',
    status: 'pending', contact_id: '', opportunity_id: ''
  })

  const activityTypes = [
    { value: 'task', label: t('activities.task'), icon: CheckCircle, color: 'emerald' },
    { value: 'call', label: t('activities.call'), icon: Phone, color: 'blue' },
    { value: 'meeting', label: t('activities.meeting'), icon: Users, color: 'purple' },
    { value: 'note', label: t('activities.note'), icon: FileText, color: 'amber' }
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
      await api.post('/api/activities/', {
        ...formData,
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
        opportunity_id: formData.opportunity_id ? parseInt(formData.opportunity_id) : null
      })
      setShowForm(false)
      setFormData({ type: 'task', subject: '', description: '', due_date: '', due_time: '', status: 'pending', contact_id: '', opportunity_id: '' })
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

  // Stats
  const stats = useMemo(() => ({
    total: activities.length,
    pending: activities.filter(a => a.status === 'pending').length,
    completed: activities.filter(a => a.status === 'completed').length,
    overdue: activities.filter(a => a.status === 'pending' && a.due_date && new Date(a.due_date) < new Date()).length
  }), [activities])

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
              <CalendarDays className="w-8 h-8 text-amber-400" />
              {t('activities.title')}
            </h1>
            <p className="text-slate-400 mt-1">Manage tasks, calls, and meetings</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="flex bg-white/5 border border-white/10 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'list' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                  }`}
              >
                <LayoutList className="w-4 h-4" />
                List
              </button>
              <button
                onClick={() => setViewMode('calendar')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'calendar' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                  }`}
              >
                <CalendarDays className="w-4 h-4" />
                Calendar
              </button>
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
            >
              <Plus className="w-5 h-5" />
              {t('activities.new')}
            </motion.button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total', value: stats.total, icon: List, color: 'blue' },
            { label: 'Pending', value: stats.pending, icon: Clock, color: 'amber' },
            { label: 'Completed', value: stats.completed, icon: CheckCircle, color: 'emerald' },
            { label: 'Overdue', value: stats.overdue, icon: CalendarDays, color: 'red' }
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
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
              >
                <option value="all" className="bg-slate-900">{t('common.all')}</option>
                {activityTypes.map((type) => (
                  <option key={type.value} value={type.value} className="bg-slate-900">{type.label}</option>
                ))}
              </select>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">{t('common.all')}</option>
              <option value="pending" className="bg-slate-900">{t('activities.pending')}</option>
              <option value="completed" className="bg-slate-900">{t('activities.completed')}</option>
              <option value="cancelled" className="bg-slate-900">{t('activities.cancelled')}</option>
            </select>
          </div>
        </div>

        {/* Calendar View */}
        {viewMode === 'calendar' && (
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
            <Calendar
              events={calendarEvents}
              onDateClick={(date) => {
                setSelectedDate(date)
                setShowForm(true)
                setFormData(prev => ({ ...prev, due_date: format(date, 'yyyy-MM-dd') }))
              }}
              onEventClick={(event) => {
                const activity = activities.find(a => a.id === event.id)
                if (activity) toast.info(`Activity: ${activity.subject}`)
              }}
            />
          </div>
        )}

        {/* List View */}
        {viewMode === 'list' && (
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.type')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('activities.subject')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Due</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.status')}</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredActivities.map((activity, i) => {
                    const typeInfo = activityTypes.find(t => t.value === activity.type) || activityTypes[0]
                    const TypeIcon = typeInfo.icon
                    return (
                      <motion.tr
                        key={activity.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.03 }}
                        className="hover:bg-white/[0.03] transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-lg bg-${typeInfo.color}-500/20 flex items-center justify-center`}>
                              <TypeIcon className={`w-4 h-4 text-${typeInfo.color}-400`} />
                            </div>
                            <span className="text-slate-400 text-sm">{typeInfo.label}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-white font-medium">{activity.subject}</div>
                          {activity.description && (
                            <div className="text-sm text-slate-500 truncate max-w-xs">{activity.description}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-slate-400 text-sm">
                          {activity.due_date ? (
                            <>
                              {new Date(activity.due_date).toLocaleDateString('pt-BR')}
                              {activity.due_time && ` ${activity.due_time}`}
                            </>
                          ) : '-'}
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={activity.status}
                            onChange={(e) => updateStatus(activity.id, e.target.value)}
                            className={`text-xs font-medium rounded-full px-3 py-1 border cursor-pointer transition-colors ${activity.status === 'completed'
                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                                : activity.status === 'cancelled'
                                  ? 'bg-red-500/20 text-red-300 border-red-500/30'
                                  : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                              }`}
                          >
                            <option value="pending" className="bg-slate-900">{t('activities.pending')}</option>
                            <option value="completed" className="bg-slate-900">{t('activities.completed')}</option>
                            <option value="cancelled" className="bg-slate-900">{t('activities.cancelled')}</option>
                          </select>
                        </td>
                        <td className="px-6 py-4">
                          <button className="px-3 py-1 text-xs bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors">
                            {t('common.edit')}
                          </button>
                        </td>
                      </motion.tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {filteredActivities.length === 0 && (
              <div className="p-12 text-center">
                <CalendarDays className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">{activities.length === 0 ? t('activities.noActivities') : t('activities.noFiltered')}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={t('activities.new')} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Select label={t('common.type')} required value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              options={activityTypes.map((type) => ({ value: type.value, label: type.label }))} />
            <Select label={t('common.status')} value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={[
                { value: 'pending', label: t('activities.pending') },
                { value: 'completed', label: t('activities.completed') },
                { value: 'cancelled', label: t('activities.cancelled') }
              ]} />
          </div>
          <Input label={t('activities.subject')} type="text" required value={formData.subject} onChange={(e) => setFormData({ ...formData, subject: e.target.value })} />
          <Textarea label={t('common.description')} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} />
          <div className="grid grid-cols-3 gap-4">
            <Input label={t('activities.dueDate')} type="date" value={formData.due_date} onChange={(e) => setFormData({ ...formData, due_date: e.target.value })} />
            <Input label={t('activities.dueTime')} type="time" value={formData.due_time} onChange={(e) => setFormData({ ...formData, due_time: e.target.value })} />
            <Select label={t('activities.contact')} value={formData.contact_id} onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              options={[{ value: '', label: t('common.none') }, ...contacts.map((c) => ({ value: c.id.toString(), label: c.name }))]} />
          </div>
          <Select label={t('activities.opportunity')} value={formData.opportunity_id} onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
            options={[{ value: '', label: t('common.none') }, ...opportunities.map((o) => ({ value: o.id.toString(), label: o.name }))]} />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>{t('common.cancel')}</Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
