"""المختبر السمعي واللغوي للتاريخ الشفهي — دورة المعالجة ذات الاثنتي عشرة خطوة، والتفريغ بطوابع زمنية.

قاعدة إلزامية: لا تُستبدل الكلمات المحلية بالفصحى داخل التفريغ الحرفي؛ تُحفظ كما نطقها الراوي.
المقاطع غير المفهومة تُعلَّم «[غير مفهوم]» دون تخمين.
"""
from __future__ import annotations
import re
import shutil

from . import db
from . import vault

STEPS = [
    (1, "تسجيل مصدر الملف وصاحبه وحقوق استخدامه", "AG-ARC", "auto"),
    (2, "إنشاء بصمة رقمية للتحقق من سلامة الأصل", "AG-ARC", "auto"),
    (3, "حفظ نسخة أصلية لا تُعدَّل", "AG-ARC", "auto"),
    (4, "التعرف على المتحدثين وفصل المقاطع عند الإمكان", "AG-TRN", "manual"),
    (5, "تفريغ الكلام تفريغاً حرفياً مع الطوابع الزمنية", "AG-TRN", "manual"),
    (6, "تمييز ألفاظ اللهجة والمفردات المحلية", "AG-DIA", "manual"),
    (7, "استخراج الأسماء والأماكن والتواريخ والوقائع", "AG-ORL", "manual"),
    (8, "تمييز المقاطع غير المفهومة دون تخمين", "AG-TRN", "manual"),
    (9, "إعداد نسخة لغوية مقروءة إلى جانب الحرفية", "AG-DIA", "manual"),
    (10, "مراجعة بشرية مع متحدث محلي مؤهل", "HUM-NATIVE", "human"),
    (11, "ربط كل معلومة بالتسجيل وموضعها الزمني", "AG-ORL", "manual"),
    (12, "مراجعة أحكام الخصوصية والموافقة قبل النشر", "AG-ETH", "manual"),
]
UNCLEAR = "[غير مفهوم]"
TS = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(?:[-–]\s*\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?)?\s*(?:([^:：]{1,30})[:：])?\s*(.*)$")


def asr_available() -> dict:
    """التفريغ الآلي أداة مشروطة: لا يُدَّعى توفره إلا إذا وُجدت المكتبة فعلاً."""
    try:
        import faster_whisper  # noqa: F401
        return {"available": True, "engine": "faster-whisper"}
    except Exception:
        return {"available": False, "engine": None, "hint": "pip install faster-whisper — ثم يتاح زر «تفريغ أولي آلي» (يبقى مسودة حتى المراجعة البشرية)"}


def status(interview_id: str) -> list[dict]:
    done = {r["step"]: r for r in db.rows("SELECT * FROM lab_steps WHERE interview_id=?", (interview_id,))}
    iv = db.get_raw("interviews", interview_id) or {}
    out = []
    for n, label, actor, mode in STEPS:
        d = done.get(n)
        ok = bool(d and d["done"])
        if mode == "auto" and iv.get("asset_id"):
            ok = True
        out.append({"step": n, "label": label, "actor": actor, "mode": mode, "done": ok,
                    "by": d and d["by_user"], "at": d and d["at"], "note": d and d["note"]})
    return out


def mark(user: dict, interview_id: str, step: int, done: bool, note: str = "") -> list[dict]:
    iv = db.get(user, "interviews", interview_id)
    if not db.can_write(user, "interviews", iv):
        raise db.Denied("لا صلاحية")
    if step == 10 and done and user.get("role") not in ("native_reviewer", "director", "admin", "researcher"):
        raise db.Denied("المراجعة البشرية تُسجَّل بحساب بشري")
    with db.WRITE_LOCK:
        db.conn().execute("INSERT OR REPLACE INTO lab_steps(interview_id,step,done,by_user,at,note) VALUES(?,?,?,?,?,?)",
                          (interview_id, step, 1 if done else 0, user["id"], db.now(), note))
        st = status(interview_id)
        stage = max([s["step"] for s in st if s["done"]] or [0])
        db.conn().execute("UPDATE interviews SET lab_stage=? WHERE id=?", (stage, interview_id))
        if step == 10 and done:
            db.conn().execute("UPDATE interviews SET transcript_status='native_reviewed' WHERE id=?", (interview_id,))
        db.log(user["id"], "lab_step", "interviews", interview_id, None, {"step": step, "done": done, "note": note})
        db.conn().commit()
    return status(interview_id)


def parse_transcript(text: str) -> list[dict]:
    """يحوّل نصاً مفرغاً إلى مقاطع. الصيغة: «[00:01:12] الراوي: النص» أو «00:01:12 - 00:01:30 م1: النص»."""
    segs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = TS.match(line)
        if m and m.group(1):
            start, end, spk, body = m.groups()
            segs.append({"start": start, "end": end or "", "speaker": (spk or "").strip(), "verbatim": body.strip()})
        elif segs:
            segs[-1]["verbatim"] += "\n" + line
        else:
            segs.append({"start": "", "end": "", "speaker": "", "verbatim": line})
    for s in segs:
        s["unclear"] = s["verbatim"].count(UNCLEAR) + s["verbatim"].count("[؟]")
    return segs


