"""يولّد مهارات Claude Code القابلة للاستدعاء (.claude/skills/<slug>/SKILL.md) من سجل المهارات وبطاقات الوكلاء.

بهذا تصير الأوامر «ابحث تراثياً» و«فرغ مقابلة»… مهارات فعلية في Claude Code داخل هذا المستودع.
"""
from __future__ import annotations
from pathlib import Path

from . import agents as AG

ROOT = Path(__file__).parent.parent


def render(sk: dict) -> str:
    leads = [AG.card(a) for a in sk["agents"]]
    lines = [
        "---",
        f"name: {sk['slug']}",
        f"description: استدعِ هذه المهارة عند الأمر «{sk['command']}» أو ما في معناه. {sk['purpose']} "
        "تعمل ضمن «إدارة الدراسات والبحوث التراثية الإماراتية» بانضباط صفر تلفيق والإحالة إلى الأرشيف.",
        "---", "",
        f"# «{sk['command']}» — {sk['id']}", "",
        sk["purpose"], "",
        "## الوكيل القائد", "",
    ]
    for a in leads:
        lines.append(f"- **{a['id']} — {a['name_ar']}** ({a['name_en']}): {a['mission']}")
    lines += ["", "## المدخلات", "", *[f"- {i}" for i in sk["inputs"]], "",
              "## الإجراءات", "", *[f"{i}. {s}" for i, s in enumerate(sk["steps"], 1)], "",
              "## المخرجات الإلزامية", "", *[f"- {o}" for o in sk["outputs"]], "",
              "## القواعد الحاكمة", "", AG.CONSTITUTION, "",
              "## موجه النظام للوكيل القائد", "", leads[0]["system_prompt"], "",
              "## الأرشيف", "",
              "إن كانت لوحة «تراث» تعمل، فاعمل على سجلاتها بمعرّفاتها؛ وإلا فاقرأ `pilot/` و`docs/` في هذا المستودع. "
              "لا تُنشئ سجلاً لم يُتحقق منه، ولا تعلن تنفيذ ما لم يُنفذ.", ""]
    return "\n".join(lines)


def generate() -> list[Path]:
    out = []
    for sk in AG.skills():
        d = ROOT / ".claude" / "skills" / sk["slug"]
        d.mkdir(parents=True, exist_ok=True)
        p = d / "SKILL.md"
        p.write_text(render(sk), encoding="utf-8")
        out.append(p)
    return out
