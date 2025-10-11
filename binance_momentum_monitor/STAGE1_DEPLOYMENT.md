# Stage 1 Deployment Guide: EMA Trend Data Collection

**Date:** October 10, 2025  
**Goal:** Deploy EMA calculation with data collection only (no filtering)

---

## 📋 Pre-Deployment Checklist

- [ ] All code changes committed to version control
- [ ] Database backup completed
- [ ] SSH access to `app-greyjoy-01` server
- [ ] Docker network `azerothcore-wotlk_ac-network` accessible
- [ ] MySQL credentials available

---

## 🚀 Deployment Steps

### Step 1: Database Migration

Connect to MySQL and run the migration script:

```bash
# SSH into server
ssh user@app-greyjoy-01

# Connect to MySQL
docker exec -it ac-database mysql -u root -p

# Run migration
source /path/to/migrations/001_add_ema_columns.sql

# Verify columns were added
DESCRIBE momentum_signal_monitor.alerts;

# Check indexes
SHOW INDEXES FROM momentum_signal_monitor.alerts;
```

**Expected Output:**
```
+------------------+----------------+------+-----+---------+
| Field            | Type           | Null | Key | Default |
+------------------+----------------+------+-----+---------+
| ema_21_daily     | decimal(20,8)  | YES  | MUL | NULL    |
| ema_50_daily     | decimal(20,8)  | YES  |     | NULL    |
| price_vs_ema_21  | varchar(20)    | YES  | MUL | NULL    |
| ema_trend_bias   | varchar(20)    | YES  | MUL | neutral |
+------------------+----------------+------+-----+---------+
```

---

### Step 2: Rebuild Scanner Docker Image

```powershell
# From binance_momentum_monitor directory
cd C:\Home\Dempsey\Development\github\binance_trading_tools\binance_momentum_monitor

# Build new image with EMA code
docker build -t momentum-monitor:ema-stage1 .

# Tag for deployment
docker tag momentum-monitor:ema-stage1 momentum-monitor:latest
```

---

### Step 3: Stop Current Scanner

```bash
# On app-greyjoy-01
docker ps | grep momentum-monitor

# Stop the container
docker stop <container_name>

# Optional: Remove old container
docker rm <container_name>
```

---

### Step 4: Deploy Updated Scanner

```bash
# Pull new image (if using registry)
docker pull momentum-monitor:ema-stage1

# Or copy image from local machine
# On local machine:
docker save momentum-monitor:ema-stage1 | gzip > momentum-monitor-ema-stage1.tar.gz
scp momentum-monitor-ema-stage1.tar.gz user@app-greyjoy-01:/tmp/

# On server:
docker load < /tmp/momentum-monitor-ema-stage1.tar.gz

# Start container
docker-compose up -d
```

---

### Step 5: Verify Deployment

#### Check Container Health

```bash
# Check if container is running
docker ps | grep momentum-monitor

# Check logs
docker logs -f momentum-monitor --tail 100

# Look for EMA-related log entries
docker logs momentum-monitor 2>&1 | grep -i "ema"
```

#### Expected Log Entries:

```
DEBUG - daily_cache_miss - Fetching daily klines for BTCUSDT
DEBUG - daily_cache_stored - Cached 22 daily klines for BTCUSDT
DEBUG - ema_calculated - BTCUSDT: Price $43250.5000 vs 21 EMA $42100.3500 (bullish)
INFO - momentum_detected - Momentum signal for BTCUSDT ... ema_trend_bias: bullish
```

---

### Step 6: Verify Database Writes

```sql
-- Check if new signals have EMA data
SELECT 
    symbol,
    current_price,
    ema_21_daily,
    price_vs_ema_21,
    ema_trend_bias,
    created_at
FROM momentum_signal_monitor.alerts
WHERE ema_21_daily IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

**Expected Output:**
```
+----------+---------------+--------------+-----------------+----------------+---------------------+
| symbol   | current_price | ema_21_daily | price_vs_ema_21 | ema_trend_bias | created_at          |
+----------+---------------+--------------+-----------------+----------------+---------------------+
| BTCUSDT  |   43250.5000  |  42100.3500  | above           | bullish        | 2025-10-10 14:23:15 |
| ETHUSDT  |    2456.7800  |   2501.2300  | below           | bearish        | 2025-10-10 14:22:45 |
+----------+---------------+--------------+-----------------+----------------+---------------------+
```

---

### Step 7: Monitor Cache Performance

```bash
# Watch logs for cache hit/miss ratio
docker logs momentum-monitor 2>&1 | grep "daily_cache" | tail -50

