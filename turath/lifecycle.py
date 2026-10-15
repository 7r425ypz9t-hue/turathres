"""دورة المشروع من التكليف إلى النشر — ست عشرة مرحلة، وبوابة جودة ملزمة عند كل انتقال.

كل بوابة قائمة فحوص تُحسب من البيانات الفعلية؛ لا يتقدم المشروع حتى تجتاز كلها.
بعض البوابات تشترط قرار مراجعة مسجلاً (review_decisions) من الصفة المخولة.
"""
from __future__ import annotations
import json

from . import db
from . import evidence as EV

STAGES = [
    ("S01", "الفكرة البحثية", "AG-DIR"), ("S02", "تحليل المشكلة والفجوة", "AG-PLN"), ("S03", "خطة البحث", "AG-PLN"),
    ("S04", "مراجعة الدراسات", "AG-HIS"), ("S05", "تحديد المصادر", "AG-SRC"), ("S06", "الموافقات والأخلاقيات", "AG-ETH"),
    ("S07", "الجمع الوثائقي والميداني", "AG-FLD"), ("S08", "الفهرسة والتفريغ", "AG-TRN"), ("S09", "نقد المصادر والتثليث", "AG-SRC"),
    ("S10", "التحليل", "AG-DAT"), ("S11", "كتابة النتائج", "AG-PUB"), ("S12", "التحكيم العلمي", "AG-PUB"),
    ("S13", "التدقيق القانوني والحقوقي", "AG-LAW"), ("S14", "الإخراج", "AG-PUB"), ("S15", "الاعتماد البشري", "AG-DIR"),
    ("S16", "النشر والأرشفة", "AG-ARC"),
]
STAGE_IDS = [s[0] for s in STAGES]
HUMAN_ROLES = ("director", "admin")


def _count(table: str, pid: str, where: str = "", args=()) -> int:
    return db.one(f"SELECT COUNT(*) n FROM {table} WHERE project_id=? {where}", (pid, *args))["n"]


def _decision(pid: str, gate: str, human: bool = False) -> bool:
    sql = "SELECT * FROM review_decisions WHERE project_id=? AND gate=? AND decision IN ('approve','approve_with_changes')"
    rs = db.rows(sql, (pid, gate))
    if human:
        rs = [r for r in rs if (r.get("reviewer_role") or "").startswith("HUM")]
    return bool(rs)


