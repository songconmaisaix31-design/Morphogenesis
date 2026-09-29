# Read-only local preflight, adapted from governance 40577cb v41flash preflight.
# Only approved standard credential locations; existence only, never contents.
param([Parameter(Mandatory)][string]$Output)
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Output) { throw 'Use a new evidence output; never overwrite failures' }
$fcRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$fcAuth='C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm/.runtime/fc-auth'
$fcEnvNames=@('DEEPSEEK_API_KEY','DEEPSEEK_BASE_URL','DSH_HOME','DSH_SETTINGS_FILE','MORPH_EVOMAP_API_KEY','DASHSCOPE_API_KEY')
$fcPresence=@(foreach($fcScope in @('Process','User','Machine')) {
  foreach($fcName in $fcEnvNames) {
    @{name=$fcName;scope=$fcScope;present=(-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($fcName,$fcScope)))}
  }
})
$fcPaths=@(foreach($fcHome in @('C:/Users/DW/.dsh',"$fcAuth/dsh-home")) {
  foreach($fcName in @('settings.yaml','.credentials.yaml','.env','profiles/headless/cordis.patch.yml')) {
    @{path="$fcHome/$fcName";exists=(Test-Path -LiteralPath "$fcHome/$fcName")}
  }
})
$fcPaths+=@{path="$fcRoot/.env";exists=(Test-Path -LiteralPath "$fcRoot/.env")}
$fcCommands=@()
foreach($fcArgs in @(@('--version'),@('--help'),@('--profile','headless','--help'))) {
  $fcText=(& dsh @fcArgs | Out-String)
  $fcCommands+=@{command=('dsh '+($fcArgs -join ' '));exit_code=$LASTEXITCODE;stdout=$fcText}
}
$fcPorts=@(foreach($fcPort in @(7526,7527,7844,7861,7862,7863)) {
  $fcListeners=@(Get-NetTCPConnection -State Listen -LocalPort $fcPort -ErrorAction SilentlyContinue)
  @{port=$fcPort;listener_pids=@($fcListeners | ForEach-Object {$_.OwningProcess})}
})
$fcEnvironment=@(foreach($fcPath in @('.venv/Scripts/python.exe','node_modules/@evomap/gep-sdk/package.json','node_modules/echarts/package.json','viz/static/app.js')) {
  @{path=$fcPath;exists=(Test-Path -LiteralPath (Join-Path $fcRoot $fcPath))}
})
$fcRefs=(& git ls-remote origin refs/heads/decentralized-swarm refs/heads/morph-fc-candidate-0929 refs/heads/morph-fc-governance-final-0929 refs/heads/morph-fc-release-preflight-0929 | Out-String)
$fcRefExit=$LASTEXITCODE
$fcHead=(& git rev-parse HEAD | Out-String).Trim()
$fcStatus=(& git status --short | Out-String)
[ordered]@{
  captured_utc=[DateTime]::UtcNow.ToString('o');head=$fcHead;worktree=$fcRoot;worktree_status=$fcStatus
  remote_refs=$fcRefs;remote_exit=$fcRefExit;commands=$fcCommands
  credential_environment_presence=$fcPresence;standard_file_presence=$fcPaths
  credential_scope='Known standard sources from governance 40577cb only; no secret content, no historical scan, no remote authentication'
  ports=$fcPorts;environment=$fcEnvironment
  submitted=$false;model_requests=0;hub_requests=0;returned_model=$null;usage=$null;cost=$null
  interpretation='Preflight observations only, not release/FC-E/live acceptance; inspect presence flags, never infer a key is valid'
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding utf8
if($fcRefExit -ne 0 -or @($fcCommands | Where-Object {$_.exit_code -ne 0}).Count) { exit 1 }
Write-Output 'Read-only preflight captured; model/Hub requests 0; no credential values emitted.'
