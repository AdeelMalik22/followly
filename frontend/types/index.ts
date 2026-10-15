// Central TypeScript types matching the FastAPI backend schemas

export type LeadStatus =
  | "new"
  | "contacted"
  | "qualified"
  | "booked"
  | "cold"
  | "recovered"
  | "not_interested";

export type ConversationStatus =
  | "active"
  | "cold"
  | "human_takeover"
  | "closed";

export interface UserMe {
  id: number;
  email: string;
  name: string;
  role: string;
  business_id: number;
  business_name: string;
  industry: string;
  knowledge_base_count: number;
  onboarding_completed: boolean;
}

export interface Lead {
  id: number;
  business_id: number;
  phone: string | null;
  name: string | null;
  email: string | null;
  status: LeadStatus;
  source: string | null;
  created_at: string;
  last_contact_at: string | null;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ConversationListItem {
  id: number;
  business_id: number;
  lead_id: number;
  channel: string;
  status: ConversationStatus;
  last_message_at: string | null;
  created_at: string;
  lead: Lead | null;
  last_message: Message | null;
}

export interface ConversationDetail {
  id: number;
  business_id: number;
  lead_id: number;
  channel: string;
  status: ConversationStatus;
  last_message_at: string | null;
  created_at: string;
  lead: Lead | null;
}

export interface Appointment {
  id: number;
  business_id: number;
  lead_id: number;
  calendar_event_id: string | null;
  start_time: string;
  end_time: string;
  service: string | null;
  status: string;
  created_at: string;
  lead: Lead | null;
}

export interface KnowledgeEntry {
  id: number;
  business_id: number;
  category: string;
  question: string | null;
  answer: string;
  extra_data: Record<string, unknown>;
  created_at: string;
}

export interface FollowUpRule {
  id: number;
  business_id: number;
  trigger_condition: string;
  delay_hours: number;
  message_template: string;
  active: number;
  created_at: string;
}

export interface FunnelSummary {
  total_leads: number;
  contacted: number;
  qualified: number;
  booked: number;
  recovered: number;
  not_interested: number;
  cold: number;
}

export interface DailyLeadCount {
  date: string;
  count: number;
}

export interface AnalyticsSummary {
  funnel: FunnelSummary;
  leads_over_time: DailyLeadCount[];
}

export interface BillingStatus {
  plan: string;
  status: string;
  customer_id: string | null;
  subscription_id: string | null;
  limits: Record<string, number>;
  usage: Record<string, number>;
  usage_period_start: string | null;
  usage_period_end: string | null;
}

export interface ConfigurationAudit {
  id: number;
  business_id: number;
  changed_by: number | null;
  configuration: Record<string, unknown>;
  created_at: string;
}
