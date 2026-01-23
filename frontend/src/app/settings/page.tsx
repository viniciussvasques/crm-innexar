'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import { motion } from 'framer-motion'
import { Settings, CreditCard, Mail, Globe, Cog, Eye, EyeOff, Save, RefreshCw } from 'lucide-react'

interface Config {
    key: string
    value: string | null
    value_type: string
    category: string
    description: string | null
    is_secret: boolean
}

const categoryConfig: Record<string, { label: string; icon: React.ComponentType<any>; description: string; color: string }> = {
    stripe: { label: 'Stripe Payments', icon: CreditCard, description: 'Configure Stripe API keys for processing payments', color: 'purple' },
    email: { label: 'Email Settings', icon: Mail, description: 'Configure SMTP or email service provider', color: 'blue' },
    site: { label: 'Site Sales', icon: Globe, description: 'Configure Launch Site product settings', color: 'emerald' },
    general: { label: 'General', icon: Cog, description: 'General system settings', color: 'slate' }
}

export default function SettingsPage() {
    const router = useRouter()
    const [configs, setConfigs] = useState<Config[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [activeTab, setActiveTab] = useState('stripe')
    const [editedValues, setEditedValues] = useState<Record<string, string>>({})
    const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({})

    const loadConfigs = useCallback(async () => {
        try {
            const response = await api.get<Config[]>('/api/system-config/')
            setConfigs(response.data)
            const values: Record<string, string> = {}
            response.data.forEach(c => { values[c.key] = c.value || '' })
            setEditedValues(values)
        } catch (error) {
            console.error('Error loading configs:', error)
            toast.error('Failed to load settings')
        } finally {
            setLoading(false)
        }
    }, [])

    const seedDefaults = async () => {
        try {
            await api.post('/api/system-config/seed')
            loadConfigs()
            toast.success('Default configurations seeded')
        } catch (error) {
            console.error('Error seeding configs:', error)
            toast.error('Failed to seed configurations')
        }
    }

    useEffect(() => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
        if (!token) { router.push('/login'); return }
        loadConfigs()
    }, [router, loadConfigs])

    const handleSave = async (category: string) => {
        setSaving(true)
        try {
            const categoryConfigs = configs.filter(c => c.category === category)
            const updates: Record<string, string> = {}
            categoryConfigs.forEach(c => {
                const originalValue = c.value || ''
                const newValue = editedValues[c.key] || ''
                if (newValue !== originalValue && !(c.is_secret && newValue.includes('****'))) { updates[c.key] = newValue }
            })
            if (Object.keys(updates).length === 0) { toast.info('No changes to save'); setSaving(false); return }
            await api.put('/api/system-config/bulk/update', { configs: updates })
            toast.success('Settings saved successfully')
            loadConfigs()
        } catch (error) {
            console.error('Error saving configs:', error)
            toast.error('Failed to save settings')
        } finally {
            setSaving(false)
        }
    }

    const handleValueChange = (key: string, value: string) => setEditedValues(prev => ({ ...prev, [key]: value }))
    const toggleSecret = (key: string) => setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))

    const filteredConfigs = configs.filter(c => c.category === activeTab)
    const categories = Object.keys(categoryConfig)

    const formatLabel = (key: string): string => key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
                <div className="animate-pulse space-y-6">
                    <div className="h-8 bg-white/10 rounded-lg w-48"></div>
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
                            <Settings className="w-8 h-8 text-slate-400" />
                            System Settings
                        </h1>
                        <p className="text-slate-400 mt-1">Configure Stripe, Email, and system settings</p>
                    </div>
                    {configs.length === 0 && (
                        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={seedDefaults}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium">
                            <RefreshCw className="w-5 h-5" />
                            Initialize Default Settings
                        </motion.button>
                    )}
                </div>

                {/* Tabs */}
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl">
                    <div className="border-b border-white/10">
                        <nav className="flex -mb-px overflow-x-auto">
                            {categories.map(cat => {
                                const catConfig = categoryConfig[cat]
                                const CatIcon = catConfig.icon
                                return (
                                    <button key={cat} onClick={() => setActiveTab(cat)}
                                        className={`px-6 py-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${activeTab === cat ? 'border-blue-500 text-blue-400' : 'border-transparent text-slate-500 hover:text-slate-300'
                                            }`}>
                                        <CatIcon className="w-4 h-4" />
                                        {catConfig.label}
                                    </button>
                                )
                            })}
                        </nav>
                    </div>

                    {/* Category Description */}
                    <div className="p-4 bg-white/[0.02] border-b border-white/10">
                        <p className="text-sm text-slate-400">{categoryConfig[activeTab]?.description}</p>
                    </div>

                    {/* Config Fields */}
                    <div className="p-6">
                        {filteredConfigs.length === 0 ? (
                            <div className="text-center py-8">
                                <Settings className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">No settings found for this category.</p>
                                <Button onClick={seedDefaults} className="mt-4">Initialize Default Settings</Button>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {filteredConfigs.map((config, i) => (
                                    <motion.div key={config.key} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                                        className="border-b border-white/10 pb-4 last:border-b-0">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <label className="block text-sm font-medium text-white">
                                                    {formatLabel(config.key)}
                                                    {config.is_secret && (<span className="ml-2 px-2 py-0.5 text-xs bg-amber-500/20 text-amber-300 rounded">Secret</span>)}
                                                </label>
                                                {config.description && (<p className="text-sm text-slate-500 mt-0.5">{config.description}</p>)}
                                            </div>
                                            {config.is_secret && (
                                                <button type="button" onClick={() => toggleSecret(config.key)} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                                                    {showSecrets[config.key] ? <><EyeOff className="w-3 h-3" /> Hide</> : <><Eye className="w-3 h-3" /> Show</>}
                                                </button>
                                            )}
                                        </div>
                                        {config.value_type === 'boolean' ? (
                                            <div className="flex items-center gap-3">
                                                <button onClick={() => handleValueChange(config.key, editedValues[config.key] === 'true' ? 'false' : 'true')}
                                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${editedValues[config.key] === 'true' ? 'bg-blue-600' : 'bg-white/20'}`}>
                                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${editedValues[config.key] === 'true' ? 'translate-x-6' : 'translate-x-1'}`} />
                                                </button>
                                                <span className="text-sm text-slate-400">{editedValues[config.key] === 'true' ? 'Enabled' : 'Disabled'}</span>
                                            </div>
                                        ) : (
                                            <input type={config.is_secret && !showSecrets[config.key] ? 'password' : 'text'} value={editedValues[config.key] || ''}
                                                onChange={(e) => handleValueChange(config.key, e.target.value)} placeholder={config.is_secret ? 'Enter to update' : `Enter ${formatLabel(config.key)}`}
                                                className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-blue-500/50 transition-colors" />
                                        )}
                                    </motion.div>
                                ))}
                                <div className="pt-4 flex justify-end">
                                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => handleSave(activeTab)} disabled={saving}
                                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium disabled:opacity-50">
                                        <Save className="w-4 h-4" />
                                        {saving ? 'Saving...' : 'Save Changes'}
                                    </motion.button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Help Section */}
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
                    <h3 className="font-medium text-blue-300 mb-2 flex items-center gap-2">💡 Configuration Tips</h3>
                    <ul className="text-sm text-blue-200 space-y-1">
                        <li>• <strong>Stripe:</strong> Get your API keys from the <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-100">Stripe Dashboard</a></li>
                        <li>• <strong>Email:</strong> For Gmail, use an <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-100">App Password</a></li>
                        <li>• <strong>Webhooks:</strong> Configure webhook endpoint at <code className="bg-blue-500/20 px-1 rounded">/api/launch/webhook</code></li>
                    </ul>
                </div>
            </div>
        </div>
    )
}
