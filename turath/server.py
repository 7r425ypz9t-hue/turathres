"""خادم لوحة التحكم — مكتبة بايثون القياسية وحدها (اعتمادية ذاتية، بلا خدمات خارجية).

الحماية:
- كل طلب API يحمل رمز جلسة في ترويسة Authorization (لا ملفات تعريف ارتباط، فلا CSRF).
- النمط الفردي: الاستماع على 127.0.0.1 فقط، ورفض أي ترويسة Host غير محلية (حماية من DNS rebinding).
- نمطا الشبكة والفريق: دخول بكلمة مرور، وTLS اختياري بشهادة يحددها المسؤول.
"""
from __future__ import annotations
import json
import mimetypes
import re
import ssl
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import __version__
from . import agents as AG
from . import auth
from . import db
from . import entities as EN
from . import evidence as EV
from . import export as EX
from . import kpis
from . import lifecycle as LC
from . import oral_lab as LAB
from . import pilot
from . import vault
from .config import CFG, MODES

STATIC = Path(__file__).parent / "static"
ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
MAX_UPLOAD = 1024 * 1024 * 1024   # 1 جيجابايت للملف الواحد


class ApiError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def info() -> dict:
    return {"version": __version__, "institution": CFG.institution, "mode": CFG.mode, "mode_label": MODES[CFG.mode]["label"],
            "modes": MODES, "engines": AG.engines(), "engine": CFG.engine, "asr": LAB.asr_available(),
            "ffmpeg": LAB.ffmpeg_available(), "stages": [{"id": s, "label": l, "agent": a} for s, l, a in LC.STAGES],
            "lab_steps": [{"step": n, "label": l, "actor": a, "mode": m} for n, l, a, m in LAB.STEPS],
            "roles": auth.ROLES, "levels": EN.LEVELS, "narrative_types": EN.NARRATIVE_TYPES,
            "evidence_types": EN.EVIDENCE_TYPES, "regions": EN.REGION_LABELS, "domains": EN.DOMAINS,
            "home": str(CFG.home)}


def dashboard(user: dict) -> dict:
    P = db.list_rows(user, "projects", limit=1000)
    stages = {s: 0 for s in LC.STAGE_IDS}
    for p in P:
        stages[p.get("stage") or "S01"] = stages.get(p.get("stage") or "S01", 0) + 1
    counts = {t: len(db.list_rows(user, t, limit=100000)) for t in EN.E}
    recent = [r for r in db.rows("SELECT at,user_id,action,item_table,item_id FROM change_log ORDER BY seq DESC LIMIT 40")
              if r["user_id"] == user["id"] or CFG.mode != "team"][:14]
    last_backup = db.one("SELECT v FROM meta WHERE k='last_backup'")
    return {"projects": P, "stages": stages, "counts": counts, "kpis": kpis.compute(), "recent": recent,
            "last_backup": last_backup and last_backup["v"],
            "assets": db.one("SELECT COUNT(*) n, COALESCE(SUM(size),0) s FROM assets")}


def docs_list() -> list[dict]:
    out = []
    for p in sorted(DOCS.glob("*.md")) if DOCS.exists() else []:
        first = next((l.lstrip("# ").strip() for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("#")), p.stem)
        out.append({"name": p.name, "title": first})
    for extra in ("pilot/README.md", "README.md", "FEATURE_PARITY.md", "MERGE.md"):
        q = ROOT / extra
        if q.exists():
            first = next((l.lstrip("# ").strip() for l in q.read_text(encoding="utf-8").splitlines() if l.startswith("#")), extra)
            out.append({"name": extra, "title": first})
    return out


