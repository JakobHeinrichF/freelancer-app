'use client'
import { useState, useEffect, useRef } from 'react'
import RoleProfileForm from '@/components/RoleProfileForm'
import ProfileCard from '@/components/ProfileCard'
import SearchStatus from '@/components/SearchStatus'
import { startSearch, pollSearch, downloadDocx } from '@/lib/api'
import type { RoleProfile, ProfileResult, SearchStatus as SearchStatusType } from '@/lib/api'

type AppState = 'idle' | 'running' | 'done' | 'error'

export default function Home() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [searchStatus, setSearchStatus] = useState<SearchStatusType | null>(null)
  const [results, setResults] = useState<ProfileResult[]>([])
  const [downloading, setDownloading] = useState<number | null>(null)
  const [error, setError] = useState<string>('')
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // Polling
  useEffect(() => {
    if (!jobId || appState !== 'running') return

    const poll = async () => {
      try {
        const status = await pollSearch(jobId)
        setSearchStatus(status)

        if (status.status === 'done') {
          setResults(status.results ?? [])
          setAppState('done')
          if (pollRef.current) clearInterval(pollRef.current)
        } else if (status.status === 'error') {
          setError(status.error ?? 'Unbekannter Fehler')
          setAppState('error')
          if (pollRef.current) clearInterval(pollRef.current)
        }
      } catch (e: any) {
        setError(e.message)
        setAppState('error')
        if (pollRef.current) clearInterval(pollRef.current)
      }
    }

    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [jobId, appState])

  async function handleSearch(role: RoleProfile) {
    setAppState('running')
    setResults([])
    setError('')
    setSearchStatus(null)
    try {
      const id = await startSearch(role, 6)
      setJobId(id)
    } catch (e: any) {
      setError(e.message)
      setAppState('error')
    }
  }

  async function handleApprove(index: number) {
    if (!jobId) return
    setDownloading(index)
    try {
      await downloadDocx(jobId, index)
    } catch (e: any) {
      alert(`Fehler beim Generieren: ${e.message}`)
    } finally {
      setDownloading(null)
    }
  }

  function handleReset() {
    setAppState('idle')
    setJobId(null)
    setSearchStatus(null)
    setResults([])
    setError('')
  }

  // Filter: empfohlen zuerst, dann bedingt
  const passed = results.filter(r => r.kr_pass && r.deutsch_native !== false)
  const rejected = results.filter(r => !r.kr_pass || r.deutsch_native === false)

  return (
    <div className="space-y-6">
      {/* Intro */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gs-blue mb-1">Freelancer-Suche & Profilierung</h2>
        <p className="text-sm text-gray-500">
          Rollenprofil eingeben → automatische Suche auf gulp.de & freelancermap.de →
          KI-Bewertung nach Key Responsibilities + Deutsch → OK geben → .docx im Grashoff-Template
        </p>
      </div>

      {/* Form */}
      {appState === 'idle' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Rollenprofil</h3>
          <RoleProfileForm onSubmit={handleSearch} loading={false} />
        </div>
      )}

      {/* Status */}
      {appState === 'running' && searchStatus && (
        <SearchStatus
          status={searchStatus.status}
          keywords={searchStatus.keywords}
          totalFound={searchStatus.total_found}
        />
      )}

      {/* Error */}
      {appState === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5">
          <p className="text-sm font-medium text-red-700 mb-1">Fehler</p>
          <p className="text-sm text-red-600">{error}</p>
          <button onClick={handleReset} className="mt-3 text-sm text-red-700 underline">
            Neu starten
          </button>
        </div>
      )}

      {/* Results */}
      {appState === 'done' && (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="flex items-center justify-between bg-white rounded-xl border border-gray-200 px-5 py-4">
            <div className="flex gap-4 text-sm">
              <span className="text-green-700 font-medium">{passed.length} passen</span>
              <span className="text-gray-400">·</span>
              <span className="text-red-500">{rejected.length} aussortiert</span>
              <span className="text-gray-400">·</span>
              <span className="text-gray-500">{results.length} gesamt</span>
            </div>
            <button onClick={handleReset}
              className="text-xs text-gray-400 hover:text-gray-600 border border-gray-200 rounded px-3 py-1">
              Neue Suche
            </button>
          </div>

          {/* Passing profiles */}
          {passed.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                ✓ Kandidaten — KR bestanden, Deutsch ✓
              </h3>
              <div className="space-y-4">
                {passed.map((p, i) => (
                  <ProfileCard
                    key={i}
                    profile={p}
                    index={results.indexOf(p)}
                    onApprove={handleApprove}
                    downloading={downloading === results.indexOf(p)}
                  />
                ))}
              </div>
            </div>
          )}

          {passed.length === 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-sm text-yellow-700">
              Kein Profil hat KR + Deutsch gleichzeitig bestanden. Überprüfe die Suchbegriffe oder
              erweitere die Kriterien.
            </div>
          )}

          {/* Rejected summary */}
          {rejected.length > 0 && (
            <details className="bg-white rounded-xl border border-gray-200 p-4">
              <summary className="text-sm text-gray-500 cursor-pointer select-none">
                {rejected.length} aussortierte Profile anzeigen
              </summary>
              <div className="mt-4 space-y-3">
                {rejected.map((p, i) => (
                  <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                      {p.platform}
                    </span>
                    <span className="text-sm text-gray-600 flex-1 truncate">{p.name_or_title}</span>
                    <span className="text-xs text-red-500">
                      {!p.kr_pass ? 'KR fehlen' : 'Deutsch fehlt'}
                    </span>
                    <a href={p.url} target="_blank" rel="noreferrer"
                      className="text-xs text-blue-500 hover:underline flex-shrink-0">
                      Profil →
                    </a>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  )
}
