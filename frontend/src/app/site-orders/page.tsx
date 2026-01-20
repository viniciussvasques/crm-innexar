'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Modal from '@/components/Modal'
import Button from '@/components/Button'

// Types
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
    addon?: {
        name: string
        slug: string
    }
}

interface OrderStats {
    status_counts: Record<string, number>
    total_revenue: number
    orders_this_month: number
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string }> = {
    pending_payment: { label: 'Pending Payment', color: 'text-gray-700', bgColor: 'bg-gray-100' },
    paid: { label: 'Paid', color: 'text-yellow-700', bgColor: 'bg-yellow-100' },
    onboarding_pending: { label: 'Onboarding', color: 'text-orange-700', bgColor: 'bg-orange-100' },
    building: { label: 'Building', color: 'text-blue-700', bgColor: 'bg-blue-100' },
    review: { label: 'In Review', color: 'text-purple-700', bgColor: 'bg-purple-100' },
    delivered: { label: 'Delivered', color: 'text-green-700', bgColor: 'bg-green-100' },
    cancelled: { label: 'Cancelled', color: 'text-red-700', bgColor: 'bg-red-100' },
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
        if (!token) {
            router.push('/login')
            return
        }
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

    // Group orders by status for Kanban
    const ordersByStatus = useMemo(() => {
        const grouped: Record<string, SiteOrder[]> = {
            paid: [],
            building: [],
            review: [],
            delivered: [],
        }
        orders.forEach(order => {
            if (grouped[order.status]) {
                grouped[order.status].push(order)
            }
        })
        return grouped
    }, [orders])

    if (loading) {
        return (
            <div className="space-y-4">
                <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
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
                    <h2 className="text-3xl font-bold text-gray-900">Site Orders</h2>
                    <p className="text-gray-500 text-sm mt-1">Manage Launch Site orders and deliveries</p>
                </div>
                <div className="flex items-center gap-3">
                    {/* View Toggle */}
                    <div className="bg-gray-100 rounded-lg p-1 flex">
                        <button
                            onClick={() => setViewMode('kanban')}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'kanban' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                                }`}
                        >
                            📋 Kanban
                        </button>
                        <button
                            onClick={() => setViewMode('table')}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                                }`}
                        >
                            📊 Table
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-500">Total Revenue</div>
                        <div className="text-2xl font-bold text-green-600">${stats.total_revenue.toLocaleString()}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-500">Orders This Month</div>
                        <div className="text-2xl font-bold text-blue-600">{stats.orders_this_month}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-500">In Progress</div>
                        <div className="text-2xl font-bold text-orange-600">
                            {(stats.status_counts['building'] || 0) + (stats.status_counts['review'] || 0)}
                        </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-500">Delivered</div>
                        <div className="text-2xl font-bold text-green-600">{stats.status_counts['delivered'] || 0}</div>
                    </div>
                </div>
            )}

            {/* Kanban View */}
            {viewMode === 'kanban' && (
                <div className="grid grid-cols-4 gap-4">
                    {['paid', 'building', 'review', 'delivered'].map(status => (
                        <div key={status} className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[status].bgColor} ${statusConfig[status].color}`}>
                                        {statusConfig[status].label}
                                    </span>
                                    <span className="text-gray-400 text-sm">{ordersByStatus[status]?.length || 0}</span>
                                </div>
                            </div>
                            <div className="space-y-3">
                                {ordersByStatus[status]?.map(order => (
                                    <div
                                        key={order.id}
                                        onClick={() => {
                                            setSelectedOrder(order)
                                            setShowDetails(true)
                                        }}
                                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
                                    >
                                        <div className="font-medium text-gray-900 truncate">
                                            {order.onboarding?.business_name || order.customer_name}
                                        </div>
                                        <div className="text-sm text-gray-500 mt-1">{order.customer_email}</div>
                                        <div className="flex items-center justify-between mt-3">
                                            <span className="text-sm font-medium text-blue-600">${order.total_price}</span>
                                            {order.expected_delivery_date && (
                                                <span className="text-xs text-gray-400">
                                                    Due: {new Date(order.expected_delivery_date).toLocaleDateString()}
                                                </span>
                                            )}
                                        </div>
                                        {order.onboarding && (
                                            <div className="mt-2 flex flex-wrap gap-1">
                                                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                                    {order.onboarding.niche}
                                                </span>
                                                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                                    {order.onboarding.primary_city}, {order.onboarding.state}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                {(!ordersByStatus[status] || ordersByStatus[status].length === 0) && (
                                    <div className="text-center py-8 text-gray-400 text-sm">No orders</div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Table View */}
            {viewMode === 'table' && (
                <>
                    {/* Filters */}
                    <div className="mb-6 bg-white rounded-lg shadow p-4">
                        <div className="flex items-center gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                                <select
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="all">All Statuses</option>
                                    {Object.entries(statusConfig).map(([value, config]) => (
                                        <option key={value} value={value}>{config.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Orders Table */}
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Business</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredOrders.map(order => (
                                    <tr key={order.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">{order.customer_name}</div>
                                            <div className="text-sm text-gray-500">{order.customer_email}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{order.onboarding?.business_name || '-'}</div>
                                            <div className="text-sm text-gray-500">
                                                {order.onboarding ? `${order.onboarding.primary_city}, ${order.onboarding.state}` : '-'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs font-medium rounded-full ${statusConfig[order.status]?.bgColor} ${statusConfig[order.status]?.color}`}>
                                                {statusConfig[order.status]?.label || order.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">${order.total_price}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-500">
                                                {new Date(order.created_at).toLocaleDateString()}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <button
                                                onClick={() => {
                                                    setSelectedOrder(order)
                                                    setShowDetails(true)
                                                }}
                                                className="text-blue-600 hover:text-blue-800 font-medium"
                                            >
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {filteredOrders.length === 0 && (
                            <div className="text-center py-12 text-gray-500">No orders found</div>
                        )}
                    </div>
                </>
            )}

            {/* Order Details Modal */}
            <Modal
                isOpen={showDetails}
                onClose={() => {
                    setShowDetails(false)
                    setSelectedOrder(null)
                }}
                title="Order Details"
                size="xl"
            >
                {selectedOrder && (
                    <div className="space-y-6">
                        {/* Status and Actions */}
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <span className="text-sm text-gray-500">Current Status</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig[selectedOrder.status]?.bgColor} ${statusConfig[selectedOrder.status]?.color}`}>
                                        {statusConfig[selectedOrder.status]?.label}
                                    </span>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                {selectedOrder.status === 'paid' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'building')}>
                                        Start Building
                                    </Button>
                                )}
                                {selectedOrder.status === 'building' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'review')}>
                                        Send for Review
                                    </Button>
                                )}
                                {selectedOrder.status === 'review' && (
                                    <Button onClick={() => handleStatusUpdate(selectedOrder.id, 'delivered')}>
                                        Mark Delivered
                                    </Button>
                                )}
                            </div>
                        </div>

                        {/* Customer Info */}
                        <div>
                            <h4 className="font-medium text-gray-900 mb-3">Customer Information</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-500">Name</label>
                                    <div className="text-gray-900">{selectedOrder.customer_name}</div>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-500">Email</label>
                                    <div className="text-gray-900">{selectedOrder.customer_email}</div>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-500">Phone</label>
                                    <div className="text-gray-900">{selectedOrder.customer_phone || '-'}</div>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-500">Total Paid</label>
                                    <div className="text-gray-900 font-medium">${selectedOrder.total_price}</div>
                                </div>
                            </div>
                        </div>

                        {/* Onboarding Data */}
                        {selectedOrder.onboarding && (
                            <div>
                                <h4 className="font-medium text-gray-900 mb-3">Business Details</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-gray-500">Business Name</label>
                                        <div className="text-gray-900">{selectedOrder.onboarding.business_name}</div>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500">Niche</label>
                                        <div className="text-gray-900 capitalize">{selectedOrder.onboarding.niche}</div>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500">Location</label>
                                        <div className="text-gray-900">
                                            {selectedOrder.onboarding.primary_city}, {selectedOrder.onboarding.state}
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500">Primary Service</label>
                                        <div className="text-gray-900">{selectedOrder.onboarding.primary_service}</div>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500">Tone</label>
                                        <div className="text-gray-900 capitalize">{selectedOrder.onboarding.tone}</div>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500">Primary CTA</label>
                                        <div className="text-gray-900 capitalize">{selectedOrder.onboarding.primary_cta}</div>
                                    </div>
                                </div>
                                <div className="mt-4">
                                    <label className="text-sm text-gray-500">Services</label>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {selectedOrder.onboarding.services.map((service, i) => (
                                            <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                                                {service}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                {selectedOrder.onboarding.primary_color && (
                                    <div className="mt-4">
                                        <label className="text-sm text-gray-500">Primary Color</label>
                                        <div className="flex items-center gap-2 mt-1">
                                            <div
                                                className="w-6 h-6 rounded-full border"
                                                style={{ backgroundColor: selectedOrder.onboarding.primary_color }}
                                            />
                                            <span className="text-gray-900">{selectedOrder.onboarding.primary_color}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Delivery Info */}
                        <div>
                            <h4 className="font-medium text-gray-900 mb-3">Delivery</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-500">Expected Delivery</label>
                                    <div className="text-gray-900">
                                        {selectedOrder.expected_delivery_date
                                            ? new Date(selectedOrder.expected_delivery_date).toLocaleDateString()
                                            : '-'}
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-500">Revisions</label>
                                    <div className="text-gray-900">
                                        {selectedOrder.revisions_used} / {selectedOrder.revisions_included} used
                                    </div>
                                </div>
                                {selectedOrder.site_url && (
                                    <div className="col-span-2">
                                        <label className="text-sm text-gray-500">Site URL</label>
                                        <a
                                            href={selectedOrder.site_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:underline"
                                        >
                                            {selectedOrder.site_url}
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    )
}