def save_transcript(user: dict, interview_id: str, text: str, readable: str = "") -> dict:
    iv = db.get(user, "interviews", interview_id)
    if not db.can_write(user, "interviews", iv):
        raise db.Denied("لا صلاحية")
    segs = parse_transcript(text)
    rsegs = parse_transcript(readable) if readable.strip() else []
    with db.WRITE_LOCK:
        old = db.rows("SELECT verbatim FROM transcript_segments WHERE interview_id=? ORDER BY seq", (interview_id,))
        db.conn().execute("DELETE FROM transcript_segments WHERE interview_id=?", (interview_id,))
        for i, s in enumerate(segs):
            corr = 0
            if i < len(old) and old[i]["verbatim"] != s["verbatim"]:
                corr = 1
            db.conn().execute(
                "INSERT INTO transcript_segments(id,interview_id,seq,start,end,speaker,verbatim,readable,unclear,owner_id,project_id,created_at,updated_at,corrections)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"{interview_id}-S{i + 1:04d}", interview_id, i + 1, s["start"], s["end"], s["speaker"], s["verbatim"],
                 rsegs[i]["verbatim"] if i < len(rsegs) else None, s["unclear"], user["id"], iv.get("project_id"), db.now(), db.now(), corr))
        if iv.get("transcript_status") in (None, "none"):
            db.conn().execute("UPDATE interviews SET transcript_status='draft' WHERE id=?", (interview_id,))
        db.log(user["id"], "transcript", "interviews", interview_id, {"segments": len(old)}, {"segments": len(segs)})
        db.conn().commit()
    body = " ".join(s["verbatim"] for s in segs)
    db.conn().execute("DELETE FROM search_index WHERE item_table='transcript' AND item_id=?", (interview_id,))
    db.conn().execute("INSERT INTO search_index(item_table,item_id,project_id,title,body) VALUES('transcript',?,?,?,?)",
                      (interview_id, iv.get("project_id"), f"تفريغ {iv.get('archive_code') or interview_id}", body))
    db.conn().commit()
    return {"segments": len(segs), "unclear": sum(s["unclear"] for s in segs)}


def transcript(user: dict, interview_id: str) -> list[dict]:
    db.get(user, "interviews", interview_id)
    return db.rows("SELECT * FROM transcript_segments WHERE interview_id=? ORDER BY seq", (interview_id,))


def to_srt(segs: list[dict]) -> str:
    def t(x):
        if not x:
            return "00:00:00,000"
        p = x.split(":")
        p = ["0"] * (3 - len(p)) + p
        return f"{int(p[0]):02d}:{int(p[1]):02d}:{int(p[2]):02d},000"
    out = []
    for i, s in enumerate(segs, 1):
        end = s.get("end") or (segs[i]["start"] if i < len(segs) and segs[i].get("start") else s.get("start"))
        out.append(f"{i}\n{t(s.get('start'))} --> {t(end)}\n{(s.get('speaker') + ': ') if s.get('speaker') else ''}{s['verbatim']}\n")
    return "\n".join(out)


def auto_transcribe(user: dict, interview_id: str) -> dict:
    """تفريغ أولي آلي (مسودة) عند توفر faster-whisper فقط؛ يبقى مسودة حتى المراجعة البشرية."""
    if not asr_available()["available"]:
        raise RuntimeError("التفريغ الآلي غير متاح على هذا الجهاز: " + asr_available()["hint"])
    iv = db.get(user, "interviews", interview_id)
    a = db.one("SELECT * FROM assets WHERE id=?", (iv.get("asset_id"),))
    if not a:
        raise RuntimeError("لا ملف صوتي مرتبط بالمقابلة")
    from faster_whisper import WhisperModel
    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(str(vault.path_of(a)), language="ar")

    def hms(x):
        x = int(x)
        return f"{x // 3600:02d}:{x % 3600 // 60:02d}:{x % 60:02d}"
    text = "\n".join(f"[{hms(s.start)}] - [{hms(s.end)}] {s.text.strip()}" for s in segments)
    return save_transcript(user, interview_id, text) | {"engine": "faster-whisper", "note": "مسودة آلية — تلزم المراجعة البشرية"}


def dialect_error_rate(pid: str | None = None) -> float | None:
    """معدل أخطاء التفريغ اللهجي بعد التدقيق = المقاطع المصححة ÷ مقاطع المقابلات المراجَعة."""
    sql = ("SELECT SUM(t.corrections) c, COUNT(*) n FROM transcript_segments t JOIN interviews i ON i.id=t.interview_id "
           "WHERE i.transcript_status IN ('native_reviewed','approved')")
    args = ()
    if pid:
        sql += " AND i.project_id=?"
        args = (pid,)
    r = db.one(sql, args)
    return round(100 * (r["c"] or 0) / r["n"], 1) if r and r["n"] else None


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffprobe"))