# Expected: After first scan, mostly cache hits
# Cache hit example:
# DEBUG - daily_cache_hit - Using cached daily klines for BTCUSDT (cache_age_hours: 0.17)

# Cache miss (first time or after 23h expiry):
# DEBUG - daily_cache_miss - Fetching daily klines for BTCUSDT
```

---

## 📊 Stage 1 Success Criteria

✅ **Database:**
- [ ] New columns exist in `alerts` table
- [ ] Indexes created on EMA fields
- [ ] No schema errors in logs

✅ **Application:**
- [ ] Scanner starts without errors
- [ ] EMA calculations appear in logs
- [ ] Daily kline cache working (95%+ hit rate after first scan)
- [ ] No increase in API errors or rate limiting

✅ **Data Collection:**
- [ ] New signals have `ema_21_daily` populated
- [ ] `ema_trend_bias` is either 'bullish' or 'bearish'
- [ ] `price_vs_ema_21` is either 'above' or 'below'
- [ ] No signals with NULL EMA data (unless API error)

✅ **Performance:**
- [ ] Scan time increase < 5 seconds per cycle
- [ ] API call count increased by ~0.7% (< 1 per symbol per day)
- [ ] No memory leaks or cache bloat
- [ ] Discord alerts still working

---

## 🐛 Troubleshooting

### Issue: No EMA data in database

**Check:**
```bash
# Look for EMA calculation errors
docker logs momentum-monitor 2>&1 | grep -i "ema.*error"

# Check if daily klines are being fetched
docker logs momentum-monitor 2>&1 | grep "daily_klines"
```

**Solution:**
- Verify Binance API is accessible
- Check rate limiting logs
- Ensure `get_cached_daily_klines()` method exists in `rest_client.py`

---

### Issue: High API usage or rate limiting

**Check:**
```bash
# Monitor API call frequency
docker logs momentum-monitor 2>&1 | grep "rate_limit_hit"

# Check cache hit rate
docker logs momentum-monitor 2>&1 | grep "daily_cache" | wc -l
```

**Solution:**
- Increase `cache_ttl_hours` if needed (currently 23h)
- Reduce scan frequency temporarily
- Monitor Binance API status

---

### Issue: EMA values seem incorrect

**Validation:**
```python
# Test EMA calculation manually
import pandas as pd

# Sample daily closes for BTCUSDT (replace with real data)
closes = [42000, 42500, 43000, 42800, 43200, ...]  # 22 values

df = pd.DataFrame({'close': closes})
ema_21 = df['close'].ewm(span=21, adjust=False).iloc[-1]

print(f"21 EMA: {ema_21}")  # Compare with database value
```

**Compare with TradingView:**
- Go to https://www.tradingview.com/chart/
- Select symbol (e.g., BTCUSDT)
- Add indicator: EMA (21) on Daily chart
- Compare value with database

---

## 📈 Next Steps (Future Stages)

**Stage 2: A/B Testing (Week 2-3)**
- Add configuration flag `require_ema_alignment`
- Send both filtered and unfiltered alerts
- Compare signal quality

**Stage 3: Full Deployment (Week 4)**
- Enable EMA filtering based on data
- Update API endpoints for EMA filtering
- Update OpenAPI wrapper for AI queries

---

## 🔄 Rollback Procedure

If issues occur, rollback to previous version:

```bash
# 1. Stop new container
docker stop momentum-monitor

# 2. Revert to old image
docker run -d --name momentum-monitor momentum-monitor:pre-ema

# 3. Optional: Remove EMA columns (data preserved)
# Only do this if you want to clean up completely
# ALTER TABLE alerts 
# DROP COLUMN ema_21_daily,
# DROP COLUMN ema_50_daily,
# DROP COLUMN price_vs_ema_21,
# DROP COLUMN ema_trend_bias;
```

---

## 📝 Post-Deployment Tasks

- [ ] Monitor logs for 24 hours
- [ ] Verify cache hit rate > 95% after first full cycle
- [ ] Check database growth rate
- [ ] Document any issues encountered
- [ ] Update API documentation if needed
- [ ] Plan Stage 2 A/B testing timeline

---

## 🎯 Performance Benchmarks

**Before EMA (Baseline):**
- Scan time: ~X seconds per cycle
- API calls: Y per hour
- Signals per day: Z

**After EMA Stage 1 (Target):**
- Scan time: < X + 5 seconds
- API calls: < Y × 1.01 (1% increase max)
- Signals per day: Z (unchanged, no filtering yet)
- Cache hit rate: > 95%

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Status:** ✅ Success / ⚠️ Issues / ❌ Rollback  
**Notes:** _____________________
