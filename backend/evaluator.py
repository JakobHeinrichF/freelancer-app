"""
Claude-basierte Bewertung von Freelancer-Profilen gegen ein Rollenprofil.
Priorität: 1) Key Responsibilities, 2) Deutsch native/C2
"""
import anthropic
import json
from config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


SYSTEM_PROMPT = """Du bist ein spezialisierter Recruiting-Assistent für Freelancer-Profile.
Du bewertest Freelancer-Profile strikt nach folgenden Prioritäten:

PRIORITÄT 1 — Key Responsibilities (KR):
Prüfe für jede KR ob das Profil einen klaren Beleg enthält.
Status: "belegt" | "implizit" | "fehlt"
Ein Profil das 2+ KRs mit "fehlt" bewertet wird ist ein KO.

PRIORITÄT 2 — Deutsch native/C2:
Prüfe ob Deutsch explizit als Muttersprache oder C2 angegeben ist.
Nur wenn KR bestanden.

Antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt. Kein Text davor oder danach.
"""

EVAL_TEMPLATE = """ROLLENPROFIL:
{role_profile}

FREELANCER-PROFIL (Plattform: {platform}):
URL: {url}
Titel: {title}
Skills: {skills}
Sprachen: {languages}
Verfügbarkeit: {availability}
Volltext:
{full_text}

Bewerte dieses Profil und antworte mit folgendem JSON:
{{
  "name_or_title": "Kurztitel/Bezeichnung des Freelancers",
  "platform": "{platform}",
  "url": "{url}",
  "kr_results": [
    {{
      "kr": "Name der Key Responsibility",
      "status": "belegt|implizit|fehlt",
      "evidence": "Kurzer Textbeleg aus dem Profil oder 'Nicht gefunden'"
    }}
  ],
  "kr_score": 0-100,
  "kr_pass": true/false,
  "deutsch_native": true/false/null,
  "deutsch_evidence": "Beleg oder 'Nicht angegeben'",
  "overall_match": 0-100,
  "recommendation": "empfohlen|bedingt|abgelehnt",
  "missing": ["Liste fehlender Punkte"],
  "short_summary": "2-3 Sätze professionelle Zusammenfassung"
}}"""


async def evaluate_profile(profile: dict, role_profile: dict) -> dict:
    """Bewertet ein einzelnes Freelancer-Profil gegen das Rollenprofil."""

    role_text = f"""Rolle: {role_profile.get('title', '')}
Layer/Sprache/Shore: {role_profile.get('layer', '')}
Mission: {role_profile.get('mission', '')}
Key Responsibilities:
{chr(10).join(f"- {kr}" for kr in role_profile.get('key_responsibilities', []))}
Must-Haves:
{chr(10).join(f"- {mh}" for mh in role_profile.get('must_haves', []))}
Warum Deutsch: {role_profile.get('why_german', '')}"""

    prompt = EVAL_TEMPLATE.format(
        role_profile=role_text,
        platform=profile.get("platform", ""),
        url=profile.get("url", ""),
        title=profile.get("title", ""),
        skills=", ".join(profile.get("skills", [])[:20]),
        languages=", ".join(profile.get("languages", [])[:10]),
        availability=profile.get("availability", ""),
        full_text=profile.get("full_text", "")[:3000],
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # JSON bereinigen falls Code-Fences vorhanden
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        result["raw_profile"] = profile
        return result

    except json.JSONDecodeError as e:
        print(f"[EVAL] JSON-Fehler für {profile.get('url')}: {e}")
        return _fallback_result(profile)
    except Exception as e:
        print(f"[EVAL] Fehler für {profile.get('url')}: {e}")
        return _fallback_result(profile)


def _fallback_result(profile: dict) -> dict:
    return {
        "name_or_title": profile.get("title", "Unbekannt"),
        "platform": profile.get("platform", ""),
        "url": profile.get("url", ""),
        "kr_results": [],
        "kr_score": 0,
        "kr_pass": False,
        "deutsch_native": None,
        "deutsch_evidence": "Nicht geprüft",
        "overall_match": 0,
        "recommendation": "abgelehnt",
        "missing": ["Profilauswertung fehlgeschlagen"],
        "short_summary": "Profil konnte nicht ausgewertet werden.",
        "raw_profile": profile,
        "error": True,
    }


async def evaluate_all_profiles(profiles: list[dict], role_profile: dict) -> list[dict]:
    """Bewertet alle Profile und filtert nach KR + Deutsch."""
    import asyncio

    # Evaluation mit leichter Verzögerung um Rate-Limits zu vermeiden
    results = []
    for i, profile in enumerate(profiles):
        if i > 0:
            await asyncio.sleep(0.5)
        result = await evaluate_profile(profile, role_profile)
        results.append(result)

    # Sortierung: empfohlen → bedingt → abgelehnt, dann nach overall_match
    priority = {"empfohlen": 0, "bedingt": 1, "abgelehnt": 2}
    results.sort(key=lambda r: (priority.get(r.get("recommendation", "abgelehnt"), 2), -r.get("overall_match", 0)))

    return results
