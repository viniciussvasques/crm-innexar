'use client'

import React, { useEffect, useState, useRef } from 'react'
import { Terminal, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import api from '@/lib/api'

interface LogEntry {
    id: number
    step: string
    message: string
    status: 'info' | 'success' | 'error' | 'warning'
    timestamp: string
    details?: any
}

interface LogViewerProps {
    orderId: number
    onComplete?: () => void
}

export default function LogViewer({ orderId, onComplete }: LogViewerProps) {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [loading, setLoading] = useState(true)
    const [polling, setPolling] = useState(true)
    const bottomRef = useRef<HTMLDivElement>(null)

    const fetchLogs = async () => {
        try {
            const res = await api.get<LogEntry[]>(`/api/site-orders/${orderId}/logs`)
            setLogs(res.data)

            // Check if finished
            const lastLog = res.data[res.data.length - 1]
            if (lastLog) {
                if (lastLog.step === 'SUCCESS' || lastLog.step === 'ERROR' || lastLog.status === 'error' || lastLog.status === 'success') {
                    setPolling(false)
                    if (lastLog.status === 'success' && onComplete) onComplete()
                }
            }
        } catch (error) {
            console.error("Failed to fetch logs", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchLogs()
        if (!polling) return

        const interval = setInterval(fetchLogs, 2000) // Poll every 2s
        return () => clearInterval(interval)
    }, [orderId, polling])

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    return (
        <div className="bg-slate-950 rounded-lg border border-white/10 overflow-hidden flex flex-col h-96">
            <div className="bg-slate-900 px-4 py-2 border-b border-white/10 flex justify-between items-center">
                <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider font-mono">
                    <Terminal className="w-4 h-4" />
                    Site Generation Logs
                </div>
                {polling && (
                    <div className="flex items-center gap-2 text-blue-400 text-xs">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Generating...
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm">
                {logs.length === 0 && loading && (
                    <div className="text-slate-500 italic text-center mt-10">Connecting to generation worker...</div>
                )}

                {logs.map((log) => (
                    <div key={log.id} className="flex gap-3">
                        <div className="w-16 text-slate-600 text-xs shrink-0 py-0.5">
                            {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center gap-2">
                                <StatusIcon status={log.status} />
                                <span className={getStatusColor(log.status)}>
                                    <span className="font-bold mr-2">[{log.step}]</span>
                                    {log.message}
                                </span>
                            </div>
                            {log.details && (
                                <div className="mt-1 ml-6 p-2 bg-black/30 rounded text-xs text-slate-400 whitespace-pre-wrap overflow-x-auto">
                                    {JSON.stringify(log.details, null, 2)}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    )
}

function StatusIcon({ status }: { status: string }) {
    switch (status) {
        case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />
        case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />
        case 'warning': return <AlertCircle className="w-4 h-4 text-amber-500" />
        default: return <div className="w-4 h-4 flex items-center justify-center"><div className="w-1.5 h-1.5 bg-blue-500 rounded-full" /></div>
    }
}

function getStatusColor(status: string) {
    switch (status) {
        case 'success': return 'text-emerald-400'
        case 'error': return 'text-red-400'
        case 'warning': return 'text-amber-400'
        default: return 'text-slate-300'
    }
}
