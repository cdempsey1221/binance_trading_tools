# Test OpenAPI specification from Open WebUI's perspective
# Run this from your Windows machine or adapt for Linux

Write-Host "Testing OpenAPI Wrapper Endpoints..." -ForegroundColor Cyan

# Test 1: Check if server is accessible
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Yellow
curl http://app-greyjoy-01:8001/healthz

# Test 2: Get OpenAPI spec
Write-Host "`n2. Fetching OpenAPI specification..." -ForegroundColor Yellow
$spec = curl http://app-greyjoy-01:8001/openapi.json | ConvertFrom-Json
Write-Host "Title: $($spec.info.title)"
Write-Host "Description: $($spec.info.description)"
Write-Host "Version: $($spec.info.version)"

# Test 3: List available endpoints
Write-Host "`n3. Available endpoints:" -ForegroundColor Yellow
$spec.paths.PSObject.Properties | ForEach-Object {
    $path = $_.Name
    $methods = $_.Value.PSObject.Properties.Name -join ", "
    Write-Host "  $path [$methods]"
}

# Test 4: Check if operations have proper metadata
Write-Host "`n4. Checking POST /search metadata:" -ForegroundColor Yellow
$searchOp = $spec.paths.'/search'.post
Write-Host "  Summary: $($searchOp.summary)"
Write-Host "  Description: $($searchOp.description)"
Write-Host "  operationId: $($searchOp.operationId)"

# Test 5: Test actual API call
Write-Host "`n5. Testing actual API call (POST /search)..." -ForegroundColor Yellow
$body = @{
    hours_ago = 1
    limit = 3
    sort_by = "momentum_desc"
} | ConvertTo-Json

curl -Method POST `
    -Uri "http://app-greyjoy-01:8001/search" `
    -ContentType "application/json" `
    -Body $body

Write-Host "`nDone!" -ForegroundColor Green
