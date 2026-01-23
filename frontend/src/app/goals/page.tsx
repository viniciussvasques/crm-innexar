'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import Modal from '@/components/Modal'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion } from 'framer-motion'
import { Target, Plus, CheckCircle, Clock, PauseCircle, AlertCircle, TrendingUp, DollarSign, Users, Calendar } from 'lucide-react'

interface Goal {
  id: number
  title: string
  description?: string
  goal_type: 'individual' | 'team' | 'department'
  category: 'revenue' | 'deals' | 'activities' | 'conversion_rate' | 'new_clients' | 'custom'
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  target_value: number
  current_value: number
  unit: string
  assignee_id?: number
  assignee_name?: string
  creator_name: string
  start_date: string
  end_date: string
  completed_at?: string
  status: 'active' | 'paused' | 'completed' | 'expired'
  progress_percentage: number
  reward_description?: string
  penalty_description?: string
  created_at: string
}

interface User { id: number; name: string; role: string }

export default function GoalsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [goals, setGoals] = useState<Goal[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterType, setFilterType] = useState('all')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({ title: '', description: '', goal_type: 'individual' as Goal['goal_type'], category: 'revenue' as Goal['category'], period: 'monthly' as Goal['period'], target_value: '', unit: 'BRL', assignee_id: '', start_date: '', end_date: '', reward_description: '', penalty_description: '' })

  const statusConfig: Record<string, { label: string; color: string; bgColor: string; icon: React.ComponentType<any> }> = {
    active: { label: t('goals.active'), color: 'text-blue-300', bgColor: 'bg-blue-500/20', icon: Target },
    paused: { label: t('goals.paused'), color: 'text-amber-300', bgColor: 'bg-amber-500/20', icon: PauseCircle },
    completed: { label: t('goals.completed'), color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', icon: CheckCircle },
    expired: { label: t('goals.expired'), color: 'text-red-300', bgColor: 'bg-red-500/20', icon: AlertCircle }
  }

  const categoryIcons: Record<string, string> = { revenue: '💰', deals: '🤝', activities: '📅', conversion_rate: '📈', new_clients: '👥', custom: '🎯' }

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    if (!token) { router.push('/login'); return }
    if (userStr) { try { setCurrentUser(JSON.parse(userStr)) } catch (e) { console.error(e) } }
    loadData()
  }, [router])

  const loadData = async () => {
    try {
      setLoading(true)
      const [goalsRes, usersRes] = await Promise.all([api.get('/api/goals/'), api.get('/api/users/')])
      setGoals(goalsRes.data)
      setUsers(usersRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      toast.error(t('goals.errorLoad'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateGoal = async () => {
    try {
      await api.post('/api/goals/', { ...formData, target_value: parseFloat(formData.target_value), assignee_id: formData.assignee_id ? parseInt(formData.assignee_id) : undefined, start_date: new Date(formData.start_date), end_date: new Date(formData.end_date) })
      setShowCreateModal(false)
      setFormData({ title: '', description: '', goal_type: 'individual', category: 'revenue', period: 'monthly', target_value: '', unit: 'BRL', assignee_id: '', start_date: '', end_date: '', reward_description: '', penalty_description: '' })
      loadData()
      toast.success(t('goals.created'))
    } catch (error) {
      console.error('Erro ao criar meta:', error)
      toast.error(t('goals.errorCreate'))
    }
  }

  const filteredGoals = useMemo(() => goals.filter(goal => (filterStatus === 'all' || goal.status === filterStatus) && (filterType === 'all' || goal.category === filterType)), [goals, filterStatus, filterType])

  const getProgressColor = (percentage: number) => percentage >= 100 ? 'from-emerald-500 to-green-400' : percentage >= 75 ? 'from-blue-500 to-cyan-400' : percentage >= 50 ? 'from-amber-500 to-yellow-400' : 'from-red-500 to-orange-400'

  const stats = useMemo(() => ({
    total: goals.length,
    active: goals.filter(g => g.status === 'active').length,
    completed: goals.filter(g => g.status === 'completed').length,
    avgProgress: goals.length > 0 ? Math.round(goals.reduce((sum, g) => sum + g.progress_percentage, 0) / goals.length) : 0
  }), [goals])

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
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <Target className="w-8 h-8 text-blue-400" />
              {t('goals.title')}
            </h1>
            <p className="text-slate-400 mt-1">{t('goals.description')}</p>
          </div>
          {currentUser?.role === 'admin' && (
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow">
              <Plus className="w-5 h-5" />
              {t('goals.new')}
            </motion.button>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Goals', value: stats.total, icon: Target, color: 'blue' },
            { label: 'Active', value: stats.active, icon: Clock, color: 'amber' },
            { label: 'Completed', value: stats.completed, icon: CheckCircle, color: 'emerald' },
            { label: 'Avg Progress', value: `${stats.avgProgress}%`, icon: TrendingUp, color: 'purple' }
          ].map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div><p className="text-slate-400 text-sm">{stat.label}</p><p className="text-2xl font-bold text-white mt-1">{stat.value}</p></div>
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}><stat.icon className={`w-5 h-5 text-${stat.color}-400`} /></div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none appearance-none cursor-pointer">
              <option value="all" className="bg-slate-900">{t('goals.allStatuses')}</option>
              <option value="active" className="bg-slate-900">{t('goals.active')}</option>
              <option value="paused" className="bg-slate-900">{t('goals.paused')}</option>
              <option value="completed" className="bg-slate-900">{t('goals.completed')}</option>
              <option value="expired" className="bg-slate-900">{t('goals.expired')}</option>
            </select>
            <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none appearance-none cursor-pointer">
              <option value="all" className="bg-slate-900">{t('goals.allTypes')}</option>
              <option value="revenue" className="bg-slate-900">{t('goals.revenue')}</option>
              <option value="deals" className="bg-slate-900">{t('goals.deals')}</option>
              <option value="activities" className="bg-slate-900">{t('goals.activities')}</option>
              <option value="conversion_rate" className="bg-slate-900">{t('goals.conversion_rate')}</option>
              <option value="new_clients" className="bg-slate-900">{t('goals.new_clients')}</option>
            </select>
          </div>
        </div>

        {/* Goals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredGoals.map((goal, i) => {
            const status = statusConfig[goal.status] || statusConfig.active
            return (
              <motion.div key={goal.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/[0.08] transition-colors cursor-pointer"
                onClick={() => { setSelectedGoal(goal); setShowDetailModal(true) }}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{categoryIcons[goal.category]}</span>
                    <div>
                      <h3 className="font-semibold text-white text-lg">{goal.title}</h3>
                      <p className="text-sm text-slate-500">{goal.creator_name}</p>
                    </div>
                  </div>
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${status.bgColor} ${status.color}`}>{status.label}</span>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-slate-400 mb-2"><span>{t('goals.progress')}</span><span>{goal.progress_percentage.toFixed(1)}%</span></div>
                  <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full bg-gradient-to-r ${getProgressColor(goal.progress_percentage)}`} style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}></div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><p className="text-slate-500">Atual</p><p className="font-semibold text-white">{goal.current_value.toLocaleString('pt-BR')} {goal.unit}</p></div>
                  <div><p className="text-slate-500">Meta</p><p className="font-semibold text-white">{goal.target_value.toLocaleString('pt-BR')} {goal.unit}</p></div>
                </div>
                {goal.assignee_name && (<div className="mt-4 pt-4 border-t border-white/10"><p className="text-sm text-slate-400"><span className="font-medium">Responsável:</span> {goal.assignee_name}</p></div>)}
                <div className="mt-3 text-xs text-slate-500">{new Date(goal.start_date).toLocaleDateString('pt-BR')} - {new Date(goal.end_date).toLocaleDateString('pt-BR')}</div>
              </motion.div>
            )
          })}
        </div>

        {filteredGoals.length === 0 && (
          <div className="text-center py-12">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">{t('goals.noGoals')}</h3>
            <p className="text-slate-400">{filterStatus !== 'all' || filterType !== 'all' ? t('goals.tryFilters') : t('goals.createFirst')}</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title={t('goals.new')} size="lg">
        <div className="space-y-6">
          <Input label={t('goals.titleLabel')} value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
          <Input label={t('common.description')} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <Select label={t('common.type')} value={formData.goal_type} onChange={(e) => setFormData({ ...formData, goal_type: e.target.value as Goal['goal_type'] })} options={[{ value: 'individual', label: t('goals.individual') }, { value: 'team', label: t('goals.team') }, { value: 'department', label: t('goals.department') }]} />
            <Select label={t('goals.category')} value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value as Goal['category'] })} options={[{ value: 'revenue', label: t('goals.revenue') }, { value: 'deals', label: t('goals.deals') }, { value: 'activities', label: t('goals.activities') }, { value: 'conversion_rate', label: t('goals.conversion_rate') }, { value: 'new_clients', label: t('goals.new_clients') }, { value: 'custom', label: t('goals.custom') }]} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select label={t('goals.period')} value={formData.period} onChange={(e) => setFormData({ ...formData, period: e.target.value as Goal['period'] })} options={[{ value: 'daily', label: t('goals.daily') }, { value: 'weekly', label: t('goals.weekly') }, { value: 'monthly', label: t('goals.monthly') }, { value: 'quarterly', label: t('goals.quarterly') }, { value: 'yearly', label: t('goals.yearly') }]} />
            <Input label={t('goals.target')} type="number" step="0.01" value={formData.target_value} onChange={(e) => setFormData({ ...formData, target_value: e.target.value })} required />
            <Input label={t('goals.unit')} value={formData.unit} onChange={(e) => setFormData({ ...formData, unit: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('goals.startDate')} type="date" value={formData.start_date} onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} required />
            <Input label={t('goals.endDate')} type="date" value={formData.end_date} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} required />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleCreateGoal}>{t('goals.create')}</Button>
          </div>
        </div>
      </Modal>

      {/* Detail Modal */}
      <Modal isOpen={showDetailModal} onClose={() => { setShowDetailModal(false); setSelectedGoal(null) }} title={selectedGoal?.title || t('goals.details')} size="lg">
        {selectedGoal && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">{t('goals.basicInfo')}</h4>
                <div className="space-y-2 text-sm">
                  <p className="flex justify-between"><span className="text-slate-400">{t('common.type')}:</span><span className="text-white">{t(`goals.${selectedGoal.goal_type}`)}</span></p>
                  <p className="flex justify-between"><span className="text-slate-400">{t('goals.category')}:</span><span className="text-white">{t(`goals.${selectedGoal.category}`)}</span></p>
                  <p className="flex justify-between"><span className="text-slate-400">{t('common.status')}:</span><span className="text-white">{t(`goals.${selectedGoal.status}`)}</span></p>
                </div>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">{t('goals.progress')}</h4>
                <div className="space-y-2 text-sm">
                  <p className="flex justify-between"><span className="text-slate-400">{t('goals.current')}:</span><span className="text-white">{selectedGoal.current_value.toLocaleString('pt-BR')} {selectedGoal.unit}</span></p>
                  <p className="flex justify-between"><span className="text-slate-400">{t('goals.target')}:</span><span className="text-white">{selectedGoal.target_value.toLocaleString('pt-BR')} {selectedGoal.unit}</span></p>
                  <p className="flex justify-between"><span className="text-slate-400">{t('goals.progress')}:</span><span className="text-emerald-400 font-semibold">{selectedGoal.progress_percentage.toFixed(1)}%</span></p>
                </div>
              </div>
            </div>
            {selectedGoal.description && (<div className="bg-white/5 rounded-lg p-4"><h4 className="font-semibold text-white mb-2">{t('common.description')}</h4><p className="text-slate-300">{selectedGoal.description}</p></div>)}
            <div className="pt-4 border-t border-white/10 flex justify-between text-sm text-slate-400"><span>{t('goals.createdBy')}: {selectedGoal.creator_name}</span><span>{new Date(selectedGoal.created_at).toLocaleDateString('pt-BR')}</span></div>
          </div>
        )}
      </Modal>
    </div>
  )
}
