'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Select from '@/components/Select'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion } from 'framer-motion'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'
import { FileBarChart, DollarSign, TrendingUp, Target, Users } from 'lucide-react'

interface ReportData {
  opportunities: any[]
  contacts: any[]
  activities: any[]
  commissions: any[]
  users: any[]
}

export default function ReportsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30')
  const [selectedUser, setSelectedUser] = useState('all')

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadReportData()
  }, [router, dateRange, selectedUser])

  const loadReportData = async () => {
    try {
      setLoading(true)
      const [oppsRes, contactsRes, activitiesRes, commissionsRes, usersRes] = await Promise.all([
        api.get('/api/opportunities/'),
        api.get('/api/contacts/'),
        api.get('/api/activities/'),
        api.get('/api/commissions/'),
        api.get('/api/users/')
      ])
      setData({ opportunities: oppsRes.data, contacts: contactsRes.data, activities: activitiesRes.data, commissions: commissionsRes.data, users: usersRes.data })
    } catch (error) {
      console.error('Erro ao carregar dados dos relatórios:', error)
      toast.error('Erro ao carregar dados dos relatórios')
    } finally {
      setLoading(false)
    }
  }

  const metrics = useMemo(() => {
    if (!data) return null
    const filteredOpps = data.opportunities
    const totalOpportunities = filteredOpps.length
    const totalValue = filteredOpps.reduce((sum, opp) => sum + (opp.value || 0), 0)
    const wonOpportunities = filteredOpps.filter(opp => opp.stage === 'fechado').length
    const conversionRate = totalOpportunities > 0 ? (wonOpportunities / totalOpportunities) * 100 : 0
    const opportunitiesByStage = filteredOpps.reduce((acc, opp) => { acc[opp.stage] = (acc[opp.stage] || 0) + 1; return acc }, {} as Record<string, number>)
    const revenueByMonth = filteredOpps.filter(opp => opp.stage === 'fechado' && opp.closed_at).reduce((acc, opp) => {
      const month = new Date(opp.closed_at).toISOString().slice(0, 7)
      acc[month] = (acc[month] || 0) + (opp.value || 0)
      return acc
    }, {} as Record<string, number>)
    return { totalOpportunities, totalValue, wonOpportunities, conversionRate, opportunitiesByStage, revenueByMonth, avgDealSize: totalOpportunities > 0 ? totalValue / totalOpportunities : 0 }
  }, [data])

  const stageDistributionData = useMemo(() => {
    if (!metrics) return []
    const colors: Record<string, string> = { qualificacao: '#3B82F6', proposta: '#F59E0B', negociacao: '#EF4444', fechado: '#10B981', perdido: '#6B7280' }
    return Object.entries(metrics.opportunitiesByStage).map(([stage, count]) => ({ name: t(`opportunity.stage.${stage}`), value: count, fill: colors[stage] || '#6B7280' }))
  }, [metrics, t])

  const revenueData = useMemo(() => {
    if (!metrics) return []
    return Object.entries(metrics.revenueByMonth).sort(([a], [b]) => a.localeCompare(b)).map(([month, value]) => ({ month: new Date(month + '-01').toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }), revenue: value }))
  }, [metrics])

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

  if (!data || !metrics) return (<div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 text-center text-slate-400">{t('reports.noData')}</div>)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <FileBarChart className="w-8 h-8 text-cyan-400" />
              {t('reports.title')}
            </h1>
          </div>
          <div className="flex gap-4">
            <select value={dateRange} onChange={(e) => setDateRange(e.target.value)} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none">
              <option value="7" className="bg-slate-900">{t('reports.last7days')}</option>
              <option value="30" className="bg-slate-900">{t('reports.last30days')}</option>
              <option value="90" className="bg-slate-900">{t('reports.last90days')}</option>
              <option value="365" className="bg-slate-900">{t('reports.lastYear')}</option>
            </select>
            <select value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none">
              <option value="all" className="bg-slate-900">{t('reports.allUsers')}</option>
              {data.users.map((user: any) => (<option key={user.id} value={user.id.toString()} className="bg-slate-900">{user.name}</option>))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: t('reports.totalOpportunities'), value: metrics.totalOpportunities, icon: Target, color: 'blue' },
            { label: t('reports.totalValue'), value: `R$ ${(metrics.totalValue / 1000).toFixed(0)}k`, icon: DollarSign, color: 'emerald' },
            { label: t('reports.conversionRate'), value: `${metrics.conversionRate.toFixed(1)}%`, icon: TrendingUp, color: 'purple' },
            { label: t('reports.avgDealSize'), value: `R$ ${(metrics.avgDealSize / 1000).toFixed(0)}k`, icon: Users, color: 'amber' }
          ].map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div><p className="text-slate-400 text-sm">{stat.label}</p><p className="text-2xl font-bold text-white mt-1">{stat.value}</p></div>
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}><stat.icon className={`w-5 h-5 text-${stat.color}-400`} /></div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">{t('reports.stageDistribution')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={stageDistributionData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {stageDistributionData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.fill} />))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">{t('reports.revenueByMonth')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <defs><linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.3} /><stop offset="95%" stopColor="#10B981" stopOpacity={0} /></linearGradient></defs>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} formatter={(value) => [`R$ ${Number(value).toLocaleString('pt-BR')}`, 'Receita']} />
                <Area type="monotone" dataKey="revenue" stroke="#10B981" fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Top Opportunities Table */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-white/10"><h3 className="text-lg font-semibold text-white">{t('reports.topOpportunities')}</h3></div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-white/10">
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.name')}</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.value')}</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('common.stage')}</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">{t('reports.contact')}</th>
              </tr></thead>
              <tbody className="divide-y divide-white/5">
                {data.opportunities.sort((a, b) => (b.value || 0) - (a.value || 0)).slice(0, 10).map((opp) => (
                  <tr key={opp.id} className="hover:bg-white/[0.03]">
                    <td className="px-6 py-4 text-white font-medium">{opp.name}</td>
                    <td className="px-6 py-4 text-emerald-400 font-semibold">R$ {(opp.value || 0).toLocaleString('pt-BR')}</td>
                    <td className="px-6 py-4"><span className={`px-2.5 py-1 text-xs font-medium rounded-full ${opp.stage === 'fechado' ? 'bg-emerald-500/20 text-emerald-300' : opp.stage === 'perdido' ? 'bg-red-500/20 text-red-300' : 'bg-blue-500/20 text-blue-300'}`}>{t(`opportunity.stage.${opp.stage}`)}</span></td>
                    <td className="px-6 py-4 text-slate-400">{opp.contact_name || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
