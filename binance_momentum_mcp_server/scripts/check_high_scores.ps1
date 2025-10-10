# Check what high-scoring signals exist in the database
Write-Host "Checking for high-scoring signals..." -ForegroundColor Cyan

# Test 1: Check all signals in last 4 hours
Write-Host "`n=== Signals in Last 4 Hours ===" -ForegroundColor Yellow
try {
    $fourHoursAgo = [int]((Get-Date).AddHours(-4).ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds
    $recent = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?after_ts=$fourHoursAgo&limit=100&sort=momentum_desc"
    
    Write-Host "Total signals in last 4 hours: $($recent.items.Count)"
    
    if ($recent.items.Count -gt 0) {
        Write-Host "`nTop 10 by momentum score:"
        $recent.items | Select-Object -First 10 | ForEach-Object {
            Write-Host "  Score $($_.momentum_score): $($_.symbol) (ID: $($_.id)) - Created: $($_.created_at)"
        }
        
        $highScores = $recent.items | Where-Object { $_.momentum_score -ge 8 }
        Write-Host "`nSignals with score >= 8: $($highScores.Count)"
        foreach ($sig in $highScores) {
            Write-Host "  - $($sig.symbol): Score $($sig.momentum_score) (ID: $($sig.id))"
        }
    } else {
        Write-Host "  No signals in last 4 hours!" -ForegroundColor Red
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Check all signals in last 24 hours
Write-Host "`n`n=== Signals in Last 24 Hours ===" -ForegroundColor Yellow
try {
    $twentyFourHoursAgo = [int]((Get-Date).AddHours(-24).ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds
    $day = Invoke-RestMethod -Uri "http://192.168.1.10:8000/alerts/search?after_ts=$twentyFourHoursAgo&limit=100&sort=momentum_desc"
    
    Write-Host "Total signals in last 24 hours: $($day.items.Count)"
    
    $scoreGroups = $day.items | Group-Object momentum_score | Sort-Object Name -Descending
    Write-Host "`nBreakdown by score:"
    foreach ($group in $scoreGroups) {
        Write-Host "  Score $($group.Name): $($group.Count) signals"
    }
    
    $highScores = $day.items | Where-Object { $_.momentum_score -ge 8 }
    Write-Host "`nSignals with score >= 8: $($highScores.Count)"
    foreach ($sig in $highScores) {
        Write-Host "  - $($sig.symbol): Score $($sig.momentum_score) (ID: $($sig.id)) - $($sig.created_at)"
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check what the wrapper returns
Write-Host "`n`n=== Test Wrapper with Same Query ===" -ForegroundColor Yellow
$body = @{
    min_momentum_score = 8
    hours_ago = 4
    limit = 20
} | ConvertTo-Json

try {
    $wrapper = Invoke-RestMethod -Uri "http://192.168.1.10:8001/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "Wrapper returned: $($wrapper.count) signals"
    
    if ($wrapper.count -gt 0) {
        foreach ($sig in $wrapper.signals) {
            Write-Host "  - $($sig.symbol): Score $($sig.momentum_score)"
        }
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Show timestamps to verify time calculations
Write-Host "`n`n=== Timestamp Verification ===" -ForegroundColor Yellow
$now = Get-Date
$fourHours = $now.AddHours(-4)
$twentyFour = $now.AddHours(-24)

Write-Host "Current time: $($now.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "4 hours ago: $($fourHours.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "24 hours ago: $($twentyFour.ToString('yyyy-MM-dd HH:mm:ss'))"

$fourHoursMs = [int](($fourHours.ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds)
$twentyFourMs = [int](($twentyFour.ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds)

Write-Host "`n4 hours ago (ms): $fourHoursMs"
Write-Host "24 hours ago (ms): $twentyFourMs"

Write-Host "`n`nDone!" -ForegroundColor Green
