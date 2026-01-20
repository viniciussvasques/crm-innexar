export interface User {
  id: number
  email: string
  name: string
  role: 'admin' | 'vendedor' | 'planejamento' | 'dev'
  is_active: boolean
}

export interface DashboardData {
  total_opportunities: number
  total_value: number
  pipeline: {
    stage: string
    count: number
    value: number
  }[]
  recent_opportunities: Opportunity[]
  pending_activities: Activity[]
}

export interface Contact {
  id: number
  name: string
  email: string
  phone: string
  company: string
  status: string
  notes: string
  project_type?: string | null
  budget_range?: string | null
  timeline?: string | null
  website?: string | null
  linkedin?: string | null
  position?: string | null
  industry?: string | null
  company_size?: string | null
  source?: string | null
  contact_metadata?: string | null
  owner_id: number
  created_at: string
  updated_at: string
}

export interface Opportunity {
  id: number
  name: string
  contact_id: number
  value: number
  stage: string
  probability: number
  expected_close_date: string
  owner_id: number
  created_at: string
  updated_at: string
  contact_name?: string
}

export interface Activity {
  id: number
  type: string
  subject: string
  description: string
  due_date: string
  due_time: string
  status: string
  contact_id: number
  opportunity_id: number
  project_id: number | null
  owner_id: number
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  name: string
  description: string | null
  contact_id: number
  opportunity_id: number | null
  project_type: 'marketing_site' | 'saas_platform' | 'enterprise_software' | 'custom_development' | 'consulting' | 'other'
  status: 'lead' | 'qualificacao' | 'proposta' | 'aprovado' | 'em_planejamento' | 'planejamento_concluido' | 'em_desenvolvimento' | 'em_revisao' | 'concluido' | 'cancelado'
  owner_id: number
  planning_owner_id: number | null
  dev_owner_id: number | null
  estimated_value: string | null
  approved_value: string | null
  start_date: string | null
  expected_delivery_date: string | null
  actual_delivery_date: string | null
  technical_requirements: string | null
  tech_stack: string | null
  repository_url: string | null
  deployment_url: string | null
  internal_notes: string | null
  planning_notes: string | null
  dev_notes: string | null
  client_notes: string | null
  created_at: string
  updated_at: string
  sent_to_planning_at: string | null
  sent_to_dev_at: string | null
  contact_name?: string
  owner_name?: string
  planning_owner_name?: string | null
  dev_owner_name?: string | null
}

export interface LeadAnalysis {
  id: number
  contact_id: number
  company_info: string | null
  market_analysis: string | null
  financial_insights: string | null
  recommendations: string | null
  risk_assessment: string | null
  opportunity_score: number | null
  analysis_metadata: Record<string, any> | null
  analysis_status: 'pending' | 'completed' | 'error'
  created_at: string
  analyzed_at: string | null
}

export type Language = 'pt' | 'en' | 'es'
