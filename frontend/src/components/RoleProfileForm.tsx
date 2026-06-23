'use client'
import { useState } from 'react'
import type { RoleProfile } from '@/lib/api'

interface Props {
  onSubmit: (role: RoleProfile) => void
  loading: boolean
}

const DEFAULT: RoleProfile = {
  title: 'Change & Adoption Lead (OCM)',
  layer: 'Shell · German native, C2 · Onshore',
  mission: 'Own internal adoption across ~3,000 users via a champion/multiplier network.',
  key_responsibilities: [
    'Build and run the change-champion network (sourced from power users); manage multiplier enablement',
    'Manage the "lost feature" expectation and resistance handling in German enterprise environment',
    'Own adoption telemetry and the feedback loop; define and track adoption KPIs',
    'Coordinate with HR on role change and Betriebsrat / works council integration',
  ],
  must_haves: [
    'Large-scale enterprise change in regulated/unionized German environments',
    'Champion/multiplier network model experience',
    'Prosci or equivalent certification (ADKAR methodology)',
    'Experience with Betriebsrat and German labor relations',
    'German native or C2 language level',
  ],
  why_german: 'All internal change comms, champion enablement, and resistance handling are in German.',
}

export default function RoleProfileForm({ onSubmit, loading }: Props) {
  const [role, setRole] = useState<RoleProfile>(DEFAULT)
  const [krInput, setKrInput] = useState(role.key_responsibilities.join('\n'))
  const [mhInput, setMhInput] = useState(role.must_haves.join('\n'))

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const finalRole = {
      ...role,
      key_responsibilities: krInput.split('\n').map(s => s.trim()).filter(Boolean),
      must_haves: mhInput.split('\n').map(s => s.trim()).filter(Boolean),
    }
    onSubmit(finalRole)
  }

  const inp = "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gs-accent"
  const lbl = "block text-xs font-medium text-gray-500 mb-1"

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Rollentitel</label>
          <input className={inp} value={role.title}
            onChange={e => setRole({ ...role, title: e.target.value })} required />
        </div>
        <div>
          <label className={lbl}>Layer / Sprache / Shore</label>
          <input className={inp} value={role.layer}
            onChange={e => setRole({ ...role, layer: e.target.value })} />
        </div>
      </div>

      <div>
        <label className={lbl}>Mission</label>
        <textarea className={inp} rows={2} value={role.mission}
          onChange={e => setRole({ ...role, mission: e.target.value })} />
      </div>

      <div>
        <label className={lbl}>
          Key Responsibilities <span className="text-gray-400">(eine pro Zeile – Prio 1 für Matching)</span>
        </label>
        <textarea className={inp} rows={5} value={krInput}
          onChange={e => setKrInput(e.target.value)} required />
      </div>

      <div>
        <label className={lbl}>
          Must-Haves <span className="text-gray-400">(eine pro Zeile)</span>
        </label>
        <textarea className={inp} rows={4} value={mhInput}
          onChange={e => setMhInput(e.target.value)} />
      </div>

      <div>
        <label className={lbl}>Warum Deutsch?</label>
        <input className={inp} value={role.why_german}
          onChange={e => setRole({ ...role, why_german: e.target.value })} />
      </div>

      <button type="submit" disabled={loading}
        className="w-full bg-gs-blue text-white py-3 rounded-lg font-medium text-sm hover:bg-gs-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
        {loading ? 'Suche läuft…' : '🔍 Freelancer suchen'}
      </button>
    </form>
  )
}
