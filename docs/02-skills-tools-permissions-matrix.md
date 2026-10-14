# مصفوفة المهارات والأدوات والصلاحيات

> **الوثيقة:** 02 · **الغاية:** ضبط ما يستطيع كل وكيل فعله: أيّ المهارات يقودها أو يشارك فيها، وأيّ الأدوات يستعملها وما حالتها الفعلية، وأيّ الجداول يقرأ منها أو يكتب فيها، وفق مبدأ الحدّ الأدنى من الصلاحيات.
> **مصدر الحقيقة:** المصفوفات في الأقسام 2–4 مستخرجة آلياً من بطاقات الوكلاء `turath/data/agents/AG-*.json` (الحقول `skills` و`tools_allowed` و`data_store`) ومن `turath/data/skills.json`. وعند أي تعارض بين هذه الوثيقة والبطاقات، فالبطاقات هي المرجع، وتُحدَّث الوثيقة.

---

## 1. القواعد الحاكمة للصلاحيات وحدود تطبيقها

### 1.1 القواعد المعلنة

1. **الكتابة في `assets` معلنة لـ AG-ARC وحده.** وفي التطبيق لا يُنشأ سجل في `assets` إلا عبر وظيفة الإيداع في الخزنة (`vault.ingest`)، التي تحسب البصمة SHA-256 وتحفظ النسخة الأصلية للقراءة فقط وتسجل الإيداع في `change_log`.
2. **الكتابة في `permissions` معلنة لـ AG-ETH وحده.**
3. **`change_log` لا يكتبه أي وكيل:** تكتبه طبقة البيانات آلياً عند كل إنشاء وتعديل وحذف وانتقال مرحلة وتشغيل وكيل وخطوة مختبر.
4. **`users` و`shares`** لا يكتب فيهما أي وكيل؛ ويديرهما المستخدمون البشريون من الواجهة (الحسابات للمسؤول، والمشاركة لمالك المادة).
5. **قرارات الصفة البشرية لا تُنتحل:** لا يُسجَّل قرار بصفة `HUM-DIR` إلا من حساب بدور `director` أو `admin` (`lifecycle.record_decision`)، ولا تُعلَّم خطوة المراجعة اللهجية في المختبر (الخطوة 10) إلا من حساب بشري.

### 1.2 كيف تُطبَّق هذه القواعد فعلاً (مُنفَّذ)

| الآلية | ما تفعله | الحالة |
|---|---|---|
| الوكلاء لا يكتبون في القاعدة مباشرة | مخرج كل تشغيل وكيل يُحفظ **مسودة** في جدول النظام `agent_runs` بمحركه وحالته، ولا يدخل الجداول البحثية إلا بإدخال مستخدم بشري يراجعه | مُنفَّذ |
| تقييد سياق القراءة | حزمة التكليف لا تتضمن من الأرشيف إلا الجداول المدرجة في `data_store.read` لبطاقة الوكيل، وفي حدود صلاحيات المستخدم الذي شغّله | مُنفَّذ |
| صلاحيات المستخدم البشري | القراءة والكتابة بحسب الملكية (`owner_id`)، وعضوية المشروع (`project_members` بدور `coauthor` أو `lead`)، ومستوى الإتاحة (`private` · `project` · `shared` · `public`)، والمشاركات (`shares` بنمط `read` أو `write`) | مُنفَّذ |
| الحذف | للمالك أو المسؤول وحده؛ حذف فعلي من الجدول مع حفظ **صورة كاملة للسجل قبل الحذف** في `change_log` | مُنفَّذ |
| ربط إعلانات `data_store.write` بحسابات بشرية ذات أدوار وظيفية (مثلاً: حساب مؤرشف وحده ينشئ الأصول) | فرض الكتابة على مستوى الدور لا على مستوى الملكية فقط | مقترح للإصدار التالي |

> **خلاصة صريحة:** مبدأ «AG-ARC وحده يكتب الأصول» و«AG-ETH وحده يكتب الأذونات» مُعلَن في البطاقات ومُطبَّق على ما يراه الوكيل وما يُسمح له باقتراحه؛ أما الكتابة الفعلية في القاعدة فيجريها إنسان بصلاحيات الملكية والعضوية. ولذلك يلزم إجرائياً أن يتولى إدخال الأذونات مسؤولُ الأخلاقيات البشري أو من يفوّضه.

**مفتاح الرموز:** ● قائد · ○ مشارك · ✓ مأذون · — لا صلاحية.

## 2. مصفوفة الوكلاء × المهارات

**المصدر:** حقل `agents` في `turath/data/skills.json` (القائد ●) وحقل `skills` في بطاقة كل وكيل (مشارك ○).

