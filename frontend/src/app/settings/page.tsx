'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'

interface Config {
    key: string
    value: string | null
    value_type: string
    category: string
    description: string | null
    is_secret: boolean
}

const categoryLabels: Record<string, { label: string; icon: string; description: string }> = {
    stripe: { label: 'Stripe Payments', icon: '💳', description: 'Configure Stripe API keys for processing payments' },
    email: { label: 'Email Settings', icon: '📧', description: 'Configure SMTP or email service provider' },
    site: { label: 'Site Sales', icon: '🌐', description: 'Configure Launch Site product settings' },
    general: { label: 'General', icon: '⚙️', description: 'General system settings' },
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

            // Initialize edited values
            const values: Record<string, string> = {}
            response.data.forEach(c => {
                values[c.key] = c.value || ''
            })
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
        if (!token) {
            router.push('/login')
            return
        }
        loadConfigs()
    }, [router, loadConfigs])

    const handleSave = async (category: string) => {
        setSaving(true)
        try {
            // Get only configs for this category that have changed
            const categoryConfigs = configs.filter(c => c.category === category)
            const updates: Record<string, string> = {}

            categoryConfigs.forEach(c => {
                const originalValue = c.value || ''
                const newValue = editedValues[c.key] || ''
                // Only include if changed and not a masked secret
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
            loadConfigs()
        } catch (error) {
            console.error('Error saving configs:', error)
            toast.error('Failed to save settings')
        } finally {
            setSaving(false)
        }
    }

    const handleValueChange = (key: string, value: string) => {
        setEditedValues(prev => ({ ...prev, [key]: value }))
    }

    const toggleSecret = (key: string) => {
        setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
    }

    const filteredConfigs = configs.filter(c => c.category === activeTab)
    const categories = Object.keys(categoryLabels)

    if (loading) {
        return (
            <div className="space-y-4">
                <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
                <div className="bg-white rounded-lg shadow p-6">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="h-16 bg-gray-100 rounded animate-pulse mb-4" />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div>
            {/* Header */}
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900">System Settings</h2>
                    <p className="text-gray-500 text-sm mt-1">Configure Stripe, Email, and system settings</p>
                </div>
                {configs.length === 0 && (
                    <Button onClick={seedDefaults}>
                        Initialize Default Settings
                    </Button>
                )}
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow mb-6">
                <div className="border-b border-gray-200">
                    <nav className="flex -mb-px">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setActiveTab(cat)}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === cat
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                <span className="mr-2">{categoryLabels[cat].icon}</span>
                                {categoryLabels[cat].label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Category Description */}
                <div className="p-4 bg-gray-50 border-b">
                    <p className="text-sm text-gray-600">{categoryLabels[activeTab]?.description}</p>
                </div>

                {/* Config Fields */}
                <div className="p-6">
                    {filteredConfigs.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <p>No settings found for this category.</p>
                            <Button onClick={seedDefaults} className="mt-4">
                                Initialize Default Settings
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {filteredConfigs.map(config => (
                                <div key={config.key} className="border-b pb-4 last:border-b-0">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-900">
                                                {formatLabel(config.key)}
                                                {config.is_secret && (
                                                    <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
                                                        Secret
                                                    </span>
                                                )}
                                            </label>
                                            {config.description && (
                                                <p className="text-sm text-gray-500 mt-0.5">{config.description}</p>
                                            )}
                                        </div>
                                        {config.is_secret && (
                                            <button
                                                type="button"
                                                onClick={() => toggleSecret(config.key)}
                                                className="text-xs text-blue-600 hover:text-blue-800"
                                            >
                                                {showSecrets[config.key] ? 'Hide' : 'Show'}
                                            </button>
                                        )}
                                    </div>

                                    {config.value_type === 'boolean' ? (
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={() => handleValueChange(config.key, editedValues[config.key] === 'true' ? 'false' : 'true')}
                                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${editedValues[config.key] === 'true' ? 'bg-blue-600' : 'bg-gray-200'
                                                    }`}
                                            >
                                                <span
                                                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${editedValues[config.key] === 'true' ? 'translate-x-6' : 'translate-x-1'
                                                        }`}
                                                />
                                            </button>
                                            <span className="text-sm text-gray-600">
                                                {editedValues[config.key] === 'true' ? 'Enabled' : 'Disabled'}
                                            </span>
                                        </div>
                                    ) : (
                                        <input
                                            type={config.is_secret && !showSecrets[config.key] ? 'password' : 'text'}
                                            value={editedValues[config.key] || ''}
                                            onChange={(e) => handleValueChange(config.key, e.target.value)}
                                            placeholder={config.is_secret ? 'Enter to update' : `Enter ${formatLabel(config.key)}`}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                                        />
                                    )}
                                </div>
                            ))}

                            {/* Save Button */}
                            <div className="pt-4 flex justify-end">
                                <Button onClick={() => handleSave(activeTab)} disabled={saving}>
                                    {saving ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Help Section */}
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">💡 Configuration Tips</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• <strong>Stripe:</strong> Get your API keys from the <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="underline">Stripe Dashboard</a></li>
                    <li>• <strong>Email:</strong> For Gmail, use an <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline">App Password</a></li>
                    <li>• <strong>Webhooks:</strong> Configure webhook endpoint at <code className="bg-blue-100 px-1 rounded">/api/launch/webhook</code></li>
                </ul>
            </div>
        </div>
    )
}

function formatLabel(key: string): string {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
}
