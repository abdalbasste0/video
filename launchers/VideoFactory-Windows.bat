<# : batch portion
@echo off
setlocal
title Video Factory
set "VF_SELF=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ([IO.File]::ReadAllText($env:VF_SELF, [Text.Encoding]::UTF8))"
if errorlevel 1 pause
goto :EOF
: end of batch portion - PowerShell code starts below #>

# ============================================================
#  Video Factory - one file for Windows
#  First run: installs Git, Python and FFmpeg + downloads the project + creates the desktop icon.
#  After that: updates the project and opens the app.
#  If an error happens, the window does not close; a log is saved to %USERPROFILE%\VideoFactory-setup-log.txt
# ============================================================
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
Add-Type -AssemblyName System.Windows.Forms

$Repo   = 'https://github.com/abdalbasste0/video.git'
$Branch = 'claude/automated-story-video-factory-uvvyxr'
$Dir    = Join-Path $env:USERPROFILE 'VideoFactory'
$Log    = Join-Path $env:USERPROFILE 'VideoFactory-setup-log.txt'
try { Start-Transcript -Path $Log -Force | Out-Null } catch {}

function Say([string]$t) { Write-Host $t -ForegroundColor Cyan }

function Box([string]$t, [string]$icon = 'Information') {
    [void][System.Windows.Forms.MessageBox]::Show($t, 'مصنع الفيديو', 'OK', $icon, 'Button1', 'RtlReading, RightAlign')
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Has([string]$name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

function Find-Python {
    # Ignore the Microsoft Store "python" stub (WindowsApps), which is not a real Python
    foreach ($c in @('py', 'python')) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if (-not $cmd -or $cmd.Source -like '*WindowsApps*') { continue }
        try {
            if ($c -eq 'py') { $out = & py -3 -c "import sys; print(sys.executable)" }
            else { $out = & python -c "import sys; print(sys.executable)" }
            if ($LASTEXITCODE -eq 0 -and $out) { return ([string]($out | Select-Object -Last 1)).Trim() }
        } catch {}
    }
    foreach ($v in @('Python313', 'Python312', 'Python311', 'Python310')) {
        $cand = Join-Path $env:LOCALAPPDATA "Programs\Python\$v\python.exe"
        if (Test-Path $cand) { return $cand }
    }
    return $null
}

function Install-Tool([string]$id, [string]$name) {
    if (-not (Has 'winget')) {
        Box "لم أجد أداة التثبيت winget على جهازك.`n`nسأفتح لك متجر مايكروسوفت: ثبّت أو حدّث تطبيق «App Installer»، ثم افتح هذا الملف مرة ثانية." 'Warning'
        Start-Process 'ms-windows-store://pdp/?productid=9NBLGGH4NNS1'
        exit 1
    }
    Say "جارٍ تثبيت $name ... (قد يطلب ويندوز إذنك، اضغط نعم)"
    & winget install -e --id $id --accept-package-agreements --accept-source-agreements
    Refresh-Path
}

try {
    Say '================ مصنع الفيديو ================'

    # 1) Required programs
    if (-not (Has 'git')) { Install-Tool 'Git.Git' 'Git' }
    if (-not (Has 'git') -and (Test-Path 'C:\Program Files\Git\cmd\git.exe')) { $env:Path += ';C:\Program Files\Git\cmd' }
    if (-not (Has 'git')) { throw 'لم أتمكن من تثبيت Git. أعد تشغيل الكمبيوتر ثم افتح الملف مرة ثانية.' }

    $py = Find-Python
    if (-not $py) { Install-Tool 'Python.Python.3.12' 'Python'; $py = Find-Python }
    if (-not $py) { throw 'لم أتمكن من تثبيت Python. أعد تشغيل الكمبيوتر ثم افتح الملف مرة ثانية.' }

    if (-not (Has 'ffmpeg')) { Install-Tool 'Gyan.FFmpeg' 'FFmpeg' }
    if (-not (Has 'ffmpeg')) { throw 'لم أتمكن من تثبيت FFmpeg. أعد تشغيل الكمبيوتر ثم افتح الملف مرة ثانية.' }

    # 2) The project
    $first = $false
    if (-not (Test-Path (Join-Path $Dir '.git'))) {
        Say 'جارٍ تحميل المشروع... (قد تفتح صفحة لتسجيل الدخول إلى GitHub، سجّل الدخول بحسابك)'
        & git clone --branch $Branch $Repo $Dir
        if ($LASTEXITCODE -ne 0) { throw 'فشل تحميل المشروع من GitHub. تأكد من الإنترنت ومن تسجيل الدخول بحسابك.' }
        $first = $true
    } else {
        Say 'جارٍ التحقق من التحديثات...'
        & git -C $Dir pull --ff-only
        if ($LASTEXITCODE -ne 0) { Write-Host 'تنبيه: لم أتمكن من التحديث، سأفتح النسخة الحالية.' -ForegroundColor Yellow }
    }
    Set-Location $Dir

    # 3) Libraries
    Say 'جارٍ تثبيت المكتبات...'
    & $py -m pip install --disable-pip-version-check -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'فشل تثبيت مكتبات Python.' }

    # 4) The desktop icon (recreated if it was deleted or never created)
    Say 'جارٍ تجهيز أيقونة «مصنع الفيديو» على سطح المكتب...'
    & $py -m factory shortcut

    # 5) Open the app with no black window, then make sure it actually started
    $pyw = Join-Path (Split-Path $py) 'pythonw.exe'
    if (-not (Test-Path $pyw)) { $pyw = $py }
    $errFile = Join-Path $Dir 'workspace\app-error.txt'
    Start-Process -FilePath $pyw -ArgumentList @('-m', 'factory', 'app') -WorkingDirectory $Dir
    Say 'جارٍ فتح التطبيق...'
    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri 'http://127.0.0.1:8765/api/auth'
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch {}
        if (Test-Path $errFile) { break }
    }
    if (-not $ok) {
        $details = ''
        if (Test-Path $errFile) { $details = (Get-Content $errFile -Raw -Encoding UTF8) }
        Write-Host $details -ForegroundColor Red
        $tail = (($details -split "`n") | Select-Object -Last 3) -join "`n"
        throw ("التطبيق لم يعمل.`n" + $tail)
    }
    Say 'تم! التطبيق يعمل الآن في المتصفح: http://127.0.0.1:8765'
    if ($first) {
        Box "تم التثبيت بنجاح ✅`n`nالتطبيق مفتوح الآن في المتصفح.`nمن المرة القادمة افتح المصنع من أيقونة «مصنع الفيديو» على سطح المكتب."
    }
    Start-Sleep -Seconds 3
    try { Stop-Transcript | Out-Null } catch {}
    exit 0
}
catch {
    Write-Host ''
    Write-Host ('حدثت مشكلة: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('السجل محفوظ في: ' + $Log) -ForegroundColor Yellow
    try { Stop-Transcript | Out-Null } catch {}
    Box ("حدثت مشكلة:`n" + $_.Exception.Message + "`n`nأرسل لي صورة لهذه الرسالة، أو الملف:`n" + $Log) 'Error'
    exit 1
}