| الوكيل | RESEARCH | NARRATIVE | TRANSCRIBE | TERM | CRAFT | IMAGE | DOCUMENT | SURVEY | ATLAS | BOOK | EXHIBIT | AUDIT | LAW | ARCHIVE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AG-DIR | ● | — | — | — | — | — | — | — | — | ● | — | — | — | — |
| AG-PLN | ● | — | — | — | — | — | — | — | — | — | — | — | — | — |
| AG-HIS | ○ | — | — | — | — | — | ○ | — | — | ○ | — | — | — | — |
| AG-ANT | ○ | ○ | — | — | ○ | — | — | — | — | — | — | — | — | — |
| AG-FLD | — | — | — | — | ○ | — | — | ● | — | — | — | — | — | ○ |
| AG-ORL | — | ● | ○ | — | — | — | — | — | — | — | — | — | — | — |
| AG-TRN | — | — | ● | — | — | — | — | — | — | — | — | — | — | — |
| AG-DIA | — | — | ● | ● | — | — | — | — | — | — | — | — | — | — |
| AG-PTR | — | ○ | ○ | ○ | — | — | — | — | — | — | — | — | — | — |
| AG-ARC | — | — | — | — | — | — | ● | — | — | — | — | — | — | ● |
| AG-MAT | — | — | — | — | — | ○ | — | — | ○ | — | ○ | — | — | — |
| AG-CRF | — | — | — | ○ | ● | — | — | — | — | — | — | — | — | — |
| AG-ENV | — | — | — | ○ | — | — | — | — | ○ | — | — | — | — | — |
| AG-LAW | — | — | — | — | — | — | — | — | — | — | — | — | ● | — |
| AG-GIS | — | — | — | — | — | — | — | — | ● | — | — | — | — | — |
| AG-DAT | — | — | — | — | — | — | — | ● | — | — | — | — | — | — |
| AG-VIS | — | — | — | — | — | ● | — | — | — | — | ● | — | — | — |
| AG-SRC | — | ● | — | — | — | — | — | — | — | — | — | ● | — | — |
| AG-ETH | — | — | — | — | — | — | — | — | — | — | — | ○ | ○ | ○ |
| AG-PUB | — | — | — | — | — | — | — | — | — | ● | ● | ○ | — | — |

## 3. مصفوفة الوكلاء × الأدوات

### 3.1 حالة الأدوات (وفق عقد البنية)

| المعرّف | الأداة | الحالة الفعلية |
|---|---|---|
| T-DB | قاعدة البيانات العلائقية SQLite | مُنفَّذ |
| T-VAULT | خزنة الأصول (SHA-256، أصل للقراءة فقط) | مُنفَّذ |
| T-FTS | البحث النصي الكامل FTS5 مع الإحالة إلى الأصل | مُنفَّذ |
| T-RAG | البحث الدلالي بالمتجهات | مواصفة (البحث المعجمي المتتبَّع يعمل حالياً) |
| T-ASR | التفريغ الآلي (faster-whisper) | مشروط بالتثبيت المحلي |
| T-FFMPEG | استخراج البيانات الفنية للوسائط | مشروط بالتثبيت |
| T-OCR | التعرف الضوئي (tesseract) | مشروط بالتثبيت |
| T-GEO | تصدير GeoJSON وطبقات الأطلس | مُنفَّذ |
| T-STATS | الإحصاء الوصفي | مُنفَّذ |
| T-EXPORT | تصدير DOCX/CSV/JSON | مُنفَّذ |
| T-WEB | البحث في الويب عبر جلسة Claude Code | مشروط |
| T-GIT | GitHub للنسخ والإصدارات | مُنفَّذ عبر git |
| T-DRIVE | Google Drive | مواصفة |
| T-ZOTERO | Zotero للمراجع | مواصفة |
| T-IMGGEN | توليد الصور التصورية | مشروط، وكل مخرَج يوسم «إعادة بناء تصورية» |

**محركات تشغيل الوكلاء** (`turath/agents.py`): `manual` (حزمة تكليف تُنسخ يدوياً — متاح دائماً)، و`claude_code` (مشروط بوجود برنامج Claude Code على الجهاز)، و`api` (مشروط بوجود مفتاح الواجهة البرمجية). وإن لم يتوفر المحرك المطلوب يعود التطبيق إلى `manual` ولا يدّعي تشغيلاً لم يحدث.

> **قيد تشغيلي:** إدراج أداة «مواصفة» في بطاقة وكيل (مثل T-RAG أو T-ZOTERO أو T-DRIVE) هو للإعلام بحدودها؛ وتنص البطاقة نفسها على أنها غير منفّذة وعلى البديل المعتمد.

