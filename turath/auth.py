"""الحسابات والجلسات — PBKDF2-SHA256، وجلسات برموز عشوائية، وصفات: admin · director · researcher · native_reviewer · viewer."""
from __future__ import annotations
import hashlib
import hmac
import secrets
import time

from . import db
from .config import CFG

ROLES = {"admin": "مسؤول النظام", "director": "مدير الإدارة (المراجع البشري المخوّل)", "researcher": "باحث",
         "native_reviewer": "مراجع لهجي محلي", "viewer": "مطّلع"}
ITER = 240_000


def hash_pw(pw: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)
    return f"pbkdf2${ITER}${salt.hex()}${dk.hex()}"


def check_pw(pw: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(dk.hex(), h)
    except Exception:
        return False


def public(u: dict | None) -> dict | None:
    return u and {k: u[k] for k in ("id", "username", "display_name", "role") if k in u}


def create_user(username: str, password: str, display_name: str = "", role: str = "researcher") -> dict:
    if role not in ROLES:
        raise ValueError("صفة غير معروفة")
    if len(password) < 8:
        raise ValueError("كلمة المرور ثمانية أحرف على الأقل")
    if db.one("SELECT 1 FROM users WHERE username=?", (username,)):
        raise ValueError("اسم المستخدم مستعمل")
    uid = db.next_id("USR")
    db.conn().execute("INSERT INTO users(id,username,display_name,pw_hash,role,created_at) VALUES(?,?,?,?,?,?)",
                      (uid, username, display_name or username, hash_pw(password), role, db.now()))
    db.log(uid, "create", "users", uid, None, {"username": username, "role": role})
    db.conn().commit()
    return public(db.one("SELECT * FROM users WHERE id=?", (uid,)))


def ensure_owner() -> dict:
    """في النمط الفردي: حساب المالك الوحيد بصفة مدير (يتولد تلقائياً بكلمة مرور عشوائية غير مستعملة)."""
    u = db.one("SELECT * FROM users WHERE username='owner'")
    if not u:
        create_user("owner", secrets.token_urlsafe(18), "صاحب الإدارة", "director")
        u = db.one("SELECT * FROM users WHERE username='owner'")
    return u


def login(username: str, password: str) -> str | None:
    u = db.one("SELECT * FROM users WHERE username=? AND active=1", (username,))
    if not u or not check_pw(password, u["pw_hash"]):
        time.sleep(0.6)
        return None
    return new_session(u["id"])


def new_session(user_id: str) -> str:
    tok = secrets.token_urlsafe(32)
    db.conn().execute("INSERT INTO sessions(token,user_id,created_at,expires_at) VALUES(?,?,?,?)",
                      (tok, user_id, db.now(), time.time() + CFG.session_hours * 3600))
    db.conn().commit()
    return tok


def user_for(token: str | None) -> dict | None:
    if not token:
        return None
    s = db.one("SELECT * FROM sessions WHERE token=?", (token,))
    if not s or s["expires_at"] < time.time():
        return None
    return db.one("SELECT id, username, display_name, role FROM users WHERE id=? AND active=1", (s["user_id"],))


def logout(token: str) -> None:
    db.conn().execute("DELETE FROM sessions WHERE token=?", (token,))
    db.conn().commit()


def users() -> list[dict]:
    return db.rows("SELECT id, username, display_name, role, active, created_at FROM users ORDER BY created_at")
