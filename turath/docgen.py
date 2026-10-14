"""توليد الوثائق المرجعية من الشيفرة نفسها، فلا تنفصل الوثيقة عن التنفيذ:
docs/03-database-schema.md · docs/17-agent-cards.md · docs/18-skills.md
"""
from __future__ import annotations
from pathlib import Path

from . import agents as AG
from . import entities as EN
from . import lifecycle as LC

ROOT = Path(__file__).parent.parent
TYPE_AR = {"text": "نص", "long": "نص طويل", "int": "عدد صحيح", "real": "عدد عشري", "date": "تاريخ", "bool": "منطقي", "json": "JSON"}


def _t(t: str) -> str:
    if t.startswith("enum:"):
        return "قائمة: " + " · ".join(t[5:].split("|"))
    if t.startswith("ref:"):
        return f"مرجع ← `{t[4:]}`"
    return TYPE_AR.get(t, t)


def schema_md() -> str:
    L = ["# مخطط قاعدة البيانات والأرشيف", "",
         "> **وثيقة مولَّدة آلياً من `turath/entities.py`** (الأمر `turath docs-gen`)؛ فهي مطابقة للتنفيذ حرفاً بحرف. "
         "الحالة: **مُنفَّذ ومختبَر** — SQLite مع وضع WAL، وفهرس بحث FTS5.", "",
         "## المبادئ", "",
         "- **معرّف فريد** لكل سجل بصيغة `بادئة-السنة-تسلسل` (مثل `NAR-2026-0001`)، يُولَّد بعداد ذري.",
         "- **أعمدة مشتركة** في كل جدول معرفي: " + "، ".join(f"`{n}` ({l})" for n, l, _ in EN.COMMON) + ".",
         "- **سجل التغييرات** `change_log`: كل إنشاء وتعديل وحذف وإيداع وانتقال مرحلة يُسجَّل بالفاعل والوقت والقيمة قبل التغيير وبعده؛ "
         "والحذف حذف فعلي تبقى صورته الكاملة السابقة في السجل.",
         "- **الأصل لا يُعدَّل:** الملف يُحفظ في الخزنة بمسار مشتق من بصمته SHA-256، بصلاحية قراءة فقط، ويُعاد حساب البصمة في كل فحص سلامة.",
         "- **الصلاحيات:** المالك، وأعضاء المشروع (مؤلف مشارك أو مطّلع)، والمشاركة الصريحة لسجل بعينه، ومستوى الإتاحة (خاص · ضمن المشروع · مشارَك · عام). "
         "السجل «الخاص» لا يراه إلا مالكه ولو كان ضمن مشروع مشترك.",
         "- **المرحلة لا تتغير بالتحرير:** حقل `projects.stage` لا يتقدم إلا عبر بوابة الجودة (`stage_log`).", "",
         "## الجداول المعرفية", ""]
    for t, v in EN.E.items():
        L += [f"### `{t}` — {v['label']}", "", f"البادئة: `{v['prefix']}` · المجموعة: {v['group']}", "",
              "| الحقل | التسمية | النوع |", "|---|---|---|"]
        L += [f"| `{n}` | {l} | {_t(ty)} |" for n, l, ty in v["fields"]]
        L.append("")
    L += ["## الجداول النظامية", "", "```sql", EN.SYSTEM_TABLES.strip(), "```", "",
          "## العلاقات", "", "```mermaid", "erDiagram"]
    for t, v in EN.E.items():
        for n, _, ty in v["fields"]:
            if ty.startswith("ref:"):
                L.append(f"    {ty[4:]} ||--o{{ {t} : \"{n}\"")
        if t != "projects":
            L.append(f"    projects ||--o{{ {t} : \"project_id\"")
    L += ["    claims ||--o{ evidence_links : \"claim_id\"", "    interviews ||--o{ transcript_segments : \"interview_id\"", "```", "",
          "## القوائم المرجعية", "", "**مستويات المصادر:** " + " · ".join(f"{k}: {v}" for k, v in EN.LEVELS.items()), "",
          "**أنواع الروايات:** " + " · ".join(f"`{k}` {v}" for k, v in EN.NARRATIVE_TYPES.items()), "",
          "**أصناف التثليث:** " + " · ".join(f"`{k}` {v}" for k, v in EN.EVIDENCE_TYPES.items()), "",
          "**النطاقات الجغرافية الثقافية:** " + " · ".join(f"`{k}` {v}" for k, v in EN.REGION_LABELS.items()), ""]
    return "\n".join(L)


