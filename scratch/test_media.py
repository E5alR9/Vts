import subprocess

ps_script = """
[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media, ContentType=WindowsRuntime] | Out-Null
$op = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
while ($op.Status -eq 'Started') { Start-Sleep -Milliseconds 50 }
$mgr = $op.GetResults()
$sessions = $mgr.GetSessions()
$found = @()
foreach ($sess in $sessions) {
    try {
        $pOp = $sess.TryGetMediaPropertiesAsync()
        while ($pOp.Status -eq 'Started') { Start-Sleep -Milliseconds 50 }
        $p = $pOp.GetResults()
        if ($p.Title) {
            $found += "$($sess.SourceAppUserModelId) ::: $($p.Title) ::: $($p.Artist)"
        }
    } catch {}
}
if ($found.Count -gt 0) {
    Write-Output ($found -join " ||| ")
} else {
    Write-Output "NO_MEDIA"
}
"""

with open("test_media.ps1", "w", encoding="utf-8") as f:
    f.write(ps_script)

res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "test_media.ps1"], capture_output=True, text=True)
print("OUT:", res.stdout.strip())
print("ERR:", res.stderr.strip())

import os
if os.path.exists("test_media.ps1"):
    os.remove("test_media.ps1")
