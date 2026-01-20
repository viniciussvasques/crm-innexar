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

interface User {
  id: number
  name: string
  role: string
}

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

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    goal_type: 'individual' as Goal['goal_type'],
    category: 'revenue' as Goal['category'],
    period: 'monthly' as Goal['period'],
    target_value: '',
    unit: 'BRL',
    assignee_id: '',
    start_date: '',
    end_date: '',
    reward_description: '',
    penalty_description: ''
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (!token) {
      router.push('/login')
      return
    }

    if (userStr) {
      try {
        setCurrentUser(JSON.parse(userStr))
      } catch (error) {
        console.error('Erro ao parsear usuário:', error)
      }
    }

    loadData()
  }, [router])

  const loadData = async () => {
    try {
      setLoading(true)
      const [goalsRes, usersRes] = await Promise.all([
        api.get('/api/goals/'),
        api.get('/api/users/')
      ])

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
      const data = {
        ...formData,
        target_value: parseFloat(formData.target_value),
        assignee_id: formData.assignee_id ? parseInt(formData.assignee_id) : undefined,
        start_date: new Date(formData.start_date),
        end_date: new Date(formData.end_date)
      }

      await api.post('/api/goals/', data)
      setShowCreateModal(false)
      resetForm()
      loadData()
      toast.success(t('goals.created'))
    } catch (error) {
      console.error('Erro ao criar meta:', error)
      toast.error(t('goals.errorCreate'))
    }
  }

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      goal_type: 'individual',
      category: 'revenue',
      period: 'monthly',
      target_value: '',
      unit: 'BRL',
      assignee_id: '',
      start_date: '',
      end_date: '',
      reward_description: '',
      penalty_description: ''
    })
  }

  const getStatusColor = (status: Goal['status']) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200'
      case 'active': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'expired': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryIcon = (category: Goal['category']) => {
    switch (category) {
      case 'revenue': return '💰'
      case 'deals': return '🤝'
      case 'activities': return '📅'
      case 'conversion_rate': return '📈'
      case 'new_clients': return '👥'
      default: return '🎯'
    }
  }

  const filteredGoals = useMemo(() => {
    return goals.filter(goal => {
      const matchesStatus = filterStatus === 'all' || goal.status === filterStatus
      const matchesType = filterType === 'all' || goal.goal_type === filterType
      return matchesStatus && matchesType
    })
  }, [goals, filterStatus, filterType])

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-green-500'
    if (percentage >= 75) return 'bg-blue-500'
    if (percentage >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-gray-600">{t('goals.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">🎯 {t('goals.title')}</h2>
          <p className="text-gray-600 mt-2">{t('goals.description')}</p>
        </div>
        {(currentUser?.role === 'admin') && (
          <Button onClick={() => setShowCreateModal(true)}>
            + {t('goals.new')}
          </Button>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Select
            label={t('common.status')}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            options={[
              { value: 'all', label: t('goals.allStatuses') },
              { value: 'active', label: t('goals.active') },
              { value: 'paused', label: t('goals.paused') },
              { value: 'completed', label: t('goals.completed') },
              { value: 'expired', label: t('goals.expired') }
            ]}
          />
          <Select
            label={t('common.type')}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            options={[
              { value: 'all', label: t('goals.allTypes') },
              { value: 'individual', label: t('goals.individual') },
              { value: 'team', label: t('goals.team') },
              { value: 'department', label: t('goals.department') }
            ]}
          />
        </div>
      </div>

      {/* Lista de Metas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredGoals.map((goal) => (
          <div
            key={goal.id}
            className="bg-white rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-all duration-200 cursor-pointer"
            onClick={() => {
              setSelectedGoal(goal)
              setShowDetailModal(true)
            }}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getCategoryIcon(goal.category)}</span>
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">{goal.title}</h3>
                    <p className="text-sm text-gray-500">{goal.creator_name}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(goal.status)}`}>
                  {goal.status === 'active' ? t('goals.active') :
                   goal.status === 'paused' ? t('goals.paused') :
                   goal.status === 'completed' ? t('goals.completed') : t('goals.expired')}
                </span>
              </div>

              {/* Progresso */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>{t('goals.progress')}</span>
                  <span>{goal.progress_percentage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(goal.progress_percentage)}`}
                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Valores */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Atual</p>
                  <p className="font-semibold text-gray-900">
                    {goal.current_value.toLocaleString('pt-BR')} {goal.unit}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Meta</p>
                  <p className="font-semibold text-gray-900">
                    {goal.target_value.toLocaleString('pt-BR')} {goal.unit}
                  </p>
                </div>
              </div>

              {/* Assignee */}
              {goal.assignee_name && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Responsável:</span> {goal.assignee_name}
                  </p>
                </div>
              )}

              {/* Datas */}
              <div className="mt-3 text-xs text-gray-500">
                <p>{new Date(goal.start_date).toLocaleDateString('pt-BR')} - {new Date(goal.end_date).toLocaleDateString('pt-BR')}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredGoals.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{t('goals.noGoals')}</h3>
          <p className="text-gray-600">
            {filterStatus !== 'all' || filterType !== 'all'
              ? t('goals.tryFilters')
              : t('goals.createFirst')
            }
          </p>
        </div>
      )}

      {/* Modal de Criação */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false)
          resetForm()
        }}
        title={t('goals.new')}
        size="lg"
      >
        <div className="space-y-6">
          <Input
            label={t('goals.titleLabel')}
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />

          <Input
            label={t('common.description')}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('common.type')}
              value={formData.goal_type}
              onChange={(e) => setFormData({ ...formData, goal_type: e.target.value as Goal['goal_type'] })}
              options={[
                { value: 'individual', label: t('goals.individual') },
                { value: 'team', label: t('goals.team') },
                { value: 'department', label: t('goals.department') }
              ]}
            />

            <Select
              label={t('goals.category')}
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value as Goal['category'] })}
              options={[
                { value: 'revenue', label: t('goals.revenue') },
                { value: 'deals', label: t('goals.deals') },
                { value: 'activities', label: t('goals.activities') },
                { value: 'conversion_rate', label: t('goals.conversion_rate') },
                { value: 'new_clients', label: t('goals.new_clients') },
                { value: 'custom', label: t('goals.custom') }
              ]}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Select
              label={t('goals.period')}
              value={formData.period}
              onChange={(e) => setFormData({ ...formData, period: e.target.value as Goal['period'] })}
              options={[
                { value: 'daily', label: t('goals.daily') },
                { value: 'weekly', label: t('goals.weekly') },
                { value: 'monthly', label: t('goals.monthly') },
                { value: 'quarterly', label: t('goals.quarterly') },
                { value: 'yearly', label: t('goals.yearly') }
              ]}
            />

            <Input
              label={t('goals.target')}
              type="number"
              step="0.01"
              value={formData.target_value}
              onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
              required
            />

            <Input
              label={t('goals.unit')}
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              placeholder={t('goals.unitPlaceholder')}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t('goals.startDate')}
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              required
            />

            <Input
              label={t('goals.endDate')}
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              required
            />
          </div>

          {(currentUser?.role === 'admin') && (
            <Select
              label={`${t('goals.assignee')} (${t('common.optional')})`}
              value={formData.assignee_id}
              onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
              options={[
                { value: '', label: t('goals.noAssignee') },
                ...users.map(user => ({ value: user.id.toString(), label: user.name }))
              ]}
            />
          )}

          <Input
            label={`${t('goals.reward')} (${t('common.optional')})`}
            value={formData.reward_description}
            onChange={(e) => setFormData({ ...formData, reward_description: e.target.value })}
            placeholder={t('goals.rewardPlaceholder')}
          />

          <Input
            label={`${t('goals.penalty')} (${t('common.optional')})`}
            value={formData.penalty_description}
            onChange={(e) => setFormData({ ...formData, penalty_description: e.target.value })}
            placeholder={t('goals.penaltyPlaceholder')}
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreateGoal}>
              {t('goals.create')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal de Detalhes */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false)
          setSelectedGoal(null)
        }}
        title={selectedGoal?.title || t('goals.details')}
        size="lg"
      >
        {selectedGoal && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('goals.basicInfo')}</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">{t('common.type')}:</span> {t(`goals.${selectedGoal.goal_type}`)}</p>
                  <p><span className="font-medium">{t('goals.category')}:</span> {t(`goals.${selectedGoal.category}`)}</p>
                  <p><span className="font-medium">{t('goals.period')}:</span> {t(`goals.${selectedGoal.period}`)}</p>
                  <p><span className="font-medium">{t('common.status')}:</span> {t(`goals.${selectedGoal.status}`)}</p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('goals.progress')}</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">{t('goals.current')}:</span> {selectedGoal.current_value.toLocaleString('pt-BR')} {selectedGoal.unit}</p>
                  <p><span className="font-medium">{t('goals.target')}:</span> {selectedGoal.target_value.toLocaleString('pt-BR')} {selectedGoal.unit}</p>
                  <p><span className="font-medium">{t('goals.progress')}:</span> {selectedGoal.progress_percentage.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-2">{t('common.description')}</h4>
              <p className="text-gray-700">{selectedGoal.description || t('goals.noDescription')}</p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('goals.reward')}</h4>
                <p className="text-gray-700">{selectedGoal.reward_description || t('goals.notSpecified')}</p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('goals.penalty')}</h4>
                <p className="text-gray-700">{selectedGoal.penalty_description || t('goals.notSpecified')}</p>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex justify-between text-sm text-gray-600">
                <span>{t('goals.createdBy')}: {selectedGoal.creator_name}</span>
                <span>{new Date(selectedGoal.created_at).toLocaleDateString('pt-BR')}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
