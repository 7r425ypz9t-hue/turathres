"""تنقية المخرج واللغة البشرية المحكمة — منقولة من «باحث» (SKL-CLEANOUT وSKL-HUMANLANG) ومكيّفة لـ«تراث».

- الوسوم والملاحظات الإنجليزية تُستبدل بترجمتها العربية بين قوسين؛ والنص الإنجليزي الحر داخلها يُحذف ويُبلَّغ عنه (لا ترجمة تخمينية).
- العلامات المائية المخفية (محارف غير مرئية ومسافات شاذة) والظاهرة (علامات التشغيل وعبارات «كُتب بواسطة») تُزال.
- مقياس اللغة البشرية: لوازم الصياغة الآلية والشَّرطة الطويلة والملاحظات الإنجليزية.
فرق مقصود عن «باحث»: معرّفات الأرشيف (SRC-… · INT-… · CLM-…) تبقى في النص لأنها إحالات التتبع إلى الأصل.
وتنبيه: التنقية لا تمس النص الحرفي للتفريغ؛ فهي لمخرجات الوكلاء وملفات التصدير وحدها.
"""
from __future__ import annotations
import io
import re
import zipfile

NOTES = {"FACT": ("واقعة", "drop"), "EBI": ("استنتاج من الدليل", "drop"), "INTERP": ("تفسير", "drop"), "HYP": ("فرضية", "drop"),
         "AUTHOR": ("قرار المؤلف", "keep"), "NEEDS-EVIDENCE": ("يحتاج توثيقاً", "keep"), "CITATION-NEEDED": ("يحتاج إحالة", "keep"),
         "TODO": ("للإكمال", "keep"), "TBD": ("يُحدَّد لاحقاً", "keep"), "NOTE": ("ملاحظة", "keep"), "CHECK": ("للتحقق", "keep"),
         "VERIFY": ("للتحقق", "keep"), "PENDING-FIELD": ("معلّق ميدانياً", "keep"), "UNCLEAR": ("غير مفهوم", "keep")}
PHRASES = {"pending approval": "بانتظار الاعتماد", "awaiting approval": "بانتظار الاعتماد", "source needed": "يحتاج مصدراً",
           "citation needed": "يحتاج إحالة", "needs evidence": "يحتاج توثيقاً", "to be verified": "للتحقق", "to be confirmed": "للتأكيد",
           "not verified": "غير متحقق", "unverified": "غير متحقق", "fieldwork needed": "يحتاج جمعاً ميدانياً"}
SECTIONS = {"NOTES": "ملاحظات الوكيل", "NOTE": "ملاحظة", "SOURCES": "المصادر", "REFERENCES": "المراجع", "SUMMARY": "الخلاصة",
            "CHANGES": "التعديلات", "QUESTIONS": "أسئلة للمراجع", "HANDOFF": "التسليم", "CLAIMS": "الادعاءات"}
INVISIBLE = [(0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0xFEFF, 0xFEFF), (0x00AD, 0x00AD), (0xFE00, 0xFE0F),
             (0xE0000, 0xE007F), (0x180E, 0x180E), (0x034F, 0x034F), (0x061C, 0x061C)]
ODD_SPACES = [0x00A0, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000]
VISIBLE = [r"===BEGIN_TEXT===|===END_TEXT===", r"(?m)^\s*(?:Generated|Written|Drafted) (?:by|with) [^\n]*$",
           r"(?im)^\s*(?:as an ai|i am an ai)[^\n]*$"]
STOCK = ["في عالمنا المعاصر", "في عالمنا اليوم", "في عالم اليوم", "في ظل التحولات المتسارعة", "لا يخفى على أحد", "تجدر الإشارة إلى",
         "ومن الجدير بالذكر", "من نافلة القول", "في الختام", "خلاصة القول", "وفي الختام", "يلعب دوراً", "يلعب دورًا", "دوراً محورياً",
         "حجر الزاوية", "حجر الأساس", "تسليط الضوء", "يسلط الضوء", "بالغ الأهمية", "أهمية بالغة", "على حد سواء", "في هذا السياق",
         "وفي هذا الإطار", "آفاقاً جديدة", "غني عن البيان", "الإرث العريق", "عبق الماضي", "أصالة الماضي"]
RULES = ["اكتب بعربية بشرية محكمة: جملة تؤدي معنى، لا قوالب جاهزة ولا لوازم لفظية متكررة.",
         "كل ملاحظة أو وسم داخل النص يُكتب بالعربية بين قوسين؛ لا إنجليزية إلا مصطلح علمي يُذكر بعد مقابله العربي.",
         "لا علامات تشغيل ولا محارف خفية؛ وتبقى معرّفات الأرشيف إحالات تتبع.",
         "لا شَرطة طويلة لوصل الجمل، ولا ثلاثيات متتالية مصطنعة، ولا افتتاح بعبارات العموم ولا ختام بعبارات التلخيص الجاهزة.",
         "لا عبارات إنشائية عن التراث («عبق الماضي»، «الإرث العريق»)؛ الوصف يقوم على الدليل."]

