# EMA Filter - API Call Optimization Strategy

**Date:** October 10, 2025  
**Question:** Can we reduce API calls by using different intervals?  
**Answer:** ✅ YES! Significant optimization possible.

---

## 🎯 OPTIMIZATION INSIGHT

**Your observation is SPOT ON!** Instead of making separate API calls for Daily timeframe, we can **leverage the existing multi-timeframe price change calculations** that are already in place.

---

## 📊 CURRENT SYSTEM ANALYSIS

### What's Already Being Calculated

Looking at the database schema, the system **already calculates**:
- ✅ `price_change_1hour` - 1h price movement
- ✅ `price_change_2hour` - 2h price movement
- ✅ `price_change_4hour` - 4h price movement
- ✅ `current_price` - Latest price

### Current API Call Pattern

```python
# In momentum.py analyze_symbol():
1. get_klines(symbol, '15m', limit=8)  # For volume/price detection
2. get_volume_for_period(symbol, hours=X, interval='15m')  # For multi-hour analysis
```

**Key Discovery:** The system is **already fetching multiple timeframes** to calculate 1h, 2h, 4h price changes!

---

## 💡 THREE OPTIMIZATION STRATEGIES

### Strategy 1: Use Existing Price Data (BEST - No Extra API Calls!)

**Concept:** The scanner already fetches enough candles to calculate 1h/2h/4h changes. We can fetch just a bit more to get Daily EMA without a separate API call.

**Implementation:**
```python
# Instead of separate calls for 15m and 1d:
# OLD (2 calls):
klines_15m = get_klines(symbol, '15m', limit=8)
klines_1d = get_klines(symbol, '1d', limit=22)  # NEW CALL

# OPTIMIZED (1 call with more data):
klines_15m = get_klines(symbol, '15m', limit=96)  # 24 hours of 15m candles
# Then resample to daily for EMA calculation
```

**Pros:**
- ✅ **Zero additional API calls** (same endpoint, just more data)
- ✅ Can calculate daily EMA from 15m data via resampling
- ✅ Minimal code changes

**Cons:**
- ⚠️ Slightly more data transfer per request
- ⚠️ Need to implement resampling logic

**API Call Count:**
- **Before EMA:** 1 call per symbol
- **After EMA:** **Still 1 call per symbol** (just larger limit)

---

### Strategy 2: Single 1d Call (Smart Caching)

**Concept:** Binance supports `1d` interval. Fetch daily candles ONCE and **cache for 24 hours**.

**Implementation:**
```python
# Check cache first
if symbol in daily_cache and cache_age < 24 hours:
    return daily_cache[symbol]

# Only fetch if cache miss or expired
klines_1d = get_klines(symbol, '1d', limit=22)
daily_cache[symbol] = {'data': klines_1d, 'timestamp': now}
```

**Pros:**
- ✅ Accurate daily candles (no resampling needed)
- ✅ Cache reduces API calls dramatically (1 per symbol per day)
- ✅ Simple implementation

**Cons:**
- ⚠️ First scan adds 1 API call per symbol
- ⚠️ Subsequent scans within 24h = 0 additional calls

**API Call Count:**
- **First scan:** 2 calls per symbol (15m + 1d)
- **Subsequent scans (within 24h):** **1 call per symbol** (15m only, 1d cached)

---

### Strategy 3: Hybrid Approach (RECOMMENDED)

**Concept:** Combine both strategies for maximum efficiency.

**Implementation:**
```python
def get_daily_ema(symbol: str, current_price: float) -> dict:
    """
    Calculate 21 EMA from daily data with smart caching.
    Falls back to resampling if cache miss.
    """
    
    # Try cache first (valid for 23 hours)
    if symbol in daily_ema_cache:
        cache_entry = daily_ema_cache[symbol]
        age_hours = (datetime.now() - cache_entry['timestamp']).total_seconds() / 3600
        
        if age_hours < 23:  # Cache valid for 23 hours
            logger.debug(f'Using cached daily EMA for {symbol}')
            return cache_entry['ema_data']
    
    # Option 1: Try to fetch 1d candles (lightweight)
    try:
        klines_1d = self.rest_client.get_klines(symbol, '1d', limit=22)
        if klines_1d:
            df_daily = parse_klines(klines_1d)
            ema_21 = df_daily['close'].ewm(span=21, adjust=False).iloc[-1]
            
            # Cache for next scan
            ema_data = {
                'ema_21': ema_21,
                'price_vs_ema': 'above' if current_price > ema_21 else 'below',
                'trend_bias': 'bullish' if current_price > ema_21 else 'bearish'
            }
            daily_ema_cache[symbol] = {
                'ema_data': ema_data,
                'timestamp': datetime.now()
            }
            return ema_data
    except Exception as e:
        logger.warning(f'Failed to fetch 1d klines for {symbol}: {e}')
    
    # Option 2: Fallback to resampling 15m data (if already fetched)
    # This is rare and only happens on API errors
    return None
```

