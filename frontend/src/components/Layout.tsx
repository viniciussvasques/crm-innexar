'use client'

import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { User } from '@/types'
import { ToastContainer } from './Toast'
import LanguageSelector from './LanguageSelector'
import NotificationDropdown from './NotificationDropdown'
import { useLanguage } from '@/contexts/LanguageContext'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)
  const { t } = useLanguage()

  useEffect(() => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    
    if (!token && pathname !== '/login') {
      router.push('/login')
      return
    }

    if (userStr) {
      try {
        setUser(JSON.parse(userStr) as User)
      } catch (error) {
        console.error('Erro ao parsear usuário:', error)
      }
    }
  }, [router, pathname])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const navigation = [
    { name: t('nav.dashboard'), href: '/dashboard', icon: '📊' },
    { name: t('nav.contacts'), href: '/contacts', icon: '👥' },
    { name: t('nav.opportunities'), href: '/opportunities', icon: '💼' },
    { name: t('nav.projects'), href: '/projects', icon: '🚀' },
    { name: t('nav.activities'), href: '/activities', icon: '📝' },
    { name: t('nav.ai'), href: '/ai', icon: '✨' },
    ...(user?.role === 'admin' ? [
      { name: t('nav.analytics'), href: '/analytics', icon: '📈' },
      { name: t('nav.commissions'), href: '/commissions', icon: '💰' }
    ] : []),
    ...(user?.role === 'planejamento' ? [
      { name: t('nav.planning'), href: '/planning', icon: '📋' }
    ] : []),
    ...(user?.role === 'admin' ? [
      { name: t('nav.users'), href: '/users', icon: '👤' },
      { name: t('nav.aiConfig'), href: '/ai-config', icon: '⚙️' }
    ] : [])
  ]

  if (pathname === '/login') {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-primary">Innexar CRM</h1>
            <div className="flex items-center gap-4">
              <NotificationDropdown />
              <LanguageSelector />
              <span className="text-sm text-gray-600">{user?.name}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)]">
          <nav className="p-4 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  <span className="font-medium">{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  )
}

