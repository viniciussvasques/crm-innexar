'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import { useLanguage } from '@/contexts/LanguageContext'

interface UserStats {
  id: number
  name: string
  avatar?: string
  role: string
  total_opportunities: number
  won_opportunities: number
  total_value: number
  conversion_rate: number
  avg_deal_size: number
  points: number
  level: number
  badges: string[]
  rank: number
}

interface LeaderboardData {
  users: UserStats[]
  period: string
}

export default function LeaderboardPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [data, setData] = useState<LeaderboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('month')
  const [sortBy, setSortBy] = useState<'points' | 'value' | 'conversion'>('points')

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
    loadLeaderboard()
  }, [router, period, sortBy])

  const loadLeaderboard = async () => {
    try {
      setLoading(true)
      // Simulando dados por enquanto - em produção viria da API
      const mockData: LeaderboardData = {
        users: [
          {
            id: 1,
            name: 'João Silva',
            role: 'vendedor',
            total_opportunities: 45,
            won_opportunities: 18,
            total_value: 450000,
            conversion_rate: 40,
            avg_deal_size: 25000,
            points: 1850,
            level: 12,
            badges: ['top_seller', 'fast_closer', 'team_player'],
            rank: 1
          },
          {
            id: 2,
            name: 'Maria Santos',
            role: 'vendedor',
            total_opportunities: 38,
            won_opportunities: 15,
            total_value: 375000,
            conversion_rate: 39.5,
            avg_deal_size: 25000,
            points: 1720,
            level: 11,
            badges: ['consistent', 'quality_deals'],
            rank: 2
          },
          {
            id: 3,
            name: 'Pedro Costa',
            role: 'vendedor',
            total_opportunities: 52,
            won_opportunities: 16,
            total_value: 320000,
            conversion_rate: 30.8,
            avg_deal_size: 20000,
            points: 1580,
            level: 10,
            badges: ['volume_master', 'persistent'],
            rank: 3
          }
        ],
        period: period
      }

      // Ordenar por critério selecionado
      mockData.users.sort((a, b) => {
        switch (sortBy) {
          case 'value':
            return b.total_value - a.total_value
          case 'conversion':
            return b.conversion_rate - a.conversion_rate
          default:
            return b.points - a.points
        }
      })

      // Atualizar ranks
      mockData.users.forEach((user, index) => {
        user.rank = index + 1
      })

      setData(mockData)
    } catch (error) {
      console.error('Erro ao carregar leaderboard:', error)
      toast.error('Erro ao carregar leaderboard')
    } finally {
      setLoading(false)
    }
  }

  const getBadgeIcon = (badge: string) => {
    const icons: Record<string, string> = {
      top_seller: '🏆',
      fast_closer: '⚡',
      team_player: '🤝',
      consistent: '📈',
      quality_deals: '💎',
      volume_master: '📊',
      persistent: '🎯'
    }
    return icons[badge] || '🏅'
  }

  const getBadgeName = (badge: string) => {
    const names: Record<string, string> = {
      top_seller: 'Top Vendedor',
      fast_closer: 'Fechador Rápido',
      team_player: 'Espírito de Equipe',
      consistent: 'Consistente',
      quality_deals: 'Qualidade Premium',
      volume_master: 'Volume Master',
      persistent: 'Persistente'
    }
    return names[badge] || badge
  }

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1: return '🥇'
      case 2: return '🥈'
      case 3: return '🥉'
      default: return `🏅`
    }
  }

  const getLevelColor = (level: number) => {
    if (level >= 15) return 'from-purple-500 to-pink-500'
    if (level >= 10) return 'from-blue-500 to-purple-500'
    if (level >= 5) return 'from-green-500 to-blue-500'
    return 'from-gray-500 to-green-500'
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

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Nenhum dado encontrado</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">🏆 Leaderboard</h2>
          <p className="text-gray-600 mt-2">Compita e ganhe badges por seu desempenho!</p>
        </div>
        <div className="flex gap-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="week">Esta Semana</option>
            <option value="month">Este Mês</option>
            <option value="quarter">Este Trimestre</option>
            <option value="year">Este Ano</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="points">Pontos</option>
            <option value="value">Valor Total</option>
            <option value="conversion">Taxa de Conversão</option>
          </select>
        </div>
      </div>

      {/* Top 3 - Destaque */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {data.users.slice(0, 3).map((user, index) => (
          <div key={user.id} className={`relative bg-white rounded-xl shadow-lg p-6 border-2 ${
            index === 0 ? 'border-yellow-400 bg-gradient-to-br from-yellow-50 to-white' :
            index === 1 ? 'border-gray-400 bg-gradient-to-br from-gray-50 to-white' :
            'border-orange-400 bg-gradient-to-br from-orange-50 to-white'
          }`}>
            <div className="text-center">
              <div className="text-6xl mb-4">{getRankIcon(user.rank)}</div>
              <div className={`w-20 h-20 mx-auto rounded-full bg-gradient-to-br ${getLevelColor(user.level)} flex items-center justify-center text-white text-2xl font-bold mb-3 shadow-lg`}>
                {user.level}
              </div>
              <h3 className="text-xl font-bold text-gray-900">{user.name}</h3>
              <p className="text-gray-600 mb-4">{user.points.toLocaleString()} pontos</p>

              {/* Badges */}
              <div className="flex flex-wrap justify-center gap-2 mb-4">
                {user.badges.slice(0, 3).map((badge) => (
                  <div key={badge} className="flex items-center gap-1 bg-white bg-opacity-70 px-2 py-1 rounded-full text-xs">
                    <span>{getBadgeIcon(badge)}</span>
                    <span className="hidden sm:inline">{getBadgeName(badge)}</span>
                  </div>
                ))}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Conversão</p>
                  <p className="font-bold text-green-600">{user.conversion_rate}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Valor Total</p>
                  <p className="font-bold text-blue-600">R$ {(user.total_value / 1000).toFixed(0)}k</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Ranking Completo */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Ranking Completo</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {data.users.map((user) => (
            <div key={user.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-6">
                {/* Rank */}
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center font-bold text-lg">
                    {user.rank <= 3 ? getRankIcon(user.rank) : user.rank}
                  </div>
                </div>

                {/* User Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-lg font-semibold text-gray-900">{user.name}</h4>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.role === 'vendedor' ? 'bg-blue-100 text-blue-800' :
                      user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {user.role}
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {user.badges.map((badge) => (
                      <div key={badge} className="flex items-center gap-1 bg-gray-100 px-3 py-1 rounded-full text-sm">
                        <span>{getBadgeIcon(badge)}</span>
                        <span>{getBadgeName(badge)}</span>
                      </div>
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Pontos</p>
                      <p className="font-bold text-purple-600">{user.points.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Conversão</p>
                      <p className="font-bold text-green-600">{user.conversion_rate}%</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Valor Total</p>
                      <p className="font-bold text-blue-600">R$ {(user.total_value / 1000).toFixed(0)}k</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Ticket Médio</p>
                      <p className="font-bold text-orange-600">R$ {(user.avg_deal_size / 1000).toFixed(0)}k</p>
                    </div>
                  </div>
                </div>

                {/* Level */}
                <div className="flex-shrink-0 text-center">
                  <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${getLevelColor(user.level)} flex items-center justify-center text-white text-xl font-bold shadow-lg`}>
                    {user.level}
                  </div>
                  <p className="text-xs text-gray-600 mt-1">Nível</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sistema de Pontos */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Como Ganhar Pontos</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">💼</div>
            <h4 className="font-medium mb-1">Fechar Negócios</h4>
            <p className="text-sm text-gray-600">Ganhe pontos baseados no valor do negócio fechado</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">⚡</div>
            <h4 className="font-medium mb-1">Velocidade</h4>
            <p className="text-sm text-gray-600">Bônus por fechar negócios rapidamente</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">🎯</div>
            <h4 className="font-medium mb-1">Qualidade</h4>
            <p className="text-sm text-gray-600">Pontos extras por deals de alto valor</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">📈</div>
            <h4 className="font-medium mb-1">Consistência</h4>
            <p className="text-sm text-gray-600">Bônus por manter performance consistente</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">🤝</div>
            <h4 className="font-medium mb-1">Equipe</h4>
            <p className="text-sm text-gray-600">Pontos por colaboração e ajuda aos colegas</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="text-2xl mb-2">📚</div>
            <h4 className="font-medium mb-1">Aprendizado</h4>
            <p className="text-sm text-gray-600">Complete treinamentos e ganhe pontos</p>
          </div>
        </div>
      </div>
    </div>
  )
}
