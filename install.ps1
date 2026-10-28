# code-video 一键安装（Windows PowerShell）
#   在技能目录执行：powershell -ExecutionPolicy Bypass -File install.ps1 [-Remotion] [-HyperFrames] [-Lemo] [-VideoHome D:\AI\claude视频制作]
param([switch]$Remotion, [switch]$HyperFrames, [switch]$Lemo, [string]$VideoHome = "$HOME\claude-video")
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
if ($Lemo) {
  Write-Host '▶ lemo-opuscar 风格库（59 种完整风格 + 98 种风格提示词，MIT）+ Windows 适配'
  $L = "$VideoHome\lemo-opuscar"
  if (-not (Test-Path $L)) { git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar $L } else { git -C $L pull --ff-only }
  Push-Location $L
  npm install --no-audit --no-fund --loglevel=error
  node node_modules/playwright-core/cli.js install chromium-headless-shell
  if (-not (Test-Path .venv\Scripts\python.exe)) { python -m venv .venv }
  .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
  # 它的文档和 build.sh 写的是 Mac/Linux 的 .venv/bin/python：放一个 sh 垫片指向 Windows 的 Scripts\python.exe，并强制 UTF-8（否则中文 Windows 控制台打印 ✓ 会 GBK 报错）
  New-Item -ItemType Directory -Force .venv\bin | Out-Null
  [IO.File]::WriteAllText("$L\.venv\bin\python", "#!/bin/sh`nexport PYTHONUTF8=1 PYTHONIOENCODING=utf-8`nexec `"`$(dirname `"`$0`")/../Scripts/python.exe`" `"`$@`"`n")
  sh tools/fetch.sh hdri
  Pop-Location
  [Environment]::SetEnvironmentVariable('LEMO', $L, 'User')
}
[Environment]::SetEnvironmentVariable('SY_STYLES', "$Skill\engines\sy-styles-20", 'User')
Write-Host "✔ 完成。引擎：$Skill\engines\sy-styles-20；你的视频项目建议放在 $VideoHome。重开终端后环境变量 SY_STYLES 生效。" -ForegroundColor Green
