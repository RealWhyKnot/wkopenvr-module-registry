param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$versionPath = Join-Path $root "version.txt"
if (-not [string]::IsNullOrWhiteSpace($Version)) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($versionPath, $Version.Trim(), $utf8NoBom)
}
if (-not (Test-Path -LiteralPath $versionPath)) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($versionPath, "0.1.0", $utf8NoBom)
}

python (Join-Path $root "scripts\validate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
