"""تعريف كيانات الأرشيف المعرفي — المصدر الوحيد للمخطط والنماذج والواجهة.

كل كيان يُولَّد منه: جدول SQLite، ونموذج الإدخال في اللوحة، وأعمدة التصدير، وفهرس البحث.
الأعمدة المشتركة تُضاف آلياً لكل كيان (انظر COMMON).
"""
from __future__ import annotations

# (الاسم، التسمية، النوع) — الأنواع: text · long · int · real · date · bool · enum:a|b · ref:table · json
COMMON = [
    ("id", "المعرّف", "text"),
    ("project_id", "المشروع", "ref:projects"),
    ("owner_id", "المالك", "text"),
    ("access_level", "مستوى الإتاحة", "enum:private|project|shared|public"),
    ("rights", "الحقوق وشروط الاستخدام", "long"),
    ("source_ref", "المصدر المرجعي", "text"),
    ("created_at", "تاريخ الإنشاء", "text"),
    ("updated_at", "تاريخ التعديل", "text"),
]

LEVELS = {1: "وثائق أولية وأرشيفات أصلية", 2: "شهادات شفهية موثقة وملاحظات ميدانية",
          3: "أبحاث محكّمة ورسائل جامعية", 4: "إصدارات رسمية مؤسسية", 5: "صحافة ومواقع عامة"}

NARRATIVE_TYPES = {
    "direct_witness": "مشاهدة مباشرة", "personal_memory": "ذاكرة شخصية",
    "transmitted": "رواية منقولة عن شاهد", "collective": "موروث جمعي",
    "symbolic": "حكاية رمزية", "reinterpretation": "تخمين أو إعادة تفسير لاحقة",
}

EVIDENCE_TYPES = {
    "oral": "شهادة شفهية", "document": "وثيقة تاريخية", "material": "دليل مكاني أو مادي",
    "photo": "صورة تاريخية", "poetry": "مادة شعرية", "independent_oral": "رواية مستقلة أخرى",
}

REGIONS = "coastal|desert|oasis|mountain|urban|contact"
REGION_LABELS = {"coastal": "المجتمعات الساحلية والبحرية", "desert": "المجتمعات الصحراوية والبدوية",
                 "oasis": "مجتمعات الواحات والزراعة", "mountain": "المجتمعات الجبلية",
                 "urban": "الحواضر التاريخية والأسواق", "contact": "مناطق التواصل التجاري والهجرات"}

EMIRATES = "abu_dhabi|dubai|sharjah|ajman|umm_al_quwain|ras_al_khaimah|fujairah|multi"

DOMAINS = {
    "history_society": "التاريخ والمجتمع", "material": "التراث المادي", "intangible": "التراث غير المادي",
    "crafts_economy": "الحرف والاقتصاد التقليدي", "natural": "التراث الطبيعي والبيئي",
    "legal": "التراث القانوني والمؤسسي",
}

