# GS Freelancer Profiler

Automatisierter Freelancer-Such- und Profilierungsassistent für Grashoff & Schumm.

**Was die App macht:**
1. Rollenprofil (Key Responsibilities, Must-Haves) eingeben
2. Automatische Suche auf **gulp.de** und **freelancermap.de**
3. KI-Bewertung (Claude) nach: ① Key Responsibilities → ② Deutsch native/C2
4. OK geben → **.docx im Grashoff-Template** wird automatisch generiert

---

## Schnellstart (lokal)

### Voraussetzungen
- Python 3.12+
- Node.js 20+
- Ein Anthropic API Key → https://console.anthropic.com

### 1. Repo klonen
```bash
git clone <dein-repo-url>
cd freelancer-app
```

### 2. Template einfügen
Lege dein Grashoff Word-Template hier ab:
```
template/GS_Profile_Template.docx
```

### 3. Backend starten
```bash
cd backend
cp .env.example .env
# .env öffnen und ANTHROPIC_API_KEY eintragen

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend läuft auf http://localhost:8000
API-Docs: http://localhost:8000/docs

### 4. Frontend starten
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

App läuft auf http://localhost:3000

---

## Deployment auf Railway (kostenlos)

### Backend
1. https://railway.app → New Project → Deploy from GitHub
2. Root Directory: `backend`
3. Environment Variables setzen:
   - `ANTHROPIC_API_KEY` = dein Key
   - `TEMPLATE_PATH` = `/app/template/GS_Profile_Template.docx`
   - `CORS_ORIGINS` = `["https://dein-frontend.railway.app"]`
4. Das Template muss über ein Volume oder im Repo (Git LFS) bereitgestellt werden

### Frontend
1. New Service → Deploy from GitHub
2. Root Directory: `frontend`
3. Environment Variables:
   - `NEXT_PUBLIC_API_URL` = URL deines Backend-Services

### Mit Docker Compose (VPS / lokaler Server)
```bash
# .env erstellen
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Starten
docker-compose up -d

# Logs
docker-compose logs -f
```

---

## Projektstruktur

```
freelancer-app/
├── backend/
│   ├── main.py           # FastAPI App + Endpoints
│   ├── scraper.py        # gulp.de + freelancermap.de Scraper
│   ├── evaluator.py      # Claude KI-Bewertung
│   ├── docx_generator.py # Word-Template befüllen
│   ├── config.py         # Einstellungen (.env)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Hauptseite
│   │   │   └── layout.tsx     # App-Shell mit GS-Header
│   │   ├── components/
│   │   │   ├── RoleProfileForm.tsx  # Eingabeformular
│   │   │   ├── ProfileCard.tsx      # Profilkarte mit Bewertung
│   │   │   └── SearchStatus.tsx     # Fortschrittsanzeige
│   │   └── lib/api.ts         # API-Hilfsfunktionen
│   └── Dockerfile
├── template/
│   └── GS_Profile_Template.docx  ← hier das Template einfügen
└── docker-compose.yml
```

---

## Bewertungslogik

```
Suche auf gulp.de + freelancermap.de (parallel)
        ↓
Claude bewertet jedes Profil:
  ① Key Responsibilities
     - belegt / implizit / fehlt
     - KO wenn 2+ KRs fehlen
  ② Deutsch native/C2
     - Nur wenn KR bestanden
        ↓
Sortierung: empfohlen → bedingt → abgelehnt
        ↓
OK geben → .docx generieren (anonym, "Recent Project")
```

---

## API-Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| `POST` | `/search` | Suche starten → gibt `job_id` zurück |
| `GET` | `/search/{job_id}` | Status + Ergebnisse abrufen |
| `POST` | `/generate-docx` | .docx für genehmigtes Profil generieren |
| `DELETE` | `/search/{job_id}` | Job löschen |
| `GET` | `/health` | Health check |

---

## Kosten

- **Anthropic API**: ~0.01–0.05€ pro vollständige Suche (je nach Profilen)
- **Railway Free Tier**: 500h/Monat kostenlos → reicht für internen Gebrauch
- **Alternativ Hetzner VPS**: ~4€/Monat für dediziertes Hosting

---

## Weiterentwicklung

- [ ] Authentifizierung (einfaches Password-Gate für internes Tool)
- [ ] Ergebnisse speichern (SQLite oder PostgreSQL)
- [ ] Mehrere Profile auf einmal genehmigen
- [ ] E-Mail-Benachrichtigung wenn Suche fertig
- [ ] Weitere Plattformen (expertlead.de, freelance.de)
- [ ] Profil-Vergleichsansicht
