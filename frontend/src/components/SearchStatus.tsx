'use client'

interface Props {
  status: string
  keywords: string[]
  totalFound: number
}

const STEPS = [
  { key: 'queued', label: 'Vorbereitung' },
  { key: 'searching', label: 'Suche läuft' },
  { key: 'evaluating', label: 'KI-Bewertung' },
  { key: 'done', label: 'Fertig' },
]

export default function SearchStatus({ status, keywords, totalFound }: Props) {
  const currentStep = STEPS.findIndex(s => s.key === status)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      {/* Progress Steps */}
      <div className="flex items-center gap-0">
        {STEPS.map((step, i) => {
          const done = i < currentStep
          const active = i === currentStep
          return (
            <div key={step.key} className="flex items-center flex-1">
              <div className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-medium flex-shrink-0
                ${done ? 'bg-green-500 text-white' : active ? 'bg-gs-blue text-white' : 'bg-gray-100 text-gray-400'}`}>
                {done ? '✓' : i + 1}
              </div>
              <div className={`flex-1 text-xs ml-1.5 ${active ? 'text-gs-blue font-medium' : done ? 'text-green-600' : 'text-gray-400'}`}>
                {step.label}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`h-0.5 flex-1 mx-2 ${done ? 'bg-green-400' : 'bg-gray-200'}`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Keywords */}
      {keywords.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-1.5">Suchbegriffe</p>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((k, i) => (
              <span key={i} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full border border-blue-100">
                {k}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Count */}
      {totalFound > 0 && (
        <p className="text-sm text-gray-600">
          <span className="font-medium text-gs-blue">{totalFound}</span> Profile gefunden, werden bewertet…
        </p>
      )}

      {/* Animated indicator */}
      {status !== 'done' && status !== 'error' && (
        <div className="flex gap-1">
          {[0, 1, 2].map(i => (
            <div key={i} className="w-2 h-2 bg-gs-blue rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      )}
    </div>
  )
}
