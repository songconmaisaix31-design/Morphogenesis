param(
  [switch]$Mock,
  [int]$Port = 7500,
  [string]$T2Command = $env:MORPHOGENESIS_T2_DEMO_COMMAND
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($Mock) {
  Write-Host "Starting labelled mock-only visual preview; this does not execute a task."
  python -m viz.server --port $Port --input demo/data/mock-run.json
  exit $LASTEXITCODE
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python is required for the T5 local preview."
}

# T0 prepares the fixed task; T5 never fabricates a task, a model result, or an
# event export. T2's command is injected by its owner once the CLI is frozen.
$workspace = Join-Path $env:TEMP "morphogenesis-t5-demo"
if (Test-Path (Join-Path $Root "bootstrap\__main__.py")) {
  python -m bootstrap prepare --workspace $workspace
} else {
  throw "T0 bootstrap entry is unavailable; do not substitute a mock task."
}
if ([string]::IsNullOrWhiteSpace($T2Command)) {
  throw "Set MORPHOGENESIS_T2_DEMO_COMMAND to T2's documented runtime/export command; no runtime was executed."
}
& powershell -NoProfile -Command $T2Command
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$export = Join-Path $Root "runtime_exports\events.jsonl"
if (-not (Test-Path $export)) {
  throw "T2 completed without runtime_exports/events.jsonl; dashboard will not infer events."
}
python -m viz.server --port $Port --input $export
