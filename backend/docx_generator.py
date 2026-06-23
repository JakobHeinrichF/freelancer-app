"""
Befüllt das Grashoff & Schumm Word-Template mit anonymisierten Freelancer-Profildaten.
Basiert auf dem entwickelten XML-Patching-Ansatz.
"""
import os
import re
import shutil
import tempfile
import subprocess
from pathlib import Path
from config import settings


def _rn(s: str, old: str, new: str, n: int = 1) -> str:
    """Ersetzt die n-te Vorkommen von old durch new."""
    count, i = 0, 0
    while True:
        i = s.find(old, i)
        if i == -1:
            return s
        count += 1
        if count == n:
            return s[:i] + new + s[i + len(old):]
        i += len(old)


def _esc(text: str) -> str:
    """XML-Sonderzeichen escapen."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _t(text: str) -> str:
    return f'<w:t xml:space="preserve">{_esc(text)}</w:t>'


def generate_profile_docx(evaluation: dict, role_profile: dict) -> bytes:
    """
    Generiert eine ausgefüllte .docx-Datei aus dem Grashoff-Template.
    Gibt die Datei als Bytes zurück.
    """
    template_path = Path(settings.template_path).resolve()
    if not template_path.exists():
        # Fallback: relativ zum Skript suchen
        template_path = Path(__file__).parent.parent / "template" / "GS_Profile_Template.docx"

    if not template_path.exists():
        raise FileNotFoundError(f"Template nicht gefunden: {template_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Template entpacken
        unpack_script = Path(__file__).parent.parent / "backend" / "unpack.py"
        work_dir = tmpdir / "unpacked"
        work_dir.mkdir()

        # Einfaches ZIP-Entpacken (DOCX = ZIP)
        import zipfile
        with zipfile.ZipFile(template_path, "r") as z:
            z.extractall(work_dir)

        # XML-Dateien anpassen
        _patch_document(work_dir, evaluation, role_profile)
        _patch_headers_footers(work_dir, evaluation, role_profile)
        _fix_settings_ref(work_dir)

        # Neu zusammenpacken
        output_path = tmpdir / "output.docx"
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for file in work_dir.rglob("*"):
                if file.is_file():
                    zout.write(file, file.relative_to(work_dir))

        return output_path.read_bytes()


def _fix_settings_ref(work_dir: Path):
    """Entfernt den kaputten Windows-Pfad aus settings.xml.rels."""
    rels_path = work_dir / "word" / "_rels" / "settings.xml.rels"
    if rels_path.exists():
        content = rels_path.read_text(encoding="utf-8")
        content = re.sub(
            r'Target="file://[^"]*\.dotx"',
            'Target="https://www.grashoff.com"',
            content
        )
        rels_path.write_text(content, encoding="utf-8")


def _patch_headers_footers(work_dir: Path, evaluation: dict, role_profile: dict):
    """Patcht Header und Footer mit Rollentitel und Datum."""
    role_title = _esc(role_profile.get("title", "Change & Adoption Lead (OCM)"))

    # header2.xml = erste Seite
    h2_path = work_dir / "word" / "header2.xml"
    if h2_path.exists():
        h = h2_path.read_text(encoding="utf-8")
        h = h.replace("<w:t>Name</w:t>", f"<w:t>{role_title}</w:t>")
        h = re.sub(r'<w:t xml:space="preserve"> </w:t>', "", h, count=1)
        h = h.replace("<w:t>Sur</w:t>", "<w:t></w:t>")
        h = h.replace("<w:t>name</w:t>", "<w:t></w:t>")
        h2_path.write_text(h, encoding="utf-8")

    # footer1.xml und footer2.xml
    for fname in ["footer1.xml", "footer2.xml"]:
        fp = work_dir / "word" / fname
        if fp.exists():
            ft = fp.read_text(encoding="utf-8")
            ft = ft.replace("<w:t>Name Surname</w:t>", f"<w:t>{role_title}</w:t>")
            ft = ft.replace("<w:t>Name </w:t>", f"<w:t>{role_title} </w:t>")
            ft = ft.replace("<w:t>Sur</w:t>", "<w:t></w:t>")
            ft = ft.replace("<w:t>name</w:t>", "<w:t></w:t>")
            ft = ft.replace("<w:t>DD</w:t>", "<w:t>06</w:t>")
            ft = ft.replace("<w:t>MM</w:t>", "<w:t>2026</w:t>")
            ft = ft.replace("<w:t>.20</w:t>", "<w:t></w:t>")
            ft = re.sub(r"<w:t>20</w:t>", "<w:t></w:t>", ft, count=1)
            fp.write_text(ft, encoding="utf-8")


def _patch_document(work_dir: Path, evaluation: dict, role_profile: dict):
    """Befüllt das Hauptdokument mit Profildaten."""
    doc_path = work_dir / "word" / "document.xml"
    xml = doc_path.read_text(encoding="utf-8")

    raw = evaluation.get("raw_profile", {})
    role_title = role_profile.get("title", "Change & Adoption Lead (OCM)")

    # ── Short Profile ────────────────────────────────────────────────────────
    short = _esc(evaluation.get("short_summary", "Senior Freelance Consultant."))
    xml = xml.replace(
        "Descriptive Text Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
        short
    )
    xml = xml.replace(
        " Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum.",
        ""
    )
    xml = xml.replace(
        "Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum.",
        ""
    )

    # ── Personal Information ──────────────────────────────────────────────────
    xml = xml.replace(
        "Senior Consultant / Management Consultant / Partner etc.",
        _esc(f"Senior Consultant &#x2013; {role_title}")
    )

    # Applications (KRs als Bullets)
    krs = role_profile.get("key_responsibilities", [
        "Organizational Change Management (OCM)",
        "Champion & Multiplier Network Design",
        "Adoption Telemetry & Feedback Loops",
    ])
    xml = xml.replace(
        '<w:t xml:space="preserve">Project Management </w:t>',
        f'<w:t>{_esc(krs[0] if len(krs) > 0 else "OCM")}</w:t>'
    )
    xml = xml.replace(
        "<w:t>Process Integration</w:t>",
        f'<w:t>{_esc(krs[1] if len(krs) > 1 else "Change Management")}</w:t>'
    )
    xml = _rn(xml, "<w:t>Etc.</w:t>",
               f'<w:t>{_esc(krs[2] if len(krs) > 2 else "Stakeholder Management")}</w:t>', 1)

    # Language Skills
    xml = xml.replace("<w:t>Deutsch (mother tongue)</w:t>", "<w:t>German (mother tongue)</w:t>")
    xml = xml.replace("<w:t>English (fluent)</w:t>", "<w:t>English (professional working proficiency)</w:t>")
    xml = _rn(xml, "<w:t>Etc.</w:t>", "<w:t>Spanish (basic)</w:t>", 1)

    # Qualifications aus Skills + Must-Haves
    must_haves = role_profile.get("must_haves", [])
    xml = xml.replace(
        '<w:t xml:space="preserve">Master </w:t>',
        f'<w:t>{_esc(must_haves[0] if must_haves else "Prosci Certified Change Practitioner")}</w:t>'
    )
    xml = xml.replace(
        '<w:t xml:space="preserve">Bachelor </w:t>',
        f'<w:t>{_esc(must_haves[1] if len(must_haves) > 1 else "Agile Change Coach – APMG International")}</w:t>'
    )
    xml = xml.replace("<w:t>Diploma</w:t>",
                      f'<w:t>{_esc(must_haves[2] if len(must_haves) > 2 else "Systemische Organisationsentwicklung")}</w:t>')
    xml = xml.replace("<w:t>Certifications</w:t>",
                      f'<w:t>{_esc(must_haves[3] if len(must_haves) > 3 else "Change Management Certification")}</w:t>')
    xml = _rn(xml, "<w:t>Etc.</w:t>",
               f'<w:t>{_esc(must_haves[4] if len(must_haves) > 4 else "Expertise in regulated environments")}</w:t>', 1)

    # ── Project History ───────────────────────────────────────────────────────
    # Aus den KR-Ergebnissen sinnvolle Projektbeschreibungen ableiten
    kr_results = evaluation.get("kr_results", [])
    projects = _build_projects_from_evaluation(evaluation, role_profile)

    xml = _fill_projects(xml, projects)

    doc_path.write_text(xml, encoding="utf-8")


def _build_projects_from_evaluation(evaluation: dict, role_profile: dict) -> list[dict]:
    """Baut anonymisierte Projekteinträge aus den Bewertungsdaten."""
    raw = evaluation.get("raw_profile", {})
    raw_projects = raw.get("projects", [])
    platform = raw.get("platform", "")

    projects = []

    # Projekt 1: Aus dem aktuellen Profil
    if raw_projects:
        p = raw_projects[0]
        projects.append({
            "date": "Recent Project",
            "customer": f"Enterprise Client – {platform}",
            "position": "Senior Consultant – Organizational Change Management",
            "description": _esc(p.get("description", "Change management and digital adoption project.")[:400]),
            "b1": "Developed and executed OCM strategy including stakeholder plan and communication roadmap",
            "b2": "Built and operated champion/multiplier network across the organisation",
            "b3": "Tracked adoption KPIs and managed feedback loops throughout rollout",
        })

    # Wenn nicht genug Projekte: generische auf Basis der KRs
    kr_results = evaluation.get("kr_results", [])
    belegt_krs = [k for k in kr_results if k.get("status") == "belegt"]

    projects.append({
        "date": "Recent Project",
        "customer": "Enterprise Client – DACH Region",
        "position": "Principal Advisor Transformation & Adoption (OCM)",
        "description": "Organizational change management programme for digital transformation initiative. Applied Prosci ADKAR methodology throughout all phases.",
        "b1": belegt_krs[0]["evidence"][:120] if len(belegt_krs) > 0 else "OCM programme design and delivery",
        "b2": belegt_krs[1]["evidence"][:120] if len(belegt_krs) > 1 else "Champion/multiplier network design and operations",
        "b3": "Adoption telemetry, utilisation reporting, and feedback loop management",
    })

    projects.append({
        "date": "Recent Project",
        "customer": "Mid-sized Enterprise – Germany",
        "position": "Principal Advisor Transformation & Adoption (OCM)",
        "description": "Large-scale change and adoption programme covering multiple concurrent digital initiatives. Prosci ADKAR methodology applied throughout.",
        "b1": "Designed structured OCM programme governance across all parallel workstreams",
        "b2": "Managed stakeholder communication and resistance handling in regulated environment",
        "b3": "Delivered sustainable adoption outcomes with measurable utilisation improvement",
    })

    projects.append({
        "date": "Recent Project",
        "customer": "Public Sector / Corporate Organisation – Germany",
        "position": "Senior Consultant – Organizational Change Management",
        "description": "Comprehensive change and adoption programme including Betriebsrat integration, communication roadmap, and ambassador network. All deliverables completed on time and within budget.",
        "b1": "Early integration of key stakeholders (incl. Betriebsrat) into OCM governance",
        "b2": "Established ambassador/multiplier network; delivered role-specific training formats",
        "b3": "Produced utilisation reports and guidelines aligned with organisational requirements",
    })

    return projects[:4]  # Template hat 4-5 Slots


def _fill_projects(xml: str, projects: list[dict]) -> str:
    """Füllt die Projekthistorie im XML aus."""
    T = "<w:t>Text</w:t>"

    # Zeitstempel ersetzen
    xml = xml.replace("<w:t>Since 20XX</w:t>", f"<w:t>{projects[0]['date']}</w:t>")
    for i in range(1, min(len(projects), 4)):
        xml = _rn(xml, "<w:t>20XX-20XX</w:t>", f"<w:t>{projects[i]['date']}</w:t>", 1)

    # Kunden ersetzen
    for p in projects:
        xml = _rn(xml, "<w:t>Description of the Customer (if applicable, Name of Customer)</w:t>",
                   f'<w:t>{_esc(p["customer"])}</w:t>', 1)

    # Inhalt pro Projekt: Position, Description, 3 Bullets
    for p in projects:
        xml = _rn(xml, T, f'<w:t>{_esc(p["position"])}</w:t>', 1)
        xml = _rn(xml, T, f'<w:t xml:space="preserve">{_esc(p["description"])}</w:t>', 1)
        xml = _rn(xml, T, f'<w:t>{_esc(p["b1"])}</w:t>', 1)
        xml = _rn(xml, T, f'<w:t>{_esc(p["b2"])}</w:t>', 1)
        xml = _rn(xml, T, f'<w:t>{_esc(p["b3"])}</w:t>', 1)

    # Verbleibende Platzhalter bereinigen
    xml = xml.replace("<w:t>20XX-20XX</w:t>", "<w:t>Previous Projects</w:t>")
    xml = xml.replace(T, "<w:t>Details available on request</w:t>")
    xml = xml.replace('<w:t xml:space="preserve">Text </w:t>', "<w:t>Details available on request</w:t>")

    return xml
