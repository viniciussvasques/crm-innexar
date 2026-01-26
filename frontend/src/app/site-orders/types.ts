import { ComponentType } from 'react'

export interface SiteOrder {
    id: number
    customer_name: string
    customer_email: string
    customer_phone?: string
    status: 'pending_payment' | 'paid' | 'onboarding_pending' | 'building' | 'generating' | 'review' | 'delivered' | 'cancelled'
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
    deliverables?: SiteDeliverable[]
}

export interface SiteDeliverable {
    id: number
    type: 'briefing' | 'sitemap' | 'content_plan' | 'wireframe' | 'code'
    title: string
    content?: string
    status: 'pending' | 'generating' | 'ready' | 'approved' | 'rejected'
    created_at: string
}

export interface SiteOnboarding {
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

export interface SiteOrderAddon {
    id: number
    addon_id: number
    price_paid: number
    addon?: { name: string; slug: string }
}

export interface OrderStats {
    status_counts: Record<string, number>
    total_revenue: number
    orders_this_month: number
}

export interface Step {
    id: string
    title: string
    description: string
    status: 'pending' | 'active' | 'completed'
    date?: string
}

export interface StatusConfig {
    label: string
    color: string
    bgColor: string
    borderColor: string
    icon: ComponentType<any>
}
