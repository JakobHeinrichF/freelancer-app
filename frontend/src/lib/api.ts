const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface RoleProfile {
  title: string
  layer: string
  mission: string
  key_responsibilities: string[]
  must_haves: string[]
  why_german: string
}

export interface KRResult {
  kr: string
  status: 'belegt' | 'implizit' | 'fehlt'
  evidence: string
}

export interface ProfileResult {
  platform: string
  url: string
  name_or_title: string
  kr_results: KRResult[]
  kr_score: number
  kr_pass: boolean
  deutsch_native: boolean | null
  deutsch_evidence: string
  overall_match: number
  recommendation: 'empfohlen' | 'bedingt' | 'abgelehnt'
  missing: string[]
  short_summary: string
  availability: string
  skills: string[]
}

export interface SearchStatus {
  job_id: string
  status: 'queued' | 'searching' | 'evaluating' | 'done' | 'error'
  keywords: string[]
  total_found: number
  results?: ProfileResult[]
  error?: string
}

export async function startSearch(role: RoleProfile, maxPerPlatform = 6): Promise<string> {
  const r = await fetch(`${API}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role_profile: role, max_per_platform: maxPerPlatform }),
  })
  if (!r.ok) throw new Error(await r.text())
  const d = await r.json()
  return d.job_id
}

export async function pollSearch(jobId: string): Promise<SearchStatus> {
  const r = await fetch(`${API}/search/${jobId}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function downloadDocx(jobId: string, profileIndex: number): Promise<void> {
  const r = await fetch(`${API}/generate-docx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, profile_index: profileIndex }),
  })
  if (!r.ok) throw new Error(await r.text())
  const blob = await r.blob()
  const cd = r.headers.get('Content-Disposition') || ''
  const match = cd.match(/filename="([^"]+)"/)
  const filename = match ? match[1] : 'GS_Profile.docx'
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