### 3.2 المصفوفة

**المصدر:** حقل `tools_allowed` في بطاقة كل وكيل. ✓ مأذون · — غير مأذون.

| الوكيل | DB | VAULT | FTS | RAG | ASR | FFMPEG | OCR | GEO | STATS | EXPORT | WEB | GIT | DRIVE | ZOTERO | IMGGEN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AG-DIR | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | — | ✓ | — | — | — |
| AG-PLN | ✓ | — | ✓ | ✓ | — | — | — | — | — | ✓ | ✓ | — | — | ✓ | — |
| AG-HIS | ✓ | — | ✓ | ✓ | — | — | — | — | — | ✓ | ✓ | — | — | — | — |
| AG-ANT | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | — | — | — | — | — |
| AG-FLD | ✓ | — | — | — | — | ✓ | — | ✓ | — | ✓ | — | — | ✓ | — | — |
| AG-ORL | ✓ | — | ✓ | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| AG-TRN | ✓ | ✓ | — | — | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — |
| AG-DIA | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | — | — | — | — | — |
| AG-PTR | ✓ | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | — | — | — | — | — |
| AG-ARC | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | — | — | — | — | ✓ | — | — | — |
| AG-MAT | ✓ | — | ✓ | — | — | — | — | ✓ | — | ✓ | — | — | — | — | ✓ |
| AG-CRF | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | — | — | — | — | — |
| AG-ENV | ✓ | — | ✓ | — | — | — | — | ✓ | ✓ | — | ✓ | — | — | — | — |
| AG-LAW | ✓ | — | ✓ | — | — | — | — | — | — | ✓ | ✓ | — | — | — | — |
| AG-GIS | ✓ | — | — | — | — | — | — | ✓ | ✓ | ✓ | — | — | — | — | — |
| AG-DAT | ✓ | — | — | — | — | — | — | ✓ | ✓ | ✓ | — | — | — | — | — |
| AG-VIS | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — | — | — | ✓ |
| AG-SRC | ✓ | ✓ | ✓ | — | — | — | — | — | ✓ | ✓ | ✓ | — | — | — | — |
| AG-ETH | ✓ | ✓ | ✓ | — | — | — | — | — | — | ✓ | — | — | — | — | — |
| AG-PUB | ✓ | — | ✓ | — | — | — | — | — | — | ✓ | — | ✓ | ✓ | ✓ | — |

## 4. مصفوفة الوكلاء × الجداول

**المصدر:** حقل `data_store` (`read` و`write`) في بطاقة كل وكيل. الكتابة تتضمن القراءة ضمناً.

| الجدول | يكتب (W) | يقرأ (R) |
|---|---|---|
| `projects` | AG-DIR | AG-PLN، AG-FLD، AG-DAT |
| `sources` | AG-PLN، AG-ARC | AG-HIS، AG-MAT، AG-ENV، AG-LAW، AG-VIS، AG-SRC |
| `narrators` | AG-FLD | AG-ANT، AG-ORL، AG-PTR، AG-CRF، AG-ETH |
| `interviews` | AG-FLD | AG-ANT، AG-ORL، AG-TRN، AG-ARC، AG-CRF، AG-DAT، AG-ETH |
| `audio_assets` | AG-ARC | AG-TRN، AG-PTR |
| `video_assets` | AG-ARC | AG-TRN، AG-VIS |
| `images` | AG-ARC | AG-MAT، AG-CRF، AG-VIS، AG-ETH، AG-PUB |
| `manuscripts` | AG-ARC | AG-HIS، AG-PTR، AG-SRC |
| `historical_documents` | AG-ARC | AG-HIS، AG-ORL، AG-DIA، AG-MAT، AG-CRF، AG-LAW، AG-SRC |
| `oral_narratives` | AG-ORL | AG-HIS، AG-ANT، AG-DIA، AG-ENV، AG-SRC |
| `poems` | AG-PTR | AG-ANT، AG-DIA، AG-SRC، AG-ETH |
| `dialect_lexicon` | AG-DIA | AG-ANT، AG-TRN، AG-PTR، AG-CRF، AG-ENV، AG-GIS، AG-DAT، AG-PUB |
| `crafts` | AG-CRF | AG-ANT، AG-DIA، AG-ENV، AG-GIS |
| `heritage_practices` | AG-ANT | AG-PLN، AG-MAT، AG-CRF، AG-GIS |
| `places` | AG-GIS | AG-PLN، AG-HIS، AG-ANT، AG-FLD، AG-ORL، AG-MAT، AG-ENV، AG-VIS، AG-ETH، AG-PUB |
| `persons` | AG-HIS | AG-ORL |
| `events` | AG-HIS | AG-ORL، AG-GIS |
| `observations` | AG-ANT، AG-FLD، AG-MAT، AG-ENV، AG-VIS | AG-GIS، AG-DAT |
| `surveys` | AG-DAT | AG-FLD، AG-GIS |
| `legislation` | AG-LAW | AG-ETH |
| `bibliography` | AG-PLN | AG-HIS، AG-SRC، AG-PUB |
| `permissions` | AG-ETH | AG-DIR، AG-FLD، AG-TRN، AG-ARC، AG-LAW، AG-GIS، AG-VIS، AG-PUB |
| `claims` | AG-HIS، AG-ANT، AG-ORL، AG-PTR، AG-MAT، AG-CRF، AG-ENV، AG-LAW، AG-VIS | AG-DIR، AG-PLN، AG-SRC، AG-PUB |
| `evidence_links` | AG-HIS، AG-ANT، AG-ORL، AG-PTR، AG-MAT، AG-CRF، AG-ENV، AG-LAW، AG-VIS | AG-SRC، AG-PUB |
| `review_decisions` | AG-DIR، AG-SRC، AG-ETH، AG-PUB | — |
| `publications` | AG-PUB | AG-DIR، AG-PLN، AG-ARC، AG-LAW، AG-ETH |
| `conflicts` | AG-HIS، AG-ORL، AG-PTR، AG-SRC | AG-DIR، AG-PLN، AG-PUB |
| `transcript_segments` | AG-TRN | AG-ANT، AG-ORL، AG-DIA، AG-PTR، AG-CRF، AG-ENV، AG-SRC |
| `assets` | AG-ARC | AG-SRC |
| `change_log` | — (لا وكيل) | — |
| `users` | — (لا وكيل) | AG-DIR |
| `project_members` | AG-DIR | AG-ETH |
| `shares` | — (لا وكيل) | AG-LAW، AG-VIS، AG-ETH |

