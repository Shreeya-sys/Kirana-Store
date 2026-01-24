# Flutter Dependencies Verification Script
# Run this script to check and install Flutter dependencies

Write-Host "=== Flutter Dependencies Verification ===" -ForegroundColor Cyan

# Check if Flutter is installed
Write-Host "`n1. Checking Flutter installation..." -ForegroundColor Yellow
$flutterVersion = flutter --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Flutter is installed" -ForegroundColor Green
    Write-Host $flutterVersion
} else {
    Write-Host "✗ Flutter is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Flutter from: https://flutter.dev/docs/get-started/install/windows" -ForegroundColor Yellow
    exit 1
}

# Check if pubspec.yaml exists
Write-Host "`n2. Checking project structure..." -ForegroundColor Yellow
if (Test-Path "pubspec.yaml") {
    Write-Host "✓ pubspec.yaml found" -ForegroundColor Green
} else {
    Write-Host "✗ pubspec.yaml not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n3. Installing Flutter dependencies..." -ForegroundColor Yellow
flutter pub get

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    
    # Check if pubspec.lock was created
    if (Test-Path "pubspec.lock") {
        Write-Host "✓ pubspec.lock created" -ForegroundColor Green
    }
    
    # List installed packages
    Write-Host "`n4. Installed packages:" -ForegroundColor Yellow
    Get-Content pubspec.lock | Select-String -Pattern "^\s+name:|^\s+version:" | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "You can now run: flutter run" -ForegroundColor Green
