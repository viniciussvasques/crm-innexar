'use client'

import React, { useEffect, useState, useCallback, useMemo, memo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { DashboardData, User } from '@/types'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { useLanguage } from '@/contexts/LanguageContext'

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
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error)
      // Manter dados padrão em caso de erro
      setData({
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
        console.error('Erro ao parsear usuário:', error)
        router.push('/login')
      }
    } else {
      router.push('/login')
    }
  }, [router, loadDashboard])

  const COLORS = ['#3B82F6', '#F59E0B', '#EF4444', '#10B981', '#8B5CF6']

  const getStageColor = (stage: string): string => {
    const colors: Record<string, string> = {
      qualificacao: '#3B82F6',
      proposta: '#F59E0B',
      negociacao: '#EF4444',
      fechado: '#10B981',
      perdido: '#6B7280'
    }
    return colors[stage] || '#6B7280'
  }

  // Preparar dados para gráficos
  const pipelineData = data?.stats?.opportunities_by_stage 
    ? Object.entries(data.stats.opportunities_by_stage).map(([stage, count]) => ({
        name: t(`opportunity.stage.${stage}`) || stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: count as number,
        stage: stage,
        fill: getStageColor(stage)
      }))
    : []

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

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900">{t('dashboard.title')}</h2>
        <p className="mt-2 text-gray-600">
          {user?.role === 'admin' ? t('dashboard.teamOverview') : t('dashboard.overview')}
        </p>
      </div>

      {data && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">{t('dashboard.totalContacts')}</h3>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{data.stats?.total_contacts || 0}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">{t('dashboard.totalOpportunities')}</h3>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{data.stats?.total_opportunities || 0}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">{t('dashboard.totalValue')}</h3>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {Number(data.stats?.total_value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-full">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">{t('dashboard.pendingActivities')}</h3>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{data.stats?.pending_activities || 0}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Gráficos */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Pipeline por Estágio */}
            {pipelineData.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.opportunitiesByStage')}</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pipelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Distribuição do Pipeline */}
            {pipelineData.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.pipelineDistribution')}</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <PieChart>
                    <Pie
                      data={pipelineData}
                      cx="50%"
                      cy="45%"
                      labelLine={false}
                      label={false}
                      outerRadius={90}
                      innerRadius={50}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pipelineData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value: number, name: string, props: any) => {
                        const total = pipelineData.reduce((sum: number, item: any) => sum + item.value, 0)
                        const percent = total > 0 ? ((value / total) * 100).toFixed(1) : '0'
                        return [`${value} (${percent}%)`, props.payload.name]
                      }}
                    />
                    <Legend 
                      verticalAlign="bottom" 
                      height={80}
                      wrapperStyle={{ paddingTop: '20px' }}
                      formatter={(value, entry: any) => {
                        const total = pipelineData.reduce((sum: number, item: any) => sum + item.value, 0)
                        const percent = total > 0 ? ((entry.payload.value / total) * 100).toFixed(1) : '0'
                        return `${value}: ${entry.payload.value} (${percent}%)`
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Pipeline em Grid */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">{t('dashboard.salesPipeline')}</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              {data.stats?.opportunities_by_stage && Object.entries(data.stats.opportunities_by_stage).map(([stage, count], index) => (
                <div key={stage} className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200 hover:shadow-md transition-shadow">
                  <p className="text-4xl font-bold text-blue-600 mb-2">{count as number}</p>
                  <p className="text-sm font-medium text-blue-800 capitalize">
                    {t(`opportunity.stage.${stage}`) || stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <div className="w-full bg-blue-200 rounded-full h-2 mt-3">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${(() => {
                          if (!data.stats?.opportunities_by_stage) return 0
                          const total = Object.values(data.stats.opportunities_by_stage).reduce((a: any, b: any) => (Number(a) || 0) + (Number(b) || 0), 0)
                          if (total === 0) return 0
                          const countNum = Number(count) || 0
                          const totalNum = Number(total) || 1
                          return (countNum / totalNum) * 100
                        })()}%`
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Opportunities */}
          {data.top_opportunities && data.top_opportunities.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">{t('dashboard.topOpportunities')}</h3>
              <div className="overflow-hidden">
                <div className="space-y-4">
                  {data.top_opportunities.slice(0, 5).map((opp: any, index: number) => (
                    <div key={opp.id} className="flex items-center gap-4 p-4 bg-gradient-to-r from-gray-50 to-white border border-gray-200 rounded-xl hover:shadow-md transition-all duration-200">
                      <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-gray-900 truncate">{opp.name}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                            opp.stage === 'fechado' ? 'bg-green-100 text-green-800' :
                            opp.stage === 'perdido' ? 'bg-red-100 text-red-800' :
                            opp.stage === 'qualificacao' ? 'bg-blue-100 text-blue-800' :
                            opp.stage === 'proposta' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-purple-100 text-purple-800'
                          }`}>
                            {t(`opportunity.stage.${opp.stage}`) || opp.stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                          <span className="text-sm text-gray-500">
                            {opp.probability}% {t('opportunities.probability')}
                          </span>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-2xl font-bold text-green-600">
                          {Number(opp.value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, style: 'currency', currency: 'BRL' })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recent Activities */}
          {data.recent_activities && data.recent_activities.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.recentActivities')}</h3>
              <div className="space-y-3">
                {data.recent_activities.slice(0, 5).map((activity: any) => (
                  <div key={activity.id} className="flex items-center gap-4 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{activity.subject}</p>
                      <p className="text-sm text-gray-500">{activity.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      activity.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : activity.status === 'cancelled'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {activity.status === 'completed' ? t('activities.completed') : activity.status === 'cancelled' ? t('activities.cancelled') : t('activities.pending')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
