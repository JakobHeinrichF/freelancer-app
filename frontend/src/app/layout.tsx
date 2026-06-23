import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GS Freelancer Profiler',
  description: 'Grashoff & Schumm – Automatisierter Freelancer-Such- und Profilierungsassistent',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="min-h-screen">
        <header className="bg-gs-blue text-white px-6 py-4 flex items-center justify-between shadow">
          <div>
            <h1 className="text-lg font-semibold tracking-wide">GRASHOFF &amp; SCHUMM</h1>
            <p className="text-xs text-blue-200 mt-0.5">Freelancer Profiler</p>
          </div>
          <span className="text-xs text-blue-300">MC GmbH &amp; Co KG · Bielefeld</span>
        </header>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  )
}
