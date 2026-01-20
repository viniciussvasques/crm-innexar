import { useState, useEffect, useCallback } from 'react'
import api from '@/lib/api'

export interface Notification {
  id: number
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  recipient_id: number
  is_read: boolean
  created_at: string
  related_entity_type?: string
  related_entity_id?: number
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)

  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get<Notification[]>('/api/notifications/')
      setNotifications(response.data)
      setUnreadCount(response.data.filter(n => !n.is_read).length)
    } catch (error: any) {
      // Silenciar erros 401 (não autenticado) e 500 intermitentes
      if (error?.response?.status !== 401) {
        console.error('Erro ao carregar notificações:', error)
      }
      // Manter notificações existentes em caso de erro
    } finally {
      setLoading(false)
    }
  }, [])

  const markAsRead = useCallback(async (notificationId: number) => {
    try {
      await api.put(`/api/notifications/${notificationId}/read`)
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Erro ao marcar notificação como lida:', error)
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      await api.put('/api/notifications/mark-all-read')
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      )
      setUnreadCount(0)
    } catch (error) {
      console.error('Erro ao marcar todas notificações como lidas:', error)
    }
  }, [])

  // Carregar notificações ao montar
  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  // Polling para novas notificações (a cada 30 segundos)
  useEffect(() => {
    const interval = setInterval(() => {
      loadNotifications()
    }, 30000) // 30 segundos

    return () => clearInterval(interval)
  }, [loadNotifications])

  return {
    notifications,
    unreadCount,
    loading,
    loadNotifications,
    markAsRead,
    markAllAsRead
  }
}
