import { useState, useCallback, useEffect } from 'react'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import { SiteOrder, OrderStats } from '@/app/site-orders/types'

export const useSiteOrders = () => {
    const [orders, setOrders] = useState<SiteOrder[]>([])
    const [stats, setStats] = useState<OrderStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)

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

    const updateStatus = async (
        orderId: number,
        newStatus: string,
        extra?: Partial<{
            admin_notes: string
            expected_delivery_date: string
            site_url: string
            repository_url: string
        }>
    ) => {
        try {
            await api.patch(`/api/site-orders/${orderId}/status`, {
                status: newStatus,
                ...(extra || {})
            })
            await loadOrders()
            toast.success('Status updated successfully')
        } catch (error) {
            console.error('Error updating status:', error)
            toast.error('Failed to update status')
        }
    }

    const generateSite = async (orderId: number) => {
        if (!confirm('Are you sure you want to trigger AI generation? This will overwrite existing files.')) return false

        setGenerating(true)
        try {
            await api.post(`/api/site-orders/${orderId}/build`)
            toast.success('Site generation started successfully!')
            await loadOrders()
            return true
        } catch (error: any) {
            console.error(error)
            toast.error(error.response?.data?.detail || 'Failed to start generation')
            return false
        } finally {
            setGenerating(false)
        }
    }

    const checkEmptyGenerations = async () => {
        try {
            const res = await api.get('/api/site-orders/check-empty-generations')
            return res.data
        } catch (error: any) {
            console.error('Error checking empty generations:', error)
            let errorMessage = 'Failed to check empty generations'
            
            if (error.response?.data) {
                errorMessage = error.response.data.error || error.response.data.detail || errorMessage
            } else if (error.message) {
                errorMessage = error.message
            }
            
            // Handle 422 specifically
            if (error.response?.status === 422) {
                errorMessage = 'Erro de validação. Verifique se está autenticado corretamente.'
            }
            
            toast.error(errorMessage)
            return null
        }
    }

    const resetEmptyGenerations = async () => {
        if (!confirm('Are you sure you want to reset all empty generations? This will clear files and reset status to BUILDING.')) return false

        try {
            const res = await api.post('/api/site-orders/reset-empty-generations')
            toast.success(`Reset ${res.data.reset_count} orders successfully!`)
            await loadOrders()
            return res.data
        } catch (error: any) {
            console.error(error)
            toast.error(error.response?.data?.detail || 'Failed to reset empty generations')
            return null
        }
    }

    const resetGeneration = async (orderId: number) => {
        if (!confirm('Are you sure you want to reset this generation? This will clear files and allow retry.')) return false

        try {
            const res = await api.post(`/api/site-orders/${orderId}/reset-generation`)
            toast.success('Generation reset successfully!')
            await loadOrders()
            return res.data
        } catch (error: any) {
            console.error(error)
            toast.error(error.response?.data?.detail || 'Failed to reset generation')
            return null
        }
    }

    const generateBriefingDoc = async (orderId: number) => {
        try {
            const res = await api.post(`/api/site-orders/${orderId}/deliverables/briefing`)
            toast.success('Briefing document generated successfully')
            await loadOrders()
            return res.data
        } catch (error: any) {
            console.error('Error generating briefing document:', error)
            toast.error(error.response?.data?.error || 'Failed to generate briefing document')
            return null
        }
    }

    const generateSitemapAI = async (orderId: number) => {
        try {
            const res = await api.post(`/api/site-orders/${orderId}/ai/plan-sitemap`)
            toast.success('AI sitemap generated successfully')
            await loadOrders()
            return res.data
        } catch (error: any) {
            console.error('Error generating sitemap with AI:', error)
            toast.error(error.response?.data?.error || 'Failed to generate sitemap with AI')
            return null
        }
    }

    const generateHomeCopyAI = async (orderId: number) => {
        try {
            const res = await api.post(`/api/site-orders/${orderId}/ai/home-copy`)
            toast.success('AI Home copy draft generated successfully')
            await loadOrders()
            return res.data
        } catch (error: any) {
            console.error('Error generating home copy with AI:', error)
            toast.error(error.response?.data?.error || 'Failed to generate Home copy with AI')
            return null
        }
    }

    return {
        orders,
        stats,
        loading,
        generating,
        loadOrders,
        updateStatus,
        generateSite,
        checkEmptyGenerations,
        resetEmptyGenerations,
        resetGeneration,
        generateBriefingDoc,
        generateSitemapAI,
        generateHomeCopyAI,
        setGenerating // Exporting setter if UI needs strict control
    }
}
