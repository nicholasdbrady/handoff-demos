param([switch]$Live)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python) -or -not (Test-Path 'node_modules\@slidev\cli')) {
    throw 'Install the demo-local dependencies in README.md first.'
}
if ($Live) { $env:SLIDEV_ENABLE_LIVE = '1' }
$logs = Join-Path $PSScriptRoot '.logs'
New-Item -ItemType Directory -Force $logs | Out-Null
$adapter = Start-Process -FilePath $python -ArgumentList 'demo_server.py' -WorkingDirectory $PSScriptRoot -PassThru -NoNewWindow `
    -RedirectStandardOutput (Join-Path $logs 'adapter.stdout.log') `
    -RedirectStandardError (Join-Path $logs 'adapter.stderr.log')
try {
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        if ($adapter.HasExited) { throw 'Demo adapter exited before startup.' }
        try {
            $null = Invoke-RestMethod 'http://127.0.0.1:3071/demo-api/status' -Headers @{'X-Demo-Client'='slidev'}
            $ready = $true
            break
        } catch [System.Net.Http.HttpRequestException] { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw 'Demo adapter did not become responsive.' }
    & npm run dev
} finally {
    if (-not $adapter.HasExited) { Stop-Process -Id $adapter.Id }
}
