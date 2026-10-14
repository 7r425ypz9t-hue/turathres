"""لوحة القيادة: المؤشرات الاثنا عشر محسوبة من البيانات الفعلية.

لا تُعتمد مستهدفات رقمية نهائية قبل تأسيس خط أساس تجريبي: كل مؤشر يُعرض بقيمته الحالية،
ويُحفظ أول قياس بعد «تثبيت خط الأساس» بقرار بشري، ثم تُقارن القيم اللاحقة به.
"""
from __future__ import annotations
import json

from . import db
from . import evidence as EV
from . import oral_lab
from .entities import REGION_LABELS

DEFS = [
    ("provenance", "نسبة الملفات ذات المصدر المعروف", "%", "archive"),
    ("metadata", "نسبة الملفات المكتملة بياناتها الوصفية", "%", "database"),
    ("transcripts", "نسبة التفريغات المعتمدة بشرياً", "%", "mic"),
    ("witnesses", "متوسط الشهادات المستقلة لكل ادعاء", "", "people"),
    ("consents", "نسبة المواد ذات الموافقات المكتملة", "%", "handshake"),
    ("dialect_err", "معدل أخطاء التفريغ اللهجي بعد التدقيق", "%", "ear"),
    ("claims_linked", "نسبة الادعاءات المرتبطة بأدلة", "%", "link"),
    ("conflicts_open", "عدد التعارضات غير المحسومة", "", "alert"),
    ("integrity", "سلامة الأصول الرقمية", "%", "shield"),
    ("peer_passed", "نسبة المخرجات المجتازة للتحكيم", "%", "gate"),
    ("elements", "عدد عناصر التراث الموثقة", "", "star"),
    ("diversity", "تنوع المناطق والفئات الممثلة", "/6", "map"),
]


def _pct(a, b):
    return round(100 * a / b, 1) if b else None


def compute(pid: str | None = None) -> dict:
    w, args = ("WHERE project_id=?", (pid,)) if pid else ("", ())
    A = db.rows(f"SELECT * FROM assets {w}", args)
    n = len(A)
    prov = sum(1 for a in A if a.get("provenance") and a.get("rights"))
    meta_ok = 0
    for a in A:
        linked = any(db.one(f"SELECT 1 FROM {t} WHERE asset_id=?", (a["id"],)) for t in
                     ("audio_assets", "video_assets", "images", "manuscripts", "historical_documents", "interviews", "sources"))
        if linked and a.get("provenance") and a.get("rights") and a.get("depositor"):
            meta_ok += 1
    IV = db.rows(f"SELECT * FROM interviews {w}", args)
    approved = sum(1 for i in IV if i.get("transcript_status") in ("native_reviewed", "approved"))
    transcribed = sum(1 for i in IV if i.get("transcript_status") not in (None, "none"))
    rep = EV.claims_report(pid)
    subjects = IV + db.rows(f"SELECT id FROM images {w}", args)
    consented = 0
    for s in subjects:
        tbl = "interviews" if s in IV else "images"
        if db.one("SELECT 1 FROM permissions WHERE subject_table=? AND subject_id=? AND (withdrawn IS NULL OR withdrawn=0)", (tbl, s["id"])):
            consented += 1
    conf = db.one(f"SELECT COUNT(*) n FROM conflicts {w + (' AND' if w else 'WHERE')} status='open'", args)["n"]
    integ = sum(1 for a in A if a.get("integrity") == "ok")
    P = db.rows(f"SELECT * FROM publications {w}", args)
    reviewed = [p for p in P if p.get("peer_review") in ("passed", "failed")]
    elements = db.one(f"SELECT COUNT(*) n FROM heritage_practices {w}", args)["n"] + db.one(f"SELECT COUNT(*) n FROM crafts {w}", args)["n"]
    regions = set()
    for t in ("narrators", "heritage_practices", "crafts", "places", "dialect_lexicon"):
        regions |= {r["region"] for r in db.rows(f"SELECT region FROM {t} {w}", args) if r.get("region")}
    vals = {
        "provenance": _pct(prov, n), "metadata": _pct(meta_ok, n), "transcripts": _pct(approved, transcribed),
        "witnesses": rep["independent_avg"] if rep["total"] else None, "consents": _pct(consented, len(subjects)),
        "dialect_err": oral_lab.dialect_error_rate(pid), "claims_linked": _pct(rep["total"] - rep["unlinked"], rep["total"]),
        "conflicts_open": conf, "integrity": _pct(integ, n), "peer_passed": _pct(sum(1 for p in reviewed if p["peer_review"] == "passed"), len(reviewed)),
        "elements": elements, "diversity": len(regions),
    }
    base = baseline()
    out = []
    for key, label, unit, icon in DEFS:
        out.append({"key": key, "label": label, "unit": unit, "icon": icon, "value": vals[key],
                    "baseline": (base or {}).get("values", {}).get(key)})
    return {"indicators": out, "baseline_set": bool(base), "baseline_at": (base or {}).get("at"),
            "regions": sorted(REGION_LABELS[r] for r in regions if r in REGION_LABELS),
            "counts": {"assets": n, "interviews": len(IV), "claims": rep["total"], "publications": len(P)}}


def baseline() -> dict | None:
    r = db.one("SELECT v FROM meta WHERE k='kpi_baseline'")
    return json.loads(r["v"]) if r else None


def set_baseline(user: dict) -> dict:
    if user.get("role") not in ("director", "admin"):
        raise db.Denied("تثبيت خط الأساس قرار بشري للمدير")
    vals = {i["key"]: i["value"] for i in compute()["indicators"]}
    b = {"at": db.now(), "by": user["id"], "values": vals}
    db.conn().execute("INSERT OR REPLACE INTO meta(k,v) VALUES('kpi_baseline',?)", (json.dumps(b, ensure_ascii=False),))
    db.log(user["id"], "baseline", "kpis", "baseline", None, b)
    db.conn().commit()
    return b