E: dict[str, dict] = {
    "projects": {"prefix": "PRJ", "label": "المشاريع", "one": "مشروع", "icon": "folder", "group": "core", "fields": [
        ("title", "عنوان المشروع", "text"), ("domain", "المجال", "enum:" + "|".join(DOMAINS)),
        ("question", "السؤال البحثي", "long"), ("gap", "الفجوة البحثية", "long"),
        ("region", "النطاق الجغرافي الثقافي", "enum:" + REGIONS), ("emirate", "الإمارة", "enum:" + EMIRATES),
        ("localities", "المدن والمناطق", "text"), ("output_type", "نوع المخرج", "text"),
        ("stage", "المرحلة", "text"), ("status", "الحالة", "enum:active|paused|closed"),
        ("lead_agent", "الوكيل القائد", "text"), ("summary", "الملخص", "long")]},
    "sources": {"prefix": "SRC", "label": "المصادر", "one": "مصدر", "icon": "book", "group": "evidence", "fields": [
        ("title", "العنوان", "text"), ("creator", "المؤلف أو الجهة", "text"), ("year", "السنة", "text"),
        ("publisher", "الناشر أو الحافظ", "text"), ("kind", "النوع",
         "enum:book|article|thesis|manuscript|archival|oral|photo|film|map|poem|object|field_note|legal|web|report"),
        ("level", "مستوى المصدر (1–5)", "int"), ("url", "الرابط", "text"), ("doi", "DOI (إن وُجد فعلاً)", "text"),
        ("pages", "الصفحات", "text"), ("language", "اللغة", "text"), ("accessed", "تاريخ الاطلاع", "date"),
        ("verified", "تحقّق من وجوده", "bool"), ("critique", "نقد المصدر وملاءمته", "long"), ("asset_id", "الأصل الرقمي", "ref:assets")]},
    "narrators": {"prefix": "NAR", "label": "الرواة", "one": "راوٍ", "icon": "people", "group": "oral", "fields": [
        ("code", "الرمز المصرّح به", "text"), ("display_name", "الاسم (عند الإذن)", "text"),
        ("name_permitted", "أذن بإظهار اسمه", "bool"), ("birth_year", "سنة الميلاد التقريبية", "text"),
        ("gender", "الجنس", "enum:m|f"), ("locality", "البلدة أو المنطقة", "text"), ("region", "النطاق", "enum:" + REGIONS),
        ("emirate", "الإمارة", "enum:" + EMIRATES), ("occupation", "المهنة أو الأصل المهني", "text"),
        ("dialect_notes", "ملاحظات اللهجة", "long"), ("bio", "سيرة مختصرة", "long")]},
    "interviews": {"prefix": "INT", "label": "المقابلات", "one": "مقابلة", "icon": "mic", "group": "oral", "fields": [
        ("narrator_id", "الراوي", "ref:narrators"), ("researcher", "الباحث", "text"), ("date", "تاريخ المقابلة", "date"),
        ("place", "مكان المقابلة", "text"), ("conditions", "ظروف المقابلة والحاضرون", "long"),
        ("archive_code", "المعرّف الأرشيفي الثابت", "text"), ("asset_id", "الملف", "ref:assets"),
        ("duration", "المدة", "text"), ("topics", "الموضوعات", "long"), ("bias_notes", "مراجعة التحيز وأثر الحضور", "long"),
        ("lab_stage", "مرحلة المختبر", "int"), ("transcript_status", "حالة التفريغ", "enum:none|draft|native_reviewed|approved")]},
    "audio_assets": {"prefix": "AUD", "label": "الأصول الصوتية", "one": "أصل صوتي", "icon": "wave", "group": "media", "fields": [
        ("title", "العنوان", "text"), ("asset_id", "الملف الأصلي", "ref:assets"), ("interview_id", "المقابلة", "ref:interviews"),
        ("format", "الصيغة", "text"), ("duration", "المدة", "text"), ("recorded_on", "تاريخ التسجيل", "date"),
        ("recordist", "المسجِّل", "text"), ("condition", "حالة الأصل", "text"), ("lab_stage", "مرحلة المختبر", "int")]},
    "video_assets": {"prefix": "VID", "label": "الأصول المرئية", "one": "أصل مرئي", "icon": "play", "group": "media", "fields": [
        ("title", "العنوان", "text"), ("asset_id", "الملف الأصلي", "ref:assets"), ("interview_id", "المقابلة", "ref:interviews"),
        ("format", "الصيغة", "text"), ("duration", "المدة", "text"), ("recorded_on", "تاريخ التصوير", "date"),
        ("camera_operator", "المصوّر", "text"), ("lab_stage", "مرحلة المختبر", "int")]},
    "images": {"prefix": "IMG", "label": "الصور", "one": "صورة", "icon": "camera", "group": "media", "fields": [
        ("title", "العنوان", "text"), ("asset_id", "الملف الأصلي", "ref:assets"), ("track", "المسار البصري",
         "enum:documentary|analytical|conceptual"), ("photographer", "المصوّر", "text"), ("date_taken", "تاريخ الالتقاط", "text"),
        ("place_id", "المكان", "ref:places"), ("provenance", "سلسلة المصدر", "long"), ("description", "الوصف المرئي دون تخمين", "long"),
        ("subjects", "الموضوعات", "text"), ("evidence_limits", "حدود الدليل", "long")]},
    "manuscripts": {"prefix": "MSS", "label": "المخطوطات", "one": "مخطوط", "icon": "scroll", "group": "documents", "fields": [
        ("title", "العنوان", "text"), ("author", "المؤلف أو الناسخ", "text"), ("date_text", "التاريخ المدوّن", "text"),
        ("holding", "الجهة الحافظة ورقم الحفظ", "text"), ("folios", "الأوراق", "text"), ("script", "نوع الخط", "text"),
        ("condition", "الحالة المادية", "text"), ("asset_id", "النسخة الرقمية", "ref:assets"), ("notes", "ملاحظات التحقيق", "long")]},
    "historical_documents": {"prefix": "DOC", "label": "الوثائق التاريخية", "one": "وثيقة", "icon": "archive", "group": "documents", "fields": [
        ("title", "العنوان", "text"), ("doc_type", "النوع", "enum:letter|deed|court|treaty|report|map|register|other"),
        ("date_text", "التاريخ", "text"), ("issuer", "المُصدِر", "text"), ("recipient", "المرسَل إليه", "text"),
        ("holding", "الجهة الحافظة والرقم المرجعي", "text"), ("asset_id", "النسخة الرقمية", "ref:assets"),
        ("external_critique", "النقد الخارجي", "long"), ("internal_critique", "النقد الداخلي", "long")]},
    "oral_narratives": {"prefix": "ORN", "label": "الروايات الشفهية", "one": "رواية", "icon": "quote", "group": "oral", "fields": [
        ("title", "العنوان", "text"), ("interview_id", "المقابلة", "ref:interviews"), ("narrator_id", "الراوي", "ref:narrators"),
        ("narrative_type", "نوع الرواية", "enum:" + "|".join(NARRATIVE_TYPES)), ("timecode", "الموضع الزمني", "text"),
        ("text_verbatim", "النص الحرفي", "long"), ("summary", "الخلاصة", "long"), ("event_date_text", "زمن الحدث المروي", "text"),
        ("gap_years", "الفاصل بين الحدث والتسجيل (سنوات)", "int"), ("chain", "سلسلة النقل", "long"),
        ("critique", "النقد الخارجي والداخلي", "long")]},
    "poems": {"prefix": "PEM", "label": "الشعر والأهازيج", "one": "قصيدة", "icon": "feather", "group": "oral", "fields": [
        ("title", "العنوان أو المطلع", "text"), ("genre", "النوع", "enum:nabati|hazij|song|chant|other"),
        ("poet", "الشاعر (إن عُرف)", "text"), ("reciter_id", "الراوي المنشد", "ref:narrators"), ("interview_id", "المقابلة", "ref:interviews"),
        ("timecode", "الموضع الزمني", "text"), ("text", "النص كما رُوي", "long"), ("meter", "البحر أو الطرق", "text"),
        ("variants", "الروايات المختلفة", "long"), ("occasion", "المناسبة", "text")]},
    "dialect_lexicon": {"prefix": "LEX", "label": "المعجم اللهجي", "one": "مفردة", "icon": "ear", "group": "oral", "fields": [
        ("term", "اللفظ المحلي", "text"), ("phonetic", "الضبط الصوتي", "text"), ("meaning", "المعنى", "long"),
        ("context", "السياق", "long"), ("region", "النطاق", "enum:" + REGIONS), ("locality", "المنطقة", "text"),
        ("narrator_id", "الراوي المستعمل", "ref:narrators"), ("interview_id", "المقابلة", "ref:interviews"), ("timecode", "الموضع الزمني", "text"),
        ("comparative", "الشواهد المقارنة", "long"), ("confidence", "درجة الثقة", "enum:high|medium|low")]},
    "crafts": {"prefix": "CRF", "label": "الحرف والمهن", "one": "حرفة", "icon": "loom", "group": "heritage", "fields": [
        ("name", "اسم الحرفة", "text"), ("category", "الفئة", "enum:sea|agri|pastoral|textile|wood_metal|trade|other"),
        ("materials", "المواد", "long"), ("tools", "الأدوات", "long"), ("techniques", "التقنيات والمراحل", "long"),
        ("practitioners", "الممارسون (بالرمز)", "text"), ("transmission", "طرق النقل بين الأجيال", "long"),
        ("viability", "حالة الحيوية", "enum:living|endangered|dormant|revived"), ("threats", "المخاطر", "long"), ("region", "النطاق", "enum:" + REGIONS)]},
    "heritage_practices": {"prefix": "HPR", "label": "العناصر والممارسات التراثية", "one": "عنصر", "icon": "star", "group": "heritage", "fields": [
        ("name", "اسم العنصر", "text"), ("domain", "المجال", "enum:" + "|".join(DOMAINS)), ("description", "الوصف", "long"),
        ("community", "الجماعة الحاملة", "text"), ("region", "النطاق", "enum:" + REGIONS), ("emirate", "الإمارة", "enum:" + EMIRATES),
        ("viability", "الحيوية", "enum:living|endangered|dormant|revived"), ("inscription", "التسجيل الوطني أو الدولي", "text"),
        ("risk_level", "مستوى خطر الفقدان", "enum:low|medium|high|critical"), ("safeguarding", "تدابير الصون", "long")]},
    "places": {"prefix": "PLC", "label": "الأماكن", "one": "مكان", "icon": "map-pin", "group": "context", "fields": [
        ("name", "الاسم", "text"), ("alt_names", "أسماء أخرى", "text"), ("kind", "النوع",
         "enum:town|village|oasis|port|souq|fort|well|falaj|mountain|desert|site|other"),
        ("emirate", "الإمارة", "enum:" + EMIRATES), ("region", "النطاق", "enum:" + REGIONS),
        ("lat", "خط العرض", "real"), ("lon", "خط الطول", "real"), ("sensitive", "موقع حساس (تُحجب الإحداثيات)", "bool"),
        ("description", "الوصف", "long")]},
    "persons": {"prefix": "PER", "label": "الأشخاص", "one": "شخص", "icon": "people", "group": "context", "fields": [
        ("name", "الاسم", "text"), ("dates", "التواريخ", "text"), ("role", "الدور أو الصفة", "text"),
        ("family", "الأسرة أو البيت", "text"), ("place_id", "المكان", "ref:places"), ("bio", "السيرة الموثقة", "long")]},
    "events": {"prefix": "EVT", "label": "الأحداث", "one": "حدث", "icon": "calendar", "group": "context", "fields": [
        ("title", "الحدث", "text"), ("date_from", "من", "text"), ("date_to", "إلى", "text"), ("date_certainty", "يقين التاريخ",
         "enum:exact|approximate|disputed|unknown"), ("place_id", "المكان", "ref:places"), ("description", "الوصف", "long")]},
    "observations": {"prefix": "OBS", "label": "الملاحظات الميدانية", "one": "ملاحظة", "icon": "eye", "group": "field", "fields": [
        ("date", "التاريخ", "date"), ("place_id", "المكان", "ref:places"), ("observer", "الملاحِظ", "text"),
        ("mode", "النوع", "enum:direct|participant"), ("activity", "النشاط الملاحَظ", "text"), ("description", "الوصف", "long"),
        ("reflexive", "الملاحظات الانعكاسية", "long"), ("bias_review", "مراجعة التحيز", "long")]},
    "surveys": {"prefix": "SRV", "label": "المسوح والاستبانات", "one": "مسح", "icon": "chart", "group": "field", "fields": [
        ("title", "العنوان", "text"), ("population", "مجتمع الدراسة", "long"), ("sampling", "خطة المعاينة", "long"),
        ("instrument", "الأداة (أسئلة JSON)", "json"), ("responses", "عدد الاستجابات", "int"),
        ("status", "الحالة", "enum:design|pilot|fielding|closed"), ("results_quant", "نتائج كمية", "long"),
        ("results_qual", "نتائج نوعية", "long")]},
    "legislation": {"prefix": "LEG", "label": "التشريعات", "one": "تشريع", "icon": "scale", "group": "documents", "fields": [
        ("title", "العنوان", "text"), ("jurisdiction", "النطاق", "enum:federal|local|gcc|international"),
        ("number_year", "الرقم والسنة (كما في النص الرسمي)", "text"), ("issuer", "الجهة المصدرة", "text"),
        ("status_text", "حالة النفاذ", "enum:in_force|amended|repealed|unverified"), ("official_url", "المصدر الرسمي", "text"),
        ("topics", "الموضوعات", "text"), ("analysis", "التحليل", "long")]},
    "bibliography": {"prefix": "BIB", "label": "قائمة المراجع", "one": "مرجع", "icon": "book", "group": "evidence", "fields": [
        ("source_id", "المصدر", "ref:sources"), ("style", "النمط", "enum:apa7|chicago_nb"), ("formatted", "الإحالة المنسقة", "long"),
        ("public_list", "يُدرج في القائمة العامة", "bool")]},
    "permissions": {"prefix": "PRM", "label": "الموافقات والأذونات", "one": "موافقة", "icon": "handshake", "group": "ethics", "fields": [
        ("subject_table", "نوع المادة", "text"), ("subject_id", "معرّف المادة", "text"), ("grantor", "المانح (رمز)", "text"),
        ("consent_recording", "موافقة التسجيل", "bool"), ("consent_transcription", "موافقة التفريغ", "bool"),
        ("consent_publication", "موافقة النشر", "bool"), ("consent_commercial", "موافقة الاستخدام التجاري", "bool"),
        ("restrictions", "القيود وطلبات الحجب", "long"), ("granted_on", "تاريخ المنح", "date"),
        ("review_on", "تاريخ المراجعة المستمرة", "date"), ("withdrawn", "سُحبت الموافقة", "bool"), ("document_asset", "وثيقة الموافقة", "ref:assets")]},
    "claims": {"prefix": "CLM", "label": "الادعاءات العلمية", "one": "ادعاء", "icon": "check", "group": "evidence", "fields": [
        ("text", "نص الادعاء", "long"), ("kind", "طبيعته", "enum:measured|narrative|inference|hypothesis|model"),
        ("status", "الحالة", "enum:established|probable|disputed|hypothesis|pending_field|rejected"),
        ("topic", "الموضوع", "text"), ("notes", "ملاحظات", "long")]},
    "evidence_links": {"prefix": "EVL", "label": "روابط الأدلة", "one": "رابط دليل", "icon": "link", "group": "evidence", "fields": [
        ("claim_id", "الادعاء", "ref:claims"), ("target_table", "نوع الدليل", "text"), ("target_id", "معرّف الدليل", "text"),
        ("evidence_type", "صنف التثليث", "enum:" + "|".join(EVIDENCE_TYPES)), ("relation", "العلاقة", "enum:supports|contradicts|context"),
        ("locator", "الموضع (صفحة/توقيت/ورقة)", "text"), ("excerpt", "الشاهد", "long"), ("origin_group", "أصل الشهادة (لفحص الاستقلال)", "text")]},
    "review_decisions": {"prefix": "REV", "label": "قرارات المراجعة", "one": "قرار", "icon": "gate", "group": "quality", "fields": [
        ("subject_table", "نوع المادة", "text"), ("subject_id", "المعرّف", "text"), ("gate", "البوابة", "text"),
        ("reviewer", "المراجع", "text"), ("reviewer_role", "صفة المراجع", "text"),
        ("decision", "القرار", "enum:approve|approve_with_changes|revise|reject|escalate"), ("rationale", "التعليل", "long")]},
    "publications": {"prefix": "PUB", "label": "المنشورات", "one": "منشور", "icon": "book", "group": "quality", "fields": [
        ("title", "العنوان", "text"), ("output_type", "نوع المخرج", "text"), ("formats", "الصيغ", "text"),
        ("status", "الحالة", "enum:draft|peer_review|legal_review|approved|published"), ("peer_review", "نتيجة التحكيم", "enum:none|pending|passed|failed"),
        ("published_on", "تاريخ النشر", "date"), ("doi_or_handle", "المعرّف الدائم", "text"), ("asset_id", "الملف", "ref:assets")]},
    "conflicts": {"prefix": "CNF", "label": "سجل التعارضات", "one": "تعارض", "icon": "alert", "group": "evidence", "fields": [
        ("topic", "موضوع التعارض", "text"), ("positions", "المواقف وأسانيدها (JSON)", "json"), ("claim_id", "الادعاء", "ref:claims"),
        ("status", "الحالة", "enum:open|explained|resolved_by_evidence"), ("analysis", "التحليل دون تسوية مصطنعة", "long")]},
}

