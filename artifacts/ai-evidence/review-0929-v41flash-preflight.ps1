# Read-only local CLI/configuration inspection. No model invocation or secret output.
$ErrorActionPreference = 'Stop'
$fcRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$fcAuth = 'C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm/.runtime/fc-auth'
$fcInstall = 'C:/Users/DW/AppData/Roaming/npm/node_modules/@deepseek-ai/dsh'
$fcLib = Join-Path $fcInstall 'node_modules/@deepseek-ai'
$fcVersion = (& dsh --version | Out-String).Trim()
$fcVersionExit = $LASTEXITCODE
$fcHelp = (& dsh --help | Out-String)
$fcHelpExit = $LASTEXITCODE
$fcHeadlessHelp = (& dsh --profile headless --help | Out-String)
$fcHeadlessHelpExit = $LASTEXITCODE
$fcEnvs = foreach ($fcScope in @('Process', 'User', 'Machine')) {
    foreach ($fcName in @('DEEPSEEK_API_KEY', 'DEEPSEEK_BASE_URL', 'DSH_HOME', 'DSH_SETTINGS_FILE')) {
        [ordered]@{ name = $fcName; scope = $fcScope; present = (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($fcName, $fcScope))) }
    }
}
$fcPaths = foreach ($fcHome in @('C:/Users/DW/.dsh', "$fcAuth/dsh-home")) {
    foreach ($fcFilename in @('settings.yaml', '.credentials.yaml', '.env')) {
        [ordered]@{ path = "$fcHome/$fcFilename"; exists = (Test-Path -LiteralPath "$fcHome/$fcFilename") }
    }
}
$fcPaths += [ordered]@{ path = "$fcRoot/.env"; exists = (Test-Path -LiteralPath "$fcRoot/.env") }
$fcSelections = @()
foreach ($fcConfigPath in @("$fcAuth/dsh-dashscope.patch.yml", "$fcAuth/dsh-composed.yml")) {
    $fcText = [IO.File]::ReadAllText($fcConfigPath)
    $fcSelections += [ordered]@{
        path = $fcConfigPath
        provider = ([regex]::Match($fcText, '(?m)^\s+provider: ([^\r\n]+)')).Groups[1].Value.Trim()
        model = ([regex]::Match($fcText, '(?m)^\s+model: ([^\r\n]+)')).Groups[1].Value.Trim()
        endpoint = ([regex]::Match($fcText, '(?m)^\s+baseURL: ([^\r\n]+)')).Groups[1].Value.Trim()
        max_retries = ([regex]::Match($fcText, '(?m)^\s+maxRetries: ([0-9]+)')).Groups[1].Value
        has_v41_identifier = ($fcText -match 'deepseek-flash|DeepSeek-V41-Flash')
    }
}
$fcProfiles = foreach ($fcProfilePath in @("$fcAuth/dsh-home/profiles/headless/cordis.patch.yml", 'C:/Users/DW/.dsh/profiles/headless/cordis.patch.yml', 'C:/Users/DW/.dsh/profiles/web/cordis.patch.yml')) {
    $fcData = ((Get-Content -LiteralPath $fcProfilePath | Where-Object { $_ -notmatch '^\s*#' }) -join "`n").Trim()
    [ordered]@{ path = $fcProfilePath; empty_patch = ($fcData -eq '[]') }
}
$fcEvidence = @()
foreach ($fcSpan in @(
    @('dsh-llm-deepseek/lib/index.js',1838,1856),
    @('dsh-llm-deepseek/lib/index.js',1884,1898),
    @('dsh-llm-deepseek/lib/index.js',1990,2003),
    @('dsh-credentials-local/lib/index.js',13,20),
    @('dsh-headless/lib/startup.js',24,35),
    @('dsh-headless/lib/index.js',127,145),
    @('dsh-agent-loop/lib/index.js',927,981),
    @('dsh-agent-loop/lib/index.js',1115,1119),
    @('dsh-agent-loop/lib/index.js',1490,1503),
    @('dsh-tools/lib/types/index.d.ts',449,470),
    @('dsh-base/cordis.patch.yml',73,79)
)) {
    $fcFile = Join-Path $fcLib $fcSpan[0]
    $fcLines = [IO.File]::ReadAllLines($fcFile)
    $fcEvidence += [ordered]@{ path = $fcFile; first_line = $fcSpan[1]; last_line = $fcSpan[2]; quote = ($fcLines[($fcSpan[1]-1)..($fcSpan[2]-1)] -join "`n") }
}
$fcResult = [ordered]@{
    candidate = 'c552250c0d07f5f70f09eb0a5ab3c322195e34ec'
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    package = '@deepseek-ai/dsh'; version = $fcVersion; license = 'MIT'
    commands = @(
        @{ command = 'dsh --version'; exit_code = $fcVersionExit; stdout = $fcVersion },
        @{ command = 'dsh --help'; exit_code = $fcHelpExit; stdout = $fcHelp },
        @{ command = 'dsh --profile headless --help'; exit_code = $fcHeadlessHelpExit; stdout = $fcHeadlessHelp }
    )
    configured_original = $fcSelections
    standard_profile_patches = $fcProfiles
    requested_name = 'deepseekV4.1flash'
    resolved_catalog = @{ provider = 'deepseek-official'; model = 'deepseek-flash'; name = 'DeepSeek-V41-Flash'; source = 'installed official dsh-llm-deepseek 0.1.5-rc.3; not live model enumeration' }
    official_default_endpoint = 'https://api.deepseek.com'
    credential_environment_presence = $fcEnvs
    native_config_file_presence = $fcPaths
    credential_resolution = 'process env > DSH_HOME/.credentials.yaml > invocation cwd/.env > DSH_HOME/.env'
    credential_status = 'MISSING_IN_CHECKED_NATIVE_SOURCES'
    bounds = @{
        finite_output_supported = 'llm-deepseek.config.maxTokens'
        zero_retries_supported = 'llm-deepseek.config.retryPolicy.maxRetries=0, mode=normal'
        tools_disable = 'individual plugin disabled entries supported; read-only still permits multiple tool rounds; isolated final composition NOT_RUN'
        hard_step_request_cap = 'CLI limitation, NOT an independent blocker: no explicit step/request limit; one bounded invocation authorized by coordinator msg_a077597131fd'
        input_transport = 'headless accepts positional task only; full packet exceeds ordinary Windows command-line size; native config task binding must be validated before sending'
        actual_returned_model_observability = 'NOT_VERIFIED: headless returns final text; session source.model copies request.model, not independent returned model proof'
    }
    invocation_policy = @{ invocations = 1; max_wall_time_ms = 600000; automatic_retry = $false; timeout_effect = 'unknown if already submitted; preserve and never retry'; actual_request_count_if_unobservable = $null; status = 'authorized but NOT_RUN due to credential absence' }
    source_evidence = $fcEvidence
    submitted = $false; request_count = 0; returned_model = $null; usage = $null; cost = $null
    review_exit_code = $null; preflight = 'BLOCKED'; fc_e = 'OPEN'; signature = 'unsigned'
}
if ($fcVersionExit -ne 0 -or $fcHelpExit -ne 0 -or $fcHeadlessHelpExit -ne 0) { throw 'CLI discovery failed; inspect command results.' }
$fcResult | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'review-0929-v41flash-preflight.json') -Encoding utf8
Write-Output 'CLI discovery exit 0; preflight BLOCKED; model requests 0; no credential values emitted.'
