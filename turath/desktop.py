"""سطح المكتب: أيقونة «تراث» وتشغيل اللوحة في نافذة تطبيق مستقلة.

- `turath install-icon` ينشئ الأيقونة على سطح المكتب وفي قائمة البرامج (ويندوز وماك ولينكس)، و`--remove` يزيلها.
- النقر الثاني على الأيقونة لا يُنشئ خادماً ثانياً: إن كانت اللوحة تعمل من النسخة نفسها فُتحت نافذة جديدة لها؛
  وإن كانت تعمل من نسخة أقدم (بعد تحديث) أُوقفت وشُغّلت الجديدة.
- تُفتح اللوحة في نافذة تطبيق بلا شريط عناوين (Edge أو Chrome بوضع --app)، وإلا ففي المتصفح الافتراضي.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path

PKG = Path(__file__).parent
APP_DIR = PKG.parent
NAME = "تراث"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def fingerprint() -> str:
    """بصمة النسخة الجارية من الشيفرة: تتغير مع أي تحديث لملفات الحزمة."""
    h = hashlib.sha256()
    for p in sorted(PKG.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            st = p.stat()
            h.update(f"{p.relative_to(PKG)}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()[:16]


def running(port: int) -> dict | None:
    """هل تعمل لوحة «تراث» على هذا المنفذ؟ يعيد بياناتها العامة أو None."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/public", timeout=1.5) as r:
            d = json.loads(r.read())
        return d if "institution" in d else None
    except Exception:
        return None


def stop_running(port: int, token: str) -> bool:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/shutdown", data=b"{}", method="POST",
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=3).read()
    except Exception:
        pass
    import time
    for _ in range(30):
        if not running(port):
            return True
        time.sleep(0.2)
    return False


def _browsers() -> list[str]:
    if os.name == "nt":
        roots = [os.environ.get(k, "") for k in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
        rel = [r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"]
        return [str(Path(r) / x) for r in roots if r for x in rel if (Path(r) / x).exists()]
    if sys.platform == "darwin":
        apps = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
        return [a for a in apps if Path(a).exists()]
    return [b for b in (shutil.which(x) for x in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge")) if b]


def open_window(url: str) -> None:
    """نافذة تطبيق مستقلة إن أمكن، وإلا فالمتصفح الافتراضي."""
    for exe in _browsers():
        try:
            subprocess.Popen([exe, f"--app={url}", "--new-window", "--window-size=1440,920"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
            return
        except Exception:
            continue
    webbrowser.open(url)


# ------------------------------------------------------------------ الأيقونة
def _desktop_dir() -> Path:
    if os.name == "nt":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                                 capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW)
            if out.stdout.strip():
                return Path(out.stdout.strip())
        except Exception:
            pass
    for cand in (Path.home() / "Desktop", Path.home() / "سطح المكتب"):
        if cand.exists():
            return cand
    return Path.home() / "Desktop"


def _pythonw() -> str:
    exe = Path(sys.executable)
    if os.name == "nt":
        w = exe.with_name("pythonw.exe")
        return str(w if w.exists() else exe)
    return str(exe)


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _windows(remove: bool) -> list[Path]:
    targets = [_desktop_dir() / f"{NAME}.lnk",
               Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{NAME}.lnk"]
    done = []
    for lnk in targets:
        if remove:
            if lnk.exists():
                lnk.unlink()
                done.append(lnk)
            continue
        lnk.parent.mkdir(parents=True, exist_ok=True)
        ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut({_ps_quote(str(lnk))});"
              f"$s.TargetPath={_ps_quote(_pythonw())};$s.Arguments='-m turath.launch';"
              f"$s.WorkingDirectory={_ps_quote(str(APP_DIR))};"
              f"$s.IconLocation={_ps_quote(str(PKG / 'static' / 'img' / 'turath.ico'))};"
              f"$s.Description='إدارة الدراسات والبحوث التراثية الإماراتية';$s.Save()")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True,
                       timeout=60, creationflags=NO_WINDOW)
        done.append(lnk)
    return done


def _mac(remove: bool) -> list[Path]:
    done = []
    for base in (_desktop_dir(), Path.home() / "Applications"):
        app = base / f"{NAME}.app"
        if remove:
            if app.exists():
                shutil.rmtree(app)
                done.append(app)
            continue
        macos, res = app / "Contents" / "MacOS", app / "Contents" / "Resources"
        macos.mkdir(parents=True, exist_ok=True)
        res.mkdir(parents=True, exist_ok=True)
        run = macos / "turath"
        run.write_text(f'#!/bin/bash\ncd "{APP_DIR}"\nexec "{sys.executable}" -m turath.launch\n', encoding="utf-8")
        run.chmod(0o755)
        icns = PKG / "static" / "img" / "turath.icns"
        if icns.exists():
            shutil.copy(icns, res / "turath.icns")
        (app / "Contents" / "Info.plist").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
            f"<key>CFBundleName</key><string>{NAME}</string><key>CFBundleDisplayName</key><string>{NAME}</string>"
            "<key>CFBundleIdentifier</key><string>ae.turath.app</string><key>CFBundleExecutable</key><string>turath</string>"
            "<key>CFBundleIconFile</key><string>turath</string><key>CFBundlePackageType</key><string>APPL</string>"
            "<key>CFBundleShortVersionString</key><string>1.0</string><key>LSUIElement</key><true/></dict></plist>\n",
            encoding="utf-8")
        done.append(app)
    return done


def _linux(remove: bool) -> list[Path]:
    entry = (f"[Desktop Entry]\nName={NAME}\nComment=إدارة الدراسات والبحوث التراثية الإماراتية\n"
             f"Exec={sys.executable} -m turath.launch\nPath={APP_DIR}\nIcon={PKG / 'static' / 'img' / 'logo-turath.png'}\n"
             "Terminal=false\nType=Application\nCategories=Education;Office;\n")
    done = []
    for p in (_desktop_dir() / "turath.desktop", Path.home() / ".local" / "share" / "applications" / "turath.desktop"):
        if remove:
            if p.exists():
                p.unlink()
                done.append(p)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entry, encoding="utf-8")
        p.chmod(0o755)
        done.append(p)
    return done


def install_icon(remove: bool = False) -> list[Path]:
    if os.name == "nt":
        return _windows(remove)
    if sys.platform == "darwin":
        return _mac(remove)
    return _linux(remove)


def icon_paths() -> list[Path]:
    """مواضع الأيقونة المتوقعة في هذا النظام (للتشخيص)."""
    d = _desktop_dir()
    if os.name == "nt":
        return [d / f"{NAME}.lnk",
                Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{NAME}.lnk"]
    if sys.platform == "darwin":
        return [d / f"{NAME}.app", Path.home() / "Applications" / f"{NAME}.app"]
    return [d / "turath.desktop", Path.home() / ".local" / "share" / "applications" / "turath.desktop"]
