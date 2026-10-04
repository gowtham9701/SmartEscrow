export type Role = 'contributor' | 'client';

export interface Service {
  title: string;
  rate: number;
}

export interface Experience {
  company: string;
  role: string;
  period: string;
  summary: string;
}

export interface PortfolioItem {
  title: string;
  url?: string;
  summary?: string;
}

export interface User {
  id: string;
  email: string;
  username?: string;
  phone?: string;
  full_name: string;
  role: Role;
  active_mode?: 'freelancer' | 'employer';
  is_freelancer?: number;
  is_employer?: number;
  firm_verified?: number;
  firm_reg_number?: string;
  firm_work_email?: string;
  resume_text?: string;
  resume_url?: string;
  resume_filename?: string;
  headline?: string;
  bio?: string;
  location?: string;
  skills?: string[];
  services?: Service[];
  rating?: number;
  avatar_hue?: number;
  // contributor
  title?: string;
  hourly_rate_usd?: number;
  years_experience?: number;
  availability?: string;
  experiences?: Experience[];
  achievements?: string[];
  portfolio?: PortfolioItem[];
  languages?: string[];
  completed_jobs?: number;
  github_username?: string;
  // client
  company_name?: string;
  company_size?: string;
  industry?: string;
  website?: string;
  jobs_posted?: number;
  // ranking (populated by recommendation endpoints)
  match_score?: number;
}

export interface JobAI {
  summary: string;
  key_points: string[];
  recommended_skills: string[];
  suggested_seniority: string;
  reading_time_sec: number;
  recommendation: string;
}

export interface Job {
  id: string;
  client_id: string;
  company_name: string;
  title: string;
  category: string;
  description: string;
  skills_required: string[];
  engagement_type: string;
  hourly_rate_min: number;
  hourly_rate_max: number;
  experience_level: string;
  location: string;
  hours_per_week: number;
  duration: string;
  status: string;
  created_at: string;
  ai: JobAI;
  applicant_count?: number;
  match_score?: number;
  recommended_talent?: User[];
}

export interface Application {
  id: string;
  job_id: string;
  contributor_id: string;
  proposed_hourly_rate: number;
  status: string;
  cover_letter: string;
  created_at: string;
  job?: Job;
  contributor?: User;
}

export interface Engagement {
  id: string;
  job_id: string;
  client_id: string;
  contributor_id: string;
  title: string;
  hourly_rate: number;
  hours_logged: number;
  status: string;
  started_at: string;
  timesheets: { week: string; hours: number; note: string }[];
  client?: User;
  contributor?: User;
  total_billed?: number;
  escrow_held?: number;
}

export interface Payment {
  id: string;
  engagement_id: string;
  client_id: string;
  contributor_id: string;
  amount_usd: number;
  type: string;
  status: string;
  hours: number;
  note: string;
  created_at: string;
  engagement_title?: string;
  contributor_name?: string;
  client_name?: string;
}

export interface PlatformStats {
  open_jobs: number;
  contributors: number;
  clients: number;
  active_engagements: number;
  total_paid_out: number;
  in_escrow: number;
}

export interface Wallet {
  id: string;
  user_id: string;
  available_balance: number;
  blocked_balance: number;
  currency: string;
  created_at: string;
}

export interface WalletTransaction {
  id: string;
  type: string;
  amount: number;
  available_after: number;
  blocked_after: number;
  ref: string;
  note: string;
  created_at: string;
}

export interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  holder_name: string;
  is_default: number;
}

export interface WalletSummary {
  wallet: Wallet;
  transactions: WalletTransaction[];
  payment_methods: PaymentMethod[];
}

export interface ResumeMatch {
  id: string;
  title: string;
  company_name: string;
  hourly_rate_min: number;
  hourly_rate_max: number;
  category: string;
  match_score: number;
  missing_skills: string[];
}

export interface ResumeAnalysis {
  extracted_skills: string[];
  all_skills: string[];
  summary: string;
  seniority: string;
  years_experience: number | null;
  keywords: string[];
  top_matches: ResumeMatch[];
  recommended_skills: string[];
  has_resume?: boolean;
}

export interface AuditEvent {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  detail: Record<string, unknown>;
  created_at: string;
}
