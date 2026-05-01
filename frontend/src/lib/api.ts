const BASE = '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? res.statusText)
  }
  return res.json()
}

// ---------- auth ----------

export async function register(email: string, password: string) {
  return request<{ id: number; email: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password })
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? 'Login failed')
  }
  const data: { access_token: string; token_type: string } = await res.json()
  localStorage.setItem('token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('token')
}

// ---------- agent ----------

export interface ChatResponse {
  answer: string
  token_usage: {
    cheap_in: number
    cheap_out: number
    strong_in: number
    strong_out: number
    total_in: number
    total_out: number
  }
}

export async function chat(message: string): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

// ---------- user / settings ----------

export interface Me {
  id: number
  email: string
  webhook_url: string | null
}

export async function getMe(): Promise<Me> {
  return request<Me>('/auth/me')
}

export async function updateWebhook(webhook_url: string | null): Promise<Me> {
  return request<Me>('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify({ webhook_url }),
  })
}

// ---------- history ----------

export interface ToolCallRecord {
  tool_name: string
  input_args: Record<string, unknown>
  output: string | null
  called_at: string
}

export interface RunRecord {
  id: number
  question: string
  answer: string | null
  tokens_cheap_in: number
  tokens_cheap_out: number
  tokens_strong_in: number
  tokens_strong_out: number
  created_at: string
  tool_calls: ToolCallRecord[]
}

export async function getHistory(): Promise<RunRecord[]> {
  return request<RunRecord[]>('/history')
}
