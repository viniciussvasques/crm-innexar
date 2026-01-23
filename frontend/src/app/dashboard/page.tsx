'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Users, Target, DollarSign, Calendar, TrendingUp, ArrowRight,
  Sparkles, Clock, CheckCircle2, AlertCircle, Trophy
} from 'lucide-react'
import api from '@/lib/api'
import { User } from '@/types'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useLanguage } from '@/contexts/LanguageContext'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  color: 'blue' | 'green' | 'purple' | 'yellow' | 'cyan'
  delay?: number
}

const StatCard = ({ title, value, icon: Icon, color, delay = 0 }: StatCardProps) => {
  const colorClasses = {
    blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', gradient: 'from-blue-500 to-cyan-500' },
    green: { bg: 'bg-green-500/20', text: 'text-green-400', gradient: 'from-green-500 to-emerald-500' },
    purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', gradient: 'from-purple-500 to-pink-500' },
    yellow: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', gradient: 'from-yellow-500 to-orange-500' },
    cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', gradient: 'from-cyan-500 to-blue-500' },
  }

  const c = colorClasses[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="card p-6 hover:border-white/20 transition-all duration-300"
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-slate-400 text-sm font-medium">{title}</span>
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${c.text}`} />
        </div>
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.2 }}
        className="text-3xl font-bold text-white"
      >
        {value}
      </motion.p>
    </motion.div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [data, setData] = useState<any>({
    stats: {
      total_contacts: 0,
      total_opportunities: 0,
      total_value: 0,
      pending_activities: 0,
      opportunities_by_stage: {}
    },
    recent_activities: [],
    top_opportunities: []
  })
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)

  const loadDashboard = useCallback(async (userRole?: string) => {
    try {
      const endpoint = userRole === 'admin' ? '/api/dashboard/admin' : '/api/dashboard/vendedor'
      const response = await api.get<any>(endpoint)
      setData(response.data || {
        stats: { total_contacts: 0, total_opportunities: 0, total_value: 0, pending_activities: 0, opportunities_by_stage: {} },
        recent_activities: [],
        top_opportunities: []
      })
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }, [])

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
        const parsedUser = JSON.parse(userStr) as User
        setUser(parsedUser)
        loadDashboard(parsedUser.role)
      } catch (error) {
        router.push('/login')
      }
    } else {
      router.push('/login')
    }
  }, [router, loadDashboard])

  const COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444']

  const pipelineData = data?.stats?.opportunities_by_stage
    ? Object.entries(data.stats.opportunities_by_stage).map(([stage, count]) => ({
      name: t(`opportunity.stage.${stage}`) || stage.replace('_', ' '),
      value: count as number,
      stage
    }))
    : []

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400">{t('common.loading')}</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-slate-400">Innexar Workspace</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}! 👋
          </h1>
          <p className="text-slate-400">
            {user?.role === 'admin' ? 'Team performance overview' : 'Your sales overview'}
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => router.push('/opportunities')}
          className="btn-primary flex items-center gap-2"
        >
          <Target className="w-4 h-4" />
          New Opportunity
        </motion.button>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('dashboard.totalContacts')}
          value={data.stats?.total_contacts || 0}
          icon={Users}
          color="blue"
          delay={0}
        />
        <StatCard
          title={t('dashboard.totalOpportunities')}
          value={data.stats?.total_opportunities || 0}
          icon={Target}
          color="green"
          delay={0.1}
        />
        <StatCard
          title={t('dashboard.totalValue')}
          value={formatCurrency(data.stats?.total_value || 0)}
          icon={DollarSign}
          color="yellow"
          delay={0.2}
        />
        <StatCard
          title={t('dashboard.pendingActivities')}
          value={data.stats?.pending_activities || 0}
          icon={Calendar}
          color="purple"
          delay={0.3}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Chart */}
        {pipelineData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card p-6"
          >
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              {t('dashboard.opportunitiesByStage')}
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={pipelineData}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={{ stroke: '#334155' }}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={{ stroke: '#334155' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    color: '#fff'
                  }}
                />
                <Bar
                  dataKey="value"
                  fill="url(#barGradient)"
                  radius={[8, 8, 0, 0]}
                />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {/* Pie Chart */}
        {pipelineData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card p-6"
          >
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-400" />
              {t('dashboard.pipelineDistribution')}
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pipelineData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pipelineData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    color: '#fff'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap justify-center gap-4 mt-4">
              {pipelineData.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm text-slate-400">{entry.name}: {entry.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Top Opportunities */}
      {data.top_opportunities && data.top_opportunities.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              {t('dashboard.topOpportunities')}
            </h3>
            <button
              onClick={() => router.push('/opportunities')}
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              View all <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            {data.top_opportunities.slice(0, 5).map((opp: any, index: number) => (
              <motion.div
                key={opp.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="flex items-center gap-4 p-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 hover:border-white/10 transition-all cursor-pointer"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center text-white font-bold">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{opp.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                      ${opp.stage === 'fechado' ? 'status-success' :
                        opp.stage === 'perdido' ? 'status-error' :
                          opp.stage === 'qualificacao' ? 'status-info' :
                            'status-warning'} border`}
                    >
                      {t(`opportunity.stage.${opp.stage}`) || opp.stage}
                    </span>
                    <span className="text-xs text-slate-500">{opp.probability}%</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-green-400">{formatCurrency(opp.value || 0)}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Activities */}
      {data.recent_activities && data.recent_activities.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-cyan-400" />
              {t('dashboard.recentActivities')}
            </h3>
            <button
              onClick={() => router.push('/activities')}
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              View all <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            {data.recent_activities.slice(0, 5).map((activity: any, index: number) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                className="flex items-center gap-4 p-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 hover:border-white/10 transition-all"
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center
                  ${activity.status === 'completed' ? 'bg-green-500/20' :
                    activity.status === 'cancelled' ? 'bg-red-500/20' :
                      'bg-yellow-500/20'}`}
                >
                  {activity.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  ) : activity.status === 'cancelled' ? (
                    <AlertCircle className="w-5 h-5 text-red-400" />
                  ) : (
                    <Clock className="w-5 h-5 text-yellow-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{activity.subject}</p>
                  <p className="text-sm text-slate-400 capitalize">{activity.type?.replace('_', ' ')}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium border
                  ${activity.status === 'completed' ? 'status-success' :
                    activity.status === 'cancelled' ? 'status-error' :
                      'status-warning'}`}
                >
                  {activity.status === 'completed' ? t('activities.completed') :
                    activity.status === 'cancelled' ? t('activities.cancelled') :
                      t('activities.pending')}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
