# Creates "Video Factory" + "New Video" shortcuts on your Desktop
# and registers auto-start at logon (Task Scheduler). Run once:
#   powershell -ExecutionPolicy Bypass -File windows\create_desktop_shortcut.ps1
$root = Split-Path -Parent $PSScriptRoot
$desk = [Environment]::GetFolderPath("Desktop")
$ws = New-Object -ComObject WScript.Shell
foreach ($s in @(@("Video Factory", "start_factory.bat"), @("New Video", "new_video.bat"))) {
  $lnk = $ws.CreateShortcut("$desk\$($s[0]).lnk")
  $lnk.TargetPath = "$root\windows\$($s[1])"
  $lnk.WorkingDirectory = $root
  $lnk.IconLocation = "shell32.dll,115"
  $lnk.Save()
}
$action  = New-ScheduledTaskAction -Execute "$root\windows\start_factory.bat" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$set     = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
           -ExecutionTimeLimit (New-TimeSpan -Days 0) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "VideoFactory" -Action $action -Trigger $trigger -Settings $set -Force | Out-Null
Write-Host "Done: Desktop shortcuts created and VideoFactory starts automatically at logon."
