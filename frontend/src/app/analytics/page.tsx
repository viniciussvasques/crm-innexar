'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts'

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
      const response = await api.get(`/api/dashboard/admin?period=${period}`)
      // Simular dados de métricas por vendedor
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
    if (!token) {
      router.push('/login')
      return
    }
    loadMetrics()
  }, [router, loadMetrics, period])

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28DFF']

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  const chartData = metrics.map(m => ({
    name: m.user_name,
    deals: m.total_deals,
    value: m.total_value,
    conversion: m.conversion_rate
  }))

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">{t('analytics.title')}</h2>
          <p className="mt-2 text-gray-600">{t('analytics.salesPerformance')}</p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as 'week' | 'month' | 'year')}
          className="px-4 py-2 border border-gray-300 rounded-md"
        >
          <option value="week">{t('analytics.week')}</option>
          <option value="month">{t('analytics.month')}</option>
          <option value="year">{t('analytics.year')}</option>
        </select>
      </div>

      {/* Top Vendedores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">{t('analytics.topSellers')}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="deals" name={t('analytics.deals')} fill="#8884d8" />
              <Bar dataKey="value" name={t('common.value')} fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">{t('analytics.conversionRate')}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="conversion" name={t('analytics.conversionRate')} stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Métricas dos Vendedores */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">{t('analytics.sellerMetrics')}</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.name')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('analytics.totalDeals')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.value')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('analytics.conversionRate')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('analytics.averageDeal')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics.map((metric) => (
                <tr key={metric.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {metric.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.total_deals}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${metric.total_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.conversion_rate}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${metric.average_deal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
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

