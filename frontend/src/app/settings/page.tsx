'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import { motion } from 'framer-motion'
import {
    Settings, CreditCard, Mail, Cog, Eye, EyeOff, Save,
    Bot, Server, Link as LinkIcon, Plus, Trash2
} from 'lucide-react'

// --- Types ---
interface Config {
    key: string
    value: string | null
    value_type: string
    category: string
    description: string | null
    is_secret: boolean
}

interface IntegrationConfig {
    id?: number
    integration_type: string
    key: string
    value: string
    is_secret: boolean
    description?: string
    is_active: boolean
}

interface DeployServer {
    id?: number
    name: string
    server_type: string
    host: string
    username: string
    port?: number
    is_default: boolean
    is_active: boolean
}

// --- Configuration ---
const categoryConfig: Record<string, { label: string; icon: React.ComponentType<any>; description: string; color: string }> = {
    // Existing
    general: { label: 'General', icon: Cog, description: 'System general settings', color: 'slate' },
    stripe: { label: 'Stripe', icon: CreditCard, description: 'Payments configuration', color: 'purple' },
    email: { label: 'Email', icon: Mail, description: 'SMTP settings', color: 'blue' },

    // New
    ai: { label: 'AI Providers', icon: Bot, description: 'Manage OpenAI, Anthropic, and other AI models', color: 'emerald' },
    servers: { label: 'Deploy Servers', icon: Server, description: 'Manage VPS and deployment targets', color: 'orange' },
    integrations: { label: 'Integrations', icon: LinkIcon, description: 'GitHub, Cloudflare, and external tools', color: 'indigo' },
}

