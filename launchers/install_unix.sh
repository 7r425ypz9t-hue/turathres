#!/bin/bash
# «تراث» — مثبّت ماك ولينكس: يثبّت البرنامج للمستخدم الحالي، وينشئ أيقونة على سطح المكتب، ويفتح اللوحة.
# من الإنترنت (في الطرفية):
#   curl -fsSL https://raw.githubusercontent.com/7r425ypz9t-hue/turathres/refs/heads/claude/clever-carson-78yimu/launchers/install_unix.sh | bash
set -euo pipefail
ZIP="https://github.com/7r425ypz9t-hue/turathres/archive/refs/heads/claude/clever-carson-78yimu.zip"
if [ "$(uname)" = "Darwin" ]; then ROOT="$HOME/Library/Application Support/Turath"; else ROOT="$HOME/.local/share/turath"; fi
APP="$ROOT/app"
SOURCE="${1:-}"
say() { printf '  » %s\n' "$1"; }
fail() { printf '  ✖ %s\n' "$1" >&2; exit 1; }

echo; echo "  تراث — إدارة الدراسات والبحوث التراثية الإماراتية"; echo "  التثبيت على هذا الجهاز (مستخدم واحد)"; echo

say "التحقق من Python…"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PY="$(command -v "$c")"; break
  fi
done
if [ -z "$PY" ]; then
  [ "$(uname)" = "Darwin" ] && open "https://www.python.org/downloads/macos/"
  fail "يلزم Python 3.10 أو أحدث. ثبّتوه من python.org ثم أعيدوا تشغيل المثبّت."
fi
say "Python: $PY"

mkdir -p "$ROOT"
STAGE="$(mktemp -d "$ROOT/staging.XXXXXX")"
if [ -n "$SOURCE" ]; then
  say "نسخ البرنامج من المجلد المحلي…"
  (cd "$SOURCE" && tar --exclude=.git -cf - .) | (cd "$STAGE" && tar -xf -)
  NEW="$STAGE"
else
  say "تنزيل البرنامج…"
  curl -fsSL "$ZIP" -o "$STAGE/turath.zip" || fail "تعذّر التنزيل"
  (cd "$STAGE" && unzip -q turath.zip && rm turath.zip)
  NEW="$(find "$STAGE" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
fi
[ -f "$NEW/turath/__main__.py" ] || fail "ملفات البرنامج ناقصة"
rm -rf "$APP.old"; [ -d "$APP" ] && mv "$APP" "$APP.old"
mv "$NEW" "$APP"; rm -rf "$STAGE" "$APP.old"

say "إعداد تصدير Word…"
"$PY" -m pip install --user --quiet --disable-pip-version-check python-docx >/dev/null 2>&1 || \
  "$PY" -m pip install --user --quiet --break-system-packages python-docx >/dev/null 2>&1 || true

cd "$APP"
if [ ! -f "$HOME/Turath/turath.json" ]; then say "تهيئة النمط الفردي…"; "$PY" -m turath setup solo >/dev/null; fi
say "إنشاء الأيقونة على سطح المكتب…"
"$PY" -m turath install-icon

say "فتح لوحة التحكم…"
nohup "$PY" -m turath serve >/dev/null 2>&1 &
echo; echo "  ✔ اكتمل التثبيت. من الآن: انقروا أيقونة «تراث» على سطح المكتب."; echo "  البيانات: $HOME/Turath"; echo