# جداول نظامية خارج النماذج العامة
SYSTEM_TABLES = """
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT,
  pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'researcher', created_at TEXT, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT, expires_at REAL);
CREATE TABLE IF NOT EXISTS project_members(project_id TEXT, user_id TEXT, role TEXT DEFAULT 'coauthor',
  added_at TEXT, PRIMARY KEY(project_id, user_id));
CREATE TABLE IF NOT EXISTS shares(id TEXT PRIMARY KEY, item_table TEXT, item_id TEXT, owner_id TEXT,
  grantee TEXT, mode TEXT DEFAULT 'read', created_at TEXT);
CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, filename TEXT, mime TEXT, size INTEGER,
  kind TEXT, vault_path TEXT, project_id TEXT, owner_id TEXT, access_level TEXT DEFAULT 'private', provenance TEXT,
  rights TEXT, depositor TEXT, technical TEXT, created_at TEXT, updated_at TEXT, last_verified TEXT, integrity TEXT DEFAULT 'ok');
CREATE TABLE IF NOT EXISTS transcript_segments(id TEXT PRIMARY KEY, interview_id TEXT NOT NULL, seq INTEGER,
  start TEXT, end TEXT, speaker TEXT, verbatim TEXT, readable TEXT, unclear INTEGER DEFAULT 0, dialect_terms TEXT,
  entities TEXT, reviewed_by TEXT, corrections INTEGER DEFAULT 0, owner_id TEXT, project_id TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS change_log(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, user_id TEXT, action TEXT,
  item_table TEXT, item_id TEXT, before TEXT, after TEXT);
CREATE TABLE IF NOT EXISTS stage_log(seq INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, at TEXT, user_id TEXT,
  from_stage TEXT, to_stage TEXT, gate_report TEXT);
CREATE TABLE IF NOT EXISTS lab_steps(interview_id TEXT, step INTEGER, done INTEGER DEFAULT 0, by_user TEXT, at TEXT, note TEXT,
  PRIMARY KEY(interview_id, step));
CREATE TABLE IF NOT EXISTS agent_runs(id TEXT PRIMARY KEY, agent_id TEXT, skill_id TEXT, project_id TEXT, user_id TEXT,
  engine TEXT, task TEXT, prompt TEXT, output TEXT, status TEXT, created_at TEXT, reviewed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS counters(prefix TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
"""