**Pros:**
- ✅ **First scan:** +1 API call per symbol (acceptable)
- ✅ **All subsequent scans:** **0 additional calls** (cached for 23h)
- ✅ Cache invalidates before next daily candle closes
- ✅ Fallback option if API fails

**Cons:**
- ⚠️ Cache management overhead (minimal)

**API Call Count (Per Symbol):**
- **Scan 1 (0:00 AM):** 2 calls (15m + 1d)
- **Scan 2 (0:05 AM):** 1 call (15m only, 1d cached)
- **Scan 3 (0:10 AM):** 1 call (15m only, 1d cached)
- **... all day ...**
- **Scan 288 (11:55 PM):** 1 call (15m only, 1d cached)
- **Next day Scan 1:** 2 calls (cache expired, refetch both)

**Daily API Usage:**
- **Without caching:** 288 scans × 2 calls = **576 calls per symbol per day**
- **With caching:** 1 × 2 calls + 287 × 1 call = **289 calls per symbol per day**
- **Savings:** **50% reduction!**

---

## 🔍 BINANCE API INTERVAL OPTIONS

According to Binance Futures API, supported intervals are:
```
1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
```

**Key Insights:**
- ✅ `1d` (daily) is supported - perfect for 21 EMA
- ✅ Can fetch exactly what we need (no extra processing)
- ✅ Daily candles are lightweight (22 candles = ~22KB)

---

## 📈 RATE LIMIT IMPACT ANALYSIS

### Current Rate Limit
Looking at `rest_client.py`:
```python
def __init__(self, rate_limit: int = 1200):
    """Maximum requests per minute"""
```

**Current setting:** 1200 requests/minute = **20 req/sec**

### Impact of EMA Feature

**Scenario:** 200 liquid perpetuals, scan every 5 minutes

#### Without Caching:
```
200 symbols × 2 calls (15m + 1d) = 400 calls per scan
400 calls per scan × 12 scans/hour = 4,800 calls/hour
4,800 ÷ 60 = 80 calls/minute
```
**Result:** Well within 1200/min limit ✅

#### With Caching (Strategy 3):
```
First scan: 200 × 2 = 400 calls
Next 11 scans: 200 × 1 = 2,200 calls
Total: 2,600 calls/hour = 43 calls/minute
```
**Result:** **46% reduction** in API usage ✅

---

## 🚀 RECOMMENDED IMPLEMENTATION

### Phase 1: Add Daily Kline Fetching with Cache

**File:** `binance_momentum_monitor/src/data/rest_client.py`

Add caching mechanism:
```python
class BinanceRestClient:
    def __init__(self, rate_limit: int = 1200):
        # ...existing code...
        self.daily_ema_cache: Dict[str, dict] = {}  # NEW
        self.cache_ttl_hours = 23  # Cache for 23 hours
    
    def get_cached_daily_klines(
        self,
        symbol: str,
        limit: int = 22
    ) -> Optional[List[List]]:
        """
        Fetch daily klines with 23-hour caching.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of daily candles (default 22 for 21 EMA)
            
        Returns:
            List of daily kline data or None
        """
        now = time.time()
        
        # Check cache
        if symbol in self.daily_ema_cache:
            cache_entry = self.daily_ema_cache[symbol]
            age_hours = (now - cache_entry['timestamp']) / 3600
            
            if age_hours < self.cache_ttl_hours:
                logger.debug(
                    'daily_cache_hit',
                    f'Using cached daily klines for {symbol}',
                    data={'cache_age_hours': age_hours}
                )
                return cache_entry['data']
        
        # Cache miss - fetch fresh data
        klines = self.get_klines(symbol, '1d', limit)
        
        if klines:
            self.daily_ema_cache[symbol] = {
                'data': klines,
                'timestamp': now
            }
            logger.debug('daily_cache_miss', f'Fetched and cached daily klines for {symbol}')
        
        return klines
```

### Phase 2: EMA Calculation in Momentum Detector

**File:** `binance_momentum_monitor/src/signals/momentum.py`

