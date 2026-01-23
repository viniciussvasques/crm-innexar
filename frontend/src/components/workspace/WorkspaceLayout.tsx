'use client'

import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    LayoutDashboard,
    Users,
    FolderOpen,
    Rocket,
    MessageSquare,
    BarChart3,
    DollarSign,
    Globe,
    Settings,
    LogOut,
    ChevronLeft,
    Bell,
    Menu,
    X,
    Sparkles,
    Bot,
    Calendar,
    Target,
    Trophy,
    FileText
} from 'lucide-react'
import { User } from '@/types'
import { ToastContainer } from '../Toast'
import { useLanguage } from '@/contexts/LanguageContext'

interface WorkspaceLayoutProps {
    children: React.ReactNode
}

interface NavItem {
    name: string
    href: string
    icon: React.ElementType
    roles?: string[]
    badge?: number
}

export default function WorkspaceLayout({ children }: WorkspaceLayoutProps) {
    const router = useRouter()
    const pathname = usePathname()
    const [user, setUser] = useState<User | null>(null)
    const [sidebarOpen, setSidebarOpen] = useState(true)
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
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
                console.error('Error parsing user:', error)
            }
        }
    }, [router, pathname])

    const handleLogout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
    }

    const mainNavItems: NavItem[] = [
        { name: t('nav.dashboard'), href: '/dashboard', icon: LayoutDashboard },
        { name: t('nav.contacts'), href: '/contacts', icon: Users },
        { name: t('nav.opportunities'), href: '/opportunities', icon: Target },
        { name: t('nav.projects'), href: '/projects', icon: Rocket },
        { name: t('nav.activities'), href: '/activities', icon: Calendar },
    ]

    const toolsNavItems: NavItem[] = [
        { name: t('nav.ai'), href: '/ai', icon: Sparkles },
        { name: t('nav.siteOrders'), href: '/site-orders', icon: Globe, roles: ['admin'] },
        { name: 'Support Tickets', href: '/tickets', icon: MessageSquare, roles: ['admin'], badge: 0 },
    ]

    const adminNavItems: NavItem[] = [
        { name: t('nav.analytics'), href: '/analytics', icon: BarChart3, roles: ['admin'] },
        { name: t('nav.commissions'), href: '/commissions', icon: DollarSign, roles: ['admin'] },
        { name: t('nav.planning'), href: '/planning', icon: FileText, roles: ['admin', 'planejamento'] },
        { name: t('nav.leaderboard'), href: '/leaderboard', icon: Trophy, roles: ['admin'] },
        { name: t('nav.users'), href: '/users', icon: Users, roles: ['admin'] },
        { name: t('nav.aiConfig'), href: '/ai-config', icon: Bot, roles: ['admin'] },
        { name: t('nav.settings'), href: '/settings', icon: Settings, roles: ['admin'] },
    ]

    const filterByRole = (items: NavItem[]) => {
        return items.filter(item => {
            if (!item.roles) return true
            return item.roles.includes(user?.role || '')
        })
    }

    const isActive = (href: string) => pathname === href

    if (pathname === '/login') {
        return <>{children}</>
    }

    const NavSection = ({ title, items }: { title?: string; items: NavItem[] }) => (
        <div className="space-y-1">
            {title && sidebarOpen && (
                <p className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {title}
                </p>
            )}
            {items.map((item) => {
                const Icon = item.icon
                const active = isActive(item.href)

                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
              ${active
                                ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border border-blue-500/30'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <motion.div
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.95 }}
                            className={`flex-shrink-0 ${active ? 'text-blue-400' : 'text-slate-400 group-hover:text-blue-400'}`}
                        >
                            <Icon className="w-5 h-5" />
                        </motion.div>

                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.span
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    className="flex-1 font-medium whitespace-nowrap"
                                >
                                    {item.name}
                                </motion.span>
                            )}
                        </AnimatePresence>

                        {item.badge !== undefined && item.badge > 0 && sidebarOpen && (
                            <motion.span
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full"
                            >
                                {item.badge}
                            </motion.span>
                        )}
                    </Link>
                )
            })}
        </div>
    )

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            <ToastContainer />

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                        onClick={() => setMobileMenuOpen(false)}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: sidebarOpen ? 280 : 80 }}
                className={`fixed top-0 left-0 h-full bg-slate-900/95 backdrop-blur-xl border-r border-white/5 z-50 flex flex-col
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} transition-transform lg:transition-none`}
            >
                {/* Logo Section */}
                <div className="h-20 flex items-center justify-between px-6 border-b border-white/5">
                    <Link href="/dashboard" className="flex items-center gap-3">
                        <motion.div
                            animate={{ scale: sidebarOpen ? 1 : 0.8 }}
                            className="relative"
                        >
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                        </motion.div>
                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.div
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                >
                                    <span className="text-lg font-bold text-white">Innexar</span>
                                    <span className="text-lg font-light text-slate-400 ml-1">Workspace</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </Link>

                    {/* Collapse Button - Desktop */}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="hidden lg:flex w-8 h-8 items-center justify-center rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        <motion.div animate={{ rotate: sidebarOpen ? 0 : 180 }}>
                            <ChevronLeft className="w-4 h-4 text-slate-400" />
                        </motion.div>
                    </button>

                    {/* Close Button - Mobile */}
                    <button
                        onClick={() => setMobileMenuOpen(false)}
                        className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg bg-white/5 hover:bg-white/10"
                    >
                        <X className="w-4 h-4 text-slate-400" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-6 px-3 overflow-y-auto space-y-6">
                    <NavSection items={mainNavItems} />
                    <NavSection title="Tools" items={filterByRole(toolsNavItems)} />
                    {filterByRole(adminNavItems).length > 0 && (
                        <NavSection title="Administration" items={filterByRole(adminNavItems)} />
                    )}
                </nav>

                {/* User Section */}
                <div className="p-3 border-t border-white/5">
                    {sidebarOpen ? (
                        <div className="flex items-center gap-3 px-4 py-3 mb-2">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                                <span className="text-sm font-bold text-white">
                                    {user?.name?.[0]?.toUpperCase() || 'U'}
                                </span>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">{user?.name}</p>
                                <p className="text-xs text-slate-400 capitalize">{user?.role}</p>
                            </div>
                        </div>
                    ) : null}

                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
                    >
                        <LogOut className="w-5 h-5 flex-shrink-0" />
                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.span
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    className="font-medium"
                                >
                                    Logout
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </button>
                </div>
            </motion.aside>

            {/* Main Content */}
            <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-[280px]' : 'lg:ml-20'}`}>
                {/* Top Header */}
                <header className="sticky top-0 z-30 h-20 bg-slate-900/80 backdrop-blur-xl border-b border-white/5">
                    <div className="h-full px-4 lg:px-8 flex items-center justify-between">
                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(true)}
                            className="lg:hidden w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            <Menu className="w-5 h-5 text-white" />
                        </button>

                        {/* Page Title */}
                        <div className="hidden lg:flex items-center gap-2">
                            <h1 className="text-xl font-bold text-white">
                                {/* Dynamic based on pathname */}
                                {pathname === '/dashboard' && 'Dashboard'}
                                {pathname === '/contacts' && 'Contacts'}
                                {pathname === '/opportunities' && 'Opportunities'}
                                {pathname === '/projects' && 'Projects'}
                                {pathname === '/activities' && 'Activities'}
                                {pathname === '/site-orders' && 'Site Orders'}
                                {pathname === '/analytics' && 'Analytics'}
                                {pathname === '/settings' && 'Settings'}
                            </h1>
                        </div>

                        {/* Right Actions */}
                        <div className="flex items-center gap-3">
                            {/* Notifications */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="relative w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                            >
                                <Bell className="w-5 h-5 text-slate-400" />
                            </motion.button>

                            {/* User Avatar - Mobile */}
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="lg:hidden w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center cursor-pointer"
                            >
                                <span className="text-sm font-bold text-white">
                                    {user?.name?.[0]?.toUpperCase() || 'U'}
                                </span>
                            </motion.div>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <main className="p-4 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    )
}
