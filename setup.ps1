# 7L VM Setup Script (PowerShell Native)
# 🛡️ 安全閘門：預設拒絕從 HTTP（明文）下載並執行 zip。
#    - 要用內網 HTTP 來源：加 -AllowInsecureHttp 明確宣告風險自負
#    - 或設環境變數 AGENT_ZIP_URL（建議用 https://...）
param(
    [switch]$AllowInsecureHttp
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " [*] Downloading and setting up 7L VM Agent..." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

$destDir = "C:\7L_VM_Agent"
if (!(Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

# 來源優先序：AGENT_ZIP_URL（建議 https）→ 內網預設（需 -AllowInsecureHttp）
$zipUrl = $env:AGENT_ZIP_URL
$fallbackUrl = $null
if (-not $zipUrl) {
    if (-not $AllowInsecureHttp) {
        Write-Host "[!] 已中止：未設定來源，且不允許明文 HTTP 下載。" -ForegroundColor Red
        Write-Host "    請二選一：" -ForegroundColor Yellow
        Write-Host "      A) 設定安全來源：`$env:AGENT_ZIP_URL = 'https://<host>/7L_VM_Agent.zip' 後重跑" -ForegroundColor Yellow
        Write-Host "      B) 確認來源可信後加旗標重跑：.\setup.ps1 -AllowInsecureHttp" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[!] -AllowInsecureHttp 已指定：將以明文 HTTP 從內網主機下載（無憑證驗證）" -ForegroundColor Yellow
    $zipUrl = "http://172.22.208.1:8888/7L_VM_Agent.zip"
    $fallbackUrl = "http://192.168.1.102:8888/7L_VM_Agent.zip"
}

if ($zipUrl.StartsWith("http://") -and -not $AllowInsecureHttp) {
    Write-Host "[!] 已中止：AGENT_ZIP_URL 是明文 http://，需加 -AllowInsecureHttp 才准用。" -ForegroundColor Red
    exit 1
}

$zipPath = "$destDir\7L_VM_Agent.zip"

Write-Host "[1/3] Downloading 7L_VM_Agent.zip from $zipUrl ..." -ForegroundColor Green
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    if ($fallbackUrl) {
        Write-Host "[!] Trying fallback IP 192.168.1.102..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $fallbackUrl -OutFile $zipPath -UseBasicParsing
    } else {
        Write-Host "[X] 下載失敗且無備用來源：$($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[2/3] Extracting archive..." -ForegroundColor Green
Expand-Archive -Path $zipPath -DestinationPath $destDir -Force

Write-Host "[3/3] Running installer script..." -ForegroundColor Green
Set-Location $destDir
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$destDir\install.ps1"
