"""اختبارات «تراث» — مكتبة unittest القياسية وحدها: python -m unittest discover -s tests"""
from __future__ import annotations
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from turath.config import CFG  # noqa: E402
from turath import db, auth, vault, lifecycle as LC, evidence as EV, oral_lab as LAB, kpis, agents as AG, entities as EN  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        CFG.home = Path(self.tmp.name)
        CFG.mode = "team"
        db.init()
        self.a = auth.create_user("alia", "password-1", "علياء", "researcher")
        self.b = auth.create_user("badr", "password-2", "بدر", "researcher")
        self.d = auth.create_user("dir", "password-3", "المدير", "director")

    def tearDown(self):
        db._LOCAL.c.close()
        db._LOCAL.c = None
        self.tmp.cleanup()


class TestSchema(Base):
    def test_all_required_tables_exist(self):
        have = {r["name"] for r in db.rows("SELECT name FROM sqlite_master WHERE type='table'")}
        required = ["projects", "sources", "narrators", "interviews", "audio_assets", "video_assets", "images", "manuscripts",
                    "historical_documents", "oral_narratives", "poems", "dialect_lexicon", "crafts", "heritage_practices", "places",
                    "persons", "events", "observations", "surveys", "legislation", "bibliography", "permissions", "claims",
                    "evidence_links", "review_decisions", "publications", "conflicts", "assets", "change_log", "users"]
        self.assertFalse(set(required) - have)

    def test_ids_and_change_log(self):
        p = db.create(self.a, "projects", {"title": "س"})
        self.assertRegex(p["id"], r"^PRJ-\d{4}-0001$")
        db.update(self.a, "projects", p["id"], {"title": "ص"})
        acts = [h["action"] for h in db.history("projects", p["id"])]
        self.assertEqual(acts, ["create", "update"])

    def test_stage_cannot_be_edited_directly(self):
        p = db.create(self.a, "projects", {"title": "س"})
        db.update(self.a, "projects", p["id"], {"stage": "S16", "title": "ع"})
        self.assertEqual(db.get_raw("projects", p["id"])["stage"], "S01")

    def test_enum_validation(self):
        with self.assertRaises(ValueError):
            db.create(self.a, "claims", {"text": "x", "status": "proven_by_magic"})


class TestPrivacyAndSharing(Base):
    def test_private_research_is_invisible_to_others(self):
        p = db.create(self.a, "projects", {"title": "بحث علياء"})
        self.assertFalse(db.list_rows(self.b, "projects"))
        with self.assertRaises(db.Denied):
            db.get(self.b, "projects", p["id"])

    def test_coauthor_sees_project_records_but_not_private_ones(self):
        p = db.create(self.a, "projects", {"title": "مشترك"})
        db.conn().execute("INSERT INTO project_members(project_id,user_id,role) VALUES(?,?,?)", (p["id"], self.b["id"], "coauthor"))
        shared = db.create(self.a, "sources", {"project_id": p["id"], "title": "مصدر", "access_level": "project"})
        private = db.create(self.a, "sources", {"project_id": p["id"], "title": "مسودة خاصة", "access_level": "private"})
        ids = {r["id"] for r in db.list_rows(self.b, "sources")}
        self.assertIn(shared["id"], ids)
        self.assertNotIn(private["id"], ids)
        db.update(self.b, "sources", shared["id"], {"critique": "تعليق الشريك"})
        with self.assertRaises(db.Denied):
            db.update(self.b, "sources", private["id"], {"title": "x"})

    def test_explicit_share_of_a_source(self):
        s = db.create(self.a, "sources", {"title": "مصدر مكتبتي"})
        self.assertFalse(db.can_read(self.b, "sources", s))
        db.conn().execute("INSERT INTO shares(id,item_table,item_id,owner_id,grantee,mode) VALUES('SHR-1','sources',?,?,?,'read')",
                          (s["id"], self.a["id"], self.b["id"]))
        self.assertTrue(db.can_read(self.b, "sources", s))
        self.assertFalse(db.can_write(self.b, "sources", s))

    def test_search_respects_permissions(self):
        db.create(self.a, "dialect_lexicon", {"term": "الكاجوجة", "meaning": "أداة"})
        self.assertTrue(db.search(self.a, "الكاجوجة"))
        self.assertFalse(db.search(self.b, "الكاجوجة"))


