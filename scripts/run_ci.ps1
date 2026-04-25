#!/usr/bin/env pwsh
#Requires -Version 7

param(
    [switch]$Fix
)

$fail = $false

# ─── ruff format ───────────────────────────────
if ($Fix) {
    Write-Host "→ Formatting with ruff" -ForegroundColor Cyan
    ruff format pcap2kml_player tests
} else {
    Write-Host "→ Checking format with ruff" -ForegroundColor Cyan
    ruff format --check pcap2kml_player tests
    if ($LASTEXITCODE -ne 0) { $fail = $true }
}

# ─── ruff lint ─────────────────────────────────
Write-Host "→ Linting with ruff" -ForegroundColor Cyan
ruff check pcap2kml_player tests
if ($LASTEXITCODE -ne 0) { $fail = $true }

# ─── mypy ──────────────────────────────────────
Write-Host "→ Type checking with mypy" -ForegroundColor Cyan
mypy pcap2kml_player --ignore-missing-imports
if ($LASTEXITCODE -ne 0) { $fail = $true }

# ─── tests + coverage ──────────────────────────
Write-Host "→ Running tests with coverage" -ForegroundColor Cyan
pytest --cov=pcap2kml_player --cov-report=term-missing -q
if ($LASTEXITCODE -ne 0) { $fail = $true }

if ($fail) {
    Write-Host "`nCI checks FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`nAll CI checks PASSED" -ForegroundColor Green
    exit 0
}
