# Quick test runner for Vecinita
# Bypasses uv run which has venv locking issues on Windows

param(
    [string]$TestFile = "tests/",
    [switch]$Verbose = $false,
    [switch]$Coverage = $false
)

$args = @("--tb=short")

if ($Verbose) {
    $args += "-v"
}

if ($Coverage) {
    $args += "--cov=src", "--cov-report=term-missing"
}

$args += $TestFile

Write-Host "Running pytest with args: $($args -join ' ')" -ForegroundColor Cyan
python -m pytest @args

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
}

exit $LASTEXITCODE
