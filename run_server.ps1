$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source --version *> $null
    if ($LASTEXITCODE -ne 0) {
        $python = $null
    }
}

if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source --version *> $null
        if ($LASTEXITCODE -ne 0) {
            $python = $null
        }
    }
}

if (-not $python) {
    Write-Host "No se encontró Python. Instale Python 3 y vuelva a ejecutar este archivo." -ForegroundColor Red
    exit 1
}

& $python.Source (Join-Path $PSScriptRoot "server.py")
