"""
Scraper für gulp.de und freelancermap.de
Sucht nach Freelancern anhand von Keywords und gibt Profilinformationen zurück.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = httpx.Timeout(20.0)


# ─── GULP.DE ─────────────────────────────────────────────────────────────────

async def search_gulp(keywords: list[str], max_results: int = 8) -> list[dict]:
    """Sucht Freelancer auf gulp.de und gibt grundlegende Profilinformationen zurück."""
    query = " ".join(keywords)
    url = f"https://www.gulp.de/gulp2/g/spezialisten?q={query.replace(' ', '+')}"

    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            print(f"[GULP] Suche fehlgeschlagen: {e}")
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    profiles = []

    # Profilkarten auf der Suchergebnisseite
    cards = soup.select("a[href*='/gulp2/g/spezialisten/'], a[href*='/freelancer/'], a[href*='/freiberufler/']")
    seen = set()

    for card in cards:
        href = card.get("href", "")
        if not href or href in seen:
            continue
        # Nur echte Profillinks
        if not re.search(r"/(freelancer|freiberufler|spezialisten)/[A-Z0-9]{6,}", href):
            continue
        seen.add(href)

        full_url = href if href.startswith("http") else f"https://www.gulp.de{href}"
        title = card.get_text(strip=True)[:120]

        profiles.append({
            "platform": "gulp.de",
            "url": full_url,
            "title": title or "Freelancer Profil",
            "raw_data": None,
        })

        if len(profiles) >= max_results:
            break

    # Profildetails parallel abrufen (max 4 gleichzeitig)
    sem = asyncio.Semaphore(4)
    tasks = [fetch_gulp_profile(p["url"], sem) for p in profiles]
    details = await asyncio.gather(*tasks, return_exceptions=True)

    enriched = []
    for profile, detail in zip(profiles, details):
        if isinstance(detail, dict) and detail:
            profile.update(detail)
        enriched.append(profile)

    return enriched


async def fetch_gulp_profile(url: str, sem: asyncio.Semaphore) -> dict:
    """Ruft ein einzelnes gulp.de Profil ab und extrahiert die relevanten Daten."""
    async with sem:
        await asyncio.sleep(0.3)  # sanftes Rate-Limiting
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except Exception as e:
                print(f"[GULP] Profil {url} fehlgeschlagen: {e}")
                return {}

    soup = BeautifulSoup(resp.text, "lxml")

    # Titel / Hauptbezeichnung
    title_el = soup.select_one("h1, h2.profile-title, .profile-headline")
    title = title_el.get_text(strip=True) if title_el else ""

    # Skills / Top-Skills
    skills = []
    for el in soup.select(".skill-tag, .top-skill, [class*='skill']")[:20]:
        t = el.get_text(strip=True)
        if t and len(t) < 60:
            skills.append(t)

    # Sprachen
    languages = []
    lang_section = soup.find(string=re.compile(r"Sprachen|Languages", re.I))
    if lang_section:
        parent = lang_section.find_parent()
        if parent:
            for sib in parent.find_next_siblings()[:6]:
                t = sib.get_text(strip=True)
                if t:
                    languages.append(t)

    # Projekthistorie (Text der ersten 3 Projekte)
    projects = []
    proj_els = soup.select("h3, h4, .project-title, [class*='project']")[:6]
    for el in proj_els:
        t = el.get_text(strip=True)
        if t and len(t) > 10:
            # Projektbeschreibung folgt oft im nächsten Element
            desc_el = el.find_next_sibling()
            desc = desc_el.get_text(strip=True)[:300] if desc_el else ""
            projects.append({"title": t, "description": desc})

    # Verfügbarkeit
    avail_el = soup.find(string=re.compile(r"Verf.gbar|Available", re.I))
    availability = avail_el.find_next().get_text(strip=True) if avail_el and avail_el.find_next() else ""

    # Volltext für Claude-Analyse
    full_text = soup.get_text(separator="\n", strip=True)[:4000]

    return {
        "title": title,
        "skills": list(set(skills)),
        "languages": languages,
        "projects": projects[:4],
        "availability": availability,
        "full_text": full_text,
    }


# ─── FREELANCERMAP.DE ─────────────────────────────────────────────────────────

async def search_freelancermap(keywords: list[str], max_results: int = 8) -> list[dict]:
    """Sucht Freelancer auf freelancermap.de."""
    query = " ".join(keywords)
    url = f"https://www.freelancermap.de/freelancer-verzeichnis.html?q={query.replace(' ', '+')}&projectType=contracting&type=profile"

    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            print(f"[FLM] Suche fehlgeschlagen: {e}")
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    profiles = []
    seen = set()

    # Profillinks auf der Ergebnisseite
    for a in soup.select("a[href*='/profil/'], a[href*='/freelancer-verzeichnis/profile/']"):
        href = a.get("href", "")
        if not href or href in seen:
            continue
        if "freelancer-verzeichnis" in href and "profile" not in href:
            continue
        seen.add(href)

        full_url = href if href.startswith("http") else f"https://www.freelancermap.de{href}"
        title = a.get_text(strip=True)[:120]

        profiles.append({
            "platform": "freelancermap.de",
            "url": full_url,
            "title": title or "Freelancer Profil",
            "raw_data": None,
        })

        if len(profiles) >= max_results:
            break

    sem = asyncio.Semaphore(4)
    tasks = [fetch_freelancermap_profile(p["url"], sem) for p in profiles]
    details = await asyncio.gather(*tasks, return_exceptions=True)

    enriched = []
    for profile, detail in zip(profiles, details):
        if isinstance(detail, dict) and detail:
            profile.update(detail)
        enriched.append(profile)

    return enriched


async def fetch_freelancermap_profile(url: str, sem: asyncio.Semaphore) -> dict:
    """Ruft ein einzelnes freelancermap.de Profil ab."""
    async with sem:
        await asyncio.sleep(0.3)
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except Exception as e:
                print(f"[FLM] Profil {url} fehlgeschlagen: {e}")
                return {}

    soup = BeautifulSoup(resp.text, "lxml")

    title_el = soup.select_one("h1, .profile-title, [class*='headline']")
    title = title_el.get_text(strip=True) if title_el else ""

    skills = []
    for el in soup.select("[class*='skill'], [class*='tag'], [class*='keyword']")[:25]:
        t = el.get_text(strip=True)
        if t and len(t) < 60:
            skills.append(t)

    languages = []
    lang_el = soup.find(string=re.compile(r"Sprachkenntnisse|Sprache|Languages", re.I))
    if lang_el:
        parent = lang_el.find_parent()
        if parent:
            for sib in parent.find_next_siblings()[:8]:
                t = sib.get_text(strip=True)
                if t:
                    languages.append(t)

    avail_el = soup.find(string=re.compile(r"Verfügbar|verfügbar|Available", re.I))
    availability = ""
    if avail_el:
        p = avail_el.find_parent()
        availability = p.get_text(strip=True) if p else ""

    full_text = soup.get_text(separator="\n", strip=True)[:4000]

    return {
        "title": title,
        "skills": list(set(skills)),
        "languages": languages,
        "projects": [],
        "availability": availability,
        "full_text": full_text,
    }


# ─── COMBINED SEARCH ──────────────────────────────────────────────────────────

async def search_all_platforms(keywords: list[str], max_per_platform: int = 6) -> list[dict]:
    """Sucht gleichzeitig auf gulp.de und freelancermap.de."""
    gulp_task = search_gulp(keywords, max_per_platform)
    flm_task = search_freelancermap(keywords, max_per_platform)

    gulp_results, flm_results = await asyncio.gather(gulp_task, flm_task)

    # Zusammenführen: gulp zuerst, dann freelancermap
    all_results = gulp_results + flm_results
    return all_results
