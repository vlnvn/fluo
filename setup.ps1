param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
foreach ($fluoPort in @(8000, 5173)) {
    $fluoConnection = [System.Net.Sockets.TcpClient]::new()
    try {
        $fluoConnection.Connect('127.0.0.1', $fluoPort)
        throw "Port $fluoPort is active. Stop the running Fluo servers before setup; Windows locks installed executables."
    } catch [System.Net.Sockets.SocketException] {
        # No server is using this local port.
    } finally { $fluoConnection.Dispose() }
}
if (-not $PythonPath) {
    $fluoCandidates = @(
        (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'),
        (Get-Command python -ErrorAction SilentlyContinue).Source
    )
    foreach ($fluoCandidate in $fluoCandidates) {
        if ($fluoCandidate -and (Test-Path -LiteralPath $fluoCandidate)) {
            $fluoVersion = & $fluoCandidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            if ($fluoVersion -in @('3.12', '3.13')) { $PythonPath = $fluoCandidate; break }
        }
    }
}
if (-not $PythonPath) { throw 'Python 3.12 or 3.13 is required. Run setup.ps1 -PythonPath C:\path\to\python.exe.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $PythonPath -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& '.\.venv\Scripts\python.exe' tools\prepare_runtime.py
if ($LASTEXITCODE -ne 0) { throw 'Audited artifact preparation failed.' }
Push-Location web
try { npm ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' } } finally { Pop-Location }
Write-Host 'Setup complete. Run: .\.venv\Scripts\python.exe tools\dev.py'
