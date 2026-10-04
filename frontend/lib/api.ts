import type {
  Application,
  AuditEvent,
  Engagement,
  Job,
  JobAI,
  Payment,
  PlatformStats,
  ResumeAnalysis,
  User,
  Wallet,
  WalletSummary,
} from './types';

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const PREFIX = '/api/v1/market';
const TOKEN_KEY = 'smartescrow_token';
const USER_KEY = 'smartescrow_user';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${PREFIX}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // auth
  register: (payload: Record<string, unknown>) =>
    request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  registerStart: (payload: Record<string, unknown>) =>
    request<{ registration_id: string; email: string; phone: string; delivery: string; demo_email_otp?: string }>(
      '/auth/register/start',
      { method: 'POST', body: JSON.stringify(payload) },
    ),
  registerVerify: (registration_id: string, email_otp: string) =>
    request<{ access_token: string; user: User }>('/auth/register/verify', {
      method: 'POST',
      body: JSON.stringify({ registration_id, email_otp }),
    }),
  registerResend: (registration_id: string) =>
    request<{ registration_id: string; delivery: string; demo_email_otp?: string }>('/auth/register/resend', {
      method: 'POST',
      body: JSON.stringify({ registration_id }),
    }),
  login: (identifier: string, password: string) =>
    request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ identifier, password }),
    }),
  me: () => request<User>('/auth/me'),
  demoUsers: () =>
    request<{ contributor: { email: string; password: string }; client: { email: string; password: string } }>(
      '/auth/demo-users',
    ),

  // profile
  updateProfile: (payload: Record<string, unknown>) =>
    request<User>('/profile', { method: 'PATCH', body: JSON.stringify(payload) }),
  switchMode: (mode: 'freelancer' | 'employer') =>
    request<{ needs_firm: boolean; user: User }>('/profile/switch-mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  registerFirm: (payload: Record<string, unknown>) =>
    request<User>('/profile/register-firm', { method: 'POST', body: JSON.stringify(payload) }),
  resumeText: (text: string, filename?: string) =>
    request<{ user: User; analysis: ResumeAnalysis }>('/profile/resume-text', {
      method: 'POST',
      body: JSON.stringify({ text, filename }),
    }),
  resumeUpload: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const token = getToken();
    const res = await fetch(`${API_BASE}${PREFIX}/profile/resume-upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    });
    if (!res.ok) {
      let detail = `Upload failed (${res.status})`;
      try {
        detail = (await res.json()).detail || detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    return res.json() as Promise<{ user: User; analysis: ResumeAnalysis }>;
  },
  resumeInsights: () => request<ResumeAnalysis>('/ai/resume-insights'),

  // jobs
  listJobs: (params: { search?: string; category?: string; skill?: string } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v) as [string, string][],
    ).toString();
    return request<{ jobs: Job[] }>(`/jobs${qs ? `?${qs}` : ''}`);
  },
  getJob: (id: string) => request<Job>(`/jobs/${id}`),
  createJob: (payload: Record<string, unknown>) =>
    request<Job>('/jobs', { method: 'POST', body: JSON.stringify(payload) }),

  // talent
  listTalent: (params: { search?: string; skill?: string } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v) as [string, string][],
    ).toString();
    return request<{ talent: User[] }>(`/talent${qs ? `?${qs}` : ''}`);
  },
  getTalent: (id: string) => request<User>(`/talent/${id}`),

  // applications
  apply: (jobId: string, payload: { proposed_hourly_rate: number; cover_letter: string }) =>
    request<Application>(`/jobs/${jobId}/apply`, { method: 'POST', body: JSON.stringify(payload) }),
  myApplications: () => request<{ applications: Application[] }>('/applications'),
  setApplicationStatus: (id: string, status: string) =>
    request<Application>(`/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  // engagements
  myEngagements: () => request<{ engagements: Engagement[] }>('/engagements'),
  logHours: (id: string, hours: number, note: string) =>
    request<Engagement>(`/engagements/${id}/log-hours`, {
      method: 'POST',
      body: JSON.stringify({ hours, note }),
    }),

  // payments
  myPayments: () => request<{ payments: Payment[] }>('/payments'),
  releasePayment: (id: string) =>
    request<Payment>(`/payments/${id}/release`, { method: 'POST' }),

  // ai + stats
  summarize: (title: string, text: string) =>
    request<JobAI>('/ai/summarize', { method: 'POST', body: JSON.stringify({ title, text }) }),
  recommendJobs: () => request<{ jobs: Job[] }>('/ai/recommend-jobs'),
  stats: () => request<PlatformStats>('/stats'),

  // wallet + gateway
  wallet: () => request<WalletSummary>('/wallet'),
  deposit: (payload: {
    amount: number;
    card_number: string;
    exp_month: number;
    exp_year: number;
    cvv: string;
    pin: string;
    holder_name: string;
    save_card?: boolean;
  }) => request<{ success: boolean; status: string; gateway_ref: string; brand: string; last4: string; amount: number; wallet: Wallet }>(
    '/wallet/deposit',
    { method: 'POST', body: JSON.stringify(payload) },
  ),
  withdraw: (amount: number) =>
    request<{ success: boolean; wallet: Wallet }>('/wallet/withdraw', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    }),
  fundEscrow: (engagementId: string, hours: number) =>
    request<Engagement>(`/engagements/${engagementId}/fund-escrow`, {
      method: 'POST',
      body: JSON.stringify({ hours }),
    }),
  audit: () => request<{ events: AuditEvent[] }>('/audit'),
  dashboard: () =>
    request<{
      user: User;
      stats: PlatformStats;
      engagements: Engagement[];
      payments: Payment[];
      applications: Application[];
      recommended_jobs?: Job[];
      jobs?: Job[];
    }>('/dashboard'),
};

export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${Math.max(mins, 1)}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