### 4.1 جدول الكتابة المختصر لكل وكيل

| الوكيل | الجداول التي يكتب فيها |
|---|---|
| AG-DIR | projects، project_members، review_decisions |
| AG-PLN | sources، bibliography |
| AG-HIS | claims، evidence_links، events، persons، conflicts |
| AG-ANT | observations، heritage_practices، claims، evidence_links |
| AG-FLD | interviews، narrators، observations |
| AG-ORL | oral_narratives، claims، evidence_links، conflicts |
| AG-TRN | transcript_segments |
| AG-DIA | dialect_lexicon |
| AG-PTR | poems، claims، evidence_links، conflicts |
| AG-ARC | assets، audio_assets، video_assets، images، manuscripts، historical_documents، sources |
| AG-MAT | observations، claims، evidence_links |
| AG-CRF | crafts، claims، evidence_links |
| AG-ENV | observations، claims، evidence_links |
| AG-LAW | legislation، claims، evidence_links |
| AG-GIS | places |
| AG-DAT | surveys |
| AG-VIS | observations، claims، evidence_links |
| AG-SRC | review_decisions، conflicts |
| AG-ETH | permissions، review_decisions |
| AG-PUB | publications، review_decisions |

### 4.2 جداول النظام خارج العقد

يحتوي التطبيق جداول نظامية لا يكتب فيها أي وكيل: `sessions` (جلسات الدخول)، و`stage_log` (سجل الانتقال بين المراحل مع تقرير البوابة)، و`lab_steps` (خطوات المختبر الاثنتا عشرة لكل مقابلة)، و`agent_runs` (تشغيلات الوكلاء ومسوداتها)، و`counters` (تسلسل المعرّفات السنوية)، و`meta` (ومنه خط الأساس للمؤشرات)، و`search_index` (فهرس FTS5).

## 5. التحقق من الالتزام

| الضابط | الحالة |
|---|---|
| عدم كتابة الوكلاء في القاعدة مباشرةً (مسودات في `agent_runs`) | مُنفَّذ |
| تقييد سياق الوكيل بجداول `data_store.read` | مُنفَّذ |
| إنشاء الأصول عبر الإيداع في الخزنة وحده | مُنفَّذ |
| تسجيل كل إنشاء وتعديل وحذف في `change_log` مع الصورة السابقة واللاحقة | مُنفَّذ |
| اقتصار قرار `HUM-DIR` على حساب بدور مدير أو مسؤول | مُنفَّذ |
| فرض `data_store.write` على أدوار المستخدمين البشريين | مقترح للإصدار التالي |
| مراجعة المصفوفة ربعياً وإعادة توليدها من البطاقات | مُصمَّم (إجراء مؤسسي) |
