"""خزنة الأصول: نسخة أصلية لا تُعدَّل، وبصمة SHA-256، وفحص السلامة الدوري، والنسخ الاحتياطي."""
from __future__ import annotations
import hashlib
import json
import mimetypes
import os
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

from . import db
from .config import CFG

KINDS = {"audio": (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"), "video": (".mp4", ".mov", ".mkv", ".avi"),
         "image": (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif"), "document": (".pdf", ".docx", ".doc", ".txt", ".md", ".odt"),
         "data": (".csv", ".json", ".geojson", ".xlsx")}


def kind_of(name: str) -> str:
    ext = Path(name).suffix.lower()
    for k, exts in KINDS.items():
        if ext in exts:
            return k
    return "other"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe(p: Path) -> dict:
    """البيانات الفنية عبر ffprobe إن وُجد (أداة مشروطة T-FFMPEG)."""
    if not shutil.which("ffprobe"):
        return {}
    try:
        out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(p)],
                             capture_output=True, text=True, timeout=30)
        d = json.loads(out.stdout or "{}")
        fmt = d.get("format", {})
        return {"duration_s": round(float(fmt.get("duration", 0) or 0), 2), "format": fmt.get("format_name"),
                "bit_rate": fmt.get("bit_rate"),
                "streams": [{k: s.get(k) for k in ("codec_type", "codec_name", "sample_rate", "channels", "width", "height")}
                            for s in d.get("streams", [])]}
    except Exception:
        return {}


def exif_gps(data: bytes) -> bool:
    """هل في صورة JPEG إحداثيات GPS ضمن بيانات EXIF؟ (قراءة مباشرة بلا مكتبات)
    الأصل لا يُعدَّل أبداً؛ وإنما يُعلَّم ليُحجب الموقع قبل أي نشر (الأخلاقيات وحماية المواقع الحساسة)."""
    import struct
    if not data.startswith(b"\xff\xd8"):
        return False
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker, size = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker == 0xE1 and data[i + 4:i + 10] == b"Exif\x00\x00":
            t = data[i + 10:i + 2 + size]
            end = "<" if t[:2] == b"II" else ">"
            try:
                off = struct.unpack(end + "I", t[4:8])[0]
                n = struct.unpack(end + "H", t[off:off + 2])[0]
                for k in range(n):
                    e = off + 2 + 12 * k
                    tag = struct.unpack(end + "H", t[e:e + 2])[0]
                    if tag == 0x8825:
                        gps_off = struct.unpack(end + "I", t[e + 8:e + 12])[0]
                        return struct.unpack(end + "H", t[gps_off:gps_off + 2])[0] > 0
            except (struct.error, IndexError):
                return False
            return False
        if marker in (0xDA, 0xD9):
            break
        i += 2 + size
    return False


def ingest(user: dict, filename: str, data: bytes, *, project_id: str | None = None, provenance: str = "",
           rights: str = "", depositor: str = "", access_level: str = "private") -> dict:
    """يحفظ الأصل في الخزنة بمساره المشتق من بصمته، للقراءة فقط، ويسجّله. تكرار الملف نفسه لا يُنشئ نسخة ثانية."""
    if project_id:
        p = db.get_raw("projects", project_id)
        if not p or not db.can_write(user, "projects", p):
            raise db.Denied("لا صلاحية للإيداع في هذا المشروع")
    h = hashlib.sha256(data).hexdigest()
    ext = Path(filename).suffix.lower()[:10]
    rel = Path("originals") / h[:2] / f"{h}{ext}"
    dest = CFG.vault / rel
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        os.chmod(dest, stat.S_IRUSR | stat.S_IRGRP)
    with db.WRITE_LOCK:
        existing = db.one("SELECT * FROM assets WHERE sha256=? AND owner_id=?", (h, user["id"]))
        if existing:
            return existing | {"duplicate": True}
        aid = db.next_id("AST")
        ts = db.now()
        row = {"id": aid, "sha256": h, "filename": Path(filename).name, "mime": mimetypes.guess_type(filename)[0] or "application/octet-stream",
               "size": len(data), "kind": kind_of(filename), "vault_path": rel.as_posix(), "project_id": project_id,
               "owner_id": user["id"], "access_level": access_level, "provenance": provenance, "rights": rights,
               "depositor": depositor, "technical": json.dumps(_probe(dest) | ({"gps": True} if exif_gps(data) else {}), ensure_ascii=False), "created_at": ts,
               "updated_at": ts, "last_verified": ts, "integrity": "ok"}
        db.conn().execute(f"INSERT INTO assets({','.join(row)}) VALUES({','.join('?' * len(row))})", list(row.values()))
        db.log(user["id"], "ingest", "assets", aid, None, {k: row[k] for k in ("sha256", "filename", "size", "kind")})
        db.conn().commit()
    return row


def path_of(asset: dict) -> Path:
    return CFG.vault / asset["vault_path"]


def verify_all(user_id: str | None = None) -> dict:
    """يعيد حساب البصمة لكل أصل ويقارنها بالمسجل — مؤشر «سلامة الأصول الرقمية»."""
    report = {"ok": 0, "missing": [], "altered": []}
    for a in db.rows("SELECT * FROM assets"):
        p = path_of(a)
        status = "ok"
        if not p.exists():
            status = "missing"
            report["missing"].append(a["id"])
        elif sha256_file(p) != a["sha256"]:
            status = "altered"
            report["altered"].append(a["id"])
        else:
            report["ok"] += 1
        db.conn().execute("UPDATE assets SET integrity=?, last_verified=? WHERE id=?", (status, db.now(), a["id"]))
    db.log(user_id, "verify", "assets", "*", None, {"ok": report["ok"], "missing": len(report["missing"]), "altered": len(report["altered"])})
    db.conn().commit()
    return report


def backup(user_id: str | None = None) -> Path:
    """نسخة احتياطية كاملة: لقطة متسقة من القاعدة + الخزنة + بيان بالبصمات (على نمط BagIt المبسط)."""
    CFG.backups.mkdir(parents=True, exist_ok=True)
    stamp = db.now().replace(":", "").replace("-", "")[:15]
    out = CFG.backups / f"turath-backup-{stamp}.zip"
    snap = CFG.backups / f".snapshot-{stamp}.db"
    src = db.conn()
    dst = __import__("sqlite3").connect(snap)
    src.backup(dst)
    dst.close()
    manifest = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(snap, "data/turath.db")
        for a in db.rows("SELECT id, sha256, vault_path FROM assets"):
            p = path_of(a)
            if p.exists():
                z.write(p, f"data/vault/{a['vault_path']}")
                manifest.append(f"{a['sha256']}  data/vault/{a['vault_path']}")
        z.writestr("manifest-sha256.txt", "\n".join(manifest) + "\n")
        z.writestr("bag-info.txt", f"Source-Organization: {CFG.institution}\nBagging-Date: {db.now()}\nPayload-Oxum: {len(manifest)}\n")
    snap.unlink(missing_ok=True)
    db.conn().execute("INSERT OR REPLACE INTO meta(k,v) VALUES('last_backup',?)", (db.now(),))
    db.log(user_id, "backup", "system", out.name, None, {"assets": len(manifest)})
    db.conn().commit()
    return out
