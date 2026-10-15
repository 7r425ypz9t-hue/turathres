"""التصدير والاستشهاد: CSV · JSON · GeoJSON · SRT · DOCX بالهوية البصرية، وتنسيق APA 7 وChicago."""
from __future__ import annotations
import csv
import io
import json
import re

from . import db
from . import entities as EN
from . import evidence as EV
from . import lifecycle as LC
from . import sanitize

BLUE, GOLD, RED = "1F4E79", "B8860B", "FF0000"


def apa(s: dict) -> str:
    """APA 7 من الحقول المسجلة وحدها — لا يُضاف ما ليس في السجل."""
    creator = s.get("creator") or s.get("publisher") or "مؤلف غير محدد"
    year = s.get("year") or "د.ت."
    out = f"{creator}. ({year}). {s.get('title') or '[بلا عنوان]'}."
    if s.get("publisher") and s.get("publisher") != creator:
        out += f" {s['publisher']}."
    if s.get("doi"):
        out += f" https://doi.org/{s['doi']}"
    elif s.get("url"):
        out += f" {s['url']}"
    if s.get("kind") == "oral":
        out += " [تسجيل شفهي غير منشور — يُحال إليه منهجياً لا في القائمة العامة]"
    return out


def chicago(s: dict) -> str:
    creator = s.get("creator") or s.get("publisher") or "مؤلف غير محدد"
    out = f"{creator}. {s.get('title') or '[بلا عنوان]'}."
    if s.get("publisher") and s.get("publisher") != creator:
        out += f" {s['publisher']},"
    out += f" {s.get('year') or 'د.ت.'}."
    if s.get("url"):
        out += f" {s['url']}" + (f" (اطُّلع عليه {s['accessed']})." if s.get("accessed") else "")
    return out


def oral_citation(iv: dict, narrator: dict | None, seg_time: str = "") -> str:
    code = (narrator or {}).get("display_name") if (narrator or {}).get("name_permitted") else (narrator or {}).get("code", "راوٍ")
    return (f"مقابلة {iv.get('archive_code') or iv['id']}، الراوي: {code}، الباحث: {iv.get('researcher') or '—'}، "
            f"{iv.get('date') or 'تاريخ غير مسجل'}، الملف {iv.get('asset_id') or '—'}" + (f"، الموضع {seg_time}" if seg_time else "") + ".")


def to_csv(user: dict, table: str, pid: str | None = None) -> str:
    R = db.list_rows(user, table, pid, limit=100000)
    cols = [n for n, _, _ in EN.fields_of(table)]
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(R)
    return buf.getvalue()


def to_json(user: dict, pid: str) -> str:
    out = {"project": db.get(user, "projects", pid), "exported_at": db.now(), "consent_gaps": EV.consent_gaps(pid)}
    for t in EN.E:
        if t != "projects":
            out[t] = db.list_rows(user, t, pid, limit=100000)
    return json.dumps(out, ensure_ascii=False, indent=2)


def geojson(user: dict, pid: str | None = None) -> dict:
    feats = []
    for p in db.list_rows(user, "places", pid, limit=100000):
        if p.get("lat") is None or p.get("lon") is None:
            continue
        lat, lon = p["lat"], p["lon"]
        if p.get("sensitive"):
            lat, lon = round(lat, 1), round(lon, 1)   # حجب الدقة للمواقع الحساسة (نحو 10 كم)
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
                      "properties": {"id": p["id"], "name": p.get("name"), "kind": p.get("kind"), "emirate": p.get("emirate"),
                                     "region": p.get("region"), "masked": bool(p.get("sensitive"))}})
    return {"type": "FeatureCollection", "features": feats}


