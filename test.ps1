$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

python (Join-Path $root "scripts\validate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python (Join-Path $root "scripts\test_import_synthetic_release.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
