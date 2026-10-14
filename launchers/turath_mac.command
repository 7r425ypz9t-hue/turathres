#!/bin/bash
# «تراث» — تثبيت وتشغيل على ماك (انقر نقراً مزدوجاً)
cd "$(dirname "$0")/.." || exit 1
command -v python3 >/dev/null || { echo "يلزم Python 3.10 أو أحدث"; exit 1; }
python3 -m pip install --user -e ".[docx]" >/dev/null
[ -f "$HOME/Turath/turath.json" ] || python3 -m turath setup solo
python3 -m turath serve
