# Check the BRETTUSDT signal in the database
Write-Host "Checking BRETTUSDT signal (ID 41) in database..." -ForegroundColor Cyan

# Test 1: Get signal by ID directly
Write-Host "`n=== TEST 1: Get signal by ID ===" -ForegroundColor Yellow
try {
    $signal = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/41"
    Write-Host "✅ Found signal ID 41" -ForegroundColor Green
    Write-Host "  Symbol: $($signal.symbol)"
    Write-Host "  Timeframe: '$($signal.timeframe)'" -ForegroundColor Cyan
    Write-Host "  Momentum Score: $($signal.momentum_score)"
    Write-Host "  Price Change 4h: $($signal.price_change_4hour)"
    Write-Host "  Created: $($signal.created_at)"
    Write-Host "  Candle Timestamp: $($signal.candle_timestamp)"
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Search for BRETTUSDT without timeframe filter
Write-Host "`n`n=== TEST 2: Search for BRETTUSDT (no timeframe filter) ===" -ForegroundColor Yellow
try {
    $brett = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?symbol=BRETTUSDT&limit=10"
    Write-Host "✅ Found $($brett.items.Count) BRETTUSDT signals" -ForegroundColor Green
    foreach ($item in $brett.items) {
        Write-Host "  ID $($item.id): Timeframe='$($item.timeframe)' Score=$($item.momentum_score)"
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Search with timeframe=4h
Write-Host "`n`n=== TEST 3: Search with timeframe=4h ===" -ForegroundColor Yellow
try {
    $tf4h = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?timeframe=4h&limit=10"
    Write-Host "✅ Found $($tf4h.items.Count) signals with timeframe=4h" -ForegroundColor Green
    foreach ($item in $tf4h.items) {
        Write-Host "  ID $($item.id): Symbol=$($item.symbol) Timeframe='$($item.timeframe)'"
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Get all distinct timeframes in database
Write-Host "`n`n=== TEST 4: All timeframes in database ===" -ForegroundColor Yellow
try {
    $all = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?limit=100"
    $timeframes = $all.items | Group-Object timeframe | Sort-Object Count -Descending
    Write-Host "Timeframes found:"
    foreach ($tf in $timeframes) {
        Write-Host "  '$($tf.Name)': $($tf.Count) signals"
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n`nDone!" -ForegroundColor Green