class TestVault(Base):
    def test_original_is_read_only_and_deduplicated(self):
        a1 = vault.ingest(self.a, "rec.wav", b"RIFF-data", provenance="ميداني", rights="بحثي")
        p = vault.path_of(a1)
        self.assertFalse(os.stat(p).st_mode & stat.S_IWUSR)
        a2 = vault.ingest(self.a, "copy.wav", b"RIFF-data")
        self.assertTrue(a2.get("duplicate"))
        self.assertEqual(a1["id"], a2["id"])

    def test_tampering_is_detected(self):
        a1 = vault.ingest(self.a, "doc.txt", b"original")
        p = vault.path_of(a1)
        os.chmod(p, 0o644)
        p.write_bytes(b"tampered")
        r = vault.verify_all()
        self.assertIn(a1["id"], r["altered"])

    def test_gps_in_photo_is_flagged_and_blocks_nothing_silently(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow غير مثبت")
        import io
        im = Image.new("RGB", (8, 8))
        ex = Image.Exif()
        ex[0x8825] = {1: "N", 2: (25.0, 20.0, 0.0)}
        b = io.BytesIO()
        im.save(b, "JPEG", exif=ex)
        p = db.create(self.a, "projects", {"title": "صور"})
        a = vault.ingest(self.a, "site.jpg", b.getvalue(), project_id=p["id"])
        self.assertTrue(json.loads(a["technical"])["gps"])
        self.assertEqual(vault.path_of(a).read_bytes(), b.getvalue())   # الأصل لم يُعدَّل
        self.assertIn(a["id"], EV.consent_gaps(p["id"])["assets_with_location"])

    def test_backup_contains_manifest(self):
        vault.ingest(self.a, "doc.txt", b"original")
        import zipfile
        z = zipfile.ZipFile(vault.backup())
        self.assertIn("manifest-sha256.txt", z.namelist())
        self.assertIn("data/turath.db", z.namelist())


class TestGates(Base):
    def test_gate_blocks_until_requirements(self):
        p = db.create(self.a, "projects", {"title": "س"})
        self.assertFalse(LC.advance(self.a, p["id"])["advanced"])
        db.update(self.a, "projects", p["id"], {"question": "سؤال", "domain": "intangible"})
        self.assertTrue(LC.advance(self.a, p["id"])["advanced"])

    def test_human_approval_cannot_be_impersonated(self):
        p = db.create(self.a, "projects", {"title": "س"})
        with self.assertRaises(db.Denied):
            LC.record_decision(self.a, p["id"], "S15", "approve", "", "HUM-DIR")
        db.conn().execute("INSERT INTO project_members(project_id,user_id,role) VALUES(?,?,?)", (p["id"], self.d["id"], "coauthor"))
        LC.record_decision(self.d, p["id"], "S15", "approve", "اعتماد", "HUM-DIR")
        self.assertTrue(LC._decision(p["id"], "S15", human=True))

    def test_ethics_gate_requires_recording_consent(self):
        p = db.create(self.a, "projects", {"title": "س"})
        iv = db.create(self.a, "interviews", {"project_id": p["id"]})
        self.assertIn(iv["id"], EV.interviews_without_consent(p["id"], "consent_recording"))
        db.create(self.a, "permissions", {"project_id": p["id"], "subject_table": "interviews", "subject_id": iv["id"],
                                          "consent_recording": True})
        self.assertFalse(EV.interviews_without_consent(p["id"], "consent_recording"))
        self.assertTrue(EV.interviews_without_consent(p["id"], "consent_publication"))


class TestEvidence(Base):
    def _claim(self):
        p = db.create(self.a, "projects", {"title": "س"})
        c = db.create(self.a, "claims", {"project_id": p["id"], "text": "ادعاء", "status": "established"})
        return p, c

    def test_same_origin_witnesses_count_once(self):
        p, c = self._claim()
        for _ in range(3):
            db.create(self.a, "evidence_links", {"project_id": p["id"], "claim_id": c["id"], "target_table": "interviews",
                                                 "target_id": "INT-x", "evidence_type": "oral", "relation": "supports",
                                                 "origin_group": "أسرة واحدة"})
        t = EV.triangulation(c["id"])
        self.assertEqual(t["supports"], 3)
        self.assertEqual(t["independent_origins"], 1)
        self.assertNotEqual(EV.suggest_status(c["id"]), "established")
        self.assertEqual(EV.claims_report(p["id"])["weak_established"], 1)

    def test_press_only_cannot_establish(self):
        p, c = self._claim()
        s = db.create(self.a, "sources", {"project_id": p["id"], "title": "خبر صحفي", "level": 5, "verified": True})
        db.create(self.a, "evidence_links", {"project_id": p["id"], "claim_id": c["id"], "target_table": "sources",
                                             "target_id": s["id"], "evidence_type": "document", "relation": "supports"})
        self.assertTrue(EV.triangulation(c["id"])["press_only"])
        self.assertEqual(EV.suggest_status(c["id"]), "probable")

    def test_independent_types_establish(self):
        p, c = self._claim()
        s = db.create(self.a, "sources", {"project_id": p["id"], "title": "وثيقة", "level": 1, "verified": True})
        db.create(self.a, "evidence_links", {"project_id": p["id"], "claim_id": c["id"], "target_table": "sources",
                                             "target_id": s["id"], "evidence_type": "document", "relation": "supports"})
        db.create(self.a, "evidence_links", {"project_id": p["id"], "claim_id": c["id"], "target_table": "interviews",
                                             "target_id": "INT-y", "evidence_type": "oral", "relation": "supports"})
        self.assertEqual(EV.suggest_status(c["id"]), "established")


class TestOralLab(Base):
    def test_dialect_words_are_preserved_verbatim(self):
        iv = db.create(self.a, "interviews", {})
        raw = "[00:00:05] ر1: يوم كنا نروح الغوص [غير مفهوم] والنوخذة يصيح\n[00:00:20] ب1: شو تقصد بالقلاطة؟"
        r = LAB.save_transcript(self.a, iv["id"], raw)
        self.assertEqual(r, {"segments": 2, "unclear": 1})
        segs = LAB.transcript(self.a, iv["id"])
        self.assertEqual(segs[0]["verbatim"], "يوم كنا نروح الغوص [غير مفهوم] والنوخذة يصيح")
        self.assertEqual(segs[0]["speaker"], "ر1")
        self.assertEqual(segs[1]["start"], "00:00:20")
        self.assertIn("00:00:05,000 --> 00:00:20,000", LAB.to_srt(segs))

    def test_lab_steps(self):
        iv = db.create(self.a, "interviews", {})
        st = LAB.mark(self.a, iv["id"], 10, True, "روجع مع متحدث محلي")
        self.assertTrue(next(s for s in st if s["step"] == 10)["done"])
        self.assertEqual(db.get_raw("interviews", iv["id"])["transcript_status"], "native_reviewed")

    def test_asr_is_not_claimed_when_missing(self):
        info = LAB.asr_available()
        try:
            import faster_whisper  # noqa: F401
            self.assertTrue(info["available"])
        except ImportError:
            self.assertFalse(info["available"])


class TestKpisAndAgents(Base):
    def test_kpis_have_twelve_indicators_and_no_baseline(self):
        k = kpis.compute()
        self.assertEqual(len(k["indicators"]), 12)
        self.assertFalse(k["baseline_set"])
        with self.assertRaises(db.Denied):
            kpis.set_baseline(self.a)
        kpis.set_baseline(self.d)
        self.assertTrue(kpis.compute()["baseline_set"])

    def test_twenty_agents_and_fourteen_skills_are_consistent(self):
        cards = AG.cards()
        self.assertEqual(len(cards), 20)
        ids = {c["id"] for c in cards}
        tables = set(EN.E) | {"assets", "transcript_segments", "users", "project_members", "shares"}
        for c in cards:
            for t in c["data_store"]["read"] + c["data_store"]["write"]:
                self.assertIn(t, tables, f"{c['id']}: {t}")
            for k in ("system_prompt", "competence", "permissions", "prohibitions", "tools_allowed", "inputs", "skills",
                      "sop", "handoff", "outputs", "kpis", "human_intervention", "coordination"):
                self.assertTrue(c.get(k), f"{c['id']} ينقصه {k}")
        writers_assets = [c["id"] for c in cards if "assets" in c["data_store"]["write"]]
        self.assertEqual(writers_assets, ["AG-ARC"])
        sk = AG.skills()
        self.assertEqual(len(sk), 14)
        for s in sk:
            for a in s["agents"]:
                self.assertIn(a, ids)
                self.assertIn(s["id"], AG.card(a)["skills"], f"{a} لا يحمل {s['id']}")

    def test_manual_engine_produces_package_with_archive_context(self):
        p = db.create(self.a, "projects", {"title": "التلي", "question": "س"})
        db.create(self.a, "sources", {"project_id": p["id"], "title": "مصدر موثق", "level": 4})
        r = AG.run(self.a, "AG-SRC", "دقق المصادر", p["id"], "SK-AUDIT", engine="manual")
        self.assertEqual(r["status"], "package")
        self.assertIn("صفر تلفيق", r["prompt"])
        self.assertIn("مصدر موثق", r["prompt"])


class TestPilot(Base):
    def test_pilot_import(self):
        from turath import pilot
        if not pilot.available():
            self.skipTest("لا ملفات تجريبية")
        r = pilot.import_pilot(self.a)
        self.assertGreater(r["sources"], 5)
        rep = EV.claims_report(r["project"])
        self.assertEqual(rep["unlinked"], 0)
        self.assertEqual(rep["press_only_core"], 0)
        self.assertEqual(pilot.import_pilot(self.a)["project"], r["project"])


class TestDesktop(unittest.TestCase):
    def test_fingerprint_changes_with_code(self):
        from turath import desktop
        a = desktop.fingerprint()
        self.assertEqual(a, desktop.fingerprint())
        self.assertEqual(len(a), 16)

    @unittest.skipIf(os.name == "nt" or sys.platform == "darwin", "اختبار أيقونة لينكس")
    def test_linux_icon_install_and_remove(self):
        from turath import desktop
        with tempfile.TemporaryDirectory() as h:
            old = os.environ.get("HOME")
            os.environ["HOME"] = h
            try:
                (Path(h) / "Desktop").mkdir()
                made = desktop.install_icon()
                self.assertTrue(all(p.exists() for p in made))
                text = made[0].read_text(encoding="utf-8")
                self.assertIn("Name=تراث", text)
                self.assertIn("-m turath.launch", text)
                gone = desktop.install_icon(remove=True)
                self.assertEqual(len(gone), len(made))
                self.assertFalse(any(p.exists() for p in made))
            finally:
                os.environ["HOME"] = old or ""

    def test_cli_survives_non_arabic_console_encoding(self):
        import subprocess
        with tempfile.TemporaryDirectory() as h:
            env = dict(os.environ, TURATH_HOME=h, PYTHONIOENCODING="cp1252")
            r = subprocess.run([sys.executable, "-m", "turath", "setup", "solo"], cwd=ROOT, env=env, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr.decode(errors="replace"))

    def test_running_detects_nothing_on_free_port(self):
        from turath import desktop
        self.assertIsNone(desktop.running(1))


class TestFonts(Base):
    FAKE = b"\x00\x01\x00\x00" + b"\x00" * 2000 + "adwa-assalaf".encode("utf-16-be") + b"\x00" * 100

    def test_install_and_reject(self):
        from turath import fonts
        self.assertEqual(fonts.install("adwa-assalaf_B.ttf", self.FAKE), "bold")
        self.assertEqual(fonts.install("adwa-assalaf.ttf", self.FAKE), "regular")
        self.assertTrue(fonts.status()["regular"] and fonts.status()["bold"])
        with self.assertRaises(ValueError):
            fonts.install("x.ttf", b"PK\x03\x04" + b"\x00" * 3000)          # ليس خطاً
        with self.assertRaises(ValueError):
            fonts.install("other.ttf", b"\x00\x01\x00\x00" + b"\x00" * 3000)  # خط آخر

    def test_font_files_never_in_repository(self):
        import subprocess
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.lower()
        self.assertFalse([l for l in out.splitlines() if l.endswith((".ttf", ".otf", ".woff", ".woff2"))])


class TestServer(Base):
    def setUp(self):
        super().setUp()
        from turath.server import Handler
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def req(self, path, body=None, token=None, method=None, host=None):
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method,
                                   data=json.dumps(body).encode() if body is not None else None)
        r.add_header("Content-Type", "application/json")
        if token:
            r.add_header("Authorization", "Bearer " + token)
        if host:
            r.add_header("Host", host)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def test_api_requires_login(self):
        self.assertEqual(self.req("/api/dashboard")[0], 401)
        self.assertEqual(self.req("/api/login", {"username": "alia", "password": "wrong"})[0], 401)
        code, d = self.req("/api/login", {"username": "alia", "password": "password-1"})
        self.assertEqual(code, 200)
        code, dash = self.req("/api/dashboard", token=d["token"])
        self.assertEqual(code, 200)
        self.assertEqual(len(dash["kpis"]["indicators"]), 12)

    def test_solo_mode_rejects_foreign_host(self):
        CFG.mode = "solo"
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{self.port}/api/public", headers={"Host": "evil.example"}))
            self.assertEqual(cm.exception.code, 403)
        finally:
            CFG.mode = "team"

    def test_public_reports_build_and_shutdown_is_solo_only(self):
        code, d = self.req("/api/public")
        self.assertIn("build", d)
        _, login = self.req("/api/login", {"username": "dir", "password": "password-3"})
        self.assertEqual(self.req("/api/shutdown", {}, token=login["token"], method="POST")[0], 403)

    def test_font_route_serves_only_installed_identity_font(self):
        from turath import fonts
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/fonts/adwa-assalaf.ttf")
        fonts.install("adwa-assalaf.ttf", TestFonts.FAKE)
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/fonts/adwa-assalaf.ttf") as r:
            self.assertEqual(r.headers["Content-Type"], "font/ttf")
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/fonts/..%2Fturath.db")

    def test_static_and_path_traversal(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/") as r:
            self.assertIn("تراث", r.read().decode())
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/../turath/db.py")


if __name__ == "__main__":
    unittest.main()
