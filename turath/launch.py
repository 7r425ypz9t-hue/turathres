"""نقطة تشغيل الأيقونة: `pythonw -m turath.launch`.

تعمل بلا نافذة طرفية، فلا يُرى أي خطأ؛ لذلك:
- تُكتب الرسائل والأخطاء كاملة في ~/Turath/turath.log.
- وأي خطأ يمنع التشغيل يظهر في نافذة رسالة واضحة بالسبب وموضع السجل، ولا يمر صامتاً.
"""
from __future__ import annotations
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path


def _log_path() -> Path:
    home = Path(os.environ.get("TURATH_HOME") or Path.home() / "Turath")
    home.mkdir(parents=True, exist_ok=True)
    return home / "turath.log"


def _alert(title: str, text: str) -> None:
    """نافذة رسالة أصلية في كل نظام، دون أي مكتبة خارجية."""
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, title, 0x10 | 0x00100000 | 0x00080000)  # خطأ · من اليمين · قراءة من اليمين
        elif sys.platform == "darwin":
            safe = text.replace('"', "'")
            subprocess.run(["osascript", "-e", f'display dialog "{safe}" with title "{title}" buttons {{"حسناً"}} with icon stop'],
                           timeout=300)
        else:
            for tool in (["zenity", "--error", f"--title={title}", f"--text={text}"], ["notify-send", title, text]):
                try:
                    subprocess.run(tool, timeout=300)
                    break
                except FileNotFoundError:
                    continue
    except Exception:
        pass


def main() -> None:
    log = _log_path()
    f = open(log, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None or not sys.stdout.isatty():
        sys.stdout = f
    if sys.stderr is None or not sys.stderr.isatty():
        sys.stderr = f
    print(f"\n=== تشغيل {datetime.now().isoformat(timespec='seconds')} · Python {sys.version.split()[0]} · {sys.executable}")
    try:
        os.chdir(Path(__file__).resolve().parent.parent)
        from .cli import main as cli_main
        cli_main(["serve"])
    except SystemExit as e:
        if e.code not in (0, None):
            msg = str(e.code)
            print("توقف:", msg)
            _alert("تراث — تعذّر التشغيل", f"{msg}\n\nالسجل: {log}")
    except Exception as e:
        traceback.print_exc()
        _alert("تراث — تعذّر التشغيل",
               f"حدث خطأ منع فتح اللوحة:\n{type(e).__name__}: {e}\n\nالتفاصيل في السجل:\n{log}\n\n"
               "للتشخيص: python -m turath doctor")


if __name__ == "__main__":
    main()
