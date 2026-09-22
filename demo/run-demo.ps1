param(
  [switch]$Mock,
  [int]$Port = 7500,
  [string]$Model = "gpt-5.6-luna",
  [int]$MaxTokens = 20000,
  [double]$MaxCostUsd = 1.0,
  [int]$TimeoutSeconds = 120
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

# T2 owns the live one-call fixed task entry. It invokes T0 bootstrap itself,
# writes T2's fixed evidence sidecars under a fresh temp root, and does not
# retry or substitute mock data when an execution fails.
if (-not (Test-Path (Join-Path $Root "orchestration\acceptance.py"))) {
  throw "T2 acceptance entry is not merged; do not substitute a mock runtime."
}
$runRoot = Join-Path $env:TEMP ("morph-t2-live-demo-" + [guid]::NewGuid().ToString("N"))
python -m orchestration.acceptance --root $runRoot --model $Model --max-tokens $MaxTokens --max-cost-usd $MaxCostUsd --timeout $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

foreach ($required in @("events.jsonl", "result.json", "genes.json", "adoption.json")) {
  if (-not (Test-Path (Join-Path $runRoot $required))) {
    throw "T2 completed without $required; dashboard will not infer its contents."
  }
}
python -m viz.server --port $Port --t2-root $runRoot
