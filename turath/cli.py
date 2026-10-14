"""واجهة الأوامر: turath setup · serve · user · verify · backup · status · skills-gen · pilot."""
from __future__ import annotations
import argparse
import getpass
import json
import sys

from . import __version__
from .config import CFG, MODES


def _init(home=None):
    if home:
        CFG.use_home(home)
    from . import db
    db.init()


def cmd_setup(a):
    _init(a.home)
    CFG.mode = a.mode
    if a.port:
        CFG.port = a.port
    if a.cert and a.key:
        CFG.tls_cert, CFG.tls_key = a.cert, a.key
    CFG.save()
    from . import auth
    print(f"النمط: {MODES[CFG.mode]['label']} · المجلد: {CFG.home}")
    if CFG.mode == "solo":
        auth.ensure_owner()
        print("لا حاجة إلى حسابات: الدخول برمز يتولد عند كل تشغيل.")
    elif not auth.users() or not [u for u in auth.users() if u["role"] in ("admin", "director")]:
        name = a.admin or input("اسم حساب المسؤول: ").strip()
        pw = getpass.getpass("كلمة المرور (8 أحرف على الأقل): ")
        role = "director" if CFG.mode == "lan" else "admin"
        auth.create_user(name, pw, name, role)
        print(f"أُنشئ الحساب «{name}» بصفة {auth.ROLES[role]}.")


def cmd_serve(a):
    _init(a.home)
    from .server import serve
    serve(open_browser=not a.no_browser, port=a.port)


def cmd_user(a):
    _init(a.home)
    from . import auth
    if a.action == "add":
        pw = a.password or getpass.getpass("كلمة المرور: ")
        print(json.dumps(auth.create_user(a.username, pw, a.display or a.username, a.role), ensure_ascii=False))
    else:
        for u in auth.users():
            print(f"{u['username']:<20} {auth.ROLES.get(u['role'], u['role'])}")


def cmd_verify(a):
    _init(a.home)
    from . import vault
    r = vault.verify_all()
    print(f"سليم: {r['ok']} · مفقود: {len(r['missing'])} · معدّل: {len(r['altered'])}")
    sys.exit(1 if r["missing"] or r["altered"] else 0)


def cmd_backup(a):
    _init(a.home)
    from . import vault
    print(vault.backup())


def cmd_status(a):
    _init(a.home)
    from . import kpis, agents, oral_lab
    k = kpis.compute()
    print(f"«تراث» {__version__} · {MODES[CFG.mode]['label']} · {CFG.home}")
    for i in k["indicators"]:
        v = "—" if i["value"] is None else f"{i['value']}{i['unit']}"
        print(f"  {i['label']}: {v}")
    print("المحركات:", ", ".join(f"{n}={'متاح' if e['available'] else 'غير متاح'}" for n, e in agents.engines().items()))
    print("التفريغ الآلي:", "متاح" if oral_lab.asr_available()["available"] else "غير مثبت")


def cmd_skills_gen(a):
    from .skillgen import generate
    for p in generate():
        print(p)


def cmd_docs_gen(a):
    from .docgen import generate
    from .skillgen import generate as gen_skills
    for p in generate() + gen_skills():
        print(p)


def cmd_forms_gen(a):
    from .forms import generate
    for p in generate():
        print(p)


def cmd_pilot(a):
    _init(a.home)
    from . import auth, pilot, db
    owner = auth.ensure_owner() if CFG.mode == "solo" else db.one("SELECT * FROM users WHERE username=?", (a.user,))
    if not owner:
        sys.exit("حدد المستخدم بـ --user")
    print(json.dumps(pilot.import_pilot(dict(owner)), ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="turath", description="«تراث» — إدارة الدراسات والبحوث التراثية الإماراتية")
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--home", help="مجلد البيانات (الافتراضي ~/Turath أو TURATH_HOME)")
    sp = ap.add_subparsers(dest="cmd")
    s = sp.add_parser("setup", help="إعداد النمط: solo · lan · team")
    s.add_argument("mode", choices=list(MODES))
    s.add_argument("--port", type=int)
    s.add_argument("--admin")
    s.add_argument("--cert")
    s.add_argument("--key")
    s.set_defaults(fn=cmd_setup)
    s = sp.add_parser("serve", help="تشغيل لوحة التحكم")
    s.add_argument("--port", type=int)
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(fn=cmd_serve)
    s = sp.add_parser("user", help="الحسابات")
    s.add_argument("action", choices=["add", "list"])
    s.add_argument("username", nargs="?")
    s.add_argument("--role", default="researcher")
    s.add_argument("--display")
    s.add_argument("--password")
    s.set_defaults(fn=cmd_user)
    sp.add_parser("verify", help="فحص سلامة الأصول ببصماتها").set_defaults(fn=cmd_verify)
    sp.add_parser("backup", help="نسخة احتياطية كاملة").set_defaults(fn=cmd_backup)
    sp.add_parser("status", help="المؤشرات والمحركات").set_defaults(fn=cmd_status)
    sp.add_parser("skills-gen", help="توليد مهارات Claude Code من سجل المهارات").set_defaults(fn=cmd_skills_gen)
    sp.add_parser("docs-gen", help="توليد وثائق المخطط والوكلاء والمهارات ومهارات Claude Code").set_defaults(fn=cmd_docs_gen)
    sp.add_parser("forms-gen", help="توليد الاستمارات بصيغة Word بالهوية البصرية").set_defaults(fn=cmd_forms_gen)
    s = sp.add_parser("pilot", help="استيراد النموذج التطبيقي التجريبي")
    s.add_argument("--user")
    s.set_defaults(fn=cmd_pilot)
    a = ap.parse_args(argv)
    if not getattr(a, "fn", None):
        a = ap.parse_args(["serve"] + (argv or sys.argv[1:]))
    if not hasattr(a, "home"):
        a.home = None
    a.fn(a)