def ftype(t: str) -> str:
    return {"int": "INTEGER", "real": "REAL", "bool": "INTEGER"}.get(t, "TEXT")


def fields_of(table: str) -> list[tuple[str, str, str]]:
    return COMMON + E[table]["fields"]


def title_of(table: str, row: dict) -> str:
    for k in ("title", "name", "term", "display_name", "code", "topic", "text", "filename"):
        if row.get(k):
            return str(row[k])[:120]
    return row.get("id", "")


def ddl() -> str:
    out = [SYSTEM_TABLES]
    for t in E:
        cols = []
        for name, _, typ in fields_of(t):
            cols.append(f"{name} {ftype(typ)}" + (" PRIMARY KEY" if name == "id" else ""))
        out.append(f"CREATE TABLE IF NOT EXISTS {t}({', '.join(cols)});")
        out.append(f"CREATE INDEX IF NOT EXISTS ix_{t}_proj ON {t}(project_id);")
    out.append("CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(item_table UNINDEXED, item_id UNINDEXED, "
               "project_id UNINDEXED, title, body, tokenize='unicode61 remove_diacritics 2');")
    return "\n".join(out)


def schema_for_ui() -> dict:
    return {t: {"prefix": v["prefix"], "label": v["label"], "one": v["one"], "icon": v["icon"], "group": v["group"],
                "fields": [{"name": n, "label": l, "type": ty} for n, l, ty in v["fields"]]} for t, v in E.items()}