def checks(pid: str) -> list[dict]:
    """فحوص البوابة الخارجة من المرحلة الحالية."""
    p = db.get_raw("projects", pid)
    st = p.get("stage") or "S01"
    C = []

    def add(ok, text):
        C.append({"ok": bool(ok), "text": text})

    if st == "S01":
        add(p.get("title"), "عنوان المشروع محدد")
        add(p.get("question"), "السؤال البحثي مصوغ")
        add(p.get("domain"), "المجال التراثي محدد")
    elif st == "S02":
        add(p.get("gap") and len(p["gap"]) >= 40, "الفجوة البحثية موصوفة وصفاً كافياً")
        add(p.get("region") or p.get("emirate"), "النطاق الجغرافي الثقافي محدد دون تعميم")
    elif st == "S03":
        add(p.get("summary"), "خطة البحث مكتوبة في الملخص")
        add(p.get("output_type"), "نوع المخرج المؤسسي محدد")
        add(p.get("lead_agent"), "الوكيل القائد معيّن")
    elif st == "S04":
        n = _count("sources", pid, "AND level IN (1,2,3)")
        add(n >= 3, f"ثلاثة مصادر علمية على الأقل من المستويات 1–3 (الموجود: {n})")
    elif st == "S05":
        add(_count("sources", pid) > 0, "سجل المصادر غير فارغ")
        add(_count("sources", pid, "AND level IS NULL") == 0, "كل مصدر مصنّف في هرم المصادر")
        add(_count("sources", pid, "AND (verified IS NULL OR verified=0)") == 0, "كل مصدر تحقق من وجوده فعلاً")
    elif st == "S06":
        add(_decision(pid, "S06"), "قرار أخلاقيات معتمد (مسؤول الأخلاقيات أو المراجع البشري)")
        miss = EV.interviews_without_consent(pid, "consent_recording")
        add(not miss, "موافقة التسجيل قائمة لكل مقابلة" + (f" — ناقصة: {', '.join(miss[:5])}" if miss else ""))
    elif st == "S07":
        n = _count("sources", pid) + db.one("SELECT COUNT(*) n FROM assets WHERE project_id=?", (pid,))["n"]
        add(n > 0, "جُمعت مواد وثائقية أو ميدانية")
        bad = db.one("SELECT COUNT(*) n FROM assets WHERE project_id=? AND (provenance IS NULL OR provenance='' OR rights IS NULL OR rights='')", (pid,))["n"]
        add(bad == 0, f"كل أصل معروف المصدر والحقوق (الناقص: {bad})")
    elif st == "S08":
        pend = db.one("SELECT COUNT(*) n FROM interviews WHERE project_id=? AND asset_id IS NOT NULL AND "
                      "(transcript_status IS NULL OR transcript_status IN ('none','draft'))", (pid,))["n"]
        add(pend == 0, f"كل تفريغ روجع مع متحدث محلي مؤهل (المعلّق: {pend})")
        miss = EV.interviews_without_consent(pid, "consent_transcription")
        add(not miss, "موافقة التفريغ قائمة لكل مقابلة مفرغة")
    elif st == "S09":
        rep = EV.claims_report(pid)
        add(rep["total"] > 0, "سُجّلت ادعاءات علمية")
        add(rep["unlinked"] == 0, f"كل ادعاء مرتبط بدليل (غير المرتبط: {rep['unlinked']})")
        add(rep["weak_established"] == 0, f"كل ادعاء «مثبت» له صنفان مستقلان من الأدلة على الأقل (المخالف: {rep['weak_established']})")
        add(rep["press_only_core"] == 0, f"لا ادعاء جوهرياً قائماً على صحافة أو مواقع عامة وحدها (المخالف: {rep['press_only_core']})")
    elif st == "S10":
        add(_count("claims", pid, "AND kind IS NULL") == 0, "كل ادعاء مصنف: بيانات مقاسة / رواية / استنتاج / فرضية / نموذج")
        add(_count("conflicts", pid, "AND (analysis IS NULL OR analysis='')") == 0, "كل تعارض محلل في سجل التعارضات دون حذف")
    elif st == "S11":
        add(_count("publications", pid) > 0, "مسودة المخرج مسجلة في المنشورات")
    elif st == "S12":
        add(_count("publications", pid, "AND peer_review='passed'") > 0, "اجتاز المخرج التحكيم العلمي")
        add(_decision(pid, "S12"), "قرار التحكيم مسجل")
    elif st == "S13":
        add(_decision(pid, "S13"), "قرار التدقيق القانوني والحقوقي مسجل")
        miss = EV.interviews_without_consent(pid, "consent_publication")
        add(not miss, "موافقة النشر قائمة لكل مقابلة مستعملة" + (f" — ناقصة: {', '.join(miss[:5])}" if miss else ""))
        g = EV.consent_gaps(pid)
        add(not g["images_no_publication"], "موافقة النشر قائمة لكل صورة في المشروع" +
            (f" — ناقصة: {', '.join(g['images_no_publication'][:5])}" if g["images_no_publication"] else ""))
        w = _count("permissions", pid, "AND withdrawn=1")
        add(w == 0, f"لا موافقات مسحوبة معلّقة — تُحجب المادة أو تُزال أولاً (المعلّق: {w})")
    elif st == "S14":
        add(_count("publications", pid, "AND formats IS NOT NULL AND formats!=''") > 0, "صيغ الإخراج محددة")
    elif st == "S15":
        add(_decision(pid, "S15", human=True), "اعتماد المراجع البشري المخوّل (HUM-DIR) مسجل")
    elif st == "S16":
        add(False, "المرحلة الأخيرة: يُغلق المشروع بعد النشر والأرشفة")
    return C


def advance(user: dict, pid: str) -> dict:
    p = db.get_raw("projects", pid)
    if not p or not db.can_write(user, "projects", p):
        raise db.Denied("لا صلاحية لتحريك المشروع")
    C = checks(pid)
    if not all(c["ok"] for c in C):
        return {"advanced": False, "checks": C, "stage": p["stage"]}
    i = STAGE_IDS.index(p["stage"])
    if i + 1 >= len(STAGE_IDS):
        return {"advanced": False, "checks": C, "stage": p["stage"]}
    nxt = STAGE_IDS[i + 1]
    with db.WRITE_LOCK:
        db.conn().execute("UPDATE projects SET stage=?, updated_at=? WHERE id=?", (nxt, db.now(), pid))
        db.conn().execute("INSERT INTO stage_log(project_id,at,user_id,from_stage,to_stage,gate_report) VALUES(?,?,?,?,?,?)",
                          (pid, db.now(), user["id"], p["stage"], nxt, json.dumps(C, ensure_ascii=False)))
        db.log(user["id"], "advance", "projects", pid, {"stage": p["stage"]}, {"stage": nxt})
        db.conn().commit()
    return {"advanced": True, "checks": C, "stage": nxt}


def record_decision(user: dict, pid: str, gate: str, decision: str, rationale: str, reviewer_role: str) -> dict:
    """قرارات HUM-* لا يسجلها إلا مستخدم بصفة مدير أو مسؤول — الاعتماد البشري لا يُنتحل."""
    if reviewer_role.startswith("HUM-DIR") and user.get("role") not in HUMAN_ROLES:
        raise db.Denied("اعتماد المراجع البشري المخول يقتصر على حساب بصفة «مدير»")
    return db.create(user, "review_decisions", {"project_id": pid, "subject_table": "projects", "subject_id": pid, "gate": gate,
                                                "reviewer": user.get("display_name") or user["username"],
                                                "reviewer_role": reviewer_role, "decision": decision, "rationale": rationale})
