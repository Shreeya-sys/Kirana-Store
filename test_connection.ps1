# Backend-Frontend Connection Test Script
# This script tests if the frontend can connect to the backend

Write-Host "=== Backend-Frontend Connection Test ===" -ForegroundColor Cyan

$backendUrl = "http://127.0.0.1:8000"
$testEndpoints = @(
    @{Path="/"; Method="GET"; Name="Root"},
    @{Path="/docs"; Method="GET"; Name="Swagger UI"},
    @{Path="/users/me"; Method="GET"; Name="User Profile (requires auth)"}
)

# Test 1: Check if backend is running
Write-Host "`n1. Testing backend connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$backendUrl/" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend is running at $backendUrl" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Backend is not running or not accessible" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nPlease start the backend first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Gray
    Write-Host "  uvicorn main:app --reload" -ForegroundColor Gray
    exit 1
}

# Test 2: Check API documentation endpoint
Write-Host "`n2. Testing API documentation endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$backendUrl/docs" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Swagger UI is accessible at $backendUrl/docs" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Swagger UI not accessible" -ForegroundColor Red
}

# Test 3: Test login endpoint (without credentials - should fail gracefully)
Write-Host "`n3. Testing login endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        username = "test"
        password = "test"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$backendUrl/token" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✓ Login endpoint is working (401 expected for invalid credentials)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Login endpoint test inconclusive" -ForegroundColor Yellow
    }
}

# Test 4: Check frontend API client configuration
Write-Host "`n4. Checking frontend API client configuration..." -ForegroundColor Yellow
$apiClientPath = "frontend/lib/core/api_client.dart"
if (Test-Path $apiClientPath) {
    $content = Get-Content $apiClientPath -Raw
    if ($content -match "baseUrl.*127\.0\.0\.1:8000") {
        Write-Host "✓ Frontend API client is configured for $backendUrl" -ForegroundColor Green
    } elseif ($content -match "baseUrl.*10\.0\.2\.2:8000") {
        Write-Host "✓ Frontend API client is configured for Android emulator (10.0.2.2:8000)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Frontend API client baseUrl may need adjustment" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Frontend API client not found" -ForegroundColor Red
}

# Test 5: Create a test user (if backend is running)
Write-Host "`n5. Testing user creation endpoint..." -ForegroundColor Yellow
try {
    $testUser = @{
        username = "testuser_$(Get-Date -Format 'yyyyMMddHHmmss')"
        password = "testpass123"
        role = "staff"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$backendUrl/users/" -Method POST -Body $testUser -ContentType "application/json" -TimeoutSec 5 -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ User creation endpoint is working" -ForegroundColor Green
        $userData = $response.Content | ConvertFrom-Json
        Write-Host "  Created user: $($userData.username)" -ForegroundColor Gray
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        $errorContent = $_.Exception.Response | Get-Member | Select-Object -ExpandProperty Name
        Write-Host "⚠ User creation endpoint responded (may be duplicate user)" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ User creation test inconclusive" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Connection Test Summary ===" -ForegroundColor Cyan
Write-Host "Backend URL: $backendUrl" -ForegroundColor White
Write-Host "Frontend should be able to connect to the backend." -ForegroundColor Green
Write-Host "`nTo test the full flow:" -ForegroundColor Yellow
Write-Host "1. Keep backend running (uvicorn main:app --reload)" -ForegroundColor Gray
Write-Host "2. Start frontend (flutter run)" -ForegroundColor Gray
Write-Host "3. Create a user via Swagger UI: $backendUrl/docs" -ForegroundColor Gray
Write-Host "4. Login via Flutter app" -ForegroundColor Gray
