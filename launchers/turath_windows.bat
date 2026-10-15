@echo off
REM «تراث» — تثبيت من نسخة محلية من المستودع: انقروا هذا الملف نقراً مزدوجاً.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" -Source "%~dp0.."
pause