TAG_RE = re.compile(r"\[(?P<tag>[A-Z][A-Z-]{1,20})(?:\s*[—–:\-]\s*(?P<body>[^\]\n]*))?\]")
LATIN = re.compile(r"[A-Za-z]{3,}")
ARABIC = re.compile(r"[ء-ي]")
ARCHIVE_ID = re.compile(r"^[A-Z]{2,4}-\d{4}-\d{4}")
_HIDDEN = re.compile("[" + "".join(f"\\U{a:08X}-\\U{b:08X}" for a, b in INVISIBLE) + "]")
_SPACES = re.compile("[" + "".join(f"\\U{c:08X}" for c in ODD_SPACES) + "]")


def hidden(text: str) -> tuple[str, int]:
    text, n1 = _HIDDEN.subn("", text)
    text, n2 = _SPACES.subn(" ", text)
    return text, n1 + n2


def _phrases(body: str) -> str:
    for en, ar in PHRASES.items():
        body = re.sub(rf"\b{re.escape(en)}\b", ar, body, flags=re.I)
    return body


def notes(text: str, mode: str = "reading") -> tuple[str, dict]:
    rep = {"translated": 0, "dropped": 0, "english_removed": []}

    def sub(m: re.Match) -> str:
        if ARCHIVE_ID.match(m.group(0)[1:]):
            return m.group(0)
        tag, body = m.group("tag"), (m.group("body") or "").strip()
        spec = NOTES.get(tag)
        if not spec:
            if LATIN.search(tag + " " + body) and not ARABIC.search(body):
                rep["english_removed"].append(m.group(0))
                return ""
            return m.group(0)
        ar, reading = spec
        if mode == "reading" and reading == "drop":
            rep["dropped"] += 1
            return ""
        body = _phrases(body) if body else ""
        if body and LATIN.search(re.sub(r"\([^)]*\)", "", body)) and not ARCHIVE_ID.search(body):
            rep["english_removed"].append(body)
            body = ""
        rep["translated"] += 1
        return f"({ar}: {body})" if body else f"({ar})"

    text = TAG_RE.sub(sub, text)
    for en, ar in SECTIONS.items():
        text = re.sub(rf"(?m)^(\s*#*\s*\**){en}(\**)\s*:", rf"\g<1>{ar}\g<2>:", text)
    return text, rep


def visible(text: str) -> tuple[str, int]:
    n = 0
    for p in VISIBLE:
        text, k = re.subn(p, "", text)
        n += k
    return text, n


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +([.،؛:,؟!)])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def clean(text: str, mode: str = "reading") -> tuple[str, dict]:
    text, nh = hidden(text or "")
    text, nv = visible(text)
    text, rep = notes(text, mode)
    rep.update({"hidden_chars": nh, "visible_marks": nv})
    return _tidy(text), rep


def humanlang_report(text: str) -> dict:
    words = max(len(re.findall(r"[ء-ي]+", text or "")), 1)
    stock = [p for p in STOCK if p in text]
    n_stock = sum(text.count(p) for p in STOCK)
    dashes = text.count("—")
    latin_notes = [m.group(0) for m in TAG_RE.finditer(text) if m.group("tag") not in NOTES and not ARCHIVE_ID.match(m.group(0)[1:])]
    per = {"stock_phrases": round(1000 * n_stock / words, 2), "em_dash": round(1000 * dashes / words, 2), "latin_notes": len(latin_notes)}
    limits = {"stock_phrases": 2, "em_dash": 3, "latin_notes": 0}
    flags = [k for k, v in per.items() if v > limits[k]]
    return {"per_1k": per, "flags": flags, "hits": {"stock_phrases": stock[:8], "latin_notes": latin_notes[:5]}, "ok": not flags}


def scrub_docx(doc, author: str = "", title: str = "") -> None:
    """يمحو بصمة المكتبة من خصائص ملف Word ويثبّت المؤلف والعنوان."""
    from datetime import datetime, timezone
    cp = doc.core_properties
    now = datetime.now(timezone.utc).replace(microsecond=0)
    cp.author = cp.last_modified_by = author or ""
    cp.title = title or ""
    cp.comments = cp.keywords = cp.subject = cp.category = cp.content_status = cp.identifier = cp.version = ""
    cp.revision = 1
    cp.created = cp.modified = now


APP_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
           'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><DocSecurity>0</DocSecurity></Properties>')


def scrub_package(data: bytes) -> bytes:
    """يزيل صورة المعاينة واسم التطبيق المولِّد ومعرّفات جلسات التحرير (rsid) من حزمة Word."""
    src = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            name = item.filename
            if name == "docProps/thumbnail.jpeg":
                continue
            body = src.read(name)
            if name == "docProps/app.xml":
                body = APP_XML.encode("utf-8")
            elif name == "_rels/.rels":
                body = re.sub(rb'<Relationship [^>]*metadata/thumbnail[^>]*/>', b"", body)
            elif name.startswith("word/") and name.endswith(".xml"):
                body = re.sub(rb'\s+w:rsid\w*="[0-9A-Fa-f]+"', b"", body)
                body = re.sub(rb"<w:rsids>.*?</w:rsids>", b"", body, flags=re.S)
                body = re.sub(rb"\s*<w:rsid [^>]*/>", b"", body)
            out.writestr(item, body)
    return buf.getvalue()
