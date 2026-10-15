# «تراث» — مثبّت ويندوز: يثبّت البرنامج للمستخدم الحالي، وينشئ أيقونة على سطح المكتب، ويفتح اللوحة.
# التشغيل من الإنترنت (الصقوا السطر في PowerShell):
#   $f="$env:TEMP\turath-install.ps1"; iwr https://raw.githubusercontent.com/7r425ypz9t-hue/turathres/refs/heads/claude/clever-carson-78yimu/launchers/install_windows.ps1 -OutFile $f; powershell -NoProfile -ExecutionPolicy Bypass -File $f
# أو بالنقر المزدوج على launchers\turath_windows.bat داخل نسخة محلية من المستودع.
param([string]$Source = "")
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Zip  = "https://github.com/7r425ypz9t-hue/turathres/archive/refs/heads/claude/clever-carson-78yimu.zip"
$Root = Join-Path $env:LOCALAPPDATA "Turath"
$App  = Join-Path $Root "app"

function Say($m) { Write-Host ("  » " + $m) -ForegroundColor Cyan }
function Fail($m) { Write-Host ("  ✖ " + $m) -ForegroundColor Red; Read-Host "اضغط Enter للإغلاق"; exit 1 }

# في Windows PowerShell 5.1 يتحول أي تحذير يكتبه برنامج خارجي إلى خطأ قاتل تحت Stop؛ فتُشغَّل البرامج الخارجية بهذا الغلاف
function Run-Native([scriptblock]$Block) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Block } finally { $ErrorActionPreference = $old }
}

function Stop-Turath {
    # إيقاف لوحة قائمة من تثبيت سابق: لا يُحذف مجلد يعمل منه برنامج في ويندوز
    Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*-m turath*" } |
        ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName Terminate -ErrorAction SilentlyContinue | Out-Null }
    Start-Sleep -Milliseconds 800
}

function Find-Python {
    $cands = @(
        @{ exe = "py"; args = @("-3") },
        @{ exe = "python"; args = @() },
        @{ exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"); args = @() },
        @{ exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"); args = @() },
        @{ exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"); args = @() }
    )
    foreach ($c in $cands) {
        try {
            $exe = $c.exe; $a = @($c.args + @("-c", "import sys;print(sys.executable if sys.version_info>=(3,10) else '')"))
            $out = Run-Native { & $exe @a 2>$null }
            if ($LASTEXITCODE -eq 0 -and $out -and (Test-Path $out.Trim())) { return $out.Trim() }
        } catch { }
    }
    return $null
}

Write-Host ""
Write-Host "  تراث — إدارة الدراسات والبحوث التراثية الإماراتية" -ForegroundColor Yellow
Write-Host "  التثبيت على هذا الجهاز (مستخدم واحد)" -ForegroundColor Yellow
Write-Host ""

# 1) Python 3.10 أو أحدث
Say "التحقق من Python…"
$py = Find-Python
if (-not $py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Say "تثبيت Python 3.12 (مرة واحدة، دقيقة أو دقيقتان)…"
        Run-Native { winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null }
        $py = Find-Python
    }
    if (-not $py) {
        Start-Process "https://www.python.org/downloads/windows/"
        Fail "لم يُعثر على Python. ثبّتوه من الصفحة التي فُتحت (مع خيار Add python.exe to PATH)، ثم أعيدوا تشغيل هذا المثبّت."
    }
}
$pyw = Join-Path (Split-Path $py) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $py }
Say ("Python: " + $py)

# 2) ملفات البرنامج (البيانات في مجلد مستقل %USERPROFILE%\Turath ولا تمسّها إعادة التثبيت)
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$staging = Join-Path $Root ("staging-" + [guid]::NewGuid().ToString("N"))
if ($Source) {
    Say "نسخ البرنامج من المجلد المحلي…"
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    Get-ChildItem -Force $Source | Where-Object { $_.Name -ne ".git" } | Copy-Item -Recurse -Force -Destination $staging
    $new = $staging
} else {
    Say "تنزيل البرنامج…"
    $zipFile = Join-Path $Root "turath.zip"
    try { Invoke-WebRequest -Uri $Zip -OutFile $zipFile -UseBasicParsing } catch { Fail ("تعذّر التنزيل: " + $_.Exception.Message) }
    Expand-Archive -Path $zipFile -DestinationPath $staging -Force
    Remove-Item $zipFile -Force
    $new = (Get-ChildItem $staging -Directory | Select-Object -First 1).FullName
}
if (-not (Test-Path (Join-Path $new "turath\__main__.py"))) { Fail "ملفات البرنامج ناقصة." }
if (Test-Path $App) { Stop-Turath; Remove-Item -Recurse -Force $App }
Move-Item $new $App
if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }

# 3) المكتبات الاختيارية: Word (تصدير .docx) وPillow (تحويل صورة الأيقونة المعتمدة بكل مقاساتها)
Say "إعداد تصدير Word…"
Run-Native { & $py -m pip install --user --quiet --disable-pip-version-check python-docx pillow 2>$null | Out-Null }

# 4) النمط الفردي والأيقونة
Push-Location $App
try {
    if (-not (Test-Path (Join-Path $env:USERPROFILE "Turath\turath.json"))) {
        Say "تهيئة النمط الفردي…"
        Run-Native { & $py -m turath setup solo | Out-Null }
    }
    Say "إنشاء الأيقونة على سطح المكتب وفي قائمة البرامج…"
    Run-Native { & $py -m turath install-icon }
    if ($LASTEXITCODE -ne 0) { Fail "تعذّر إنشاء الأيقونة." }
    # إن كان خط «أضواء السلف» مودعاً في مجلد البيانات ثُبّت في ويندوز ليظهر في Word وPowerPoint
    if (Test-Path (Join-Path $env:USERPROFILE "Turath\fonts\adwa-assalaf.ttf")) {
        Run-Native { & $py -m turath fonts system 2>$null | Out-Null }
    }
} finally { Pop-Location }

# 5) التشغيل والتحقق من أن اللوحة قامت فعلاً
Say "فتح لوحة التحكم…"
Start-Process -FilePath $pyw -ArgumentList "-m", "turath.launch" -WorkingDirectory $App
$up = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    $port = 8765
    try { $port = (Get-Content (Join-Path $env:USERPROFILE "Turath\turath.json") -Raw | ConvertFrom-Json).port } catch { }
    try { Invoke-WebRequest -Uri "http://127.0.0.1:$port/api/public" -UseBasicParsing -TimeoutSec 2 | Out-Null; $up = $true; break } catch { }
}
if (-not $up) {
    Write-Host ""
    Write-Host "  ✖ لم تبدأ اللوحة. هذا تقرير التشخيص — أرسلوه كما هو:" -ForegroundColor Red
    Push-Location $App; Run-Native { & $py -m turath doctor }; Pop-Location
    Read-Host "اضغط Enter للإغلاق"; exit 1
}
Write-Host ""
Write-Host "  ✔ اكتمل التثبيت، واللوحة تعمل. من الآن: انقروا أيقونة «تراث» على سطح المكتب." -ForegroundColor Green
Write-Host ("  البيانات: " + (Join-Path $env:USERPROFILE "Turath")) -ForegroundColor Gray
Write-Host ""
