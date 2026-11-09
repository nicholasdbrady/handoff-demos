param(
    [Parameter(Mandatory)][string] $Label,
    [Parameter(Mandatory)][string] $Command
)

$ErrorActionPreference = 'Stop'
$env:AZURE_DEV_USER_AGENT = 'microsoft_foundry_skill'
$destination = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\public\demos\azd-agent'))
New-Item -ItemType Directory -Force $destination | Out-Null
$timer = [Diagnostics.Stopwatch]::StartNew()
$output = & pwsh -NoProfile -Command $Command 2>&1 | Out-String -Width 220
$exitCode = $LASTEXITCODE
$timer.Stop()
$output = $output -replace '\x1b\[[0-9;]*[A-Za-z]', ''
$output = $output -replace '(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<redacted-id>'
$output = $output -replace '[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '<redacted-email>'
$output = $output -replace '(?i)(Bearer\s+)[A-Za-z0-9._-]+', '$1<redacted-token>'
$output = $output -replace '(?i)(AccountKey|api_key|access_token|client_secret)(\s*[=:]\s*)[^\s;]+', '$1$2<redacted-secret>'
$output = $output -replace '(https://ai\.azure\.com/nextgen/r/)[^,/\s]+', '$1<redacted-id>'
$safeCommand = $Command -replace '(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<redacted-id>'
@(@{cmd = $safeCommand; output = $output.Trim(); seconds = [Math]::Round($timer.Elapsed.TotalSeconds, 3)}) |
    ConvertTo-Json -Depth 5 -AsArray |
    Set-Content -Encoding utf8 (Join-Path $destination "$Label.json")
Write-Output $output
exit $exitCode
