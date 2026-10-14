"""طبقة البيانات: SQLite مع سجل تغييرات لكل تعديل، وصلاحيات الملكية والمشاركة، وفهرس بحث FTS5."""
from __future__ import annotations
import json
import sqlite3
import threading
from datetime import datetime, timezone

from . import entities as EN
from .config import CFG

_LOCAL = threading.local()
WRITE_LOCK = threading.RLock()


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def conn() -> sqlite3.Connection:
    c = getattr(_LOCAL, "c", None)
    if c is None or getattr(_LOCAL, "path", None) != str(CFG.db_path):
        CFG.db_path.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(CFG.db_path, check_same_thread=False, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _LOCAL.c, _LOCAL.path = c, str(CFG.db_path)
    return c


def init() -> None:
    with WRITE_LOCK:
        c = conn()
        c.executescript(EN.ddl())
        # ترحيل خفيف: إضافة أي عمود جديد عُرِّف بعد إنشاء القاعدة
        for t in EN.E:
            have = {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
            for name, _, typ in EN.fields_of(t):
                if name not in have:
                    c.execute(f"ALTER TABLE {t} ADD COLUMN {name} {EN.ftype(typ)}")
        c.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('schema_version','1')")
        c.commit()


def rows(sql: str, args=()) -> list[dict]:
    return [dict(r) for r in conn().execute(sql, args)]


def one(sql: str, args=()) -> dict | None:
    r = conn().execute(sql, args).fetchone()
    return dict(r) if r else None


def next_id(prefix: str) -> str:
    year = datetime.now().year
    key = f"{prefix}-{year}"
    with WRITE_LOCK:
        c = conn()
        r = c.execute("SELECT n FROM counters WHERE prefix=?", (key,)).fetchone()
        n = (r[0] if r else 0) + 1
        c.execute("INSERT OR REPLACE INTO counters(prefix,n) VALUES(?,?)", (key, n))
        c.commit()
    return f"{key}-{n:04d}"


def log(user_id: str | None, action: str, table: str, item_id: str, before=None, after=None) -> None:
    conn().execute("INSERT INTO change_log(at,user_id,action,item_table,item_id,before,after) VALUES(?,?,?,?,?,?,?)",
                   (now(), user_id, action, table, item_id,
                    json.dumps(before, ensure_ascii=False) if before is not None else None,
                    json.dumps(after, ensure_ascii=False) if after is not None else None))


# ------------------------------------------------------------------ الصلاحيات
class Denied(Exception):
    pass


def member_projects(user_id: str) -> set[str]:
    own = {r["id"] for r in rows("SELECT id FROM projects WHERE owner_id=?", (user_id,))}
    mem = {r["project_id"] for r in rows("SELECT project_id FROM project_members WHERE user_id=?", (user_id,))}
    return own | mem


def can_read(user: dict, table: str, row: dict) -> bool:
    if user.get("role") == "admin" and CFG.admin_sees_all:
        return True
    uid = user["id"]
    if row.get("owner_id") == uid or row.get("access_level") == "public":
        return True
    if table == "projects":
        return row["id"] in member_projects(uid)
    if row.get("project_id") and row["project_id"] in member_projects(uid) and row.get("access_level") != "private":
        return True
    if row.get("access_level") == "shared":
        return bool(one("SELECT 1 FROM shares WHERE item_table=? AND item_id=? AND grantee IN (?, '*')",
                        (table, row["id"], uid)))
    return bool(one("SELECT 1 FROM shares WHERE item_table=? AND item_id=? AND grantee IN (?, '*')", (table, row["id"], uid)))


def can_write(user: dict, table: str, row: dict) -> bool:
    uid = user["id"]
    if row.get("owner_id") == uid:
        return True
    if table == "projects":
        return bool(one("SELECT 1 FROM project_members WHERE project_id=? AND user_id=? AND role IN ('coauthor','lead')",
                        (row["id"], uid)))
    if row.get("project_id") and one("SELECT 1 FROM project_members WHERE project_id=? AND user_id=? AND role IN ('coauthor','lead')",
                                      (row["project_id"], uid)) and row.get("access_level") != "private":
        return True
    return bool(one("SELECT 1 FROM shares WHERE item_table=? AND item_id=? AND grantee IN (?, '*') AND mode='write'",
                    (table, row["id"], uid)))


def _clean(table: str, data: dict) -> dict:
    allowed = {n: t for n, _, t in EN.fields_of(table)}
    out = {}
    for k, v in data.items():
        if k not in allowed or k in ("id", "owner_id", "created_at", "updated_at"):
            continue
        t = allowed[k]
        if v == "" or v is None:
            out[k] = None
        elif t == "int":
            out[k] = int(v)
        elif t == "real":
            out[k] = float(v)
        elif t == "bool":
            out[k] = 1 if v in (True, 1, "1", "true", "on", "yes") else 0
        elif t == "json" and not isinstance(v, str):
            out[k] = json.dumps(v, ensure_ascii=False)
        elif t.startswith("enum:") and v not in t[5:].split("|"):
            raise ValueError(f"قيمة غير مقبولة للحقل {k}: {v}")
        else:
            out[k] = v
    return out


def _index(table: str, row: dict) -> None:
    c = conn()
    c.execute("DELETE FROM search_index WHERE item_table=? AND item_id=?", (table, row["id"]))
    body = " ".join(str(v) for k, v in row.items() if v and k not in ("id", "owner_id", "created_at", "updated_at", "project_id", "access_level", "level", "verified", "asset_id"))
    c.execute("INSERT INTO search_index(item_table,item_id,project_id,title,body) VALUES(?,?,?,?,?)",
              (table, row["id"], row.get("project_id"), EN.title_of(table, row), body))


def create(user: dict, table: str, data: dict) -> dict:
    if table not in EN.E:
        raise ValueError("جدول غير معروف")
    vals = _clean(table, data)
    if table == "sources" and vals.get("level") not in (None, 1, 2, 3, 4, 5):
        raise ValueError("مستوى المصدر بين 1 و5")
    if vals.get("project_id"):
        p = one("SELECT * FROM projects WHERE id=?", (vals["project_id"],))
        if not p or not can_write(user, "projects", p):
            raise Denied("لا صلاحية للكتابة في هذا المشروع")
    with WRITE_LOCK:
        rid = data.get("id") if data.get("id") and CFG.allow_explicit_ids else next_id(EN.E[table]["prefix"])
        ts = now()
        vals.update(id=rid, owner_id=user["id"], created_at=ts, updated_at=ts)
        vals.setdefault("access_level", "project" if vals.get("project_id") else "private")
        if table == "projects":
            vals.setdefault("stage", "S01")
            vals.setdefault("status", "active")
        cols = ",".join(vals)
        conn().execute(f"INSERT INTO {table}({cols}) VALUES({','.join('?' * len(vals))})", list(vals.values()))
        row = get_raw(table, rid)
        _index(table, row)
        log(user["id"], "create", table, rid, None, row)
        conn().commit()
    return row


def get_raw(table: str, rid: str) -> dict | None:
    if table not in EN.E:
        raise ValueError("جدول غير معروف")
    return one(f"SELECT * FROM {table} WHERE id=?", (rid,))


def get(user: dict, table: str, rid: str) -> dict:
    r = get_raw(table, rid)
    if not r:
        raise KeyError(rid)
    if not can_read(user, table, r):
        raise Denied("لا صلاحية للاطلاع")
    return r


def update(user: dict, table: str, rid: str, data: dict) -> dict:
    with WRITE_LOCK:
        before = get_raw(table, rid)
        if not before:
            raise KeyError(rid)
        if not can_write(user, table, before):
            raise Denied("لا صلاحية للتعديل")
        vals = _clean(table, data)
        if table == "projects":
            vals.pop("stage", None)   # المرحلة لا تتغير إلا عبر بوابات الجودة
        if not vals:
            return before
        vals["updated_at"] = now()
        conn().execute(f"UPDATE {table} SET {','.join(f'{k}=?' for k in vals)} WHERE id=?", [*vals.values(), rid])
        after = get_raw(table, rid)
        _index(table, after)
        log(user["id"], "update", table, rid, {k: before.get(k) for k in vals}, {k: after.get(k) for k in vals})
        conn().commit()
    return after


def delete(user: dict, table: str, rid: str) -> None:
    with WRITE_LOCK:
        before = get_raw(table, rid)
        if not before:
            raise KeyError(rid)
        if before.get("owner_id") != user["id"] and user.get("role") != "admin":
            raise Denied("الحذف للمالك وحده")
        conn().execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        conn().execute("DELETE FROM search_index WHERE item_table=? AND item_id=?", (table, rid))
        log(user["id"], "delete", table, rid, before, None)
        conn().commit()


def list_rows(user: dict, table: str, project_id: str | None = None, limit: int = 500) -> list[dict]:
    if table not in EN.E:
        raise ValueError("جدول غير معروف")
    sql, args = f"SELECT * FROM {table}", []
    if project_id:
        sql += " WHERE project_id=?" if table != "projects" else " WHERE id=?"
        args.append(project_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)
    return [r for r in rows(sql, args) if can_read(user, table, r)]


def search(user: dict, q: str, limit: int = 60) -> list[dict]:
    q = " ".join(f'"{w}"' for w in q.replace('"', " ").split() if w)
    if not q:
        return []
    hits = rows("SELECT item_table, item_id, project_id, title, snippet(search_index, 4, '[', ']', ' … ', 14) AS snip "
                "FROM search_index WHERE search_index MATCH ? ORDER BY rank LIMIT ?", (q, limit * 3))
    out = []
    for h in hits:
        tbl = "interviews" if h["item_table"] == "transcript" else h["item_table"]
        r = get_raw(tbl, h["item_id"]) if tbl in EN.E else None
        if r and can_read(user, tbl, r):
            out.append(h)
        if len(out) >= limit:
            break
    return out


def history(table: str, rid: str) -> list[dict]:
    return rows("SELECT * FROM change_log WHERE item_table=? AND item_id=? ORDER BY seq", (table, rid))
