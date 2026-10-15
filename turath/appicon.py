"""أيقونة البرنامج المعتمدة: الأيقونة المضمَّنة، أو صورة يعتمدها صاحب الإدارة بنفسه.

تُحفظ الأيقونة المعتمدة في مجلد البيانات (~/Turath/icon) لا في مجلد البرنامج، فتبقى بعد كل تحديث،
ويُشتق منها ملف ويندوز (ico) وملف ماك (icns) وصورة PNG للوحة ولينكس.
ويكفي ملف PNG مربع (512 بكسل فأكثر أفضل). أما JPEG وغيره فيُحوَّل إن كانت مكتبة Pillow مثبتة.
"""
from __future__ import annotations
import io
import struct
from pathlib import Path

from .config import CFG

PKG_IMG = Path(__file__).parent / "static" / "img"
MAX = 12 * 1024 * 1024
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def folder() -> Path:
    return CFG.home / "icon"


def custom() -> bool:
    return (folder() / "app-icon.png").is_file()


def paths() -> dict[str, Path]:
    """مسارات الأيقونة الفعلية: المعتمدة إن وُجدت، وإلا المضمَّنة."""
    base = folder() if custom() else PKG_IMG
    return {"ico": base / "turath.ico", "icns": base / "turath.icns",
            "png": base / ("app-icon.png" if custom() else "logo-turath.png"),
            "favicon": base / ("app-icon.png" if custom() else "favicon.png")}


def _png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24])


def _ico(pngs: list[bytes]) -> bytes:
    """ملف ICO بصور PNG داخله (يقرؤه ويندوز Vista فما بعد)."""
    head = struct.pack("<HHH", 0, 1, len(pngs))
    entries, body, off = b"", b"", 6 + 16 * len(pngs)
    for p in pngs:
        w, h = _png_size(p)
        entries += struct.pack("<BBBBHHII", w if w < 256 else 0, h if h < 256 else 0, 0, 0, 1, 32, len(p), off + len(body))
        body += p
    return head + entries + body


ICNS_TYPES = {16: b"icp4", 32: b"icp5", 64: b"icp6", 128: b"ic07", 256: b"ic08", 512: b"ic09", 1024: b"ic10"}


def _icns(pngs: list[bytes]) -> bytes:
    chunks = b""
    for p in pngs:
        w = _png_size(p)[0]
        t = ICNS_TYPES.get(w) or (b"ic10" if w >= 1024 else b"ic09" if w >= 512 else b"ic08" if w >= 256 else None)
        if t:
            chunks += t + struct.pack(">I", len(p) + 8) + p
    return b"icns" + struct.pack(">I", len(chunks) + 8) + chunks


def _renditions(data: bytes) -> dict[int, bytes]:
    """صور PNG بالمقاسات القياسية؛ بمكتبة Pillow إن وُجدت، وإلا الملف نفسه كما هو."""
    try:
        from PIL import Image
    except ImportError:
        if data[:8] != PNG_SIG:
            raise ValueError("احفظوا الأيقونة بصيغة PNG (أو ثبّتوا مكتبة Pillow لقبول JPEG)")
        w, h = _png_size(data)
        if w != h:
            raise ValueError("يجب أن تكون صورة الأيقونة مربعة")
        return {w: data}
    try:
        im = Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        raise ValueError("الملف ليس صورة يمكن قراءتها")
    side = min(im.size)
    if im.size[0] != im.size[1]:   # قصّ المربع الأوسط
        x, y = (im.size[0] - side) // 2, (im.size[1] - side) // 2
        im = im.crop((x, y, x + side, y + side))
    out = {}
    for n in (16, 24, 32, 48, 64, 128, 256, 512, 1024):
        if n <= max(side, 256):
            b = io.BytesIO()
            im.resize((n, n), Image.LANCZOS).save(b, "PNG", optimize=True)
            out[n] = b.getvalue()
    return out


def adopt(data: bytes) -> dict:
    if not 100 < len(data) <= MAX:
        raise ValueError("حجم صورة الأيقونة غير مقبول")
    sizes = _renditions(data)
    big = sizes[max(sizes)]
    folder().mkdir(parents=True, exist_ok=True)
    (folder() / "app-icon.png").write_bytes(sizes.get(512) or sizes.get(256) or big)
    (folder() / "turath.ico").write_bytes(_ico([sizes[n] for n in sorted(sizes) if n <= 256] or [big]))
    (folder() / "turath.icns").write_bytes(_icns([sizes[n] for n in sorted(sizes)]))
    return status()


def reset() -> None:
    for n in ("app-icon.png", "turath.ico", "turath.icns"):
        (folder() / n).unlink(missing_ok=True)


def status() -> dict:
    return {"custom": custom(), "folder": str(folder())}
