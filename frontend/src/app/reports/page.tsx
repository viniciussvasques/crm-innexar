'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import Select from '@/components/Select'
import { useLanguage } from '@/contexts/LanguageContext'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts'

interface ReportData {
  opportunities: any[]
  contacts: any[]
  activities: any[]
  commissions: any[]
  users: any[]
}

interface ChartData {
  name: string
  value: number
  [key: string]: any
}

export default function ReportsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30') // dias
  const [selectedUser, setSelectedUser] = useState('all')

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
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

      setData({
        opportunities: oppsRes.data,
        contacts: contactsRes.data,
        activities: activitiesRes.data,
        commissions: commissionsRes.data,
        users: usersRes.data
      })
    } catch (error) {
      console.error('Erro ao carregar dados dos relatórios:', error)
      toast.error('Erro ao carregar dados dos relatórios')
    } finally {
      setLoading(false)
    }
  }

  // Métricas calculadas
  const metrics = useMemo(() => {
    if (!data) return null

    const filteredOpps = data.opportunities.filter(opp => {
      if (selectedUser !== 'all') {
        // TODO: filtrar por usuário responsável
        return true
      }
      return true
    })

    const totalOpportunities = filteredOpps.length
    const totalValue = filteredOpps.reduce((sum, opp) => sum + (opp.value || 0), 0)
    const wonOpportunities = filteredOpps.filter(opp => opp.stage === 'fechado').length
    const conversionRate = totalOpportunities > 0 ? (wonOpportunities / totalOpportunities) * 100 : 0

    const opportunitiesByStage = filteredOpps.reduce((acc, opp) => {
      acc[opp.stage] = (acc[opp.stage] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const revenueByMonth = filteredOpps
      .filter(opp => opp.stage === 'fechado' && opp.closed_at)
      .reduce((acc, opp) => {
        const month = new Date(opp.closed_at).toISOString().slice(0, 7) // YYYY-MM
        acc[month] = (acc[month] || 0) + (opp.value || 0)
        return acc
      }, {} as Record<string, number>)

    return {
      totalOpportunities,
      totalValue,
      wonOpportunities,
      conversionRate,
      opportunitiesByStage,
      revenueByMonth,
      avgDealSize: totalOpportunities > 0 ? totalValue / totalOpportunities : 0
    }
  }, [data, selectedUser])

  // Dados para gráficos
  const stageDistributionData = useMemo(() => {
    if (!metrics) return []
    return Object.entries(metrics.opportunitiesByStage).map(([stage, count]) => ({
      name: t(`opportunity.stage.${stage}`),
      value: count,
      fill: getStageColor(stage)
    }))
  }, [metrics, t])

  const revenueData = useMemo(() => {
    if (!metrics) return []
    return Object.entries(metrics.revenueByMonth)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, value]) => ({
        month: new Date(month + '-01').toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }),
        revenue: value
      }))
  }, [metrics])

  function getStageColor(stage: string): string {
    const colors: Record<string, string> = {
      qualificacao: '#3B82F6',
      proposta: '#F59E0B',
      negociacao: '#EF4444',
      fechado: '#10B981',
      perdido: '#6B7280'
    }
    return colors[stage] || '#6B7280'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  if (!data || !metrics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{t('reports.noData')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">{t('reports.title')}</h2>
        <div className="flex gap-4">
          <Select
            label={t('reports.dateRange')}
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            options={[
              { value: '7', label: t('reports.last7days') },
              { value: '30', label: t('reports.last30days') },
              { value: '90', label: t('reports.last90days') },
              { value: '365', label: t('reports.lastYear') }
            ]}
          />
          <Select
            label={t('reports.user')}
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            options={[
              { value: 'all', label: t('reports.allUsers') },
              ...data.users.map((user: any) => ({
                value: user.id.toString(),
                label: user.name
              }))
            ]}
          />
        </div>
      </div>

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">{t('reports.totalOpportunities')}</h3>
          <p className="text-3xl font-bold text-gray-900">{metrics.totalOpportunities}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">{t('reports.totalValue')}</h3>
          <p className="text-3xl font-bold text-green-600">
            R$ {metrics.totalValue.toLocaleString('pt-BR')}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">{t('reports.conversionRate')}</h3>
          <p className="text-3xl font-bold text-blue-600">
            {metrics.conversionRate.toFixed(1)}%
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">{t('reports.avgDealSize')}</h3>
          <p className="text-3xl font-bold text-purple-600">
            R$ {metrics.avgDealSize.toLocaleString('pt-BR')}
          </p>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição por Estágio */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {t('reports.stageDistribution')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stageDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {stageDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Receita por Mês */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {t('reports.revenueByMonth')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => [`R$ ${Number(value).toLocaleString('pt-BR')}`, 'Receita']} />
              <Area type="monotone" dataKey="revenue" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabela de Top Oportunidades */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {t('reports.topOpportunities')}
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('common.name')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('common.value')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('common.stage')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('reports.contact')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.opportunities
                .sort((a, b) => (b.value || 0) - (a.value || 0))
                .slice(0, 10)
                .map((opp) => (
                  <tr key={opp.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {opp.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      R$ {(opp.value || 0).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        opp.stage === 'fechado' ? 'bg-green-100 text-green-800' :
                        opp.stage === 'perdido' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {t(`opportunity.stage.${opp.stage}`)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {opp.contact_name || 'N/A'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
