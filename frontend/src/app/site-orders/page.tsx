'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Package, DollarSign, Clock, CheckCircle, Truck, AlertCircle,
    LayoutGrid, LayoutList, Building2, MapPin, Phone, Mail, Calendar, ExternalLink, Globe
} from 'lucide-react'

interface SiteOrder {
    id: number
    customer_name: string
    customer_email: string
    customer_phone?: string
    status: 'pending_payment' | 'paid' | 'onboarding_pending' | 'building' | 'review' | 'delivered' | 'cancelled'
    base_price: number
    total_price: number
    delivery_days: number
    expected_delivery_date?: string
    actual_delivery_date?: string
    revisions_included: number
    revisions_used: number
    site_url?: string
    repository_url?: string
    admin_notes?: string
    created_at: string
    paid_at?: string
    onboarding_completed_at?: string
    delivered_at?: string
    onboarding?: SiteOnboarding
    addons?: SiteOrderAddon[]
}

interface SiteOnboarding {
    id: number
    business_name: string
    business_email: string
    business_phone: string
    has_whatsapp: boolean
    niche: string
    primary_city: string
    state: string
    services: string[]
    primary_service: string
    tone: string
    primary_cta: string
    primary_color?: string
}

interface SiteOrderAddon {
    id: number
    addon_id: number
    price_paid: number
    addon?: { name: string; slug: string }
}

interface OrderStats {
    status_counts: Record<string, number>
    total_revenue: number
    orders_this_month: number
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string; borderColor: string; icon: React.ComponentType<any> }> = {
    pending_payment: { label: 'Pending Payment', color: 'text-slate-300', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: AlertCircle },
    paid: { label: 'Paid', color: 'text-amber-300', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/30', icon: DollarSign },
    onboarding_pending: { label: 'Onboarding', color: 'text-orange-300', bgColor: 'bg-orange-500/20', borderColor: 'border-orange-500/30', icon: Clock },
    building: { label: 'Building', color: 'text-blue-300', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Package },
    review: { label: 'In Review', color: 'text-purple-300', bgColor: 'bg-purple-500/20', borderColor: 'border-purple-500/30', icon: Clock },
    delivered: { label: 'Delivered', color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30', icon: CheckCircle },
    cancelled: { label: 'Cancelled', color: 'text-red-300', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30', icon: AlertCircle },
}

export default function SiteOrdersPage() {
    const router = useRouter()
    const [orders, setOrders] = useState<SiteOrder[]>([])
    const [stats, setStats] = useState<OrderStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [selectedOrder, setSelectedOrder] = useState<SiteOrder | null>(null)
    const [showDetails, setShowDetails] = useState(false)
    const [viewMode, setViewMode] = useState<'table' | 'kanban'>('kanban')

    const loadOrders = useCallback(async () => {
        try {
            const [ordersRes, statsRes] = await Promise.all([
                api.get<SiteOrder[]>('/api/site-orders/'),
                api.get<OrderStats>('/api/site-orders/stats'),
            ])
            setOrders(ordersRes.data)
            setStats(statsRes.data)
        } catch (error) {
            console.error('Error loading orders:', error)
            toast.error('Failed to load orders')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
        if (!token) { router.push('/login'); return }
        loadOrders()
    }, [router, loadOrders])

    const handleStatusUpdate = async (orderId: number, newStatus: string) => {
        try {
            await api.patch(`/api/site-orders/${orderId}/status`, { status: newStatus })
            loadOrders()
            toast.success('Status updated successfully')
        } catch (error) {
            console.error('Error updating status:', error)
            toast.error('Failed to update status')
        }
    }

    const filteredOrders = useMemo(() => {
        if (statusFilter === 'all') return orders
        return orders.filter(order => order.status === statusFilter)
    }, [orders, statusFilter])

    const ordersByStatus = useMemo(() => {
        const grouped: Record<string, SiteOrder[]> = { paid: [], building: [], review: [], delivered: [] }
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
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: 'Total Revenue', value: `$${stats.total_revenue.toLocaleString()}`, icon: DollarSign, color: 'emerald' },
                            { label: 'Orders This Month', value: stats.orders_this_month, icon: Package, color: 'blue' },
                            { label: 'In Progress', value: (stats.status_counts['building'] || 0) + (stats.status_counts['review'] || 0), icon: Clock, color: 'amber' },
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
                            {['paid', 'building', 'review', 'delivered'].map(status => {
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
            <Modal isOpen={showDetails} onClose={() => { setShowDetails(false); setSelectedOrder(null) }} title="Order Details" size="xl">
                {selectedOrder && (
                    <div className="space-y-6">
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
                                {selectedOrder.status === 'paid' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'building')}>Start Building</Button>
                                )}
                                {selectedOrder.status === 'building' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'review')}>Send for Review</Button>
                                )}
                                {selectedOrder.status === 'review' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'delivered')}>Mark Delivered</Button>
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
