'use client'

import { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { User } from '@/types'
import { useLanguage } from '@/contexts/LanguageContext'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Select from '@/components/Select'
import { motion } from 'framer-motion'
import { Users, Plus, Shield, Code, Calendar, UserCheck, UserX, Mail } from 'lucide-react'

export default function UsersPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '', email: '', password: '', role: 'vendedor' as User['role'], is_active: true
  })

  const roleConfig: Record<string, { label: string; color: string; bgColor: string; icon: React.ComponentType<any> }> = {
    admin: { label: t('users.admin'), color: 'text-red-300', bgColor: 'bg-red-500/20', icon: Shield },
    vendedor: { label: t('users.vendedor'), color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', icon: UserCheck },
    planejamento: { label: t('users.planejamento'), color: 'text-purple-300', bgColor: 'bg-purple-500/20', icon: Calendar },
    dev: { label: t('users.dev'), color: 'text-blue-300', bgColor: 'bg-blue-500/20', icon: Code }
  }

  const loadUsers = useCallback(async () => {
    try {
      const response = await api.get<User[]>('/api/users/')
      setUsers(response.data)
    } catch (error: any) {
      console.error('Erro ao carregar usuários:', error)
      toast.error(t('users.errorLoad'))
      if (error.response?.status === 403) router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }, [router, t])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadUsers()
  }, [router, loadUsers])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/users/', { name: formData.name, email: formData.email, password: formData.password, role: formData.role })
      setShowForm(false)
      setFormData({ name: '', email: '', password: '', role: 'vendedor', is_active: true })
      loadUsers()
      toast.success(t('users.created'))
    } catch (error: any) {
      console.error('Erro ao criar usuário:', error)
      toast.error(t('users.errorCreate'))
    }
  }

  // Stats
  const stats = useMemo(() => ({
    total: users.length,
    active: users.filter(u => u.is_active).length,
    admins: users.filter(u => u.role === 'admin').length,
    devs: users.filter(u => u.role === 'dev').length
  }), [users])

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
              <Users className="w-8 h-8 text-blue-400" />
              {t('users.title')}
            </h1>
            <p className="text-slate-400 mt-1">Manage system users and roles</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-shadow"
          >
            <Plus className="w-5 h-5" />
            {t('users.new')}
          </motion.button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Users', value: stats.total, icon: Users, color: 'blue' },
            { label: 'Active', value: stats.active, icon: UserCheck, color: 'emerald' },
            { label: 'Admins', value: stats.admins, icon: Shield, color: 'red' },
            { label: 'Developers', value: stats.devs, icon: Code, color: 'purple' }
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

        {/* Users Table */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.name')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.email')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('users.role')}</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">{t('common.status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {users.map((user, i) => {
                  const role = roleConfig[user.role] || roleConfig.vendedor
                  const RoleIcon = role.icon
                  return (
                    <motion.tr
                      key={user.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="hover:bg-white/[0.03] transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
                            {user.name.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-white font-medium">{user.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-slate-400">
                          <Mail className="w-4 h-4" />
                          {user.email}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-6 h-6 rounded-md ${role.bgColor} flex items-center justify-center`}>
                            <RoleIcon className={`w-3.5 h-3.5 ${role.color}`} />
                          </div>
                          <span className={`text-sm font-medium ${role.color}`}>{role.label}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${user.is_active
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-red-500/20 text-red-300 border border-red-500/30'
                          }`}>
                          {user.is_active ? t('common.active') : t('common.inactive')}
                        </span>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {users.length === 0 && (
            <div className="p-12 text-center">
              <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">{t('users.noUsers')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={t('users.new')} size="md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('common.name')} type="text" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
            <Input label={t('common.email')} type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('users.password')} type="password" required value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
            <Select label={t('users.role')} required value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value as User['role'] })}
              options={[
                { value: 'vendedor', label: t('users.vendedor') },
                { value: 'planejamento', label: t('users.planejamento') },
                { value: 'dev', label: t('users.dev') },
                { value: 'admin', label: t('users.admin') }
              ]} />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>{t('common.cancel')}</Button>
            <Button type="submit">{t('common.save')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
