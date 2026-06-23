'use client'
import type { ProfileResult } from '@/lib/api'

interface Props {
  profile: ProfileResult
  index: number
  onApprove: (index: number) => void
  downloading: boolean
}

const STATUS_COLORS = {
  belegt: 'bg-green-100 text-green-800',
  implizit: 'bg-yellow-100 text-yellow-700',
  fehlt: 'bg-red-100 text-red-700',
}

const REC_COLORS = {
  empfohlen: 'border-green-400 bg-green-50',
  bedingt: 'border-yellow-400 bg-yellow-50',
  abgelehnt: 'border-red-300 bg-red-50',
}

const REC_BADGE = {
  empfohlen: 'bg-green-100 text-green-800',
  bedingt: 'bg-yellow-100 text-yellow-800',
  abgelehnt: 'bg-red-100 text-red-800',
}

export default function ProfileCard({ profile, index, onApprove, downloading }: Props) {
  const borderClass = REC_COLORS[profile.recommendation] ?? 'border-gray-200 bg-white'

  return (
    <div className={`rounded-xl border-2 p-5 space-y-4 ${borderClass}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {profile.platform}
            </span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${REC_BADGE[profile.recommendation]}`}>
              {profile.recommendation}
            </span>
            {profile.deutsch_native === true && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                🇩🇪 Deutsch ✓
              </span>
            )}
            {profile.deutsch_native === false && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                Deutsch ✗
              </span>
            )}
          </div>
          <h3 className="mt-1.5 font-medium text-gray-900 text-sm leading-snug">
            {profile.name_or_title}
          </h3>
          <a href={profile.url} target="_blank" rel="noreferrer"
            className="text-xs text-blue-600 hover:underline truncate block mt-0.5">
            {profile.url}
          </a>
        </div>

        {/* Match Score */}
        <div className="flex-shrink-0 text-right">
          <div className="text-2xl font-semibold text-gs-blue">{profile.overall_match}%</div>
          <div className="text-xs text-gray-400">Match</div>
        </div>
      </div>

      {/* Short Summary */}
      {profile.short_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{profile.short_summary}</p>
      )}

      {/* KR Tabelle */}
      {profile.kr_results.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">Key Responsibilities</p>
          <div className="space-y-1.5">
            {profile.kr_results.map((kr, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`flex-shrink-0 px-1.5 py-0.5 rounded font-medium ${STATUS_COLORS[kr.status]}`}>
                  {kr.status === 'belegt' ? '✓' : kr.status === 'implizit' ? '~' : '✗'}
                </span>
                <div className="min-w-0">
                  <span className="font-medium text-gray-700">{kr.kr}</span>
                  {kr.evidence && kr.evidence !== 'Nicht gefunden' && (
                    <span className="text-gray-400 ml-1">— {kr.evidence.slice(0, 80)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing */}
      {profile.missing.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-400 mb-1">Fehlend / unklar</p>
          <div className="flex flex-wrap gap-1">
            {profile.missing.map((m, i) => (
              <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Skills */}
      {profile.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {profile.skills.slice(0, 8).map((s, i) => (
            <span key={i} className="text-xs px-2 py-0.5 bg-white border border-gray-200 text-gray-600 rounded">
              {s}
            </span>
          ))}
        </div>
      )}

      {/* Approve Button */}
      {profile.recommendation !== 'abgelehnt' && (
        <button
          onClick={() => onApprove(index)}
          disabled={downloading}
          className="w-full py-2 rounded-lg text-sm font-medium bg-gs-blue text-white hover:bg-gs-accent transition-colors disabled:opacity-50"
        >
          {downloading ? 'Dokument wird erstellt…' : '✓ OK – Profil als .docx exportieren'}
        </button>
      )}
    </div>
  )
}