export default function SettingsPage() {
    const router = useRouter()
    const [activeTab, setActiveTab] = useState('general')
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    // Data State
    const [configs, setConfigs] = useState<Config[]>([])
    const [servers, setServers] = useState<DeployServer[]>([])

    // UI State
    const [editedValues, setEditedValues] = useState<Record<string, string>>({})
    const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({})

    const loadData = useCallback(async () => {
        setLoading(true)
        try {
            // Load Standard Configs
            const configRes = await api.get<Config[]>('/api/system-config/')
            setConfigs(configRes.data)

            // Populate editedValues for standard configs
            const values: Record<string, string> = {}
            configRes.data.forEach(c => { values[c.key] = c.value || '' })
            setEditedValues(values)

        } catch (error) {
            console.error('Error loading settings:', error)
            toast.error('Failed to load settings')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
        if (!token) { router.push('/login'); return }
        loadData()
    }, [router, loadData])

    // --- Handlers ---

    const handleSaveStandard = async (category: string) => {
        setSaving(true)
        try {
            const categoryConfigs = configs.filter(c => c.category === category)
            const updates: Record<string, string> = {}
            categoryConfigs.forEach(c => {
                const originalValue = c.value || ''
                const newValue = editedValues[c.key] || ''
                if (newValue !== originalValue && !(c.is_secret && newValue.includes('****'))) {
                    updates[c.key] = newValue
                }
            })

            if (Object.keys(updates).length === 0) {
                toast.info('No changes to save')
                setSaving(false)
                return
            }

            await api.put('/api/system-config/bulk/update', { configs: updates })
            toast.success('Settings saved successfully')
            loadData()
        } catch (error) {
            console.error('Error saving configs:', error)
            toast.error('Failed to save settings')
        } finally {
            setSaving(false)
        }
    }

    const toggleSecret = (key: string) => setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
    const handleValueChange = (key: string, value: string) => setEditedValues(prev => ({ ...prev, [key]: value }))

    // --- Render Helpers ---

    const renderStandardTab = (category: string) => {
        const filteredConfigs = configs.filter(c => c.category === category)

        if (filteredConfigs.length === 0) return (
            <div className="text-center py-12">
                <p className="text-slate-400">No settings found for this category.</p>
            </div>
        )

        return (
            <div className="space-y-6">
                {filteredConfigs.map((config, i) => (
                    <motion.div key={config.key} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                        className="border-b border-white/10 pb-4 last:border-b-0">
                        <div className="flex justify-between items-start mb-2">
                            <div>
                                <label className="block text-sm font-medium text-white">
                                    {config.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
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
                            <input
                                type={config.is_secret && !showSecrets[config.key] ? 'password' : 'text'}
                                value={editedValues[config.key] || ''}
                                onChange={(e) => handleValueChange(config.key, e.target.value)}
                                placeholder={config.is_secret ? 'Enter to update' : 'Enter value'}
                                className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                            />
                        )}
                    </motion.div>
                ))}
                <div className="pt-4 flex justify-end">
                    <Button onClick={() => handleSaveStandard(category)} isLoading={saving}>Save Changes</Button>
                </div>
            </div>
        )
    }

    // --- AI Providers Tab Logic ---
    const [aiConfigs, setAiConfigs] = useState<any[]>([])
    const [loadingAi, setLoadingAi] = useState(false)
    const [showAiModal, setShowAiModal] = useState(false)
    const [newAiConfig, setNewAiConfig] = useState({
        name: '', provider: 'openai', model_name: 'gpt-4o', api_key: '', is_active: true
    })

    const loadAiConfigs = useCallback(async () => {
        setLoadingAi(true)
        try {
            const res = await api.get('/api/ai-config/')
            setAiConfigs(res.data)
        } catch (error) {
            console.error(error)
            toast.error('Failed to load AI configs')
        } finally {
            setLoadingAi(false)
        }
    }, [])

    useEffect(() => {
        if (activeTab === 'ai') loadAiConfigs()
    }, [activeTab, loadAiConfigs])

    const handleCreateAiConfig = async () => {
        try {
            await api.post('/api/ai-config/', newAiConfig)
            toast.success('Provider added')
            setShowAiModal(false)
            loadAiConfigs()
        } catch (error) {
            toast.error('Failed to add provider')
        }
    }

    const handleDeleteAiConfig = async (id: number) => {
        if (!confirm('Are you sure?')) return
        try {
            await api.delete(`/api/ai-config/${id}`)
            toast.success('Provider deleted')
            loadAiConfigs()
        } catch (error) {
            toast.error('Failed to delete')
        }
    }

    const renderAiTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-white">Configured Models</h3>
                <Button onClick={() => setShowAiModal(true)} className="flex items-center gap-2">
                    <Plus className="w-4 h-4" /> Add Provider
                </Button>
            </div>

            {loadingAi ? (
                <div className="text-center py-8 text-slate-400">Loading configurations...</div>
            ) : aiConfigs.length === 0 ? (
                <div className="text-center py-12 bg-white/5 rounded-xl border border-white/10 border-dashed">
                    <Bot className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No AI providers configured yet.</p>
                    <Button onClick={() => setShowAiModal(true)} variant="secondary" className="mt-4">
                        Configure First Provider
                    </Button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {aiConfigs.map((config) => (
                        <div key={config.id} className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${config.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-400'}`}>
                                    <Bot className="w-5 h-5" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-white">{config.name}</h4>
                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                        <span className="capitalize">{config.provider}</span>
                                        <span>•</span>
                                        <span>{config.model_name}</span>
                                        {config.is_default && (
                                            <span className="bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">Default</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => handleDeleteAiConfig(config.id)} className="p-2 text-slate-400 hover:text-red-400 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {showAiModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-md space-y-4">
                        <h3 className="text-xl font-bold text-white">Add AI Provider</h3>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Friendly Name</label>
                            <input
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                placeholder="e.g. Primary GPT-4"
                                value={newAiConfig.name}
                                onChange={e => setNewAiConfig({ ...newAiConfig, name: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Provider</label>
                                <select
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    value={newAiConfig.provider}
                                    onChange={e => setNewAiConfig({ ...newAiConfig, provider: e.target.value })}
                                >
                                    <option value="openai">OpenAI</option>
                                    <option value="anthropic">Anthropic</option>
                                    <option value="google">Google Gemini</option>
                                    <option value="ollama">Ollama (Local)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Model Name</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    placeholder="gpt-4o"
                                    value={newAiConfig.model_name}
                                    onChange={e => setNewAiConfig({ ...newAiConfig, model_name: e.target.value })}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">API Key</label>
                            <input
                                type="password"
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                placeholder="sk-..."
                                value={newAiConfig.api_key}
                                onChange={e => setNewAiConfig({ ...newAiConfig, api_key: e.target.value })}
                            />
                        </div>
                        <div className="flex gap-3 pt-2">
                            <Button className="flex-1" variant="secondary" onClick={() => setShowAiModal(false)}>Cancel</Button>
                            <Button className="flex-1" onClick={handleCreateAiConfig}>Save Provider</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )

    // --- Deploy Servers Tab Logic ---
    const [loadingServers, setLoadingServers] = useState(false)
    const [showServerModal, setShowServerModal] = useState(false)
    const [newServer, setNewServer] = useState<Partial<DeployServer>>({
        name: '', server_type: 'ssh', host: '', username: '', is_active: true, is_default: false
    })
    const [serverSecrets, setServerSecrets] = useState({ password: '', ssh_key: '' })

    const loadServers = useCallback(async () => {
        setLoadingServers(true)
        try {
            const res = await api.get('/api/config/deploy-servers')
            setServers(res.data)
        } catch (error) {
            console.error(error)
            toast.error('Failed to load servers')
        } finally {
            setLoadingServers(false)
        }
    }, [])

    useEffect(() => {
        if (activeTab === 'servers') loadServers()
    }, [activeTab, loadServers])

    const handleCreateServer = async () => {
        try {
            await api.post('/api/config/deploy-servers', { ...newServer, ...serverSecrets })
            toast.success('Server added')
            setShowServerModal(false)
            loadServers()
            setServerSecrets({ password: '', ssh_key: '' })
        } catch (error) {
            toast.error('Failed to add server')
        }
    }

    const renderServersTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-white">Deployment Targets</h3>
                <Button onClick={() => setShowServerModal(true)} className="flex items-center gap-2">
                    <Plus className="w-4 h-4" /> Add Server
                </Button>
            </div>

            {loadingServers ? (
                <div className="text-center py-8 text-slate-400">Loading servers...</div>
            ) : servers.length === 0 ? (
                <div className="text-center py-12 bg-white/5 rounded-xl border border-white/10 border-dashed">
                    <Server className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No deploy servers configured.</p>
                    <Button onClick={() => setShowServerModal(true)} variant="secondary" className="mt-4">
                        Add First Server
                    </Button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {servers.map((server) => (
                        <div key={server.id} className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${server.is_active ? 'bg-orange-500/20 text-orange-400' : 'bg-slate-700/50 text-slate-400'}`}>
                                    <Server className="w-5 h-5" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-white">{server.name}</h4>
                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                        <span className="capitalize">{server.server_type}</span>
                                        <span>•</span>
                                        <span>{server.username}@{server.host}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button variant="secondary" size="sm">Edit</Button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {showServerModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-lg space-y-4 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-xl font-bold text-white">Add Deploy Server</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="block text-sm text-slate-400 mb-1">Server Name</label>
                                <input className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    placeholder="e.g. Production VPS"
                                    value={newServer.name} onChange={e => setNewServer({ ...newServer, name: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Type</label>
                                <select className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    value={newServer.server_type} onChange={e => setNewServer({ ...newServer, server_type: e.target.value })}>
                                    <option value="ssh">SSH / VPS</option>
                                    <option value="ftp">FTP</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Host / IP</label>
                                <input className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    placeholder="192.168.1.1"
                                    value={newServer.host} onChange={e => setNewServer({ ...newServer, host: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Username</label>
                                <input className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    placeholder="root"
                                    value={newServer.username} onChange={e => setNewServer({ ...newServer, username: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Port</label>
                                <input type="number" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    placeholder="22"
                                    value={newServer.port || 22} onChange={e => setNewServer({ ...newServer, port: parseInt(e.target.value) })} />
                            </div>
                            <div className="col-span-2">
                                <label className="block text-sm text-slate-400 mb-1">Password (Optional)</label>
                                <input type="password" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                                    value={serverSecrets.password} onChange={e => setServerSecrets({ ...serverSecrets, password: e.target.value })} />
                            </div>
                            <div className="col-span-2">
                                <label className="block text-sm text-slate-400 mb-1">SSH Private Key (Optional)</label>
                                <textarea className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white font-mono text-xs h-24"
                                    placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
                                    value={serverSecrets.ssh_key} onChange={e => setServerSecrets({ ...serverSecrets, ssh_key: e.target.value })} />
                            </div>
                        </div>
                        <div className="flex gap-3 pt-2">
                            <Button className="flex-1" variant="secondary" onClick={() => setShowServerModal(false)}>Cancel</Button>
                            <Button className="flex-1" onClick={handleCreateServer}>Save Server</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )

    // --- Integrations Tab Logic ---
    const [integrationForm, setIntegrationForm] = useState({ github_token: '', cloudflare_token: '', cloudflare_account: '' })

    const handleSaveIntegrations = async () => {
        try {
            if (integrationForm.github_token) {
                await api.post('/api/config/integrations', { integration_type: 'github', key: 'api_token', value: integrationForm.github_token, is_secret: true })
            }
            if (integrationForm.cloudflare_token) {
                await api.post('/api/config/integrations', { integration_type: 'cloudflare', key: 'api_token', value: integrationForm.cloudflare_token, is_secret: true })
            }
            if (integrationForm.cloudflare_account) {
                await api.post('/api/config/integrations', { integration_type: 'cloudflare', key: 'account_id', value: integrationForm.cloudflare_account, is_secret: false })
            }
            toast.success('Integrations updated')
        } catch (error) {
            toast.error('Failed to save integrations')
        }
    }

    const renderIntegrationsTab = () => (
        <div className="space-y-8 max-w-2xl">
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-white/10 rounded-lg"><LinkIcon className="w-6 h-6 text-white" /></div>
                    <div>
                        <h3 className="text-lg font-medium text-white">GitHub Integration</h3>
                        <p className="text-sm text-slate-400">Required to create repositories for new sites.</p>
                    </div>
                </div>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Personal Access Token (Classic)</label>
                        <input type="password" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                            placeholder="ghp_..."
                            value={integrationForm.github_token} onChange={e => setIntegrationForm({ ...integrationForm, github_token: e.target.value })} />
                    </div>
                </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-white/10 rounded-lg"><LinkIcon className="w-6 h-6 text-orange-400" /></div>
                    <div>
                        <h3 className="text-lg font-medium text-white">Cloudflare Integration</h3>
                        <p className="text-sm text-slate-400">Required for DNS and Pages deployment.</p>
                    </div>
                </div>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Account ID</label>
                        <input className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                            placeholder="e.g. 8d9e..."
                            value={integrationForm.cloudflare_account} onChange={e => setIntegrationForm({ ...integrationForm, cloudflare_account: e.target.value })} />
                    </div>
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">API Token</label>
                        <input type="password" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white"
                            placeholder="All operations token"
                            value={integrationForm.cloudflare_token} onChange={e => setIntegrationForm({ ...integrationForm, cloudflare_token: e.target.value })} />
                    </div>
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <Button onClick={handleSaveIntegrations}>Save Integrations</Button>
            </div>
        </div>
    )

    // --- Main Render ---

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
                            <Settings className="w-8 h-8 text-slate-400" />
                            Settings
                        </h1>
                        <p className="text-slate-400 mt-1">Manage system configurations and integrations</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
                    <div className="border-b border-white/10 overflow-x-auto">
                        <nav className="flex">
                            {Object.keys(categoryConfig).map(cat => {
                                const config = categoryConfig[cat]
                                const Icon = config.icon
                                const isActive = activeTab === cat
                                return (
                                    <button
                                        key={cat}
                                        onClick={() => setActiveTab(cat)}
                                        className={`px-6 py-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors min-w-[140px] justify-center
                                            ${isActive
                                                ? `border-${config.color}-500 text-${config.color}-400 bg-white/5`
                                                : 'border-transparent text-slate-500 hover:text-slate-300 hover:bg-white/[0.02]'
                                            }`}
                                    >
                                        <Icon className={`w-4 h-4 ${isActive ? `text-${config.color}-400` : ''}`} />
                                        {config.label}
                                    </button>
                                )
                            })}
                        </nav>
                    </div>

                    {/* Content */}
                    <div className="p-6 min-h-[400px]">
                        <div className="mb-6 pb-4 border-b border-white/10">
                            <h2 className="text-lg font-medium text-white flex items-center gap-2">
                                {React.createElement(categoryConfig[activeTab].icon, { className: "w-5 h-5 text-slate-400" })}
                                {categoryConfig[activeTab].label}
                            </h2>
                            <p className="text-sm text-slate-400 mt-1">{categoryConfig[activeTab].description}</p>
                        </div>

                        {['general', 'stripe', 'email'].includes(activeTab) ? (
                            renderStandardTab(activeTab)
                        ) : activeTab === 'ai' ? (
                            renderAiTab()
                        ) : activeTab === 'servers' ? (
                            renderServersTab()
                        ) : (
                            renderIntegrationsTab()
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
