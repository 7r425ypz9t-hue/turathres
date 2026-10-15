"""خط الهوية «أضواء السلف» (adwa-assalaf) — يُثبَّت على جهاز صاحب الإدارة لا في المستودع.

الخط مرخَّص تجارياً، والمستودع عام؛ فلا يُرفع ملفه إلى git ولا يُوزَّع مع البرنامج.
يُودَع الملفان مرة واحدة في مجلد البيانات (~/Turath/fonts) من الإعدادات أو بالأمر `turath fonts install`،
فتقدّمهما اللوحة لنفسها، ويُستعمل الاسم نفسه في ملفات Word والاستمارات.
وإن لم يُثبَّت، عملت الواجهة بخط Noto Naskh Arabic بديلاً.
"""
from __future__ import annotations
import re
from pathlib import Path

from .config import CFG

FAMILY = "adwa-assalaf"            # اسم العائلة كما في جدول أسماء الخط (يعرفه Word وPowerPoint بعد التثبيت)
LATIN = "Noto Naskh Arabic"        # الخط لا يحوي حروفاً لاتينية؛ فاللاتيني والأرقام بهذا الخط
FILES = {"regular": "adwa-assalaf.ttf", "bold": "adwa-assalaf-bold.ttf"}
MAX = 4 * 1024 * 1024


def folder() -> Path:
    return CFG.home / "fonts"


def path(weight: str) -> Path:
    return folder() / FILES[weight]


def status() -> dict:
    return {w: path(w).exists() for w in FILES} | {"family": FAMILY, "folder": str(folder())}


def _weight_of(name: str, data: bytes) -> str:
    """العريض من علامة macStyle في جدول head داخل الخط؛ وإلا فمن اسم الملف."""
    import struct
    try:
        num = struct.unpack(">H", data[4:6])[0]
        for i in range(num):
            tag, _, off, _ = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
            if tag == b"head":
                return "bold" if struct.unpack(">H", data[off + 44:off + 46])[0] & 1 else "regular"
    except struct.error:
        pass
    n = name.lower()
    return "bold" if "bold" in n or n.rsplit(".", 1)[0].endswith(("_b", "-b")) else "regular"


def install(name: str, data: bytes, weight: str | None = None) -> str:
    if len(data) > MAX or len(data) < 1000:
        raise ValueError("حجم ملف الخط غير مقبول")
    if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
        raise ValueError("الملف ليس خط TrueType أو OpenType")
    if FAMILY.encode() not in data and FAMILY.encode("utf-16-be") not in data:
        raise ValueError("هذا ليس خط «أضواء السلف» (adwa-assalaf)")
    weight = weight or _weight_of(name, data)
    folder().mkdir(parents=True, exist_ok=True)
    path(weight).write_bytes(data)
    return weight


def remove() -> None:
    for w in FILES:
        path(w).unlink(missing_ok=True)


# ------------------------------------------------------------ التثبيت في نظام التشغيل
# Word وPowerPoint لا يريان الخط ما دام في مجلد البيانات وحده؛ فيُنسخ إلى مجلد خطوط المستخدم
# (بلا صلاحيات مدير) ويُسجَّل، فتظهر الوثائق والعروض به على هذا الجهاز.

REG_NAMES = {"regular": f"{FAMILY} (TrueType)", "bold": f"{FAMILY} Bold (TrueType)"}


def system_folder() -> Path:
    import os
    import sys
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "Microsoft" / "Windows" / "Fonts"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Fonts"
    return Path.home() / ".local" / "share" / "fonts"


def system_status() -> dict:
    return {w: (system_folder() / FILES[w]).is_file() for w in FILES}


def install_system() -> list[str]:
    """ينسخ ما في مجلد البيانات من ملفَّي الخط إلى خطوط المستخدم في النظام ويسجّلهما. يعيد الأوزان المثبتة."""
    import os
    import shutil
    import subprocess
    done = []
    dest = system_folder()
    for w, name in FILES.items():
        src = path(w)
        if not src.is_file():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(src, dest / name)
        except PermissionError:   # الخط مفتوح في Word أو PowerPoint: النسخة الموجودة صالحة
            if not (dest / name).is_file():
                raise
        if os.name == "nt":
            import winreg
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts") as k:
                winreg.SetValueEx(k, REG_NAMES[w], 0, winreg.REG_SZ, str(dest / name))
        done.append(w)
    if done and os.name == "nt":
        import ctypes   # إشعار البرامج المفتوحة بتغيّر الخطوط (WM_FONTCHANGE)
        for w in done:
            ctypes.windll.gdi32.AddFontResourceW(str(dest / FILES[w]))
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
    elif done and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(dest)], capture_output=True, timeout=60)
    return done


LATIN_RUN = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.:/@#%+\-]*)")


def add_runs(par, text: str, size: float, bold: bool = False, color: str | None = None) -> None:
    """يضيف نصاً إلى فقرة Word من اليمين: العربي بخط الهوية مكبَّراً درجتين، وكل تتابع لاتيني أو رقمي
    في مقطع مستقل بخط Noto Naskh؛ لأن «أضواء السلف» بلا أرقام لاتينية فتتفرق الأرقام إن بقيت في المقطع العربي."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
    for piece in LATIN_RUN.split(text):
        if not piece:
            continue
        latin = bool(LATIN_RUN.fullmatch(piece))
        r = par.add_run(piece)
        r.font.size = Pt(size)
        r.font.bold = bold
        rPr = r._r.get_or_add_rPr()
        fonts_el = rPr.find(qn("w:rFonts"))
        if fonts_el is None:
            fonts_el = OxmlElement("w:rFonts")
            rPr.insert(0, fonts_el)
        fonts_el.set(qn("w:ascii"), LATIN)
        fonts_el.set(qn("w:hAnsi"), LATIN)
        fonts_el.set(qn("w:cs"), LATIN if latin else FAMILY)
        if not latin:
            rPr.append(OxmlElement("w:rtl"))
        if bold:
            rPr.append(OxmlElement("w:bCs"))
        szcs = OxmlElement("w:szCs")
        szcs.set(qn("w:val"), str(int((size if latin else size + 2) * 2)))
        rPr.append(szcs)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