def docx_dossier(user: dict, pid: str) -> bytes:
    """ملف المشروع بصيغة Word: الهوية البصرية، والمرحلة، والادعاءات وأدلتها، والتعارضات، والمراجع."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import Pt, RGBColor

    p = db.get(user, "projects", pid)
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Noto Naskh Arabic"
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set(qn("w:cs"), "Noto Naskh Arabic")

    def para(text, size=13, color=None, bold=False, align=WD_ALIGN_PARAGRAPH.RIGHT):
        """فقرة من اليمين؛ والأقواس وما بينها بالأحمر (اصطلاح «باحث» في كل مستند)."""
        par = d.add_paragraph()
        pPr = par._p.get_or_add_pPr()
        bidi = OxmlElement("w:bidi")
        pPr.append(bidi)
        par.alignment = align
        for i, piece in enumerate(re.split(r"(\([^()]*\)|\[[^\[\]]*\])", text)):
            if not piece:
                continue
            r = par.add_run(piece)
            r.font.size = Pt(size)
            r.font.bold = bold
            rPr = r._r.get_or_add_rPr()
            rPr.append(OxmlElement("w:rtl"))
            szcs = OxmlElement("w:szCs")
            szcs.set(qn("w:val"), str(int(size * 2)))
            rPr.append(szcs)
            if bold:
                rPr.append(OxmlElement("w:bCs"))
            if i % 2 == 1:
                r.font.color.rgb = RGBColor.from_string(RED)
            elif color:
                r.font.color.rgb = RGBColor.from_string(color)
        return par

    para("إدارة الدراسات والبحوث التراثية الإماراتية", 12, GOLD, True, WD_ALIGN_PARAGRAPH.CENTER)
    para(p.get("title") or p["id"], 22, BLUE, True, WD_ALIGN_PARAGRAPH.CENTER)
    stage = dict((s[0], s[1]) for s in LC.STAGES).get(p.get("stage"), p.get("stage"))
    para(f"{p['id']} · المرحلة: {stage}", 11, "5B6B7A", False, WD_ALIGN_PARAGRAPH.CENTER)
    for k, lbl in (("question", "السؤال البحثي"), ("gap", "الفجوة البحثية"), ("summary", "خطة البحث والملخص")):
        if p.get(k):
            para(lbl, 15, BLUE, True)
            para(p[k])
    para("الادعاءات العلمية وأدلتها", 15, BLUE, True)
    for c in db.list_rows(user, "claims", pid):
        t = EV.triangulation(c["id"])
        para(f"■ {c['id']} — {c.get('text')}", 13, None, True)
        para(f"الحالة: {c.get('status')} · الطبيعة: {c.get('kind') or '—'} · أصول مستقلة: {t['independent_origins']} · أصناف: {'، '.join(t['type_labels']) or '—'}", 11, "5B6B7A")
        for l in EV.links(c["id"]):
            para(f"   ← {l.get('relation')}: {l.get('target_id')} {('— ' + l['locator']) if l.get('locator') else ''} {('«' + l['excerpt'] + '»') if l.get('excerpt') else ''}", 11)
    conf = db.list_rows(user, "conflicts", pid)
    if conf:
        para("سجل التعارضات", 15, BLUE, True)
        for c in conf:
            para(f"{c['id']} — {c.get('topic')} ({c.get('status')})", 12, None, True)
            if c.get("analysis"):
                para(c["analysis"], 12)
    gaps = EV.consent_gaps(pid)
    para("حالة الموافقات قبل النشر", 15, BLUE, True)
    rows = [("مقابلات بلا موافقة نشر", gaps["interviews_no_publication"]), ("صور بلا موافقة نشر", gaps["images_no_publication"]),
            ("أصول تحمل إحداثيات موقع (تُحجب قبل النشر)", gaps["assets_with_location"]), ("موافقات مسحوبة", gaps["withdrawn"])]
    if not any(v for _, v in rows):
        para("لا عائق موافقات أمام نشر ما في هذا الملف.", 12)
    for label, ids in rows:
        if ids:
            para(f"{label}: {'، '.join(ids)} [لا يُنشر قبل استيفاء الموافقة]", 12)
    para("المراجع (APA 7)", 15, BLUE, True)
    for s in sorted(db.list_rows(user, "sources", pid), key=lambda x: (x.get("creator") or "")):
        if s.get("kind") != "oral":
            para(apa(s), 11)
    para("وُلِّد هذا الملف من أرشيف الإدارة؛ كل ادعاء فيه محال إلى سجله. القرار النهائي للمراجع البشري المخوّل.", 10, GOLD)
    sanitize.scrub_docx(d, author="إدارة الدراسات والبحوث التراثية الإماراتية", title=p.get("title") or "")
    buf = io.BytesIO()
    d.save(buf)
    return sanitize.scrub_package(buf.getvalue())
