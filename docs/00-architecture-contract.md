# عقد البنية المشترك — المرجع الموحّد للمعرّفات والحالات

## مسارات
- turath/data/agents/AG-XXX.json   بطاقات الوكلاء العشرين
- turath/data/skills.json          المهارات الأربع عشرة (يكتبها المنفذ الرئيس)
- turath/static/img/*.svg          الرسوم
- docs/NN-*.md                     الوثائق المؤسسية
- pilot/                           النموذج التطبيقي
- forms/                           الاستمارات (تُولَّد docx آلياً من docs)

## الهوية
أزرق عميق #1F4E79 · ذهبي #B8860B · خط Noto Naskh Arabic · ألوان مساندة: فيروزي بحري #0E7C86 · رملي #D9B26F · نخيلي #3E7C3A · طيني #A0522D · سماء #5BA4CF · ليلي #12263F · لؤلؤي #F7F3EA

## الوكلاء العشرون (المعرّف · الاسم · الوحدة · اللون)
AG-DIR  المدير التنفيذي للإدارة — Executive Director · مكتب المدير التنفيذي · #1F4E79
AG-PLN  مخطِّط البحوث ومحلل الفجوات — Research Planner & Gap Analyst · مكتب المدير التنفيذي · #1F4E79
AG-HIS  المؤرخ الاجتماعي — Social Historian · قسم التاريخ والمجتمع · #A0522D
AG-ANT  الأنثروبولوجي والإثنوغرافي — Anthropologist & Ethnographer · قسم التاريخ والمجتمع · #A0522D
AG-FLD  منسّق الجمع الميداني — Fieldwork Coordinator · قسم الجمع الميداني · #3E7C3A
AG-ORL  محقِّق الروايات الشفهية — Oral History Analyst · المختبر السمعي واللغوي · #0E7C86
AG-TRN  مفرِّغ التسجيلات — Transcription Specialist · المختبر السمعي واللغوي · #0E7C86
AG-DIA  اللساني واللهجي ومحرر المعجم — Dialectologist & Lexicographer · المختبر السمعي واللغوي · #0E7C86
AG-PTR  محقِّق الشعر والأهازيج — Poetry & Folk Song Specialist · المختبر السمعي واللغوي · #0E7C86
AG-ARC  المؤرشف ومحقق الوثائق والمخطوطات — Archivist & Document Critic · قسم الأرشيف والوثائق · #6B4E2E
AG-MAT  خبير التراث المادي والعمارة — Material Culture & Architecture Expert · قسم التراث المادي والحرف والبيئة · #B8860B
AG-CRF  موثِّق الحرف والاقتصاد التقليدي — Crafts & Traditional Economy Documentalist · قسم التراث المادي والحرف والبيئة · #B8860B
AG-ENV  باحث التراث الطبيعي والبيئي — Natural & Environmental Heritage Researcher · قسم التراث المادي والحرف والبيئة · #B8860B
AG-LAW  باحث التشريعات وسياسات الصون — Heritage Law & Policy Researcher · قسم التشريعات والسياسات · #5B3A7A
AG-GIS  محلل نظم المعلومات الجغرافية والأطالس — GIS & Atlas Analyst · وحدة التحليل المتقدم · #5BA4CF
AG-DAT  محلل البيانات والمسوح — Data & Survey Analyst · وحدة التحليل المتقدم · #5BA4CF
AG-VIS  محلل الصور ومنتج المسارات البصرية — Visual Analyst & Visual Production · وحدة التحليل المتقدم · #5BA4CF
AG-SRC  مدقِّق المصادر والأدلة — Source & Evidence Auditor · وحدة النزاهة والجودة · #8B1E3F
AG-ETH  مسؤول الأخلاقيات والحقوق والخصوصية — Ethics, Rights & Privacy Officer · وحدة النزاهة والجودة · #8B1E3F
AG-PUB  المحرر العلمي ومدير النشر — Scientific Editor & Publishing Director · وحدة النشر والإخراج · #12263F
الأدوار البشرية: HUM-DIR (المراجع البشري المخوّل/صاحب الاعتماد)، HUM-NATIVE (متحدث محلي مؤهل لمراجعة التفريغ)، HUM-PEER (محكّم خارجي)، HUM-LEGAL (مستشار قانوني)، HUM-FIELD (باحث ميداني بشري).

## المهارات الأربع عشرة (المعرّف · الأمر · الوكيل القائد)
SK-RESEARCH «ابحث تراثياً» AG-DIR+AG-PLN · SK-NARRATIVE «حقق رواية» AG-ORL+AG-SRC · SK-TRANSCRIBE «فرغ مقابلة» AG-TRN+AG-DIA · SK-TERM «حقق مفردة» AG-DIA · SK-CRAFT «وثق حرفة» AG-CRF · SK-IMAGE «حلل صورة» AG-VIS · SK-DOCUMENT «حلل وثيقة» AG-ARC · SK-SURVEY «صمم مسحاً» AG-DAT+AG-FLD · SK-ATLAS «أنشئ أطلساً» AG-GIS · SK-BOOK «اكتب كتاباً» AG-PUB+AG-DIR · SK-EXHIBIT «أنشئ معرضاً» AG-VIS+AG-PUB · SK-AUDIT «دقق المصادر» AG-SRC · SK-LAW «راجع تشريعاً» AG-LAW · SK-ARCHIVE «أرشف مادة» AG-ARC

## الأدوات (المعرّف · الحالة الفعلية)
T-DB قاعدة البيانات العلائقية SQLite — منفَّذ
T-VAULT خزنة الأصول (SHA-256، نسخة أصلية للقراءة فقط) — منفَّذ
T-FTS البحث النصي الكامل FTS5 مع إحالة إلى الأصل — منفَّذ
T-RAG البحث الدلالي بالمتجهات — مواصفة (يعمل البحث المعجمي المتتبَّع حالياً)
T-ASR التفريغ الآلي (faster-whisper) — مشروط بالتثبيت المحلي
T-FFMPEG استخراج البيانات الفنية للوسائط — مشروط بالتثبيت
T-OCR التعرف الضوئي (tesseract) — مشروط بالتثبيت
T-GEO تصدير GeoJSON وطبقات الأطلس — منفَّذ
T-STATS الإحصاء الوصفي — منفَّذ
T-EXPORT تصدير DOCX/CSV/JSON — منفَّذ
T-WEB البحث في الويب عبر جلسة Claude Code — مشروط
T-GIT GitHub للنسخ والإصدارات — منفَّذ عبر git
T-DRIVE Google Drive — مواصفة
T-ZOTERO Zotero للمراجع — مواصفة
T-IMGGEN توليد الصور التصورية — مشروط، وكل مخرَج يوسم «إعادة بناء تصورية»

## الجداول (snake_case)
projects, sources, narrators, interviews, audio_assets, video_assets, images, manuscripts, historical_documents, oral_narratives, poems, dialect_lexicon, crafts, heritage_practices, places, persons, events, observations, surveys, legislation, bibliography, permissions, claims, evidence_links, review_decisions, publications, conflicts, transcript_segments, assets, change_log, users, project_members, shares

## دورة المشروع (16 مرحلة)
S01 الفكرة البحثية · S02 تحليل المشكلة والفجوة · S03 خطة البحث · S04 مراجعة الدراسات · S05 تحديد المصادر · S06 الموافقات والأخلاقيات · S07 الجمع الوثائقي والميداني · S08 الفهرسة والتفريغ · S09 نقد المصادر والتثليث · S10 التحليل · S11 كتابة النتائج · S12 التحكيم العلمي · S13 التدقيق القانوني والحقوقي · S14 الإخراج · S15 الاعتماد البشري · S16 النشر والأرشفة

## قواعد المحتوى
- عربية فصحى رصينة بسجلّ أكاديمي، بلا حشو ولا عبارات تسويقية.
- صفر تلفيق: لا مراجع ولا أسماء رواة ولا أرقام صفحات ولا DOI مختلقة. المجهول يُكتب «يُستكمل» أو «معلّق إلى حين الجمع الفعلي».
- الفصل بين «مُصمَّم» و«مُنفَّذ ومختبَر».
