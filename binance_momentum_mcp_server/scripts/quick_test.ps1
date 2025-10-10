# Quick test of the search endpoint
$body = @{
    timeframe = "4h"
    hours_ago = 24
    limit = 10
    sort_by = "momentum_desc"
} | ConvertTo-Json

Write-Host "Testing POST /search with 4h timeframe..."
Write-Host "Body: $body"

try {
    $response = Invoke-RestMethod -Uri "http://app-greyjoy-01:8001/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "`nSuccess! Found $($response.count) signals" -ForegroundColor Green
    $response.signals | Select-Object -First 3 | Format-Table symbol, timeframe, momentum_score, volume_spike_pct
} catch {
    Write-Host "`nError!" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    Write-Host "Message: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)"
    }
}
