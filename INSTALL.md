# تنصيب «تراث» على جهاز واحد

تثبيت لمستخدم واحد على حاسوب واحد (النمط الفردي)، مع أيقونة على سطح المكتب. يستغرق دقيقتين أو ثلاثاً، ولا يحتاج إلى صلاحيات مدير النظام.

## ويندوز 10 و11

1. افتحوا قائمة «ابدأ»، واكتبوا **PowerShell**، ثم افتحوه (نافذة عادية، لا «كمسؤول»).
2. الصقوا السطر الآتي كاملاً، ثم اضغطوا Enter:

```powershell
$f="$env:TEMP\turath-install.ps1"; iwr https://raw.githubusercontent.com/7r425ypz9t-hue/turathres/refs/heads/claude/clever-carson-78yimu/launchers/install_windows.ps1 -OutFile $f; powershell -NoProfile -ExecutionPolicy Bypass -File $f
```

3. ينفّذ المثبّت ما يلي:
   - يتحقق من Python، ويثبّته تلقائياً إن لم يجده (عبر winget)؛
   - ينزّل البرنامج؛
   - يهيّئ النمط الفردي؛
   - يضع أيقونة **«تراث»** على سطح المكتب وفي قائمة «ابدأ»؛
   - يفتح لوحة التحكم.

**إن لم يكن Python مثبتاً ولم يتوفر winget:** تُفتح صفحة python.org. ثبّتوه منها، وفعّلوا خيار **Add python.exe to PATH**، ثم أعيدوا الخطوة 2.

## ماك

افتحوا **Terminal**، والصقوا هذا السطر، ثم اضغطوا Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/7r425ypz9t-hue/turathres/refs/heads/claude/clever-carson-78yimu/launchers/install_unix.sh | bash
```

تظهر أيقونة «تراث» على سطح المكتب وفي مجلد التطبيقات. إن لم يكن Python 3.10 أو أحدث مثبتاً، تُفتح صفحة تنزيله من python.org.

## من نسخة محلية من المستودع

| النظام | الملف الذي يُنقر نقراً مزدوجاً |
|---|---|
| ويندوز | `launchers\turath_windows.bat` |
| ماك | `launchers/turath_mac.command` |
| لينكس | `launchers/turath_linux.sh` |

## بعد التنصيب

- **الأيقونة** تفتح اللوحة في نافذة مستقلة.
- **النقر مرة ثانية** والبرنامج يعمل يفتح نافذة جديدة، ولا يشغّل نسخة ثانية.
- **إعادة تشغيل المثبّت** تحدّث البرنامج إلى آخر نسخة. فإن كانت نسخة قديمة تعمل، أُوقفت وشُغّلت الجديدة آلياً.
- **أول ما يُنصح به:** زر «النموذج التطبيقي: التلي» في الصفحة الرئيسية، لرؤية المنظومة تعمل على مصادر حقيقية متحقق منها.

## أين تُحفظ الأشياء

| ماذا | ويندوز | ماك |
|---|---|---|
| البيانات: القاعدة والخزنة والنسخ الاحتياطية | `%USERPROFILE%\Turath` | `~/Turath` |
| ملفات البرنامج | `%LOCALAPPDATA%\Turath\app` | `~/Library/Application Support/Turath/app` |
| سجل التشغيل | `%USERPROFILE%\Turath\turath.log` | `~/Turath/turath.log` |

إعادة التثبيت أو التحديث لا تمسّ مجلد البيانات أبداً. وللنسخ الاحتياطي: زر «نسخة احتياطية» في قسم الخزنة.

## إزالة الأيقونة

انقروا الأيقونة بالزر الأيمن واحذفوها، أو نفّذوا داخل مجلد البرنامج:

```
python -m turath install-icon --remove
```
