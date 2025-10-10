# Test both FastAPI (8000) and OpenAPI Wrapper (8001) side-by-side
# This will help us identify if the wrapper is the problem

Write-Host "Comparing FastAPI vs OpenAPI Wrapper Responses..." -ForegroundColor Cyan

# Test 1: FastAPI Direct (port 8000) - GET /alerts/search
Write-Host "`n=== TEST 1: FastAPI Service (port 8000) ===" -ForegroundColor Yellow
Write-Host "GET /alerts/search?limit=5&sort=ts_desc"

try {
    $fastapi = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?limit=5&sort=ts_desc"
    Write-Host "✅ FastAPI Success!" -ForegroundColor Green
    Write-Host "  Total items: $($fastapi.items.Count)"
    Write-Host "  Has next: $($fastapi.has_next)"
    if ($fastapi.items.Count -gt 0) {
        Write-Host "`nFirst signal:"
        $first = $fastapi.items[0]
        Write-Host "  ID: $($first.id)"
        Write-Host "  Symbol: $($first.symbol)"
        Write-Host "  Timeframe: $($first.timeframe)"
        Write-Host "  Momentum Score: $($first.momentum_score)"
        Write-Host "  Created: $($first.created_at)"
    }
} catch {
    Write-Host "❌ FastAPI Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Details: $($_.ErrorDetails.Message)"
}

# Test 2: OpenAPI Wrapper (port 8001) - POST /search
Write-Host "`n`n=== TEST 2: OpenAPI Wrapper (port 8001) ===" -ForegroundColor Yellow
Write-Host "POST /search with hours_ago=24, limit=5"

$body = @{
    hours_ago = 24
    limit = 5
    sort_by = "timestamp_desc"
} | ConvertTo-Json

try {
    $wrapper = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✅ Wrapper Success!" -ForegroundColor Green
    Write-Host "  Count: $($wrapper.count)"
    Write-Host "  Timeframe hours: $($wrapper.timeframe_hours)"
    if ($wrapper.count -gt 0) {
        Write-Host "`nFirst signal:"
        $first = $wrapper.signals[0]
        Write-Host "  ID: $($first.id)"
        Write-Host "  Symbol: $($first.symbol)"
        Write-Host "  Timeframe: $($first.timeframe)"
        Write-Host "  Momentum Score: $($first.momentum_score)"
        Write-Host "  Created: $($first.created_at)"
    }
} catch {
    Write-Host "❌ Wrapper Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Details: $($_.ErrorDetails.Message)"
}

# Test 3: Compare 15m timeframe specifically (since you had 15m data earlier)
Write-Host "`n`n=== TEST 3: 15m Timeframe Comparison ===" -ForegroundColor Yellow

Write-Host "`nFastAPI (15m in last hour):"
try {
    $cutoff = [int]((Get-Date).AddHours(-1).ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds
    $fastapi15m = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?timeframe=15m&after_ts=$cutoff&limit=10"
    Write-Host "  Found: $($fastapi15m.items.Count) signals" -ForegroundColor Green
    if ($fastapi15m.items.Count -gt 0) {
        $fastapi15m.items | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - $($_.symbol) (Score: $($_.momentum_score))"
        }
    }
} catch {
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nWrapper (15m in last hour):"
$body15m = @{
    timeframe = "15m"
    hours_ago = 1
    limit = 10
    sort_by = "momentum_desc"
} | ConvertTo-Json

try {
    $wrapper15m = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body15m -ContentType "application/json"
    Write-Host "  Found: $($wrapper15m.count) signals" -ForegroundColor Green
    if ($wrapper15m.count -gt 0) {
        $wrapper15m.signals | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - $($_.symbol) (Score: $($_.momentum_score))"
        }
    }
} catch {
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check all timeframes in database
Write-Host "`n`n=== TEST 4: All Timeframes in Database ===" -ForegroundColor Yellow
try {
    $cutoff = [int]((Get-Date).AddHours(-24).ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds
    $all = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?after_ts=$cutoff&limit=100"
    
    Write-Host "Total signals in last 24h: $($all.items.Count)"
    
    $timeframes = $all.items | Group-Object timeframe | Sort-Object Count -Descending
    Write-Host "`nBreakdown by timeframe:"
    foreach ($tf in $timeframes) {
        Write-Host "  $($tf.Name): $($tf.Count) signals"
    }
    
    Write-Host "`nTop symbols:"
    $symbols = $all.items | Group-Object symbol | Sort-Object Count -Descending | Select-Object -First 10
    foreach ($sym in $symbols) {
        Write-Host "  $($sym.Name): $($sym.Count) signals"
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n`nDone!" -ForegroundColor Green
Write-Host "`nConclusion:" -ForegroundColor Cyan
Write-Host "- If FastAPI returns data but Wrapper doesn't → Wrapper has a bug"
Write-Host "- If both return no data → Database is empty or time filter is wrong"
Write-Host "- If FastAPI errors → Database/API connection issue"