def doc_text(name: str) -> str:
    p = (ROOT / name) if "/" in name or name in ("README.md", "FEATURE_PARITY.md", "MERGE.md") else (DOCS / name)
    p = p.resolve()
    if not p.is_relative_to(ROOT.resolve()) or p.suffix != ".md" or not p.exists():
        raise ApiError("وثيقة غير موجودة", 404)
    return p.read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "Turath"

    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------ أدوات
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
                         "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
                         "script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20 * 1024 * 1024:
            raise ApiError("الطلب أكبر من المسموح")
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise ApiError("صيغة الطلب غير صحيحة")

    def _host_ok(self) -> bool:
        if CFG.mode != "solo":
            return True
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def _user(self) -> dict:
        tok = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
        if not tok:
            tok = parse_qs(urlparse(self.path).query).get("t", [""])[0]   # للتنزيلات المباشرة فقط
        u = auth.user_for(tok)
        if not u:
            raise ApiError("يلزم تسجيل الدخول", 401)
        return dict(u)

    # ------------------------------------------------------------ التوجيه
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")

    def _route(self, method: str):
        if not self._host_ok():
            return self._send(403, b"forbidden host", "text/plain")
        u = urlparse(self.path)
        path = unquote(u.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if not path.startswith("/api/"):
                return self._static(path)
            if path == "/api/login" and method == "POST":
                d = self._body()
                tok = auth.login(d.get("username", ""), d.get("password", ""))
                if not tok:
                    raise ApiError("بيانات الدخول غير صحيحة", 401)
                return self._json({"token": tok, "user": auth.public(auth.user_for(tok))})
            if path == "/api/public":
                return self._json({"institution": CFG.institution, "mode": CFG.mode, "mode_label": MODES[CFG.mode]["label"],
                                   "version": __version__})
            user = self._user()
            return self._api(method, path, q, user)
        except ApiError as e:
            self._json({"error": str(e)}, e.code)
        except db.Denied as e:
            self._json({"error": str(e)}, 403)
        except KeyError as e:
            self._json({"error": f"غير موجود: {e}"}, 404)
        except (ValueError, RuntimeError) as e:
            self._json({"error": str(e)}, 400)
        except Exception as e:  # pragma: no cover
            traceback.print_exc()
            self._json({"error": f"خطأ داخلي: {e}"}, 500)

    def _static(self, path: str):
        if path in ("/", ""):
            path = "/index.html"
        p = (STATIC / path.lstrip("/")).resolve()
        if not p.is_relative_to(STATIC.resolve()) or not p.is_file():
            return self._send(404, "غير موجود".encode(), "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self._send(200, p.read_bytes(), ctype, {"Cache-Control": "no-cache"})

    def _download(self, data: bytes, name: str, ctype: str):
        self._send(200, data, ctype, {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})

    def _api(self, method: str, path: str, q: dict, user: dict):
        seg = path.split("/")[2:]
        head = seg[0]
        if head == "me":
            return self._json({"user": user, "info": info()})
        if head == "logout" and method == "POST":
            auth.logout((self.headers.get("Authorization") or "").removeprefix("Bearer ").strip())
            return self._json({"ok": True})
        if head == "schema":
            return self._json(EN.schema_for_ui())
        if head == "dashboard":
            return self._json(dashboard(user))
        if head == "kpis":
            if method == "POST" and seg[1:] == ["baseline"]:
                return self._json(kpis.set_baseline(user))
            return self._json(kpis.compute(q.get("project")))
        if head == "search":
            return self._json(db.search(user, q.get("q", "")))
        if head == "rows":
            return self._rows(method, seg[1:], q, user)
        if head == "history":
            db.get(user, seg[1], seg[2])
            return self._json(db.history(seg[1], seg[2]))
        if head == "upload" and method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_UPLOAD:
                raise ApiError("حجم الملف غير مقبول")
            data = self.rfile.read(n)
            row = vault.ingest(user, unquote(self.headers.get("X-Filename") or "file.bin"), data,
                               project_id=q.get("project") or None, provenance=q.get("provenance", ""),
                               rights=q.get("rights", ""), depositor=q.get("depositor", ""),
                               access_level=q.get("access", "project" if q.get("project") else "private"))
            return self._json(row)
        if head == "assets":
            if len(seg) == 1:
                A = [a for a in db.rows("SELECT * FROM assets ORDER BY created_at DESC LIMIT 1000") if db.can_read(user, "assets", a)]
                if q.get("project"):
                    A = [a for a in A if a.get("project_id") == q["project"]]
                return self._json(A)
            a = db.one("SELECT * FROM assets WHERE id=?", (seg[1],))
            if not a or not db.can_read(user, "assets", a):
                raise ApiError("غير متاح", 404)
            if len(seg) > 2 and seg[2] == "file":
                p = vault.path_of(a)
                inline = q.get("inline") == "1"
                return self._send(200, p.read_bytes(), a["mime"], {} if inline else
                                  {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(a['filename'])}"})
            if method == "PUT":
                d = self._body()
                if not db.can_write(user, "assets", a):
                    raise db.Denied("لا صلاحية")
                vals = {k: d[k] for k in ("provenance", "rights", "depositor", "access_level", "project_id") if k in d}
                if vals:
                    db.conn().execute(f"UPDATE assets SET {','.join(k + '=?' for k in vals)}, updated_at=? WHERE id=?",
                                      [*vals.values(), db.now(), a["id"]])
                    db.log(user["id"], "update", "assets", a["id"], {k: a.get(k) for k in vals}, vals)
                    db.conn().commit()
                return self._json(db.one("SELECT * FROM assets WHERE id=?", (a["id"],)))
            return self._json(a)
        if head == "vault":
            if seg[1] == "verify":
                return self._json(vault.verify_all(user["id"]))
            if seg[1] == "backup":
                if user["role"] not in ("admin", "director"):
                    raise db.Denied("النسخ الاحتياطي للمدير أو المسؤول")
                return self._json({"file": str(vault.backup(user["id"]))})
        if head == "projects":
            return self._project(method, seg[1:], q, user)
        if head == "claims":
            if len(seg) > 2 and seg[2] == "link" and method == "POST":
                d = self._body()
                c = db.get(user, "claims", seg[1])
                return self._json(db.create(user, "evidence_links", d | {"claim_id": c["id"], "project_id": c.get("project_id")}))
            return self._json(EV.claim_card(user, seg[1]))
        if head == "lab":
            iid = seg[1]
            act = seg[2] if len(seg) > 2 else ""
            if act == "step" and method == "POST":
                d = self._body()
                return self._json(LAB.mark(user, iid, int(d["step"]), bool(d.get("done")), d.get("note", "")))
            if act == "transcript" and method == "POST":
                d = self._body()
                return self._json(LAB.save_transcript(user, iid, d.get("text", ""), d.get("readable", "")))
            if act == "srt":
                return self._download(LAB.to_srt(LAB.transcript(user, iid)).encode(), f"{iid}.srt", "application/x-subrip")
            if act == "asr" and method == "POST":
                return self._json(LAB.auto_transcribe(user, iid))
            db.get(user, "interviews", iid)
            return self._json({"steps": LAB.status(iid), "segments": LAB.transcript(user, iid)})
        if head == "agents":
            if len(seg) > 1 and seg[1] == "run" and method == "POST":
                d = self._body()
                if not d.get("agent") or not d.get("task"):
                    raise ApiError("الوكيل والتكليف مطلوبان")
                return self._json(AG.run(user, d["agent"], d["task"], d.get("project") or None, d.get("skill") or None, d.get("engine")))
            if len(seg) > 1:
                return self._json(AG.card(seg[1]))
            return self._json(AG.cards())
        if head == "skills":
            return self._json(AG.skills())
        if head == "runs":
            if len(seg) > 1:
                r = AG.run_detail(user, seg[1])
                if not r:
                    raise ApiError("غير موجود", 404)
                return self._json(r)
            return self._json(AG.runs(user, q.get("project")))
        if head == "users":
            if method == "POST":
                if user["role"] != "admin" and not (CFG.mode != "team" and user["role"] == "director"):
                    raise db.Denied("إنشاء الحسابات للمسؤول")
                d = self._body()
                return self._json(auth.create_user(d["username"], d["password"], d.get("display_name", ""), d.get("role", "researcher")))
            return self._json([{"username": x["username"], "display_name": x["display_name"], "role": x["role"]}
                               for x in auth.users()] if user["role"] != "admin" else auth.users())
        if head == "share" and method == "POST":
            d = self._body()
            row = db.get(user, d["table"], d["id"]) if d["table"] in EN.E else None
            if not row or row.get("owner_id") != user["id"]:
                raise db.Denied("المشاركة للمالك وحده")
            grantee = "*" if d.get("grantee") == "*" else (db.one("SELECT id FROM users WHERE username=?", (d.get("grantee"),)) or {}).get("id")
            if not grantee:
                raise ApiError("مستخدم غير موجود")
            sid = db.next_id("SHR")
            db.conn().execute("INSERT INTO shares(id,item_table,item_id,owner_id,grantee,mode,created_at) VALUES(?,?,?,?,?,?,?)",
                              (sid, d["table"], d["id"], user["id"], grantee, d.get("mode", "read"), db.now()))
            if row.get("access_level") == "private":
                db.conn().execute(f"UPDATE {d['table']} SET access_level='shared' WHERE id=?", (d["id"],))
            db.log(user["id"], "share", d["table"], d["id"], None, {"grantee": grantee, "mode": d.get("mode", "read")})
            db.conn().commit()
            return self._json({"id": sid})
        if head == "export":
            kind = seg[1]
            if kind == "csv":
                return self._download(EX.to_csv(user, seg[2], q.get("project")).encode("utf-8"), f"{seg[2]}.csv", "text/csv; charset=utf-8")
            if kind == "geojson":
                return self._download(json.dumps(EX.geojson(user, q.get("project")), ensure_ascii=False).encode(), "atlas.geojson", "application/geo+json")
            if kind == "json":
                return self._download(EX.to_json(user, seg[2]).encode(), f"{seg[2]}.json", "application/json")
            if kind == "docx":
                return self._download(EX.docx_dossier(user, seg[2]), f"{seg[2]}.docx",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if head == "docs":
            if len(seg) > 1:
                return self._json({"name": "/".join(seg[1:]), "text": doc_text("/".join(seg[1:]))})
            return self._json(docs_list())
        if head == "pilot" and method == "POST":
            return self._json(pilot.import_pilot(user))
        if head == "settings" and method == "POST":
            if user["role"] not in ("admin", "director"):
                raise db.Denied("الإعدادات للمدير")
            d = self._body()
            if d.get("engine") in AG.engines():
                CFG.engine = d["engine"]
            CFG.save()
            return self._json(info())
        raise ApiError("مسار غير معروف", 404)

    def _rows(self, method, seg, q, user):
        table = seg[0]
        if table not in EN.E:
            raise ApiError("جدول غير معروف", 404)
        if len(seg) == 1:
            if method == "POST":
                return self._json(db.create(user, table, self._body()))
            return self._json(db.list_rows(user, table, q.get("project")))
        rid = seg[1]
        if method == "PUT":
            return self._json(db.update(user, table, rid, self._body()))
        if method == "DELETE":
            db.delete(user, table, rid)
            return self._json({"ok": True})
        return self._json(db.get(user, table, rid))

    def _project(self, method, seg, q, user):
        pid = seg[0]
        act = seg[1] if len(seg) > 1 else ""
        p = db.get(user, "projects", pid)
        if act == "gate":
            return self._json({"stage": p["stage"], "checks": LC.checks(pid),
                               "log": db.rows("SELECT * FROM stage_log WHERE project_id=? ORDER BY seq", (pid,))})
        if act == "advance" and method == "POST":
            return self._json(LC.advance(user, pid))
        if act == "decision" and method == "POST":
            d = self._body()
            return self._json(LC.record_decision(user, pid, d["gate"], d["decision"], d.get("rationale", ""), d.get("reviewer_role", "")))
        if act == "members":
            if method == "POST":
                if p["owner_id"] != user["id"]:
                    raise db.Denied("دعوة الشركاء لمالك المشروع")
                d = self._body()
                m = db.one("SELECT id FROM users WHERE username=?", (d.get("username"),))
                if not m:
                    raise ApiError("مستخدم غير موجود")
                db.conn().execute("INSERT OR REPLACE INTO project_members(project_id,user_id,role,added_at) VALUES(?,?,?,?)",
                                  (pid, m["id"], d.get("role", "coauthor"), db.now()))
                db.log(user["id"], "member", "projects", pid, None, {"user": m["id"], "role": d.get("role", "coauthor")})
                db.conn().commit()
            return self._json(db.rows("SELECT m.role, m.added_at, u.username, u.display_name FROM project_members m "
                                      "JOIN users u ON u.id=m.user_id WHERE m.project_id=?", (pid,)))
        if act == "overview":
            out = {"project": p, "checks": LC.checks(pid), "kpis": kpis.compute(pid), "claims": EV.claims_report(pid)}
            out["counts"] = {t: len(db.list_rows(user, t, pid, limit=100000)) for t in EN.E if t != "projects"}
            return self._json(out)
        return self._json(p)


def serve(open_browser: bool = True, port: int | None = None) -> None:
    db.init()
    host = CFG.bind_host()
    port = port or CFG.port
    httpd = ThreadingHTTPServer((host, port), Handler)
    scheme = "http"
    if CFG.tls_cert and CFG.tls_key:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CFG.tls_cert, CFG.tls_key)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"
    url = f"{scheme}://127.0.0.1:{port}/"
    if CFG.mode == "solo":
        owner = auth.ensure_owner()
        url += f"#t={auth.new_session(owner['id'])}"
    print(f"«تراث» — {MODES[CFG.mode]['label']}")
    print(f"العنوان: {url if CFG.mode == 'solo' else f'{scheme}://<عنوان هذا الجهاز>:{port}/'}")
    if CFG.mode != "solo" and not auth.users():
        print("لا حسابات بعد: أنشئ المسؤول بالأمر  turath user add <اسم> --role admin")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
