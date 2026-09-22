param(
  [switch]$Mock,
  [ValidateSet("auto", "manual")][string]$Mode = "auto",
  [string]$Replay,
  [switch]$AuthorizeLive,
  [int]$Port = 7500,
  [ValidateSet("codex", "evomap")][string]$Executor = "codex",
  [string]$Model,
  [int]$MaxTokens = 20000,
  [double]$MaxCostUsd = 1.0,
  [int]$TimeoutSeconds = 120,
  [double]$TauSeconds = 10,
  [double]$ArchiveThreshold = 0.2,
  [double]$StageDelay = 2,
  [double]$TickSeconds = 1
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not $Model) { $Model = if ($Executor -eq "evomap") { "evomap-gpt-5.6-luna" } else { "gpt-5.6-luna" } }

function Stop-OwnViewer {
  param([int]$LauncherProcessId, [int]$ViewerPort)
  $launcher = Get-CimInstance Win32_Process -Filter "ProcessId=$LauncherProcessId" -ErrorAction SilentlyContinue
  $listener = Get-NetTCPConnection -State Listen -LocalPort $ViewerPort -ErrorAction SilentlyContinue
  $listenerProcess = if ($listener) { Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue }
  if ($listenerProcess -and $listenerProcess.ParentProcessId -eq $LauncherProcessId -and $listenerProcess.CommandLine -match "m viz\.server --port $ViewerPort") {
    Stop-Process -Id $listenerProcess.ProcessId -ErrorAction SilentlyContinue
  }
  if ($launcher -and $launcher.CommandLine -match "m viz\.server --port $ViewerPort") {
    Stop-Process -Id $LauncherProcessId -ErrorAction SilentlyContinue
  }
}

if (-not (Test-Path $Python)) {
  throw "缺少本工作树锁定环境 .venv；先运行: `$env:POETRY_VIRTUALENVS_IN_PROJECT='true'; uv tool run poetry install --no-interaction"
}
if (-not (1..65535 -contains $Port)) { throw "Port 必须在 1 到 65535 之间。" }
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
  throw "Port $Port 已被占用；不会终止未知进程。"
}

if ($Mock) {
  if ($Replay -or $AuthorizeLive) { throw "-Mock 不能与 -Replay 或 -AuthorizeLive 组合。" }
  Write-Host "启动标记为 mock 的旧仪表板预览；这不会执行任务。"
  Remove-Item Env:MORPH_EVOMAP_API_KEY -ErrorAction SilentlyContinue
  & $Python -m viz.server --port $Port --input demo/data/mock-run.json
  exit $LASTEXITCODE
}

if ($Replay) {
  $rehearsalJson = (Resolve-Path -LiteralPath $Replay -ErrorAction Stop).Path
  if ((Split-Path -Leaf $rehearsalJson) -ne "rehearsal.json") { throw "-Replay 必须指向已有 rehearsal.json。" }
  Write-Host "只读回放：$rehearsalJson"
  Write-Host "打开 http://127.0.0.1:$Port；页面明确标为回放，不调用模型、不改原证据。"
  Remove-Item Env:MORPH_EVOMAP_API_KEY -ErrorAction SilentlyContinue
  & $Python -m viz.server --port $Port --rehearsal $rehearsalJson --replay
  exit $LASTEXITCODE
}

if (-not $AuthorizeLive) {
  throw "真实彩排必须显式传入 -AuthorizeLive；该操作只授权 repair 与 recovery 两个新任务。"
}

$runRoot = Join-Path $env:TEMP ("morph-rehearsal-" + [guid]::NewGuid().ToString("N"))
$rehearsalJson = Join-Path $runRoot "rehearsal.json"
$viewerLogRoot = Join-Path $env:TEMP ("morph-viz-viewer-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $viewerLogRoot | Out-Null
$viewerOut = Join-Path $viewerLogRoot "viewer.stdout.log"
$viewerErr = Join-Path $viewerLogRoot "viewer.stderr.log"
# PowerShell 7.4+ per-child override: the executor retains its process credential.
$viewer = Start-Process -FilePath $Python -ArgumentList @("-m", "viz.server", "--port", "$Port", "--rehearsal", "$rehearsalJson") -WorkingDirectory $Root -WindowStyle Hidden -Environment @{ MORPH_EVOMAP_API_KEY = $null } -RedirectStandardOutput $viewerOut -RedirectStandardError $viewerErr -PassThru
$readyBy = (Get-Date).AddSeconds(12)
$viewerListener = $null
while ((Get-Date) -lt $readyBy) {
  Start-Sleep -Milliseconds 200
  $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
  if (-not $listener) { continue }
  $candidate = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
  if ($candidate -and $candidate.ParentProcessId -eq $viewer.Id -and $candidate.CommandLine -match "m viz\.server --port $Port") {
    $viewerListener = $candidate
    break
  }
  Stop-OwnViewer -LauncherProcessId $viewer.Id -ViewerPort $Port
  throw "Port $Port 在启动期间被非本次页面进程占用；不会开始彩排。"
}
if (-not $viewerListener) {
  Stop-OwnViewer -LauncherProcessId $viewer.Id -ViewerPort $Port
  throw "本地只读页面在 12 秒内未就绪；已仅清理本次页面进程。日志：$viewerLogRoot"
}

Write-Host "页面已启动：http://127.0.0.1:$Port"
Write-Host "页面 launcher PID=$($viewer.Id)，监听 PID=$($viewerListener.ProcessId)，日志：$viewerLogRoot"
Write-Host "展示结束后，先核对这两个 PID 的命令行均为本次 viz.server，再关闭它们；不会自动处理其他进程。"
Write-Host "本轮最多两个明确授权的新任务；失败、未知或中断时不自动重试。"
if ($Mode -eq "manual") { Write-Host "手动模式将在成员下线前停在控制台；确认后按 Enter。" }

& $Python -m orchestration.rehearsal --root $runRoot --mode $Mode --executor $Executor --model $Model --authorize-task repair --authorize-task recovery --tau-seconds $TauSeconds --archive-threshold $ArchiveThreshold --stage-delay $StageDelay --tick-seconds $TickSeconds --timeout $TimeoutSeconds --max-tokens $MaxTokens --max-cost-usd $MaxCostUsd
$result = $LASTEXITCODE
if ($result -ne 0) {
  Write-Host "彩排未完成（exit $result）。只读页面仍指向保留的证据根：$runRoot"
  exit $result
}
Write-Host "彩排流程已结束；页面继续只读显示 $rehearsalJson。"
