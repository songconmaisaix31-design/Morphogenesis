# Native dsh configuration preparation ONLY. Never boots a runner or invokes a model.
# Reuses installed @deepseek-ai/dsh 0.1.5-rc.3 (MIT) headless/config-dump interface.
param(
  [Parameter(Mandatory)][string]$InputJson,
  [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{40}$')][string]$Candidate,
  [Parameter(Mandatory)][string]$OutputDirectory,
  [ValidateRange(1024,32768)][int]$MaxOutputTokens = 16384
)
$ErrorActionPreference = 'Stop'
$fcInput = Get-Content -LiteralPath $InputJson -Raw | ConvertFrom-Json
if ($fcInput.candidate -ne $Candidate -or $fcInput.submitted -ne $false) { throw 'Input identity/status mismatch' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh output directory; preserve old preparation' }
$fcOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $fcOutput | Out-Null
$fcDisabled = @('headless-startup','session-title-llm','compaction-basic','command-compact',
  'tool-result-pruner','repeat-tool-reminder','session-telemetry-otel','llm-pi-ai',
  'tool-bash','tool-pwsh','tool-jobs','tool-fs','tool-fs-search','tool-skill',
  'tool-subagent-control','tool-subagent-list-agents','tool-subagent','tool-subagent-fork',
  'tool-workflow','tool-todo','tool-goal','tool-ralph','tool-web','code-runtime',
  'subagent','subagent-spawn-in-process','subagent-fork-in-process','workflow-worker-thread',
  'goal-round-driver','agent-instructions','skill-filesystem','web-search-deepseek','web-fetch-http')
$fcPatch = @($fcDisabled | ForEach-Object { @{ id=$_; disabled=$true } })
$fcPatch += @{ id='agent-default-model'; config=@{provider='deepseek-official';model='deepseek-flash'} }
$fcPatch += @{ id='llm-deepseek'; config=@{apiKeyEnv='DEEPSEEK_API_KEY';baseURL='https://api.deepseek.com';maxTokens=$MaxOutputTokens;retryPolicy=@{mode='normal';maxRetries=0}} }
$fcPatch += @{ id='tools'; config=@{mode='native'} }
$fcPatch += @{ id='headless-runner'; inject=@(); config=@{task=$fcInput.content} }
$fcOverlay = Join-Path $fcOutput 'overlay.json'
$fcPatch | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $fcOverlay -Encoding utf8
$fcPreviousHome=$env:DSH_HOME
$fcPreviousSettings=$env:DSH_SETTINGS_FILE
try {
  $env:DSH_HOME=Join-Path $fcOutput 'dsh-home'
  Remove-Item Env:DSH_SETTINGS_FILE -ErrorAction SilentlyContinue
  & dsh --profile headless --patch $fcOverlay --dump-config 1> (Join-Path $fcOutput 'composed.yml') 2> (Join-Path $fcOutput 'dump.stderr.log')
  $fcExit=$LASTEXITCODE
  $fcExit | Set-Content -LiteralPath (Join-Path $fcOutput 'dump.exit')
  if ($fcExit -ne 0) { throw "Native config dump failed exit=$fcExit; preserve logs" }
} finally {
  if ($null -eq $fcPreviousHome) { Remove-Item Env:DSH_HOME -ErrorAction SilentlyContinue } else { $env:DSH_HOME=$fcPreviousHome }
  if ($null -eq $fcPreviousSettings) { Remove-Item Env:DSH_SETTINGS_FILE -ErrorAction SilentlyContinue } else { $env:DSH_SETTINGS_FILE=$fcPreviousSettings }
}
[ordered]@{
  candidate=$Candidate; input_json=[IO.Path]::GetFullPath($InputJson); preparation_control=$fcInput.preparation_control
  overlay=$fcOverlay; dsh_home=(Join-Path $fcOutput 'dsh-home'); dump_exit=$fcExit
  configured_provider='deepseek-official'; configured_model='deepseek-flash'; returned_model=$null
  max_output_tokens=$MaxOutputTokens; retry_max=0; disabled_plugins=$fcDisabled
  submitted=$false; model_requests=0; usage=$null;cost=$null
  status='CONFIG_DUMP_ONLY_NOT_RUNTIME_VALIDATED'
  invocation_limit='Future authorized invocation <=600000ms, no retry, preserve unknown effects; actual request count unknown unless evidenced'
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $fcOutput 'native-prepare.json') -Encoding utf8
Write-Output "Native config dump exit 0; no model invocation; output=$fcOutput"