def agents_md() -> str:
    L = ["# البطاقات التشغيلية للوكلاء العشرين", "",
         "> **مولَّدة آلياً من `turath/data/agents/`.** كل بطاقة مواصفة تشغيلية كاملة؛ ويُشغَّل الوكيل فعلاً عبر المحرك المتاح "
         "(Claude Code أو واجهة Anthropic)، وإلا أُنتجت حزمة تكليف جاهزة. لا يُدّعى تشغيل لم يحدث.", "",
         "| المعرّف | الوكيل | الوحدة | المراحل |", "|---|---|---|---|"]
    A = AG.cards()
    L += [f"| {a['id']} | {a['name_ar']} — {a['name_en']} | {a['unit']} | {' '.join(a.get('stages', []))} |" for a in A]
    for a in A:
        L += ["", f"## {a['id']} — {a['name_ar']}", f"*{a['name_en']}* · {a['unit']}", "", f"**المهمة:** {a['mission']}", "",
              "### موجه النظام", "", "```text", a["system_prompt"], "```", ""]
        for key, title in (("competence", "الاختصاص"), ("permissions", "الصلاحيات"), ("prohibitions", "المحظورات"), ("inputs", "المدخلات المقبولة"),
                           ("outputs", "المخرجات الإلزامية"), ("kpis", "مقاييس الأداء والجودة"), ("human_intervention", "حالات التدخل البشري"),
                           ("coordination", "التنسيق مع الوكلاء")):
            L += [f"### {title}", "", *[f"- {x}" for x in a.get(key, [])], ""]
        L += ["### الأدوات", "", *[f"- `{x['tool']}` — {x['use']}" for x in a.get("tools_allowed", [])], "",
              "### البيانات", "", f"- قراءة: {'، '.join(f'`{t}`' for t in a['data_store']['read'])}",
              f"- كتابة: {'، '.join(f'`{t}`' for t in a['data_store']['write']) or '—'}", "",
              "### المهارات", "", "، ".join(a.get("skills", [])) or "—", "",
              "### إجراءات العمل", "", *[f"{i}. {s}" for i, s in enumerate(a.get("sop", []), 1)], "",
              "### التسليم", "", f"- يستلم من: {'، '.join(a['handoff']['receives_from'])}", f"- يسلّم إلى: {'، '.join(a['handoff']['delivers_to'])}",
              *[f"- {x}" for x in a["handoff"].get("package", [])], f"- معيار القبول: {a['handoff'].get('acceptance', '')}", ""]
    return "\n".join(L)


def skills_md() -> str:
    L = ["# المهارات الأربع عشرة ومصفوفة الأوامر", "",
         "> **مولَّدة آلياً من `turath/data/skills.json`.** كل مهارة متاحة في اللوحة (المهارات والأوامر)، ومهارةً قابلة للاستدعاء في Claude Code "
         "داخل المستودع (`.claude/skills/<slug>/SKILL.md`).", "",
         "| الأمر | المعرّف | الوكلاء | المرحلة | مهارة Claude Code |", "|---|---|---|---|---|"]
    stages = dict((s[0], s[1]) for s in LC.STAGES)
    S = AG.skills()
    L += [f"| «{s['command']}» | {s['id']} | {'، '.join(s['agents'])} | {s['stage']} {stages.get(s['stage'], '')} | `{s['slug']}` |" for s in S]
    for s in S:
        L += ["", f"## «{s['command']}» — {s['id']}", "", s["purpose"], "", "**المدخلات:**", *[f"- {x}" for x in s["inputs"]], "",
              "**الإجراءات:**", *[f"{i}. {x}" for i, x in enumerate(s["steps"], 1)], "", "**المخرجات:**", *[f"- {x}" for x in s["outputs"]]]
    return "\n".join(L) + "\n"


def generate() -> list[Path]:
    out = []
    for name, fn in (("03-database-schema.md", schema_md), ("17-agent-cards.md", agents_md), ("18-skills.md", skills_md)):
        p = ROOT / "docs" / name
        p.write_text(fn(), encoding="utf-8")
        out.append(p)
    return out
