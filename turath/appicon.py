"""أيقونة البرنامج المعتمدة: الأيقونة المضمَّنة، أو صورة يعتمدها صاحب الإدارة بنفسه.

تُحفظ الأيقونة المعتمدة في مجلد البيانات (~/Turath/icon) لا في مجلد البرنامج، فتبقى بعد كل تحديث،
ويُشتق منها ملف ويندوز (ico) وملف ماك (icns) وصورة PNG للوحة ولينكس.
ويكفي ملف PNG (يُصغَّر إلى المقاسات القياسية بلا مكتبات). أما JPEG وغيره فيُحوَّل إن كانت مكتبة Pillow مثبتة.
وتُعطى الاختصاراتُ نسخةً اسمها من بصمة محتواها، فيعيد ويندوز رسمها ولا يبقى رسم مخزَّن قديم.
"""
from __future__ import annotations
import hashlib
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
    """صور PNG بالمقاسات القياسية؛ بمكتبة Pillow إن وُجدت، وإلا بالتصغير الداخلي لملف PNG."""
    try:
        from PIL import Image
    except ImportError:
        if data[:8] != PNG_SIG:
            raise ValueError("احفظوا الأيقونة بصيغة PNG (أو ثبّتوا مكتبة Pillow لقبول JPEG)")
        return _pure_renditions(data)
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


def _png_decode(data: bytes) -> tuple[int, int, bytearray]:
    """فكّ PNG بلا مكتبات: 8 بت، غير متشابك، رمادي أو RGB أو لوحة ألوان، بشفافية أو دونها. يعيد RGBA."""
    import zlib
    if data[:8] != PNG_SIG:
        raise ValueError("ليست صورة PNG")
    pos, idat, plte, trns = 8, b"", b"", b""
    w = h = depth = ctype = inter = 0
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + n
    if depth != 8 or inter or ctype not in (0, 2, 3, 4, 6):
        raise ValueError("صيغة PNG هذه تحتاج مكتبة Pillow (pip install pillow)")
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw, stride = zlib.decompress(idat), w * bpp
    px, prev, i = bytearray(), bytearray(stride), 0
    for _ in range(h):
        f, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                line[x] = (line[x] + ((line[x - bpp] if x >= bpp else 0) + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        px += line
        prev = line
    if ctype == 6:
        return w, h, px
    out = bytearray(w * h * 4)
    for k in range(w * h):
        if ctype == 2:
            r, g, b = px[3 * k:3 * k + 3]; a = 255
        elif ctype == 0:
            r = g = b = px[k]; a = 255
        elif ctype == 4:
            r = g = b = px[2 * k]; a = px[2 * k + 1]
        else:
            j = px[k]; r, g, b = plte[3 * j:3 * j + 3]; a = trns[j] if j < len(trns) else 255
        out[4 * k:4 * k + 4] = bytes((r, g, b, a))
    return w, h, out


def _png_encode(w: int, h: int, rgba: bytes) -> bytes:
    import zlib
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))  # noqa: E731
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    return (PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _shrink(w: int, h: int, rgba: bytes, n: int) -> bytes:
    """تصغير بمتوسط المساحة (مع مراعاة الشفافية) إلى n×n."""
    out = bytearray(n * n * 4)
    for ty in range(n):
        y0, y1 = ty * h // n, max(ty * h // n + 1, (ty + 1) * h // n)
        for tx in range(n):
            x0, x1 = tx * w // n, max(tx * w // n + 1, (tx + 1) * w // n)
            r = g = b = a = cnt = 0
            for y in range(y0, y1):
                row = y * w * 4
                for x in range(x0, x1):
                    k = row + 4 * x
                    al = rgba[k + 3]
                    r += rgba[k] * al; g += rgba[k + 1] * al; b += rgba[k + 2] * al; a += al; cnt += 1
            o = 4 * (ty * n + tx)
            if a:
                out[o:o + 4] = bytes((r // a, g // a, b // a, a // cnt))
    return bytes(out)


def _pure_renditions(data: bytes) -> dict[int, bytes]:
    """المقاسات القياسية بلا Pillow: يُصغَّر المربع الأوسط إلى 256 ثم إلى ما دونه."""
    w, h, px = _png_decode(data)
    side, square = min(w, h), w == h
    if not square:   # قصّ المربع الأوسط
        x0, y0 = (w - side) // 2, (h - side) // 2
        px = b"".join(bytes(px[((y0 + y) * w + x0) * 4:((y0 + y) * w + x0 + side) * 4]) for y in range(side))
        w = h = side
    out = {side: data} if square and side in (512, 1024) else {}
    base = _shrink(w, h, px, 256) if side != 256 else bytes(px)
    out[256] = _png_encode(256, 256, base)
    for n in (16, 24, 32, 48, 64, 128):
        out[n] = _png_encode(n, n, _shrink(256, 256, base, n))
    return out


def stamped(kind: str, dest: Path, stem: str) -> Path:
    """نسخة من ملف الأيقونة (ico أو icns أو png) باسم مشتق من بصمة محتواه، وتُحذف النسخ السابقة.
    يخزّن ويندوز رسم الأيقونة بمسار ملفها؛ فإن بقي المسار نفسه بقي الرسم القديم ولو تغيّر الملف."""
    src = paths()[kind]
    data = src.read_bytes()
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / f"{stem}-{hashlib.sha256(data).hexdigest()[:10]}{src.suffix}"
    for old in dest.glob(f"{stem}-*{src.suffix}"):
        if old != target:
            old.unlink(missing_ok=True)
    if not target.exists():
        target.write_bytes(data)
    return target


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
