#!/bin/bash
# «تراث» — تثبيت وتشغيل على لينكس، مع مدخل في قائمة التطبيقات
cd "$(dirname "$0")/.." || exit 1
python3 -m pip install --user -e ".[docx]" >/dev/null
[ -f "$HOME/Turath/turath.json" ] || python3 -m turath setup solo
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/turath.desktop" <<DESK
[Desktop Entry]
Name=تراث
Comment=إدارة الدراسات والبحوث التراثية الإماراتية
Exec=python3 -m turath serve
Path=$PWD
Icon=$PWD/turath/static/img/logo-turath.svg
Terminal=false
Type=Application
DESK
python3 -m turath serve
