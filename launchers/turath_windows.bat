@echo off
chcp 65001 >nul
REM «تراث» — تثبيت وتشغيل على ويندوز (النمط الفردي افتراضياً) وإنشاء أيقونة على سطح المكتب
cd /d "%~dp0\.."
where python >nul 2>nul || (echo يلزم تثبيت Python 3.10 او احدث من python.org & pause & exit /b 1)
python -m pip install --user -e ".[docx]" >nul
if not exist "%USERPROFILE%\Turath\turath.json" python -m turath setup solo
set LNK=%USERPROFILE%\Desktop\تراث.lnk
if not exist "%LNK%" powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%');$s.TargetPath='pythonw.exe';$s.Arguments='-m turath serve';$s.WorkingDirectory='%CD%';$s.IconLocation='%CD%\turath\static\img\turath.ico';$s.Save()"
start "" pythonw -m turath serve
