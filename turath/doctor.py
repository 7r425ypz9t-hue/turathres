"""`turath doctor` — تشخيص التشغيل خطوة خطوة، بلغة يفهمها غير المختص، مع ما يلزم فعله عند كل خلل."""
from __future__ import annotations
import os
import socket
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .config import CFG, MODES

OK, BAD, WARN = "✔", "✖", "!"


def _line(mark: str, text: str, fix: str = "") -> None:
    print(f"  {mark} {text}")
    if fix:
        print(f"      ← {fix}")


def report() -> bool:
    from . import desktop
    healthy = True
    print(f"\n  تشخيص «تراث» {__version__}\n")

    v = sys.version_info
    if v >= (3, 10):
        _line(OK, f"Python {v.major}.{v.minor}.{v.micro} — {sys.executable}")
    else:
        healthy = False
        _line(BAD, f"Python {v.major}.{v.minor} أقدم من المطلوب", "ثبّتوا Python 3.10 أو أحدث من python.org ثم أعيدوا التثبيت")

    pkg = Path(__file__).parent
    missing = [p for p in ("static/index.html", "static/app.js", "static/app.css", "static/img/logo-turath.svg", "data/skills.json")
               if not (pkg / p).exists()]
    if missing:
        healthy = False
        _line(BAD, "ملفات البرنامج ناقصة: " + "، ".join(missing), "أعيدوا تشغيل المثبّت")
    else:
        _line(OK, f"ملفات البرنامج كاملة — {pkg.parent}")

    try:
        CFG.home.mkdir(parents=True, exist_ok=True)
        probe = CFG.home / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        _line(OK, f"مجلد البيانات قابل للكتابة — {CFG.home}")
    except Exception as e:
        healthy = False
        _line(BAD, f"تعذّرت الكتابة في مجلد البيانات {CFG.home}: {e}", "تحققوا من صلاحيات المجلد أو من برامج الحماية")

    if CFG.db_path.exists():
        try:
            c = sqlite3.connect(CFG.db_path)
            res = c.execute("PRAGMA quick_check").fetchone()[0]
            c.close()
            _line(OK if res == "ok" else BAD, f"قاعدة البيانات: {res}")
            healthy &= res == "ok"
        except Exception as e:
            healthy = False
            _line(BAD, f"تعذّر فتح قاعدة البيانات: {e}")
    else:
        _line(WARN, "قاعدة البيانات لم تُنشأ بعد (تُنشأ عند أول تشغيل)")

    _line(OK, f"النمط: {MODES.get(CFG.mode, {}).get('label', CFG.mode)} · المنفذ {CFG.port}")
    live = desktop.running(CFG.port)
    if live:
        same = live.get("build") == desktop.fingerprint()
        _line(OK if same else WARN, "اللوحة تعمل الآن" + ("" if same else " (من نسخة أقدم، وتُستبدل عند النقر على الأيقونة)"),
              "" if same else "")
    else:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", CFG.port))
            _line(OK, f"المنفذ {CFG.port} متاح")
        except OSError:
            healthy = False
            _line(BAD, f"المنفذ {CFG.port} يشغله برنامج آخر", f"python -m turath setup {CFG.mode} --port 8790")
        finally:
            s.close()

    b = desktop._browsers()
    _line(OK if b else WARN, ("نافذة التطبيق: " + b[0]) if b else "لم يُعثر على Edge أو Chrome؛ تُفتح اللوحة في المتصفح الافتراضي")

    icons = [p for p in desktop.icon_paths() if p.exists()]
    if icons:
        _line(OK, "الأيقونة موجودة: " + "، ".join(str(p) for p in icons))
    else:
        _line(WARN, "لا أيقونة على سطح المكتب", "python -m turath install-icon")

    log = CFG.home / "turath.log"
    if log.exists():
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]
        print("\n  آخر سطور السجل:")
        for l in tail:
            print("    " + l)
    print("\n  " + ("✔ لا خلل يمنع التشغيل." if healthy else "✖ يوجد خلل؛ اتبعوا الإرشاد المكتوب بجانبه.") + "\n")
    return healthy
