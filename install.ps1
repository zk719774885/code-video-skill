# code-video 一键安装（Windows PowerShell）
#   在技能目录执行：powershell -ExecutionPolicy Bypass -File install.ps1 [-Remotion] [-HyperFrames] [-VideoHome D:\AI\claude视频制作]
param([switch]$Remotion, [switch]$HyperFrames, [string]$VideoHome = "$HOME\claude-video")
$ErrorActionPreference = 'Stop'
$Skill = $PSScriptRoot
function Need($cmd, $hint) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Write-Host "缺少 $cmd：$hint" -ForegroundColor Red; exit 1 } }
Need node   '请安装 Node.js 18+（https://nodejs.org）'
Need python '请安装 Python 3.10+（https://python.org）'
Need ffmpeg '请安装 ffmpeg 并加入 PATH（winget install ffmpeg）'
Write-Host '▶ Python 依赖 numpy scipy'; python -m pip install --quiet numpy scipy
Write-Host '▶ sy-styles-20 依赖与浏览器内核'
Push-Location "$Skill\engines\sy-styles-20"; npm install --silent; npx --yes playwright install chromium; Pop-Location
New-Item -ItemType Directory -Force $VideoHome | Out-Null
if ($Remotion) {
  Write-Host '▶ Remotion 项目 + 官方技能（>3 人营利公司商用需购买 Company License）'
  Push-Location $VideoHome; if (-not (Test-Path remotion-studio)) { npx -y create-video@latest --yes --blank remotion-studio }; Pop-Location
  npx -y skills add remotion-dev/skills -g -y -a claude-code
}
if ($HyperFrames) {
  Write-Host '▶ HyperFrames 项目 + 官方技能'
  Push-Location $VideoHome; if (-not (Test-Path hyperframes-studio)) { npx -y hyperframes@latest init hyperframes-studio --example blank --non-interactive }; Pop-Location
  npx -y hyperframes@latest skills update
}
[Environment]::SetEnvironmentVariable('SY_STYLES', "$Skill\engines\sy-styles-20", 'User')
Write-Host "✔ 完成。引擎：$Skill\engines\sy-styles-20；你的视频项目建议放在 $VideoHome。重开终端后环境变量 SY_STYLES 生效。" -ForegroundColor Green
