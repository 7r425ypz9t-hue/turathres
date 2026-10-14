"""الوكلاء العشرون والمهارات الأربع عشرة: تحميل البطاقات، وبناء حزمة التكليف، والتشغيل عبر المحرك المتاح فعلاً.

المحركات:
  manual       — تُنتَج حزمة التكليف لتُلصق في Claude يدوياً (متاح دائماً).
  claude_code  — يُستدعى برنامج Claude Code المثبت على الجهاز (claude -p) إن وُجد.
  api          — واجهة Anthropic عند وجود ANTHROPIC_API_KEY.
لا يُدّعى تشغيل وكيل لم يُنفَّذ: كل تشغيل يُسجل في agent_runs بمحركه وحالته، ومخرجه مسودة حتى المراجعة.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from . import db
from . import sanitize
from .config import CFG

DATA = Path(__file__).parent / "data"
API_MODEL = os.environ.get("TURATH_MODEL", "claude-opus-5-5")

CONSTITUTION = """دستور الإدارة (يسبق كل تكليف):
1. صفر تلفيق: لا مراجع ولا وثائق ولا أسماء رواة ولا مقابلات ولا أرقام صفحات ولا DOI مختلقة. المجهول يُكتب «يُستكمل».
2. الأرشيف الموثق هو المرجع، لا ذاكرة النموذج: استشهد بمعرّفات السجلات المرفقة (SRC-… · INT-… · DOC-…) وحدها.
3. ميّز صراحة بين: بيانات مقاسة · رواية · استنتاج · فرضية · نموذج تفسيري.
4. لا تستبدل اللفظ المحلي بالفصحى في أي نص حرفي، ولا تخمّن المقطع غير المفهوم.
5. لا تعمم خصائص منطقة على المجتمع الإماراتي كله، ولا تُسقط مفاهيم معاصرة على الماضي.
6. كل مادة مولدة أو تخيلية توسم «إعادة بناء تصورية».
7. افصل بين ما صُمِّم وما نُفِّذ فعلاً. القرار النهائي والاعتماد للمراجع البشري المخوّل.
8. اكتب بعربية فصحى رصينة بسجلّ أكاديمي، بلا حشو ولا عبارات تسويقية.
قواعد اللغة البشرية المحكمة:
""" + "\n".join(f"- {r}" for r in sanitize.RULES)


def cards() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "agents").glob("AG-*.json"))]


def card(aid: str) -> dict:
    p = DATA / "agents" / f"{aid}.json"
    if not p.exists():
        raise KeyError(aid)
    return json.loads(p.read_text(encoding="utf-8"))


def skills() -> list[dict]:
    p = DATA / "skills.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def skill(sid: str) -> dict:
    for s in skills():
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def engines() -> dict:
    return {"manual": {"available": True, "label": "يدوي — نسخ الحزمة إلى Claude"},
            "claude_code": {"available": bool(shutil.which("claude")), "label": "Claude Code على هذا الجهاز"},
            "api": {"available": bool(os.environ.get("ANTHROPIC_API_KEY")), "label": f"واجهة Anthropic ({API_MODEL})"}}


def _context(user: dict, agent: dict, project_id: str | None) -> str:
    """لقطة من الأرشيف في حدود جداول القراءة المسموحة للوكيل وصلاحيات المستخدم."""
    if not project_id:
        return "لا مشروع محدد: اعمل على المدخلات المرفقة في التكليف وحدها."
    from . import entities as EN
    p = db.get(user, "projects", project_id)
    lines = [f"المشروع {p['id']}: {p.get('title')}", f"المرحلة: {p.get('stage')} · المجال: {p.get('domain') or '—'}",
             f"السؤال البحثي: {p.get('question') or '—'}", f"الفجوة: {p.get('gap') or '—'}"]
    allowed = set(agent.get("data_store", {}).get("read", []))
    for t in ("sources", "claims", "conflicts", "interviews", "oral_narratives", "dialect_lexicon", "crafts",
              "heritage_practices", "places", "historical_documents", "manuscripts", "legislation", "poems", "images"):
        if t not in allowed:
            continue
        R = db.list_rows(user, t, project_id, limit=80)
        if not R:
            continue
        lines.append(f"\n## {EN.E[t]['label']} ({len(R)})")
        for r in R:
            extra = ""
            if t == "sources":
                extra = f" · المستوى {r.get('level')} · {r.get('creator') or ''} {r.get('year') or ''} · {r.get('url') or ''}"
            elif t == "claims":
                extra = f" · الحالة {r.get('status')} · الطبيعة {r.get('kind')}"
            lines.append(f"- {r['id']}: {EN.title_of(t, r)}{extra}")
    return "\n".join(lines)


def package(user: dict, agent_id: str, task: str, project_id: str | None = None, skill_id: str | None = None) -> str:
    a = card(agent_id)
    sk = skill(skill_id) if skill_id else None
    parts = [CONSTITUTION, "", "## موجه النظام للوكيل", a["system_prompt"]]
    if sk:
        parts += ["", f"## المهارة: «{sk['command']}» ({sk['id']})", sk.get("purpose", ""), "الخطوات:",
                  *[f"{i}. {s}" for i, s in enumerate(sk.get("steps", []), 1)], "المخرجات الإلزامية:",
                  *[f"- {o}" for o in sk.get("outputs", [])]]
    parts += ["", "## المخرجات الإلزامية للوكيل", *[f"- {o}" for o in a.get("outputs", [])],
              "", "## حالات التصعيد إلى الإنسان", *[f"- {o}" for o in a.get("human_intervention", [])],
              "", "## سياق الأرشيف (في حدود صلاحيات الوكيل)", _context(user, a, project_id),
              "", "## التكليف", task.strip(),
              "", "## صيغة التسليم", "سلّم بالعربية: (1) المخرج، (2) جدول الادعاءات بمعرّفات أدلتها، (3) ما بقي معلقاً، "
              f"(4) حزمة التسليم إلى: {', '.join(a.get('handoff', {}).get('delivers_to', []))}."]
    return "\n".join(parts)


def _call_api(system: str, prompt: str) -> str:
    body = json.dumps({"model": API_MODEL, "max_tokens": 8000, "system": system,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read())
    return "".join(b.get("text", "") for b in d.get("content", []))


def _call_claude_code(prompt: str) -> str:
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    r = subprocess.run(["claude", "-p", "--output-format", "text"], input=prompt, capture_output=True, text=True,
                       timeout=1800, encoding="utf-8", **kw)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:500] or "تعذر تشغيل Claude Code")
    return r.stdout


def run(user: dict, agent_id: str, task: str, project_id: str | None = None, skill_id: str | None = None,
        engine: str | None = None) -> dict:
    engine = engine or CFG.engine
    E = engines()
    if engine not in E or not E[engine]["available"]:
        engine = "manual"
    prompt = package(user, agent_id, task, project_id, skill_id)
    rid = db.next_id("RUN")
    status, output = "package", ""
    try:
        if engine == "api":
            output, status = _call_api(card(agent_id)["system_prompt"], prompt), "draft"
        elif engine == "claude_code":
            output, status = _call_claude_code(prompt), "draft"
    except Exception as e:
        status, output = "failed", f"تعذر التشغيل: {e}"
    db.conn().execute("INSERT INTO agent_runs(id,agent_id,skill_id,project_id,user_id,engine,task,prompt,output,status,created_at) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?,?)", (rid, agent_id, skill_id, project_id, user["id"], engine, task, prompt,
                                                         output, status, db.now()))
    db.log(user["id"], "agent_run", "agent_runs", rid, None, {"agent": agent_id, "engine": engine, "status": status})
    db.conn().commit()
    return {"id": rid, "engine": engine, "status": status, "prompt": prompt, "output": output}


def run_detail(user: dict, rid: str) -> dict | None:
    """التكليف مع نسخة قراءة منقّاة وتقرير اللغة البشرية؛ ويبقى الأصل محفوظاً كما ورد."""
    r = db.one("SELECT * FROM agent_runs WHERE id=? AND user_id=?", (rid, user["id"]))
    if r and r.get("output") and r["status"] == "draft":
        r["output_clean"], r["clean_report"] = sanitize.clean(r["output"])
        r["humanlang"] = sanitize.humanlang_report(r["output"])
    return r


def runs(user: dict, project_id: str | None = None) -> list[dict]:
    sql, args = "SELECT id,agent_id,skill_id,project_id,engine,task,status,created_at,reviewed FROM agent_runs WHERE user_id=?", [user["id"]]
    if project_id:
        sql += " AND project_id=?"
        args.append(project_id)
    return db.rows(sql + " ORDER BY created_at DESC LIMIT 100", args)
