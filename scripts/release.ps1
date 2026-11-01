# Build and upload a new version from a clean checkout after the quality gate.
param([switch]$CheckOnly)

$ErrorActionPreference = "Stop"

Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $status = git status --porcelain
    if ($LASTEXITCODE -ne 0 -or $status) { throw "Release requires a clean git checkout." }
    $project = Get-Content -LiteralPath pyproject.toml -Raw
    $match = [regex]::Match($project, '(?m)^version = "([0-9]+\.[0-9]+\.[0-9]+)"\r?$')
    if (-not $match.Success) { throw "Cannot read the release version." }
    $version = $match.Groups[1].Value
    $published = $true
    try {
        Invoke-WebRequest -UseBasicParsing "https://pypi.org/pypi/shortenpath/$version/json" | Out-Null
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) { $published = $false } else { throw }
    }
    if ($published) { throw "shortenpath $version is already published." }
    if ($CheckOnly) { Write-Output "shortenpath $version is available for release."; return }

    & "$PSScriptRoot/check.ps1"
    if ($LASTEXITCODE -ne 0) { throw "Quality gate failed." }
    $token = $env:PYPI_TOKEN
    if (-not $token -and (Test-Path -LiteralPath "C:\secrets\pypi-token.txt")) {
        $token = (Get-Content -LiteralPath "C:\secrets\pypi-token.txt" -Raw).Trim()
    }
    if (-not $token) { throw "No PyPI token. Set PYPI_TOKEN before publishing." }

    $output = Join-Path (Get-Location) ("dist/release-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $output | Out-Null
    python -m build --outdir $output
    if ($LASTEXITCODE -ne 0) { throw "Build failed." }
    python -m twine check --strict "$output/*"
    if ($LASTEXITCODE -ne 0) { throw "Package check failed." }

    $env:TWINE_USERNAME = "__token__"
    $env:TWINE_PASSWORD = $token
    try {
        python -m twine upload "$output/*"
        if ($LASTEXITCODE -ne 0) { throw "Upload failed." }
    } finally { Remove-Item Env:\TWINE_PASSWORD -ErrorAction SilentlyContinue }
} finally { Pop-Location }
