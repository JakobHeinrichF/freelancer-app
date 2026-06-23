"""
Grashoff & Schumm Freelancer Profiler – FastAPI Backend
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import asyncio
import uuid

from config import settings
from scraper import search_all_platforms
from evaluator import evaluate_all_profiles
from docx_generator import generate_profile_docx

app = FastAPI(title="GS Freelancer Profiler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Job Store (für Produktion: Redis verwenden)
jobs: dict[str, dict] = {}


# ── Datenmodelle ──────────────────────────────────────────────────────────────

class RoleProfile(BaseModel):
    title: str
    layer: str = ""
    mission: str = ""
    key_responsibilities: list[str]
    must_haves: list[str] = []
    why_german: str = ""

class SearchRequest(BaseModel):
    role_profile: RoleProfile
    max_per_platform: int = 6

class ApproveRequest(BaseModel):
    job_id: str
    profile_index: int


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _build_keywords(role: RoleProfile) -> list[str]:
    """Extrahiert Suchbegriffe aus dem Rollenprofil."""
    base = [role.title]
    for kr in role.key_responsibilities[:3]:
        words = [w for w in kr.split() if len(w) > 4][:2]
        base.extend(words)
    if role.must_haves:
        base.append(role.must_haves[0].split()[0])
    return list(dict.fromkeys(base))[:8]  # dedupliziert, max 8


async def _run_search_and_eval(job_id: str, request: SearchRequest):
    """Background-Task: Suche + Bewertung."""
    try:
        jobs[job_id]["status"] = "searching"
        keywords = _build_keywords(request.role_profile)
        jobs[job_id]["keywords"] = keywords

        raw_profiles = await search_all_platforms(keywords, request.max_per_platform)
        jobs[job_id]["status"] = "evaluating"
        jobs[job_id]["total"] = len(raw_profiles)

        if not raw_profiles:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["results"] = []
            return

        evaluated = await evaluate_all_profiles(raw_profiles, request.role_profile.model_dump())

        jobs[job_id]["status"] = "done"
        jobs[job_id]["results"] = evaluated

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        print(f"[JOB {job_id}] Fehler: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/search")
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """Startet eine asynchrone Suche und gibt eine Job-ID zurück."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "role_profile": request.role_profile.model_dump(),
        "results": [],
        "total": 0,
        "keywords": [],
    }
    background_tasks.add_task(_run_search_and_eval, job_id, request)
    return {"job_id": job_id}


@app.get("/search/{job_id}")
async def get_search_status(job_id: str):
    """Gibt den aktuellen Status und (falls fertig) die Ergebnisse zurück."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "keywords": job.get("keywords", []),
        "total_found": job.get("total", 0),
    }

    if job["status"] == "done":
        # Ergebnisse für Frontend aufbereiten
        response["results"] = [_serialize_result(r) for r in job.get("results", [])]
    elif job["status"] == "error":
        response["error"] = job.get("error", "Unbekannter Fehler")

    return response


def _serialize_result(r: dict) -> dict:
    """Bereitet ein Bewertungsergebnis für das Frontend auf."""
    return {
        "platform": r.get("platform", ""),
        "url": r.get("url", ""),
        "name_or_title": r.get("name_or_title", ""),
        "kr_results": r.get("kr_results", []),
        "kr_score": r.get("kr_score", 0),
        "kr_pass": r.get("kr_pass", False),
        "deutsch_native": r.get("deutsch_native"),
        "deutsch_evidence": r.get("deutsch_evidence", ""),
        "overall_match": r.get("overall_match", 0),
        "recommendation": r.get("recommendation", "abgelehnt"),
        "missing": r.get("missing", []),
        "short_summary": r.get("short_summary", ""),
        "availability": r.get("raw_profile", {}).get("availability", ""),
        "skills": r.get("raw_profile", {}).get("skills", [])[:10],
    }


@app.post("/generate-docx")
async def generate_docx(request: ApproveRequest):
    """Generiert eine .docx-Datei für ein genehmigtes Profil."""
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    job = jobs[request.job_id]
    results = job.get("results", [])

    if request.profile_index >= len(results):
        raise HTTPException(status_code=400, detail="Ungültiger Profil-Index")

    evaluation = results[request.profile_index]
    role_profile = job["role_profile"]

    try:
        docx_bytes = generate_profile_docx(evaluation, role_profile)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Template nicht gefunden: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX-Generierung fehlgeschlagen: {e}")

    filename = f"GS_Profile_{evaluation.get('name_or_title', 'Freelancer').replace(' ', '_')[:30]}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/search/{job_id}")
async def delete_job(job_id: str):
    """Löscht einen abgeschlossenen Job aus dem Speicher."""
    jobs.pop(job_id, None)
    return {"deleted": True}
