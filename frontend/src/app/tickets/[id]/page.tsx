'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    ArrowLeft, Send, User, Building2, Clock, CheckCircle2,
    AlertCircle, Loader2, UserCircle
} from 'lucide-react'
import api from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'

interface Message {
    id: number
    sender_type: string
    sender_name: string | null
    message: string
    created_at: string
}

interface TicketDetail {
    id: number
    subject: string
    status: string
    priority: string
    customer_email: string | null
    customer_id: number
    order_id: number | null
    order_name: string | null
    assigned_to: number | null
    assigned_name: string | null
    created_at: string
    updated_at: string
    resolved_at: string | null
    messages: Message[]
}

const statusOptions = ['open', 'pending', 'resolved', 'closed']
const priorityOptions = ['low', 'medium', 'high', 'urgent']

const statusColors: Record<string, { bg: string; text: string }> = {
    open: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
    pending: { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
    resolved: { bg: 'bg-green-500/20', text: 'text-green-400' },
    closed: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
}

export default function TicketDetailPage() {
    const router = useRouter()
    const params = useParams()
    const ticketId = params.id as string
    const { t } = useLanguage()

    const [ticket, setTicket] = useState<TicketDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [replyText, setReplyText] = useState('')
    const [sending, setSending] = useState(false)
    const [updatingStatus, setUpdatingStatus] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const fetchTicket = useCallback(async () => {
        try {
            const response = await api.get(`/api/tickets/${ticketId}`)
            setTicket(response.data)
        } catch (error) {
            console.error('Error fetching ticket:', error)
        } finally {
            setLoading(false)
        }
    }, [ticketId])

    useEffect(() => {
        fetchTicket()
    }, [fetchTicket])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [ticket?.messages])

    const handleSendReply = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!replyText.trim() || sending) return

        setSending(true)
        try {
            await api.post(`/api/tickets/${ticketId}/reply`, { message: replyText })
            setReplyText('')
            fetchTicket()
        } catch (error) {
            console.error('Error sending reply:', error)
        } finally {
            setSending(false)
        }
    }

    const handleStatusChange = async (newStatus: string) => {
        setUpdatingStatus(true)
        try {
            await api.patch(`/api/tickets/${ticketId}/status`, { status: newStatus })
            fetchTicket()
        } catch (error) {
            console.error('Error updating status:', error)
        } finally {
            setUpdatingStatus(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    if (!ticket) {
        return (
            <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <p className="text-white text-lg">Ticket not found</p>
            </div>
        )
    }

    const statusColor = statusColors[ticket.status] || statusColors.open

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <motion.button
                    onClick={() => router.push('/tickets')}
                    whileHover={{ x: -4 }}
                    className="p-2 bg-white/5 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors"
                >
                    <ArrowLeft className="w-5 h-5" />
                </motion.button>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-white">{ticket.subject}</h1>
                    <p className="text-slate-400 text-sm">Ticket #{ticket.id}</p>
                </div>
                <select
                    value={ticket.status}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    disabled={updatingStatus}
                    className={`px-4 py-2 rounded-xl border ${statusColor.bg} ${statusColor.text} border-current/30 bg-transparent focus:outline-none cursor-pointer disabled:opacity-50`}
                >
                    {statusOptions.map(status => (
                        <option key={status} value={status} className="bg-slate-900 text-white">
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                        </option>
                    ))}
                </select>
            </div>

            {/* Info Cards */}
            <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-3">
                        <UserCircle className="w-5 h-5 text-blue-400" />
                        <span className="text-slate-400 text-sm">Customer</span>
                    </div>
                    <p className="text-white font-medium">{ticket.customer_email || 'Unknown'}</p>
                </div>

                {ticket.order_name && (
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                        <div className="flex items-center gap-3 mb-3">
                            <Building2 className="w-5 h-5 text-purple-400" />
                            <span className="text-slate-400 text-sm">Project</span>
                        </div>
                        <p className="text-white font-medium">{ticket.order_name}</p>
                    </div>
                )}

                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-3">
                        <Clock className="w-5 h-5 text-cyan-400" />
                        <span className="text-slate-400 text-sm">Created</span>
                    </div>
                    <p className="text-white font-medium">{new Date(ticket.created_at).toLocaleString()}</p>
                </div>
            </div>

            {/* Messages */}
            <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-white/10">
                    <h2 className="text-white font-medium">Conversation</h2>
                </div>

                <div className="max-h-[400px] overflow-y-auto p-4 space-y-4">
                    {ticket.messages.map((msg, index) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className={`flex gap-3 ${msg.sender_type === 'staff' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.sender_type === 'staff' ? 'bg-blue-500/20' : 'bg-purple-500/20'
                                }`}>
                                <User className={`w-4 h-4 ${msg.sender_type === 'staff' ? 'text-blue-400' : 'text-purple-400'
                                    }`} />
                            </div>
                            <div className={`flex-1 ${msg.sender_type === 'staff' ? 'text-right' : ''}`}>
                                <div className={`inline-block max-w-[80%] p-3 rounded-xl ${msg.sender_type === 'staff'
                                        ? 'bg-blue-500/20 border border-blue-500/30'
                                        : 'bg-white/10 border border-white/10'
                                    }`}>
                                    <p className="text-white text-sm whitespace-pre-wrap">{msg.message}</p>
                                </div>
                                <p className="text-xs text-slate-500 mt-1">
                                    {msg.sender_name || (msg.sender_type === 'staff' ? 'Support' : 'Customer')} •
                                    {new Date(msg.created_at).toLocaleString()}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Reply Form */}
                <form onSubmit={handleSendReply} className="p-4 border-t border-white/10">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={replyText}
                            onChange={(e) => setReplyText(e.target.value)}
                            placeholder="Type your reply..."
                            className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                        />
                        <motion.button
                            type="submit"
                            disabled={!replyText.trim() || sending}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white font-medium flex items-center gap-2 disabled:opacity-50"
                        >
                            {sending ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                            Send
                        </motion.button>
                    </div>
                </form>
            </div>

            {/* Quick Actions */}
            {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
                <div className="flex gap-3">
                    <motion.button
                        onClick={() => handleStatusChange('resolved')}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-xl text-green-400 hover:bg-green-500/30 transition-colors"
                    >
                        <CheckCircle2 className="w-4 h-4" />
                        Mark as Resolved
                    </motion.button>
                </div>
            )}
        </div>
    )
}
