"""الادعاءات والأدلة: التثليث المنهجي، وفحص استقلال الشهادات، وسجل التعارضات، والموافقات."""
from __future__ import annotations

from . import db
from .entities import E, EVIDENCE_TYPES


def links(claim_id: str) -> list[dict]:
    return db.rows("SELECT * FROM evidence_links WHERE claim_id=?", (claim_id,))


def _source_level(link: dict) -> int | None:
    if link.get("target_table") == "sources":
        s = db.get_raw("sources", link["target_id"])
        return s and s.get("level")
    return {"historical_documents": 1, "manuscripts": 1, "interviews": 2, "oral_narratives": 2, "observations": 2,
            "images": 2, "poems": 2}.get(link.get("target_table"))


def triangulation(claim_id: str) -> dict:
    """يعدّ أصناف الأدلة المستقلة لا عدد الرواة: الشهادات المشتركة في الأصل (origin_group) تُحسب شهادة واحدة."""
    L = [l for l in links(claim_id) if l.get("relation") == "supports"]
    contra = [l for l in links(claim_id) if l.get("relation") == "contradicts"]
    origins: dict[str, set] = {}
    for l in L:
        key = l.get("origin_group") or f"{l.get('target_table')}:{l.get('target_id')}"
        origins.setdefault(key, set()).add(l.get("evidence_type") or "other")
    types = {l.get("evidence_type") for l in L if l.get("evidence_type")}
    levels = [lv for lv in (_source_level(l) for l in L) if lv]
    dependent = len(L) - len(origins)
    ctx = [l for l in links(claim_id) if l.get("relation") == "context"]
    return {"supports": len(L), "contradicts": len(contra), "context": len(ctx), "independent_origins": len(origins),
            "evidence_types": sorted(types), "types_count": len(types), "dependent_links": max(dependent, 0),
            "best_level": min(levels) if levels else None, "press_only": bool(levels) and min(levels) == 5,
            "type_labels": [EVIDENCE_TYPES.get(t, t) for t in sorted(types)]}


def suggest_status(claim_id: str) -> str:
    t = triangulation(claim_id)
    if t["supports"] == 0:
        return "pending_field"
    if t["contradicts"] and t["contradicts"] >= t["supports"]:
        return "disputed"
    if t["press_only"]:
        return "probable"
    if t["independent_origins"] >= 2 and t["types_count"] >= 2 and (t["best_level"] or 9) <= 3:
        return "established"
    return "probable"


def claims_report(pid: str | None = None) -> dict:
    sql, args = "SELECT * FROM claims", ()
    if pid:
        sql, args = sql + " WHERE project_id=?", (pid,)
    C = db.rows(sql, args)
    rep = {"total": len(C), "unlinked": 0, "weak_established": 0, "press_only_core": 0, "independent_avg": 0.0}
    tot = 0
    for c in C:
        t = triangulation(c["id"])
        tot += t["independent_origins"]
        if t["supports"] + t["contradicts"] + t["context"] == 0:
            rep["unlinked"] += 1
        if c.get("status") == "established" and (t["independent_origins"] < 2 or t["types_count"] < 2):
            rep["weak_established"] += 1
        if c.get("status") == "established" and t["press_only"]:
            rep["press_only_core"] += 1
    rep["independent_avg"] = round(tot / len(C), 2) if C else 0.0
    return rep


def interviews_without_consent(pid: str, field: str) -> list[str]:
    out = []
    for i in db.rows("SELECT id FROM interviews WHERE project_id=?", (pid,)):
        ok = db.one(f"SELECT 1 FROM permissions WHERE subject_table='interviews' AND subject_id=? AND {field}=1 "
                    "AND (withdrawn IS NULL OR withdrawn=0)", (i["id"],))
        if not ok:
            out.append(i["id"])
    return out


def claim_card(user: dict, claim_id: str) -> dict:
    c = db.get(user, "claims", claim_id)
    L = links(claim_id)
    for l in L:
        tgt = db.get_raw(l["target_table"], l["target_id"]) if l.get("target_table") in E else None
        l["target_title"] = (tgt or {}).get("title") or (tgt or {}).get("name") or (tgt or {}).get("term") or l.get("target_id")
        l["level"] = _source_level(l)
    return {"claim": c, "links": L, "triangulation": triangulation(claim_id), "suggested_status": suggest_status(claim_id)}


def consent_gaps(pid: str) -> dict:
    """ما لا يجوز نشره بعد: مقابلات بلا موافقة نشر، وصور بلا موافقة، وأصول تحمل إحداثيات، وموافقات مسحوبة."""
    import json as _json
    imgs = []
    for i in db.rows("SELECT id FROM images WHERE project_id=?", (pid,)):
        if not db.one("SELECT 1 FROM permissions WHERE subject_table='images' AND subject_id=? AND consent_publication=1 "
                      "AND (withdrawn IS NULL OR withdrawn=0)", (i["id"],)):
            imgs.append(i["id"])
    gps = [a["id"] for a in db.rows("SELECT id, technical FROM assets WHERE project_id=?", (pid,))
           if _json.loads(a.get("technical") or "{}").get("gps")]
    withdrawn = [r["subject_id"] for r in db.rows("SELECT subject_id FROM permissions WHERE project_id=? AND withdrawn=1", (pid,))]
    return {"interviews_no_publication": interviews_without_consent(pid, "consent_publication"),
            "images_no_publication": imgs, "assets_with_location": gps, "withdrawn": withdrawn}
