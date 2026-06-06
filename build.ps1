$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

python (Join-Path $root "scripts\validate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
