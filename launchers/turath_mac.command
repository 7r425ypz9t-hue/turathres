#!/bin/bash
# «تراث» — تثبيت من نسخة محلية من المستودع على ماك: انقروا هذا الملف نقراً مزدوجاً.
DIR="$(cd "$(dirname "$0")/.." && pwd)"
bash "$DIR/launchers/install_unix.sh" "$DIR"
