# FastAPI development server runner for Vecinita
# Bypasses uv run which has venv locking issues on Windows

param(
    [int]$Port = 8000,
    [string]$HostAddr = "0.0.0.0"
)

Write-Host "Starting Vecinita FastAPI server..." -ForegroundColor Cyan
Write-Host "API will be available at http://localhost:$Port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

python -m uvicorn src.main:app --reload --host $HostAddr --port $Port

if ($LASTEXITCODE -ne 0) {
    Write-Host "Server exited with code: $LASTEXITCODE" -ForegroundColor Red
}
