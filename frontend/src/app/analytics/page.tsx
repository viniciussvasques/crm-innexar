'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion } from 'framer-motion'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  LineChart, Line, AreaChart, Area
} from 'recharts'
import { BarChart3, TrendingUp, DollarSign, Users, Calendar } from 'lucide-react'

interface SellerMetrics {
  user_id: number
  user_name: string
  total_deals: number
  total_value: number
  conversion_rate: number
  average_deal: number
}

export default function AnalyticsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [metrics, setMetrics] = useState<SellerMetrics[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month')

  const loadMetrics = useCallback(async () => {
    try {
      await api.get(`/api/dashboard/admin?period=${period}`)
      setMetrics([
        { user_id: 1, user_name: 'Vendedor 1', total_deals: 15, total_value: 150000, conversion_rate: 65, average_deal: 10000 },
        { user_id: 2, user_name: 'Vendedor 2', total_deals: 12, total_value: 120000, conversion_rate: 58, average_deal: 10000 },
        { user_id: 3, user_name: 'Vendedor 3', total_deals: 8, total_value: 80000, conversion_rate: 45, average_deal: 10000 }
      ])
    } catch (error) {
      console.error('Erro ao carregar métricas:', error)
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadMetrics()
  }, [router, loadMetrics, period])

  const totalValue = metrics.reduce((sum, m) => sum + m.total_value, 0)
  const totalDeals = metrics.reduce((sum, m) => sum + m.total_deals, 0)
  const avgConversion = metrics.length > 0 ? Math.round(metrics.reduce((sum, m) => sum + m.conversion_rate, 0) / metrics.length) : 0

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

  const chartData = metrics.map(m => ({
    name: m.user_name,
    deals: m.total_deals,
    value: m.total_value / 1000,
    conversion: m.conversion_rate
  }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-emerald-400" />
              {t('analytics.title')}
            </h1>
            <p className="text-slate-400 mt-1">{t('analytics.salesPerformance')}</p>
          </div>
          <div className="flex bg-white/5 border border-white/10 rounded-lg p-1">
            {['week', 'month', 'year'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p as 'week' | 'month' | 'year')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${period === p ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                  }`}
              >
                {t(`analytics.${p}`)}
              </button>
            ))}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Revenue', value: `R$ ${(totalValue / 1000).toFixed(0)}k`, icon: DollarSign, color: 'emerald' },
            { label: 'Total Deals', value: totalDeals, icon: BarChart3, color: 'blue' },
            { label: 'Avg. Conversion', value: `${avgConversion}%`, icon: TrendingUp, color: 'purple' },
            { label: 'Active Sellers', value: metrics.length, icon: Users, color: 'amber' }
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

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">{t('analytics.topSellers')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Legend />
                <Bar dataKey="deals" name="Deals" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="value" name="Value (k)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">{t('analytics.conversionRate')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorConversion" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="conversion" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorConversion)" />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Metrics Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden"
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-semibold text-white">{t('analytics.sellerMetrics')}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('analytics.totalDeals')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.value')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('analytics.conversionRate')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('analytics.averageDeal')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {metrics.map((metric, i) => (
                  <motion.tr
                    key={metric.user_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className="hover:bg-white/[0.03] transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
                          {metric.user_name.charAt(0)}
                        </div>
                        <span className="text-white font-medium">{metric.user_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">{metric.total_deals}</td>
                    <td className="px-6 py-4 text-emerald-400 font-semibold">R$ {metric.total_value.toLocaleString('pt-BR')}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden max-w-24">
                          <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full" style={{ width: `${metric.conversion_rate}%` }}></div>
                        </div>
                        <span className="text-slate-400 text-sm">{metric.conversion_rate}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">R$ {metric.average_deal.toLocaleString('pt-BR')}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