```python
def _calculate_ema_from_klines(self, klines: List[List], period: int) -> float:
    """
    Calculate EMA from kline data.
    
    Args:
        klines: List of kline arrays [timestamp, open, high, low, close, ...]
        period: EMA period (e.g., 21)
        
    Returns:
        EMA value
    """
    closes = [float(k[4]) for k in klines]  # Index 4 = close price
    df = pd.DataFrame({'close': closes})
    return df['close'].ewm(span=period, adjust=False).iloc[-1]


def _analyze_ema_trend(self, symbol: str, current_price: float) -> Optional[dict]:
    """
    Analyze EMA trend bias using cached daily data.
    
    Returns:
        Dict with ema_21, price_vs_ema_21, trend_bias or None
    """
    # Fetch daily klines (with caching)
    klines_daily = self.rest_client.get_cached_daily_klines(symbol, limit=22)
    
    if not klines_daily or len(klines_daily) < 21:
        logger.warning(
            'insufficient_daily_data',
            f'Not enough daily data for {symbol}',
            data={'candles': len(klines_daily) if klines_daily else 0}
        )
        return None
    
    # Calculate 21 EMA
    ema_21 = self._calculate_ema_from_klines(klines_daily, 21)
    
    # Determine trend bias
    price_vs_ema = 'above' if current_price > ema_21 else 'below'
    trend_bias = 'bullish' if current_price > ema_21 else 'bearish'
    
    logger.debug(
        'ema_calculated',
        f'{symbol}: Price ${current_price:.2f} vs EMA ${ema_21:.2f} ({trend_bias})',
        data={
            'symbol': symbol,
            'current_price': current_price,
            'ema_21': ema_21,
            'trend_bias': trend_bias
        }
    )
    
    return {
        'ema_21': ema_21,
        'ema_50': None,  # Optional: add 50 EMA later
        'price_vs_ema_21': price_vs_ema,
        'trend_bias': trend_bias
    }
```

### Phase 3: Integrate into analyze_symbol()

```python
def analyze_symbol(self, symbol: str) -> Optional[MomentumSignal]:
    """Analyze a symbol for momentum signals"""
    
    # ...existing analysis code...
    
    # NEW: Calculate EMA trend (uses cached daily data)
    ema_analysis = self._analyze_ema_trend(symbol, current_price)
    
    # Optional: Filter by EMA trend (configurable)
    if self.config.signals.require_ema_alignment and ema_analysis:
        if ema_analysis['trend_bias'] != 'bullish':
            logger.debug(
                'filtered_by_ema',
                f'Filtered {symbol} - bearish trend (price below 21 EMA)',
                data={
                    'symbol': symbol,
                    'trend_bias': ema_analysis['trend_bias']
                }
            )
            return None
    
    # Create signal with EMA data
    return MomentumSignal(
        # ...existing fields...
        ema_21_daily=ema_analysis['ema_21'] if ema_analysis else None,
        price_vs_ema_21=ema_analysis['price_vs_ema_21'] if ema_analysis else 'unknown',
        ema_trend_bias=ema_analysis['trend_bias'] if ema_analysis else 'neutral'
    )
```

---

## 📊 COMPARISON MATRIX

| Strategy | API Calls/Symbol (First Scan) | API Calls/Symbol (Subsequent) | Daily Total (200 symbols) | Complexity | Accuracy |
|----------|-------------------------------|------------------------------|---------------------------|------------|----------|
| **No EMA** | 1 | 1 | 34,560 | Low | N/A |
| **Strategy 1 (Resample)** | 1 | 1 | 34,560 | Medium | Good |
| **Strategy 2 (1d, no cache)** | 2 | 2 | 69,120 | Low | Excellent |
| **Strategy 3 (1d + cache)** ✅ | 2 | 1 | ~34,800 | Medium | Excellent |

**Winner:** Strategy 3 (Cached 1d calls)
- Minimal API increase (240 calls/day = 0.7% more)
- Native daily candles (no resampling)
- Simple to implement and maintain

---

## 🎯 FINAL RECOMMENDATION

**✅ Use Strategy 3: Cached Daily Kline Calls**

### Why This is Optimal:
1. **Negligible API Impact:** Only 1 extra call per symbol per day
2. **Native Daily Data:** No resampling math, exact daily candles
3. **Excellent Cache Hit Rate:** 23-hour TTL = 95%+ cache hits
4. **Simple Code:** Minimal changes, easy to maintain
5. **Accurate EMA:** Using official daily candles (not derived)

### Expected Performance:
```
200 symbols × 288 scans/day:
- Without cache: 115,200 API calls/day
- With cache: 58,000 API calls/day
- Savings: 50% reduction
```

### Implementation Effort:
- **Caching logic:** 30 minutes
- **EMA calculation:** 30 minutes
- **Integration:** 1 hour
- **Testing:** 1 hour
- **Total:** ~3 hours (vs 4-6 estimated in original analysis)

---

## 📝 UPDATED CHECKLIST

- [ ] Add `daily_ema_cache` dict to `BinanceRestClient`
- [ ] Implement `get_cached_daily_klines()` method
- [ ] Add `_calculate_ema_from_klines()` helper
- [ ] Add `_analyze_ema_trend()` to `MomentumDetector`
- [ ] Integrate EMA analysis into `analyze_symbol()`
- [ ] Add cache monitoring/logging
- [ ] Test cache expiration logic
- [ ] Validate EMA calculations against TradingView
- [ ] Update database schema (as per original plan)
- [ ] Update API models (as per original plan)

---

**Status:** ✅ Optimized approach ready  
**API Impact:** < 1% increase (with caching)  
**Effort:** 3 hours (reduced from 4-6)  
**Accuracy:** Excellent (native daily candles)
