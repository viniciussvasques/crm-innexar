'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import { motion } from 'framer-motion'
import { Wallet, DollarSign, Calculator, Settings, TrendingUp, CheckCircle, Clock, Plus } from 'lucide-react'

interface CommissionStructure {
  id: number
  name: string
  weekly_base: number
  currency: string
  tiered_commissions: Array<{ min: number; max: number | null; rate: number }>
  performance_bonuses: Array<{ threshold: number; bonus: number }>
  recurring_commission_rate: number
  new_client_bonus: number
  new_client_threshold: number
  is_active: boolean
  created_at: string
}

interface Commission {
  id: number
  seller_id: number
  seller_name?: string
  deal_value: number
  commission_amount: number
  total_amount: number
  status: string
  payment_period?: string
  created_at: string
}

interface CommissionCalculation {
  deal_value: number
  structure_used: string
  calculation: {
    weekly_base: number
    commission_rate: number
    commission_amount: number
    performance_bonus: number
    total_amount: number
  }
}

export default function CommissionsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [structures, setStructures] = useState<CommissionStructure[]>([])
  const [commissions, setCommissions] = useState<Commission[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showStructureForm, setShowStructureForm] = useState(false)
  const [showCalculator, setShowCalculator] = useState(false)
  const [calculationResult, setCalculationResult] = useState<CommissionCalculation | null>(null)
  const [calculatorData, setCalculatorData] = useState({ deal_value: '', structure_id: '' })
  const [structureForm, setStructureForm] = useState({
    name: '', weekly_base: '100.00', currency: 'USD',
    tiered_commissions: [{ min: 0, max: null as number | null, rate: 0.05 }],
    performance_bonuses: [{ threshold: 10000, bonus: 150 }],
    recurring_commission_rate: '0.10', new_client_bonus: '100.00', new_client_threshold: '10'
  })

  const loadData = useCallback(async () => {
    try {
      const [structuresRes, commissionsRes, usersRes] = await Promise.all([
        api.get('/api/commissions/structures').catch(() => ({ data: [] })),
        api.get('/api/commissions/').catch(() => ({ data: [] })),
        api.get('/api/users/')
      ])
      setStructures(structuresRes.data || [])
      setCommissions(commissionsRes.data || [])
      setUsers(usersRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      toast.error(t('commissions.errorLoad'))
    } finally {
      setLoading(false)
    }
  }, [t])

  const handleCalculateCommission = async () => {
    try {
      const response = await api.post('/api/commissions/calculate', {
        deal_value: parseFloat(calculatorData.deal_value),
        structure_id: calculatorData.structure_id ? parseInt(calculatorData.structure_id) : null
      })
      setCalculationResult(response.data)
      toast.success(t('commissions.calculationSuccess'))
    } catch (error) {
      console.error('Erro ao calcular comissão:', error)
      toast.error(t('commissions.calculationError'))
    }
  }

  const handleCreateStructure = async () => {
    try {
      await api.post('/api/commissions/structures', structureForm)
      setShowStructureForm(false)
      loadData()
      toast.success(t('commissions.structureCreated'))
    } catch (error) {
      console.error('Erro ao criar estrutura:', error)
      toast.error(t('commissions.structureError'))
    }
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadData()
  }, [router, loadData])

  // Stats
  const stats = useMemo(() => ({
    totalCommissions: commissions.length,
    totalPaid: commissions.filter(c => c.status === 'paid').reduce((sum, c) => sum + c.commission_amount, 0),
    totalPending: commissions.filter(c => c.status !== 'paid').reduce((sum, c) => sum + c.commission_amount, 0),
    activeStructures: structures.filter(s => s.is_active).length
  }), [commissions, structures])

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="p-4 lg:p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
              <Wallet className="w-8 h-8 text-emerald-400" />
              {t('commissions.title')}
            </h1>
            <p className="text-slate-400 mt-1">Commission tracking and structures</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowCalculator(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 border border-white/10 text-white rounded-xl font-medium hover:bg-white/20 transition-colors"
            >
              <Calculator className="w-5 h-5" />
              {t('commissions.calculate')}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowStructureForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
            >
              <Plus className="w-5 h-5" />
              {t('commissions.configure')}
            </motion.button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Commissions', value: stats.totalCommissions, icon: Wallet, color: 'blue' },
            { label: 'Total Paid', value: `$${stats.totalPaid.toLocaleString()}`, icon: CheckCircle, color: 'emerald' },
            { label: 'Pending', value: `$${stats.totalPending.toLocaleString()}`, icon: Clock, color: 'amber' },
            { label: 'Active Structures', value: stats.activeStructures, icon: Settings, color: 'purple' }
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

        {/* Commission Structures */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-white mb-4">{t('commissions.structure')}</h3>
          {structures.length === 0 ? (
            <p className="text-slate-400">{t('commissions.noStructures')}</p>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {structures.map((structure) => (
                <motion.div
                  key={structure.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white/5 border border-white/10 rounded-xl p-4"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold text-white">{structure.name}</h4>
                      <p className="text-sm text-slate-400">{t('commissions.weeklyBase')}: ${structure.weekly_base} {structure.currency}</p>
                    </div>
                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${structure.is_active ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                      }`}>
                      {structure.is_active ? t('common.active') : t('common.inactive')}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500 mb-1">{t('commissions.tieredCommission')}:</p>
                      {structure.tiered_commissions.map((tier, idx) => (
                        <p key={idx} className="text-slate-300">
                          ${tier.min.toLocaleString()} - {tier.max ? `$${tier.max.toLocaleString()}` : '∞'}: {(tier.rate * 100).toFixed(1)}%
                        </p>
                      ))}
                    </div>
                    <div>
                      <p className="text-slate-500 mb-1">{t('commissions.performanceBonus')}:</p>
                      {structure.performance_bonuses.map((bonus, idx) => (
                        <p key={idx} className="text-slate-300">${bonus.threshold.toLocaleString()}: ${bonus.bonus}</p>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Commission History */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h3 className="text-xl font-semibold text-white">{t('commissions.history')}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('commissions.dealSize')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('commissions.commissionAmount')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.date')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {commissions.map((commission, i) => {
                  const user = users.find(u => u.id === commission.seller_id)
                  return (
                    <motion.tr
                      key={commission.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="hover:bg-white/[0.03] transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
                            {(user?.name || 'U').charAt(0)}
                          </div>
                          <span className="text-white font-medium">{user?.name || t('common.na')}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400">${commission.deal_value.toLocaleString()}</td>
                      <td className="px-6 py-4 text-emerald-400 font-semibold">${commission.commission_amount.toLocaleString()}</td>
                      <td className="px-6 py-4 text-slate-400">{new Date(commission.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${commission.status === 'paid'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}>
                          {commission.status === 'paid' ? t('commissions.paid') : t('commissions.pending')}
                        </span>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {commissions.length === 0 && (
            <div className="p-12 text-center">
              <Wallet className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">{t('commissions.noCommissions')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Calculator Modal */}
      <Modal isOpen={showCalculator} onClose={() => { setShowCalculator(false); setCalculationResult(null) }} title={t('commissions.calculate')} size="md">
        <div className="space-y-4">
          <Input label={t('commissions.dealSize')} type="number" step="0.01" value={calculatorData.deal_value}
            onChange={(e) => setCalculatorData({ ...calculatorData, deal_value: e.target.value })} placeholder="Enter deal value" />
          <Select label={t('commissions.structure')} value={calculatorData.structure_id}
            onChange={(e) => setCalculatorData({ ...calculatorData, structure_id: e.target.value })}
            options={[{ value: '', label: t('commissions.useDefault') }, ...structures.map(s => ({ value: s.id.toString(), label: s.name }))]} />
          <Button onClick={handleCalculateCommission} className="w-full">{t('commissions.calculate')}</Button>
          {calculationResult && (
            <div className="mt-6 p-4 bg-white/5 border border-white/10 rounded-xl">
              <h4 className="font-medium text-white mb-3">{t('commissions.calculationResult')}</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-slate-400">{t('commissions.weeklyBase')}:</span><span className="text-white">${calculationResult.calculation.weekly_base.toFixed(2)}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('commissions.commissionRate')}:</span><span className="text-white">{(calculationResult.calculation.commission_rate * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('commissions.commissionAmount')}:</span><span className="text-white">${calculationResult.calculation.commission_amount.toFixed(2)}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('commissions.performanceBonus')}:</span><span className="text-white">${calculationResult.calculation.performance_bonus.toFixed(2)}</span></div>
                <hr className="border-white/10 my-2" />
                <div className="flex justify-between font-semibold"><span className="text-white">{t('commissions.totalAmount')}:</span><span className="text-emerald-400">${calculationResult.calculation.total_amount.toFixed(2)}</span></div>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Structure Form Modal */}
      <Modal isOpen={showStructureForm} onClose={() => setShowStructureForm(false)} title={t('commissions.configure')} size="xl">
        <div className="space-y-6">
          <Input label={t('common.name')} value={structureForm.name} onChange={(e) => setStructureForm({ ...structureForm, name: e.target.value })} placeholder="Structure name" />
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('commissions.weeklyBase')} type="number" step="0.01" value={structureForm.weekly_base} onChange={(e) => setStructureForm({ ...structureForm, weekly_base: e.target.value })} />
            <Select label={t('common.currency')} value={structureForm.currency} onChange={(e) => setStructureForm({ ...structureForm, currency: e.target.value })}
              options={[{ value: 'USD', label: 'USD' }, { value: 'BRL', label: 'BRL' }, { value: 'EUR', label: 'EUR' }]} />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowStructureForm(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleCreateStructure}>{t('commissions.createStructure')}</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
