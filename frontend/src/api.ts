const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
import type { ClassLevel, ReferenceEntry, Subject } from './curriculum'

export type ApiUser = {
  id: string
  email: string
  name: string
  target_exam: string
  target_date: string | null
  created_at: string
}

export type AuthResult = {
  token: string
  user: ApiUser
  dashboard: {
    stats: { questions_solved: number; study_minutes: number; accuracy: number; streak: number }
  }
}

async function request(path: string, init: RequestInit = {}) {
  try {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 2500)
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(init.headers || {}) },
    })
    window.clearTimeout(timeout)
    return response
  } catch (error) {
    if (error instanceof TypeError || (error instanceof DOMException && error.name === 'AbortError')) return null
    throw error
  }
}

export async function authenticate(email: string, password: string): Promise<AuthResult | null> {
  const body = JSON.stringify({ email, password })
  const login = await request('/api/auth/login', { method: 'POST', body })
  if (!login) return null
  if (login.ok) return login.json() as Promise<AuthResult>
  if (login.status !== 401) throw new Error((await login.json()).detail || 'Unable to log in.')

  const signup = await request('/api/auth/signup', { method: 'POST', body })
  if (!signup) return null
  if (!signup.ok) throw new Error((await signup.json()).detail || 'Unable to create this account.')
  return signup.json() as Promise<AuthResult>
}

export async function loadContentReferences(classLevel: ClassLevel, subject: 'All' | Subject, query = ''): Promise<ReferenceEntry[] | null> {
  const params = new URLSearchParams({ class_level: classLevel, subject })
  if (query.trim()) params.set('query', query.trim())
  const response = await request(`/api/content/references?${params.toString()}`)
  if (!response?.ok) return null
  const payload = await response.json() as { references?: ReferenceEntry[] }
  return payload.references ?? null
}

export async function searchContent(query: string): Promise<ReferenceEntry[] | null> {
  return loadContentReferences('Mixed', 'All', query)
}

export async function updateProfile(token: string, values: { name?: string; target_exam?: string; target_date?: string }) {
  return authedJson('/api/profile', token, { method: 'PATCH', body: JSON.stringify(values) })
}

export type RemoteExamQuestion = { id: string; subject: Subject; chapter: string; text: string; options: string[]; source?: string; is_repeat?: boolean }
export type RemoteTestSession = { id: string; status: string; questions: RemoteExamQuestion[]; answers: Record<string, number>; marked: number[]; expires_at: string; score?: number; correct?: number; incorrect?: number; unanswered?: number }
export type TestAttempt = { id: string; test_id: string; config: { exam?: 'NEET-UG' | 'CBSE Boards'; subject?: Subject | 'Mixed'; class_level?: ClassLevel; chapter?: string; questions?: number; duration_minutes?: number; difficulty?: string }; score: number; correct: number; incorrect: number; unanswered: number; duration_seconds: number; created_at: string }

export async function createRemoteTestSession(token: string, config?: { exam?: 'NEET-UG' | 'CBSE Boards'; subject?: Subject | 'Mixed'; classLevel?: ClassLevel; chapter?: string; questions?: number; durationMinutes?: number; difficulty?: 'Easy' | 'Medium' | 'Hard' | 'Mixed' }): Promise<RemoteTestSession | null> {
  const response = await request('/api/tests/sessions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      exam: config?.exam ?? 'NEET-UG',
      subject: config?.subject ?? 'Mixed',
      class_level: config?.classLevel ?? 'Mixed',
      chapter: config?.chapter ?? 'Full syllabus',
      questions: config?.questions ?? 20,
      duration_minutes: config?.durationMinutes ?? 25,
      difficulty: config?.difficulty ?? 'Mixed',
      negative_marking: (config?.exam ?? 'NEET-UG') === 'NEET-UG',
    }),
  })
  if (!response?.ok) return null
  const payload = await response.json() as { session: RemoteTestSession }
  return payload.session
}

export async function saveRemoteAnswer(token: string, sessionId: string, questionIndex: number, option: number, marked: boolean) {
  await request(`/api/tests/sessions/${sessionId}/answer`, { method: 'PATCH', headers: { Authorization: `Bearer ${token}` }, body: JSON.stringify({ question_index: questionIndex, option, marked }) })
}

export async function submitRemoteTestSession(token: string, sessionId: string): Promise<RemoteTestSession | null> {
  const response = await request(`/api/tests/sessions/${sessionId}/submit`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
  if (!response?.ok) return null
  const payload = await response.json() as { session: RemoteTestSession }
  return payload.session
}

export async function loadTestAttempts(token: string): Promise<TestAttempt[] | null> {
  const payload = await authedJson('/api/test-attempts', token)
  return payload?.attempts ?? null
}

export type StudyItemDetails = {
  questionText: string
  options: string[]
  selectedAnswer: number | null
  correctAnswer: number
  explanation: string
}
export type StudyItem = { id: string; kind: 'queue' | 'planner' | 'mistake'; subject: Subject; class_level: ClassLevel; chapter: string; title: string; reason: string; priority: 'High' | 'Medium' | 'Low'; duration_minutes: number; status: 'open' | 'completed'; due_date: string | null; details?: StudyItemDetails | null }
export type AnalyticsSnapshot = { attempt_count: number; average_score: number; best_score: number; recent_scores: number[]; open_items: number; subject_accuracy: Record<string, number>; recommendation: string }

async function authedJson(path: string, token: string, init: RequestInit = {}) {
  const response = await request(path, { ...init, headers: { Authorization: `Bearer ${token}`, ...(init.headers || {}) } })
  if (!response?.ok) return null
  return response.json()
}

export async function loadStudyItems(token: string, kind?: StudyItem['kind']): Promise<StudyItem[] | null> {
  const query = kind ? `?kind=${kind}` : ''
  const payload = await authedJson(`/api/study/items${query}`, token)
  return payload?.items ?? null
}

export async function createStudyItem(token: string, item: Pick<StudyItem, 'kind' | 'subject' | 'class_level' | 'chapter' | 'title' | 'reason' | 'priority' | 'duration_minutes'>) {
  return authedJson('/api/study/items', token, { method: 'POST', body: JSON.stringify(item) })
}

export async function completeStudyItem(token: string, id: string) {
  return authedJson(`/api/study/items/${id}/complete`, token, { method: 'POST' })
}

export async function loadAnalytics(token: string): Promise<AnalyticsSnapshot | null> {
  return authedJson('/api/analytics', token)
}

export async function askTutor(token: string, prompt: string, mode: 'Explain simply' | 'Step-by-step' | 'Quiz me' | 'Revision plan', subject?: Subject, chapter?: string): Promise<{ reply: string } | null> {
  return authedJson('/api/tutor/respond', token, { method: 'POST', body: JSON.stringify({ prompt, mode, subject, chapter }) })
}

export async function analyzePhoto(token: string, file: File, questionText: string): Promise<{ status: string; reply: string; notice: string; source?: { content?: string; note?: string } } | null> {
  const form = new FormData()
  form.append('image', file)
  form.append('question_text', questionText)
  return authedJson('/api/photo/analyze', token, { method: 'POST', body: form })
}
