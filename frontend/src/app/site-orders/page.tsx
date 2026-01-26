'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import LogViewer from '@/components/SiteGeneration/LogViewer'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Package, DollarSign, Clock, CheckCircle, AlertCircle,
    LayoutGrid, LayoutList, MapPin, Mail, Calendar, ExternalLink, Globe,
    Wand2, FileCode, Presentation, RefreshCw
} from 'lucide-react'
import { Timeline } from '@/components/SiteGeneration/Timeline'
import { useSiteOrders } from '@/hooks/useSiteOrders'
import { SiteOrder, SiteDeliverable, StatusConfig } from './types'
import { getProcessSteps } from './utils'

const statusConfig: Record<string, StatusConfig> = {
    pending_payment: { label: 'Pending Payment', color: 'text-slate-300', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: AlertCircle },
    paid: { label: 'Paid', color: 'text-amber-300', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/30', icon: DollarSign },
    onboarding_pending: { label: 'Onboarding', color: 'text-orange-300', bgColor: 'bg-orange-500/20', borderColor: 'border-orange-500/30', icon: Clock },
    building: { label: 'Building', color: 'text-blue-300', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Package },
    generating: { label: 'Generating AI', color: 'text-blue-300', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Wand2 },
    review: { label: 'In Review', color: 'text-purple-300', bgColor: 'bg-purple-500/20', borderColor: 'border-purple-500/30', icon: Clock },
    delivered: { label: 'Delivered', color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30', icon: CheckCircle },
    cancelled: { label: 'Cancelled', color: 'text-red-300', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30', icon: AlertCircle },
}

export default function SiteOrdersPage() {
    const router = useRouter()
    const { orders, stats, loading, generating, loadOrders, updateStatus, generateSite, checkEmptyGenerations, resetEmptyGenerations, resetGeneration, setGenerating } = useSiteOrders()

    // UI State
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [selectedOrder, setSelectedOrder] = useState<SiteOrder | null>(null)
    const [showDetails, setShowDetails] = useState(false)
    const [viewMode, setViewMode] = useState<'table' | 'kanban'>('kanban')
    const [selectedArtifact, setSelectedArtifact] = useState<SiteDeliverable | null>(null)
    const [viewLogs, setViewLogs] = useState(false)

    useEffect(() => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
        if (!token) { router.push('/login'); return }
        loadOrders()
    }, [router, loadOrders])

    const [emptyGenerations, setEmptyGenerations] = useState<any>(null)
    const [checkingEmpty, setCheckingEmpty] = useState(false)

    const handleGenerateSite = async (orderId: number) => {
        const started = await generateSite(orderId)
        if (started) {
            setViewLogs(true)
        }
    }

    const handleCheckEmptyGenerations = async () => {
        setCheckingEmpty(true)
        try {
            const result = await checkEmptyGenerations()
            setEmptyGenerations(result)
            if (result && result.empty_generations > 0) {
                toast.warning(`Found ${result.empty_generations} orders with no generated files`)
            } else {
                toast.success('All generating orders have files')
            }
        } finally {
            setCheckingEmpty(false)
        }
    }

    const handleResetEmptyGenerations = async () => {
        const result = await resetEmptyGenerations()
        if (result) {
            setEmptyGenerations(null)
        }
    }

    const handleResetSingleGeneration = async (orderId: number) => {
        await resetGeneration(orderId)
    }

    const filteredOrders = useMemo(() => {
        if (statusFilter === 'all') return orders
        return orders.filter(order => order.status === statusFilter)
    }, [orders, statusFilter])

    const ordersByStatus = useMemo(() => {
        const grouped: Record<string, SiteOrder[]> = { paid: [], building: [], generating: [], review: [], delivered: [] }
        orders.forEach(order => { if (grouped[order.status]) grouped[order.status].push(order) })
        return grouped
    }, [orders])

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
                            <Package className="w-8 h-8 text-blue-400" />
                            Site Orders
                        </h1>
                        <p className="text-slate-400 mt-1">Manage Launch Site orders and deliveries</p>
                    </div>
                    <div className="flex bg-white/5 border border-white/10 rounded-lg p-1">
                        <button
                            onClick={() => setViewMode('kanban')}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'kanban' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                                }`}
                        >
                            <LayoutGrid className="w-4 h-4" />
                            Kanban
                        </button>
                        <button
                            onClick={() => setViewMode('table')}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'table' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                                }`}
                        >
                            <LayoutList className="w-4 h-4" />
                            Table
                        </button>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleCheckEmptyGenerations}
                            disabled={checkingEmpty}
                            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
                        >
                            <AlertCircle className="w-4 h-4" />
                            {checkingEmpty ? 'Checking...' : 'Check Empty Generations'}
                        </button>
                        {emptyGenerations && emptyGenerations.empty_generations > 0 && (
                            <button
                                onClick={handleResetEmptyGenerations}
                                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium text-white transition-colors"
                            >
                                Reset {emptyGenerations.empty_generations} Empty
                            </button>
                        )}
                    </div>
                </div>

                {/* Empty Generations Alert */}
                {emptyGenerations && emptyGenerations.empty_generations > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-amber-500/20 border border-amber-500/30 rounded-xl p-4 mb-6"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <AlertCircle className="w-5 h-5 text-amber-400" />
                                <div>
                                    <p className="text-amber-300 font-semibold">
                                        {emptyGenerations.empty_generations} orders in "Generating AI" have no files
                                    </p>
                                    <p className="text-amber-200/70 text-sm mt-1">
                                        These orders can be reset to allow regeneration
                                    </p>
                                </div>
                            </div>
                        </div>
                        {emptyGenerations.empty_orders && emptyGenerations.empty_orders.length > 0 && (
                            <div className="mt-4 space-y-2">
                                {emptyGenerations.empty_orders.slice(0, 5).map((order: any) => (
                                    <div key={order.order_id} className="flex items-center justify-between bg-black/20 rounded-lg p-2">
                                        <div>
                                            <span className="text-white font-medium">Order #{order.order_id}</span>
                                            <span className="text-amber-200/70 ml-2">{order.customer_name}</span>
                                            <span className="text-amber-200/50 text-xs ml-2">({order.files_count} files)</span>
                                        </div>
                                        <button
                                            onClick={() => handleResetSingleGeneration(order.order_id)}
                                            className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                                        >
                                            Reset
                                        </button>
                                    </div>
                                ))}
                                {emptyGenerations.empty_orders.length > 5 && (
                                    <p className="text-amber-200/50 text-xs">... and {emptyGenerations.empty_orders.length - 5} more</p>
                                )}
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: 'Total Revenue', value: `$${stats.total_revenue.toLocaleString()}`, icon: DollarSign, color: 'emerald' },
                            { label: 'Orders This Month', value: stats.orders_this_month, icon: Package, color: 'blue' },
                            { label: 'In Progress', value: (stats.status_counts['building'] || 0) + (stats.status_counts['generating'] || 0) + (stats.status_counts['review'] || 0), icon: Clock, color: 'amber' },
                            { label: 'Delivered', value: stats.status_counts['delivered'] || 0, icon: CheckCircle, color: 'purple' }
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
                                        <p className="text-xl lg:text-2xl font-bold text-white mt-1">{stat.value}</p>
                                    </div>
                                    <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/20 flex items-center justify-center`}>
                                        <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Kanban View */}
                {viewMode === 'kanban' && (
                    <div className="overflow-x-auto pb-4">
                        <div className="flex gap-4 min-w-max">
                            {['paid', 'building', 'generating', 'review', 'delivered'].map(status => {
                                const config = statusConfig[status]
                                const statusOrders = ordersByStatus[status] || []
                                return (
                                    <div key={status} className={`flex-1 min-w-[300px] bg-white/5 backdrop-blur-sm rounded-xl border ${config.borderColor} p-4`}>
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-2">
                                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}>{config.label}</span>
                                                <span className="text-xs text-slate-500">{statusOrders.length}</span>
                                            </div>
                                        </div>
                                        <div className="space-y-3 min-h-[200px]">
                                            <AnimatePresence>
                                                {statusOrders.map((order) => (
                                                    <motion.div
                                                        key={order.id}
                                                        layout
                                                        initial={{ opacity: 0, scale: 0.9 }}
                                                        animate={{ opacity: 1, scale: 1 }}
                                                        exit={{ opacity: 0, scale: 0.9 }}
                                                        onClick={() => { setSelectedOrder(order); setShowDetails(true) }}
                                                        className="bg-slate-800/50 border border-white/10 rounded-lg p-4 cursor-pointer hover:border-white/20 transition-all"
                                                    >
                                                        <div className="font-medium text-white truncate">{order.onboarding?.business_name || order.customer_name}</div>
                                                        <div className="text-sm text-slate-400 mt-1 flex items-center gap-1.5">
                                                            <Mail className="w-3.5 h-3.5" />
                                                            {order.customer_email}
                                                        </div>
                                                        <div className="flex items-center justify-between mt-3">
                                                            <span className="text-emerald-400 font-semibold">${order.total_price}</span>
                                                            {order.expected_delivery_date && (
                                                                <span className="text-xs text-slate-500 flex items-center gap-1">
                                                                    <Calendar className="w-3 h-3" />
                                                                    {new Date(order.expected_delivery_date).toLocaleDateString()}
                                                                </span>
                                                            )}
                                                        </div>
                                                        {order.onboarding && (
                                                            <div className="mt-2 flex flex-wrap gap-1">
                                                                <span className="px-2 py-0.5 bg-white/5 text-slate-400 text-xs rounded">{order.onboarding.niche}</span>
                                                                <span className="px-2 py-0.5 bg-white/5 text-slate-400 text-xs rounded flex items-center gap-1">
                                                                    <MapPin className="w-3 h-3" />
                                                                    {order.onboarding.primary_city}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </motion.div>
                                                ))}
                                            </AnimatePresence>
                                            {statusOrders.length === 0 && (
                                                <div className="text-center py-8 text-slate-500 text-sm border-2 border-dashed border-white/10 rounded-lg">No orders</div>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}

                {/* Table View */}
                {viewMode === 'table' && (
                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-white/10">
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Customer</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Business</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Status</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Price</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Created</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {filteredOrders.map((order, i) => (
                                        <motion.tr
                                            key={order.id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: i * 0.03 }}
                                            className="hover:bg-white/[0.03] transition-colors"
                                        >
                                            <td className="px-6 py-4">
                                                <div className="text-white font-medium">{order.customer_name}</div>
                                                <div className="text-sm text-slate-400">{order.customer_email}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="text-white">{order.onboarding?.business_name || '-'}</div>
                                                <div className="text-sm text-slate-400">
                                                    {order.onboarding ? `${order.onboarding.primary_city}, ${order.onboarding.state}` : '-'}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusConfig[order.status]?.bgColor} ${statusConfig[order.status]?.color}`}>
                                                    {statusConfig[order.status]?.label || order.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="text-emerald-400 font-semibold">${order.total_price}</span>
                                            </td>
                                            <td className="px-6 py-4 text-slate-400">{new Date(order.created_at).toLocaleDateString()}</td>
                                            <td className="px-6 py-4">
                                                <button
                                                    onClick={() => { setSelectedOrder(order); setShowDetails(true) }}
                                                    className="px-3 py-1.5 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                                                >
                                                    View Details
                                                </button>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {filteredOrders.length === 0 && (
                            <div className="p-12 text-center">
                                <Package className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">No orders found</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Order Details Modal */}
            <Modal isOpen={showDetails} onClose={() => { setShowDetails(false); setSelectedOrder(null); setViewLogs(false) }} title="Order Details" size="xl">
                {selectedOrder && (
                    <div className="space-y-6">

                        {/* Realtime Logs Section */}
                        {(viewLogs || selectedOrder.status === 'generating' || selectedOrder.status === 'review') && (
                            <div className="mb-6">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-white font-semibold">Generation Progress</h4>
                                    <button
                                        onClick={() => setViewLogs(!viewLogs)}
                                        className="text-xs text-blue-400 hover:text-blue-300"
                                    >
                                        {viewLogs ? 'Hide Logs' : 'Show Logs'}
                                    </button>
                                </div>
                                {viewLogs && (
                                    <LogViewer
                                        orderId={selectedOrder.id}
                                        onComplete={() => {
                                            setGenerating(false)
                                            loadOrders() // Refresh status to Review
                                        }}
                                    />
                                )}
                            </div>
                        )}

                        {/* Interactive Timeline */}
                        {(selectedOrder.status === 'building' || selectedOrder.status === 'generating' || selectedOrder.status === 'review' || selectedOrder.status === 'delivered') && (
                            <div className="bg-white/5 rounded-xl border border-white/10 p-6 mb-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-white font-semibold flex items-center">
                                        <Presentation className="w-5 h-5 mr-2 text-purple-400" />
                                        Creation Journey
                                    </h4>
                                </div>
                                <Timeline
                                    steps={getProcessSteps(selectedOrder)}
                                    currentStepId="strategy"
                                    onViewArtifact={(stepId) => {
                                        // Find artifact for this step
                                        const artifact = selectedOrder.deliverables?.find(d => {
                                            if (stepId === 'strategy') return d.type === 'briefing';
                                            if (stepId === 'architecture') return d.type === 'sitemap';
                                            return false;
                                        });

                                        if (artifact) {
                                            setSelectedArtifact(artifact);
                                        } else {
                                            toast.error('Detalhes ainda não disponíveis para esta etapa');
                                        }
                                    }}
                                />
                            </div>
                        )}

                        {/* Status and Actions */}
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                            <div>
                                <span className="text-sm text-slate-400">Current Status</span>
                                <div className="mt-1">
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig[selectedOrder.status]?.bgColor} ${statusConfig[selectedOrder.status]?.color}`}>
                                        {statusConfig[selectedOrder.status]?.label}
                                    </span>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                {selectedOrder.status === 'generating' && (
                                    <Button
                                        onClick={() => handleResetSingleGeneration(selectedOrder.id)}
                                        className="bg-red-600 hover:bg-red-700"
                                    >
                                        <AlertCircle className="w-4 h-4 mr-2" />
                                        Reset Generation
                                    </Button>
                                )}
                                {(selectedOrder.status === 'paid' || selectedOrder.status === 'building' || selectedOrder.status === 'generating' || selectedOrder.status === 'review') && selectedOrder.onboarding && (
                                    <Button
                                        onClick={() => handleGenerateSite(selectedOrder.id)}
                                        isLoading={generating || selectedOrder.status === 'generating'}
                                        className="bg-purple-600 hover:bg-purple-700"
                                        disabled={generating || selectedOrder.status === 'generating'}
                                    >
                                        <Wand2 className="w-4 h-4 mr-2" />
                                        {selectedOrder.status === 'generating' ? 'Generating...' : 'Generate Site with AI'}
                                    </Button>
                                )}

                                {(selectedOrder.status === 'review' || selectedOrder.status === 'delivered') && selectedOrder.site_url && (
                                    <Button
                                        variant="secondary"
                                        onClick={() => window.open(`/projects/${selectedOrder.id}/ide`, '_blank')}
                                        className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                                    >
                                        <FileCode className="w-4 h-4 mr-2" />
                                        Open IDE
                                    </Button>
                                )}

                                {selectedOrder.status === 'paid' && (
                                    <Button variant="secondary" onClick={() => updateStatus(selectedOrder.id, 'building')}>Start Manually</Button>
                                )}
                                {selectedOrder.status === 'building' && (
                                    <Button variant="secondary" onClick={() => updateStatus(selectedOrder.id, 'review')}>Send for Review</Button>
                                )}
                                {selectedOrder.status === 'review' && (
                                    <Button onClick={() => updateStatus(selectedOrder.id, 'delivered')}>Mark Delivered</Button>
                                )}
                            </div>
                        </div>

                        {/* Customer Info */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 rounded-lg p-4">
                                <p className="text-slate-400 text-sm mb-1">Customer Name</p>
                                <p className="text-white font-medium">{selectedOrder.customer_name}</p>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4">
                                <p className="text-slate-400 text-sm mb-1">Email</p>
                                <p className="text-white">{selectedOrder.customer_email}</p>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4">
                                <p className="text-slate-400 text-sm mb-1">Phone</p>
                                <p className="text-white">{selectedOrder.customer_phone || '-'}</p>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4">
                                <p className="text-slate-400 text-sm mb-1">Total Paid</p>
                                <p className="text-emerald-400 font-semibold">${selectedOrder.total_price}</p>
                            </div>
                        </div>

                        {/* Onboarding Data */}
                        {selectedOrder.onboarding && (
                            <div>
                                <h4 className="font-semibold text-white mb-3">Business Details</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-white/5 rounded-lg p-4">
                                        <p className="text-slate-400 text-sm mb-1">Business Name</p>
                                        <p className="text-white">{selectedOrder.onboarding.business_name}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-4">
                                        <p className="text-slate-400 text-sm mb-1">Niche</p>
                                        <p className="text-white capitalize">{selectedOrder.onboarding.niche}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-4">
                                        <p className="text-slate-400 text-sm mb-1">Location</p>
                                        <p className="text-white">{selectedOrder.onboarding.primary_city}, {selectedOrder.onboarding.state}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-4">
                                        <p className="text-slate-400 text-sm mb-1">Primary Service</p>
                                        <p className="text-white">{selectedOrder.onboarding.primary_service}</p>
                                    </div>
                                </div>
                                <div className="mt-4">
                                    <p className="text-slate-400 text-sm mb-2">Services</p>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedOrder.onboarding.services.map((service, i) => (
                                            <span key={i} className="px-2 py-1 bg-white/10 text-white text-sm rounded">{service}</span>
                                        ))}
                                    </div>
                                </div>
                                {/* Artifact Viewer Modal */}
                                <Modal
                                    isOpen={!!selectedArtifact}
                                    onClose={() => setSelectedArtifact(null)}
                                    title={selectedArtifact?.title || 'Detalhes do Artefato'}
                                    size="xl"
                                >
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between text-sm text-slate-400 border-b border-white/10 pb-4">
                                            <span className="flex items-center">
                                                <Clock className="w-4 h-4 mr-2" />
                                                Gerado em: {selectedArtifact?.created_at ? new Date(selectedArtifact.created_at).toLocaleString('pt-BR') : '-'}
                                            </span>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${selectedArtifact?.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                                                selectedArtifact?.status === 'ready' ? 'bg-blue-500/20 text-blue-400' :
                                                    'bg-gray-500/20 text-gray-400'
                                                }`}>
                                                {selectedArtifact?.status?.toUpperCase()}
                                            </span>
                                        </div>

                                        <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-auto max-h-[60vh] whitespace-pre-wrap">
                                            {selectedArtifact?.content || 'Conteúdo não disponível.'}
                                        </div>

                                        <div className="flex justify-end pt-4 border-t border-white/10">
                                            <Button
                                                variant="secondary"
                                                onClick={() => setSelectedArtifact(null)}
                                            >
                                                Fechar
                                            </Button>
                                        </div>
                                    </div>
                                </Modal>
                            </div>
                        )}

                        {/* Site URL */}
                        {selectedOrder.site_url && (
                            <div className="bg-white/5 rounded-lg p-4">
                                <p className="text-slate-400 text-sm mb-1">Site URL</p>
                                <a href={selectedOrder.site_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline flex items-center gap-2">
                                    <Globe className="w-4 h-4" />
                                    {selectedOrder.site_url}
                                    <ExternalLink className="w-4 h-4" />
                                </a>
                            </div>
                        )}
                    </div>
                )}
            </Modal>
        </div>
    )
}
