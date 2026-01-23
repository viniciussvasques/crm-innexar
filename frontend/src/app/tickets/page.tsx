'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    MessageSquare, AlertCircle, Clock, CheckCircle2, Users,
    Filter, RefreshCw, ChevronRight, Search
} from 'lucide-react'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'

interface Ticket {
    id: number
    subject: string
    status: string
    priority: string
    customer_email: string | null
    order_id: number | null
    assigned_to: number | null
    assigned_name: string | null
    created_at: string
    updated_at: string
    message_count: number
}

interface TicketStats {
    open: number
    pending: number
    resolved: number
    closed: number
    total: number
}

const statusConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    open: { icon: AlertCircle, label: 'Open', color: 'blue' },
    pending: { icon: Clock, label: 'Pending', color: 'yellow' },
    resolved: { icon: CheckCircle2, label: 'Resolved', color: 'green' },
    closed: { icon: CheckCircle2, label: 'Closed', color: 'slate' },
}

const priorityColors: Record<string, string> = {
    low: 'text-slate-400',
    medium: 'text-blue-400',
    high: 'text-orange-400',
    urgent: 'text-red-400',
}

export default function TicketsPage() {
    const router = useRouter()
    const { t } = useLanguage()
    const [tickets, setTickets] = useState<Ticket[]>([])
    const [stats, setStats] = useState<TicketStats>({ open: 0, pending: 0, resolved: 0, closed: 0, total: 0 })
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState<string>('')
    const [searchQuery, setSearchQuery] = useState('')

    const fetchData = useCallback(async () => {
        try {
            const [ticketsRes, statsRes] = await Promise.all([
                api.get('/api/tickets', { params: { status: statusFilter || undefined } }),
                api.get('/api/tickets/stats')
            ])
            setTickets(ticketsRes.data)
            setStats(statsRes.data)
        } catch (error) {
            console.error('Error fetching tickets:', error)
        } finally {
            setLoading(false)
        }
    }, [statusFilter])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const getColorClasses = (color: string) => {
        const colors: Record<string, { bg: string; text: string; border: string }> = {
            blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
            yellow: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' },
            green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
            slate: { bg: 'bg-slate-500/20', text: 'text-slate-400', border: 'border-slate-500/30' },
        }
        return colors[color] || colors.blue
    }

    const filteredTickets = tickets.filter(ticket => {
        if (!searchQuery) return true
        return ticket.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
            ticket.customer_email?.toLowerCase().includes(searchQuery.toLowerCase())
    })

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Support Tickets</h1>
                    <p className="text-slate-400">Manage customer support requests</p>
                </div>
                <motion.button
                    onClick={() => fetchData()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-300 transition-colors"
                >
                    <RefreshCw className="w-5 h-5" />
                </motion.button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(statusConfig).map(([key, config], index) => {
                    const count = stats[key as keyof TicketStats] || 0
                    const colors = getColorClasses(config.color)
                    const Icon = config.icon

                    return (
                        <motion.button
                            key={key}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            onClick={() => setStatusFilter(statusFilter === key ? '' : key)}
                            className={`p-4 rounded-xl border transition-all ${statusFilter === key
                                    ? `${colors.bg} ${colors.border} border-2`
                                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                                }`}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center`}>
                                    <Icon className={`w-5 h-5 ${colors.text}`} />
                                </div>
                                <div className="text-left">
                                    <p className="text-2xl font-bold text-white">{count}</p>
                                    <p className="text-xs text-slate-400">{config.label}</p>
                                </div>
                            </div>
                        </motion.button>
                    )
                })}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-4 rounded-xl bg-white/5 border border-white/10"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                            <MessageSquare className="w-5 h-5 text-purple-400" />
                        </div>
                        <div className="text-left">
                            <p className="text-2xl font-bold text-white">{stats.total}</p>
                            <p className="text-xs text-slate-400">Total</p>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Search & Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search tickets..."
                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                    />
                </div>
                {statusFilter && (
                    <button
                        onClick={() => setStatusFilter('')}
                        className="px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-300 flex items-center gap-2"
                    >
                        <Filter className="w-4 h-4" />
                        Clear filter
                    </button>
                )}
            </div>

            {/* Tickets List */}
            <div className="space-y-3">
                {filteredTickets.length > 0 ? (
                    filteredTickets.map((ticket, index) => {
                        const status = statusConfig[ticket.status] || statusConfig.open
                        const colors = getColorClasses(status.color)
                        const StatusIcon = status.icon

                        return (
                            <motion.div
                                key={ticket.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.03 }}
                                onClick={() => router.push(`/tickets/${ticket.id}`)}
                                className="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl p-4 cursor-pointer transition-all"
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-xl ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                                        <StatusIcon className={`w-5 h-5 ${colors.text}`} />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-white font-medium truncate">{ticket.subject}</h3>
                                            <span className={`text-xs font-medium ${priorityColors[ticket.priority]} capitalize`}>
                                                {ticket.priority}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-3 text-sm text-slate-400 mt-1">
                                            <span>{ticket.customer_email || 'Unknown'}</span>
                                            <span>•</span>
                                            <span>{ticket.message_count} messages</span>
                                            {ticket.assigned_name && (
                                                <>
                                                    <span>•</span>
                                                    <span className="flex items-center gap-1">
                                                        <Users className="w-3 h-3" />
                                                        {ticket.assigned_name}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    <div className="hidden md:flex items-center gap-3 flex-shrink-0">
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text} ${colors.border} border`}>
                                            {status.label}
                                        </span>
                                        <span className="text-xs text-slate-500">
                                            {new Date(ticket.updated_at).toLocaleDateString()}
                                        </span>
                                        <ChevronRight className="w-4 h-4 text-slate-400" />
                                    </div>
                                </div>
                            </motion.div>
                        )
                    })
                ) : (
                    <div className="text-center py-12">
                        <MessageSquare className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <p className="text-slate-400">No tickets found</p>
                    </div>
                )}
            </div>
        </div>
    )
}
