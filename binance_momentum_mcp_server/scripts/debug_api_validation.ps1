# Debug: Test the OpenAPI wrapper directly
# This will help us see what the AI is actually sending

Write-Host "Testing OpenAPI Wrapper Parameter Validation..." -ForegroundColor Cyan

# Test 1: Valid request with all defaults
Write-Host "`n1. Test with minimal parameters (should work):" -ForegroundColor Yellow
$body1 = @{
    hours_ago = 1
    limit = 5
} | ConvertTo-Json

Write-Host "Request body: $body1"
try {
    $response1 = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body1 -ContentType "application/json"
    Write-Host "✅ Success! Got $($response1.count) signals" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)"
}

# Test 2: Request with timeframe filter
Write-Host "`n2. Test with timeframe filter:" -ForegroundColor Yellow
$body2 = @{
    timeframe = "4h"
    hours_ago = 24
    limit = 10
    sort_by = "momentum_desc"
} | ConvertTo-Json

Write-Host "Request body: $body2"
try {
    $response2 = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body2 -ContentType "application/json"
    Write-Host "✅ Success! Got $($response2.count) signals" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)"
}

# Test 3: Request with invalid limit (should fail with 422)
Write-Host "`n3. Test with invalid limit (should fail):" -ForegroundColor Yellow
$body3 = @{
    limit = "five"  # String instead of int
    hours_ago = 1
} | ConvertTo-Json

Write-Host "Request body: $body3"
try {
    $response3 = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body3 -ContentType "application/json"
    Write-Host "✅ Success! Got $($response3.count) signals" -ForegroundColor Green
} catch {
    Write-Host "❌ Expected error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Response: $($_.ErrorDetails.Message)"
}

# Test 4: Request with limit = 0 (should fail)
Write-Host "`n4. Test with limit = 0 (should fail):" -ForegroundColor Yellow
$body4 = @{
    limit = 0
    hours_ago = 1
} | ConvertTo-Json

Write-Host "Request body: $body4"
try {
    $response4 = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body4 -ContentType "application/json"
    Write-Host "✅ Success! Got $($response4.count) signals" -ForegroundColor Green
} catch {
    Write-Host "❌ Expected error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Response: $($_.ErrorDetails.Message)"
}

# Test 5: Check OpenAPI schema for /search
Write-Host "`n5. Checking OpenAPI schema for /search:" -ForegroundColor Yellow
$spec = Invoke-RestMethod -Uri "http://192.168.1.10:8001/openapi.json"
$searchSchema = $spec.paths.'/search'.post.requestBody.content.'application/json'.schema
Write-Host "Schema type: $($searchSchema.type)"
Write-Host "Required fields: $($searchSchema.required -join ', ')"
Write-Host "`nProperties:"
$searchSchema.properties.PSObject.Properties | ForEach-Object {
    $name = $_.Name
    $prop = $_.Value
    Write-Host "  - $name ($($prop.type)): $($prop.description)"
    if ($prop.minimum) { Write-Host "    Min: $($prop.minimum), Max: $($prop.maximum)" }
    if ($prop.default) { Write-Host "    Default: $($prop.default)" }
}

Write-Host "`nDone!" -ForegroundColor Green
