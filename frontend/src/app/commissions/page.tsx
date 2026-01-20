'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'

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
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [calculatorData, setCalculatorData] = useState({
    deal_value: '',
    structure_id: ''
  })
  const [structureForm, setStructureForm] = useState({
    name: '',
    weekly_base: '100.00',
    currency: 'USD',
    tiered_commissions: [{ min: 0, max: null, rate: 0.05 }],
    performance_bonuses: [{ threshold: 10000, bonus: 150 }],
    recurring_commission_rate: '0.10',
    new_client_bonus: '100.00',
    new_client_threshold: '10'
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
      setStructureForm({
        name: '',
        weekly_base: '100.00',
        currency: 'USD',
        tiered_commissions: [{ min: 0, max: null, rate: 0.05 }],
        performance_bonuses: [{ threshold: 10000, bonus: 150 }],
        recurring_commission_rate: '0.10',
        new_client_bonus: '100.00',
        new_client_threshold: '10'
      })
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
    if (!token) {
      router.push('/login')
      return
    }
    loadData()
  }, [router, loadData])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">{t('commissions.title')}</h2>
        <div className="flex gap-3">
          <Button onClick={() => setShowCalculator(true)} variant="outline">
            {t('commissions.calculate')}
          </Button>
          <Button onClick={() => setShowStructureForm(true)}>
            {t('commissions.configure')}
          </Button>
        </div>
      </div>

      {/* Estruturas de Comissão */}
      <div className="mb-8 bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">{t('commissions.structure')}</h3>
        {structures.length === 0 ? (
          <p className="text-gray-500">{t('commissions.noStructures')}</p>
        ) : (
          <div className="space-y-4">
            {structures.map((structure) => (
              <div key={structure.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold">{structure.name}</h4>
                    <p className="text-sm text-gray-500">{t('commissions.weeklyBase')}: ${structure.weekly_base} {structure.currency}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${structure.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {structure.is_active ? t('common.active') : t('common.inactive')}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium mb-2">{t('commissions.tieredCommission')}:</p>
                    <div className="space-y-1">
                      {structure.tiered_commissions.map((tier, idx) => (
                        <div key={idx} className="text-sm text-gray-600">
                          ${tier.min.toLocaleString()} - {tier.max ? `$${tier.max.toLocaleString()}` : t('common.infinity')}: {(tier.rate * 100).toFixed(1)}%
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-2">{t('commissions.performanceBonus')}:</p>
                    <div className="space-y-1">
                      {structure.performance_bonuses.map((bonus, idx) => (
                        <div key={idx} className="text-sm text-gray-600">
                          ${bonus.threshold.toLocaleString()}: ${bonus.bonus}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-sm text-gray-500">
                  <span>{t('commissions.recurringCommission')}: {(structure.recurring_commission_rate * 100).toFixed(1)}%</span>
                  <span className="ml-4">{t('commissions.newClientBonus')}: ${structure.new_client_bonus}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Histórico de Comissões */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-xl font-semibold p-6 border-b">{t('commissions.history')}</h3>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('commissions.dealSize')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('commissions.commissionAmount')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.date')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {commissions.map((commission) => {
              const user = users.find(u => u.id === commission.user_id)
              return (
                <tr key={commission.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {user?.name || t('common.na')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${commission.deal_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                    ${commission.commission_amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(commission.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      commission.status === 'paid' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {commission.status === 'paid' ? t('commissions.paid') : t('commissions.pending')}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {commissions.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {t('commissions.noCommissions')}
          </div>
        )}
      </div>

      {/* Modal de Calculadora */}
      <Modal
        isOpen={showCalculator}
        onClose={() => {
          setShowCalculator(false)
          setCalculationResult(null)
          setCalculatorData({ deal_value: '', structure_id: '' })
        }}
        title={t('commissions.calculate')}
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('commissions.dealSize')}</label>
            <input
              type="number"
              step="0.01"
              value={calculatorData.deal_value}
              onChange={(e) => setCalculatorData({ ...calculatorData, deal_value: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder={t('commissions.placeholderDealValue')}
            />
          </div>
          <Select
            label={t('commissions.structure')}
            value={calculatorData.structure_id}
            onChange={(e) => setCalculatorData({ ...calculatorData, structure_id: e.target.value })}
            options={[
              { value: '', label: t('commissions.useDefault') },
              ...structures.map(s => ({ value: s.id.toString(), label: s.name }))
            ]}
          />
          <Button onClick={handleCalculateCommission} className="w-full">
            {t('commissions.calculate')}
          </Button>

          {calculationResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3">{t('commissions.calculationResult')}</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>{t('commissions.weeklyBase')}:</span>
                  <span>${calculationResult.calculation.weekly_base.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('commissions.commissionRate')}:</span>
                  <span>{(calculationResult.calculation.commission_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('commissions.commissionAmount')}:</span>
                  <span>${calculationResult.calculation.commission_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('commissions.performanceBonus')}:</span>
                  <span>${calculationResult.calculation.performance_bonus.toFixed(2)}</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-medium">
                  <span>{t('commissions.totalAmount')}:</span>
                  <span>${calculationResult.calculation.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Modal de Configuração */}
      <Modal
        isOpen={showStructureForm}
        onClose={() => setShowStructureForm(false)}
        title={t('commissions.configure')}
        size="xl"
      >
        <div className="space-y-6">
          <Input
            label={t('common.name')}
            value={structureForm.name}
            onChange={(e) => setStructureForm({ ...structureForm, name: e.target.value })}
            placeholder={t('commissions.placeholderName')}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t('commissions.weeklyBase')}
              type="number"
              step="0.01"
              value={structureForm.weekly_base}
              onChange={(e) => setStructureForm({ ...structureForm, weekly_base: e.target.value })}
            />
            <Select
              label={t('common.currency')}
              value={structureForm.currency}
              onChange={(e) => setStructureForm({ ...structureForm, currency: e.target.value })}
              options={[
                { value: 'USD', label: 'USD' },
                { value: 'BRL', label: 'BRL' },
                { value: 'EUR', label: 'EUR' }
              ]}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('commissions.tieredCommission')}</label>
            <div className="space-y-2">
              {structureForm.tiered_commissions.map((tier, index) => (
                <div key={index} className="flex gap-2 items-center">
                  <Input
                    placeholder={t('commissions.placeholderMin')}
                    type="number"
                    value={tier.min}
                    onChange={(e) => {
                      const newTiers = [...structureForm.tiered_commissions]
                      newTiers[index].min = parseFloat(e.target.value) || 0
                      setStructureForm({ ...structureForm, tiered_commissions: newTiers })
                    }}
                    className="w-24"
                  />
                  <span>-</span>
                  <Input
                    placeholder={t('commissions.placeholderMax')}
                    type="number"
                    value={tier.max || ''}
                    onChange={(e) => {
                      const newTiers = [...structureForm.tiered_commissions]
                      newTiers[index].max = e.target.value ? parseFloat(e.target.value) : null
                      setStructureForm({ ...structureForm, tiered_commissions: newTiers })
                    }}
                    className="w-24"
                  />
                  <Input
                    placeholder={t('commissions.placeholderRate')}
                    type="number"
                    step="0.001"
                    value={tier.rate * 100}
                    onChange={(e) => {
                      const newTiers = [...structureForm.tiered_commissions]
                      newTiers[index].rate = (parseFloat(e.target.value) || 0) / 100
                      setStructureForm({ ...structureForm, tiered_commissions: newTiers })
                    }}
                    className="w-20"
                  />
                  <span>%</span>
                  {structureForm.tiered_commissions.length > 1 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newTiers = structureForm.tiered_commissions.filter((_, i) => i !== index)
                        setStructureForm({ ...structureForm, tiered_commissions: newTiers })
                      }}
                    >
                      ✕
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setStructureForm({
                    ...structureForm,
                    tiered_commissions: [...structureForm.tiered_commissions, { min: 0, max: null, rate: 0.05 }]
                  })
                }}
              >
                + {t('common.add')} {t('commissions.tier')}
              </Button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('commissions.performanceBonus')}</label>
            <div className="space-y-2">
              {structureForm.performance_bonuses.map((bonus, index) => (
                <div key={index} className="flex gap-2 items-center">
                  <span>{t('commissions.threshold')}:</span>
                  <Input
                    type="number"
                    value={bonus.threshold}
                    onChange={(e) => {
                      const newBonuses = [...structureForm.performance_bonuses]
                      newBonuses[index].threshold = parseFloat(e.target.value) || 0
                      setStructureForm({ ...structureForm, performance_bonuses: newBonuses })
                    }}
                    className="w-32"
                  />
                  <span>{t('commissions.bonus')}:</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={bonus.bonus}
                    onChange={(e) => {
                      const newBonuses = [...structureForm.performance_bonuses]
                      newBonuses[index].bonus = parseFloat(e.target.value) || 0
                      setStructureForm({ ...structureForm, performance_bonuses: newBonuses })
                    }}
                    className="w-32"
                  />
                  {structureForm.performance_bonuses.length > 1 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newBonuses = structureForm.performance_bonuses.filter((_, i) => i !== index)
                        setStructureForm({ ...structureForm, performance_bonuses: newBonuses })
                      }}
                    >
                      ✕
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setStructureForm({
                    ...structureForm,
                    performance_bonuses: [...structureForm.performance_bonuses, { threshold: 10000, bonus: 150 }]
                  })
                }}
              >
                + {t('common.add')} {t('commissions.bonus')}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Input
              label={t('commissions.recurringCommission')}
              type="number"
              step="0.001"
              value={parseFloat(structureForm.recurring_commission_rate) * 100}
              onChange={(e) => setStructureForm({
                ...structureForm,
                recurring_commission_rate: (parseFloat(e.target.value) || 0) / 100
              })}
            />
            <Input
              label={t('commissions.newClientBonus')}
              type="number"
              step="0.01"
              value={structureForm.new_client_bonus}
              onChange={(e) => setStructureForm({ ...structureForm, new_client_bonus: e.target.value })}
            />
            <Input
              label={t('commissions.newClientThreshold')}
              type="number"
              value={structureForm.new_client_threshold}
              onChange={(e) => setStructureForm({ ...structureForm, new_client_threshold: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowStructureForm(false)}
            >
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreateStructure}>
              {t('commissions.createStructure')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

