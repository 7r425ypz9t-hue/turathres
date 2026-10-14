"""استيراد النموذج التطبيقي التجريبي (pilot/) إلى مشروع في الأرشيف — بمصادره المتحقق منها وادعاءاته وأدلته وتعارضاته."""
from __future__ import annotations
import json
from pathlib import Path

from . import db

PILOT = Path(__file__).parent.parent / "pilot"


def _load(name: str):
    p = PILOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def available() -> bool:
    return (PILOT / "sources.json").exists()


def import_pilot(user: dict) -> dict:
    if not available():
        raise RuntimeError("ملفات النموذج التجريبي غير موجودة")
    meta = json.loads((PILOT / "meta.json").read_text(encoding="utf-8")) if (PILOT / "meta.json").exists() else {}
    title = meta.get("title", "نموذج تطبيقي تجريبي")
    old = db.one("SELECT id FROM projects WHERE title=? AND owner_id=?", (title, user["id"]))
    if old:
        return {"project": old["id"], "existing": True}
    p = db.create(user, "projects", {
        "title": title, "domain": meta.get("domain", "crafts_economy"), "question": meta.get("question"),
        "gap": meta.get("gap"), "region": meta.get("region"), "emirate": meta.get("emirate", "multi"),
        "localities": meta.get("localities"), "output_type": "دراسة موثقة — نموذج تجريبي", "lead_agent": "AG-CRF",
        "summary": meta.get("summary", "نموذج تطبيقي مبني على مصادر متاحة موثقة فقط؛ الجمع الميداني معلّق."),
        "access_level": "project"})
    pid = p["id"]
    keymap = {}
    for s in _load("sources.json"):
        r = db.create(user, "sources", {
            "project_id": pid, "title": s.get("title"), "creator": s.get("creator"), "year": str(s.get("year") or ""),
            "publisher": s.get("publisher"), "kind": {"legal": "legal", "article": "article", "report": "report",
                                                      "nomination_file": "report"}.get(s.get("type"), "web"),
            "level": s.get("level"), "url": s.get("url"), "language": s.get("language"), "accessed": s.get("accessed"),
            "verified": s.get("verified_by") == "opened", "critique": s.get("notes"), "source_ref": s.get("key")})
        keymap[s["key"]] = r["id"]
    cmap = {}
    for c in _load("claims.json"):
        r = db.create(user, "claims", {"project_id": pid, "text": c.get("text_ar"), "status": c.get("status"),
                                       "kind": "narrative" if c.get("status") == "pending_field" else "inference",
                                       "notes": c.get("note"), "source_ref": c.get("id")})
        cmap[c["id"]] = r["id"]
        for ev in c.get("evidence", []):
            if ev.get("source") in keymap:
                db.create(user, "evidence_links", {"project_id": pid, "claim_id": r["id"], "target_table": "sources",
                                                   "target_id": keymap[ev["source"]], "evidence_type": "document",
                                                   "relation": ev.get("relation", "supports"), "excerpt": ev.get("excerpt"),
                                                   "origin_group": ev["source"]})
    status_map = {"resolved": "resolved_by_evidence", "open": "open", "explained": "explained"}
    for c in _load("conflicts.json"):
        pos = [dict(x, source=keymap.get(x.get("source"), x.get("source"))) for x in c.get("positions", [])]
        db.create(user, "conflicts", {"project_id": pid, "topic": c.get("topic"), "status": status_map.get(c.get("status"), "open"),
                                      "positions": json.dumps(pos, ensure_ascii=False), "source_ref": c.get("id"),
                                      "analysis": c.get("note") or c.get("analysis") or "يُحلَّل في مرحلة نقد المصادر دون تسوية مصطنعة."})
    for t in _load("lexicon.json"):
        db.create(user, "dialect_lexicon", {"project_id": pid, "term": t.get("term"), "meaning": t.get("meaning"),
                                            "context": t.get("context"), "confidence": t.get("confidence"),
                                            "comparative": f"شاهد مكتوب: {keymap.get(t.get('source'), t.get('source'))}"
                                                           + (" — يلزم التحقق الميداني" if t.get("pending_field_verification") else "")})
    if meta.get("element"):
        db.create(user, "heritage_practices", {"project_id": pid, **meta["element"]})
    return {"project": pid, "sources": len(keymap), "claims": len(cmap)}
