#Requires -Version 5.1
<#
.SYNOPSIS
  7L Live Coding 工具鏈一鍵安裝（跟 CLI 一起包）。
.DESCRIPTION
  裝：SuperCollider 3.14（scsynth 音訊引擎，FoxDot/Tidal 共用）
      Sonic Pi 4.6（最友善 live coding，7L 經 OSC 送碼演奏）
      FoxDot + python-osc（pip，Python live coding）
  不裝：Haskell/GHC（Tidal 用，~2GB，需手動裝 GHCup；見下方提示）
  冪等：裝過的自動跳過。需管理員權限（winget 需求）。
#>
$ErrorActionPreference = "Stop"

function Have($cmd) { $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host "=== 7L Live Coding toolchain ==="

if (-not (Have "winget")) { throw "找不到 winget，請先更新 App Installer (Microsoft Store)" }

$pkgs = @(
  @{ id = "SuperCollider.SuperCollider"; name = "SuperCollider"; test = { Test-Path "C:\Program Files\SuperCollider\scsynth.exe" } },
  @{ id = "SonicPi.SonicPi"; name = "Sonic Pi"; test = { Test-Path "C:\Program Files\Sonic Pi\app\server\bin\sonic-pi-server.rb" } }
)
foreach ($p in $pkgs) {
  if (& $p.test) { Write-Host "[skip] $($p.name) 已安裝" }
  else {
    Write-Host "[install] $($p.name) ..."
    winget install --id $p.id -e --silent --accept-package-agreements --accept-source-agreements
  }
}

Write-Host "[pip] FoxDot + python-osc ..."
python -m pip install --upgrade FoxDot python-osc

Write-Host ""
Write-Host "--- 驗證 ---"
python -c "import FoxDot; print('FoxDot OK', FoxDot.__version__ if hasattr(FoxDot,'__version__') else '')"
python -c "from pythonosc import udp_client; print('python-osc OK')"
if (Test-Path "C:\Program Files\SuperCollider\scsynth.exe") { Write-Host "scsynth OK" }
if (Test-Path "C:\Program Files\Sonic Pi") { Write-Host "Sonic Pi OK" }
Write-Host ""
Write-Host "TidalCycles 要另裝 Haskell（約 2GB）：https://www.haskell.org/ghcup/ 裝完跑 cabal install tidal"
Write-Host "裝完在 .env 設 LIVECODE_BACKEND=foxdot 或 sonicpi（預設 mini 零依賴）"
