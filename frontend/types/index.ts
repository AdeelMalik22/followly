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
