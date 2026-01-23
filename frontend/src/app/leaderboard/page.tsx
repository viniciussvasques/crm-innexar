'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import { useLanguage } from '@/contexts/LanguageContext'
import { motion } from 'framer-motion'
import { Trophy, Medal, TrendingUp, DollarSign, Target, Award, Zap, Users } from 'lucide-react'

interface UserStats {
  id: number
  name: string
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
    if (!token) { router.push('/login'); return }
    loadLeaderboard()
  }, [router, period, sortBy])

  const loadLeaderboard = async () => {
    try {
      setLoading(true)
      const mockData: LeaderboardData = {
        users: [
          { id: 1, name: 'João Silva', role: 'vendedor', total_opportunities: 45, won_opportunities: 18, total_value: 450000, conversion_rate: 40, avg_deal_size: 25000, points: 1850, level: 12, badges: ['top_seller', 'fast_closer', 'team_player'], rank: 1 },
          { id: 2, name: 'Maria Santos', role: 'vendedor', total_opportunities: 38, won_opportunities: 15, total_value: 375000, conversion_rate: 39.5, avg_deal_size: 25000, points: 1720, level: 11, badges: ['consistent', 'quality_deals'], rank: 2 },
          { id: 3, name: 'Pedro Costa', role: 'vendedor', total_opportunities: 52, won_opportunities: 16, total_value: 320000, conversion_rate: 30.8, avg_deal_size: 20000, points: 1580, level: 10, badges: ['volume_master', 'persistent'], rank: 3 }
        ],
        period: period
      }
      mockData.users.sort((a, b) => sortBy === 'value' ? b.total_value - a.total_value : sortBy === 'conversion' ? b.conversion_rate - a.conversion_rate : b.points - a.points)
      mockData.users.forEach((user, index) => { user.rank = index + 1 })
      setData(mockData)
    } catch (error) {
      console.error('Erro ao carregar leaderboard:', error)
      toast.error('Erro ao carregar leaderboard')
    } finally {
      setLoading(false)
    }
  }

  const getBadgeIcon = (badge: string) => {
    const icons: Record<string, string> = { top_seller: '🏆', fast_closer: '⚡', team_player: '🤝', consistent: '📈', quality_deals: '💎', volume_master: '📊', persistent: '🎯' }
    return icons[badge] || '🏅'
  }

  const getBadgeName = (badge: string) => {
    const names: Record<string, string> = { top_seller: 'Top Vendedor', fast_closer: 'Fechador Rápido', team_player: 'Espírito de Equipe', consistent: 'Consistente', quality_deals: 'Qualidade Premium', volume_master: 'Volume Master', persistent: 'Persistente' }
    return names[badge] || badge
  }

  const getLevelColor = (level: number) => level >= 15 ? 'from-purple-500 to-pink-500' : level >= 10 ? 'from-blue-500 to-purple-500' : level >= 5 ? 'from-green-500 to-blue-500' : 'from-gray-500 to-green-500'

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-48"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (<div key={i} className="h-48 bg-white/5 rounded-xl"></div>))}
          </div>
        </div>
      </div>
    )
  }

  if (!data) return <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 text-center text-slate-400">Nenhum dado encontrado</div>

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <Trophy className="w-8 h-8 text-amber-400" />
              Leaderboard
            </h1>
            <p className="text-slate-400 mt-1">Compita e ganhe badges por seu desempenho!</p>
          </div>
          <div className="flex gap-3">
            <select value={period} onChange={(e) => setPeriod(e.target.value)} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none">
              <option value="week" className="bg-slate-900">Esta Semana</option>
              <option value="month" className="bg-slate-900">Este Mês</option>
              <option value="quarter" className="bg-slate-900">Este Trimestre</option>
              <option value="year" className="bg-slate-900">Este Ano</option>
            </select>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none">
              <option value="points" className="bg-slate-900">Pontos</option>
              <option value="value" className="bg-slate-900">Valor Total</option>
              <option value="conversion" className="bg-slate-900">Taxa de Conversão</option>
            </select>
          </div>
        </div>

        {/* Top 3 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data.users.slice(0, 3).map((user, index) => {
            const colors = ['from-amber-500 to-yellow-400', 'from-slate-400 to-gray-300', 'from-orange-500 to-amber-400']
            const icons = ['🥇', '🥈', '🥉']
            return (
              <motion.div key={user.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }}
                className={`relative bg-gradient-to-br ${colors[index]} p-[1px] rounded-2xl`}>
                <div className="bg-slate-900 rounded-2xl p-6 h-full">
                  <div className="text-center">
                    <div className="text-5xl mb-4">{icons[index]}</div>
                    <div className={`w-20 h-20 mx-auto rounded-full bg-gradient-to-br ${getLevelColor(user.level)} flex items-center justify-center text-white text-2xl font-bold mb-3 shadow-lg`}>
                      {user.level}
                    </div>
                    <h3 className="text-xl font-bold text-white">{user.name}</h3>
                    <p className="text-slate-400 mb-4">{user.points.toLocaleString()} pontos</p>
                    <div className="flex flex-wrap justify-center gap-2 mb-4">
                      {user.badges.slice(0, 3).map((badge) => (
                        <div key={badge} className="flex items-center gap-1 bg-white/10 px-2 py-1 rounded-full text-xs text-white">
                          <span>{getBadgeIcon(badge)}</span>
                          <span className="hidden sm:inline">{getBadgeName(badge)}</span>
                        </div>
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><p className="text-slate-500">Conversão</p><p className="font-bold text-emerald-400">{user.conversion_rate}%</p></div>
                      <div><p className="text-slate-500">Valor Total</p><p className="font-bold text-blue-400">R$ {(user.total_value / 1000).toFixed(0)}k</p></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Full Ranking */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-white/10"><h3 className="text-lg font-semibold text-white">Ranking Completo</h3></div>
          <div className="divide-y divide-white/5">
            {data.users.map((user, i) => (
              <motion.div key={user.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="p-6 hover:bg-white/[0.03] transition-colors">
                <div className="flex items-center gap-6">
                  <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center font-bold text-lg text-white">
                    {user.rank <= 3 ? ['🥇', '🥈', '🥉'][user.rank - 1] : user.rank}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-lg font-semibold text-white">{user.name}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${user.role === 'admin' ? 'bg-purple-500/20 text-purple-300' : 'bg-blue-500/20 text-blue-300'}`}>{user.role}</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {user.badges.map((badge) => (<div key={badge} className="flex items-center gap-1 bg-white/10 px-3 py-1 rounded-full text-sm text-white"><span>{getBadgeIcon(badge)}</span><span>{getBadgeName(badge)}</span></div>))}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div><p className="text-slate-500">Pontos</p><p className="font-bold text-purple-400">{user.points.toLocaleString()}</p></div>
                      <div><p className="text-slate-500">Conversão</p><p className="font-bold text-emerald-400">{user.conversion_rate}%</p></div>
                      <div><p className="text-slate-500">Valor Total</p><p className="font-bold text-blue-400">R$ {(user.total_value / 1000).toFixed(0)}k</p></div>
                      <div><p className="text-slate-500">Ticket Médio</p><p className="font-bold text-amber-400">R$ {(user.avg_deal_size / 1000).toFixed(0)}k</p></div>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${getLevelColor(user.level)} flex items-center justify-center text-white text-xl font-bold shadow-lg`}>{user.level}</div>
                    <p className="text-xs text-slate-500 mt-1">Nível</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* How to Earn Points */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Target className="w-5 h-5 text-blue-400" /> Como Ganhar Pontos</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: '💼', title: 'Fechar Negócios', desc: 'Ganhe pontos baseados no valor do negócio fechado' },
              { icon: '⚡', title: 'Velocidade', desc: 'Bônus por fechar negócios rapidamente' },
              { icon: '🎯', title: 'Qualidade', desc: 'Pontos extras por deals de alto valor' },
              { icon: '📈', title: 'Consistência', desc: 'Bônus por manter performance consistente' },
              { icon: '🤝', title: 'Equipe', desc: 'Pontos por colaboração e ajuda aos colegas' },
              { icon: '📚', title: 'Aprendizado', desc: 'Complete treinamentos e ganhe pontos' }
            ].map((item, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-4">
                <div className="text-2xl mb-2">{item.icon}</div>
                <h4 className="font-medium text-white mb-1">{item.title}</h4>
                <p className="text-sm text-slate-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
