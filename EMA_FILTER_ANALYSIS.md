# EMA Trend Filter Implementation Analysis

**Date:** October 10, 2025  
**Analyst:** GitHub Copilot  
**Context:** Evaluating 21 EMA Daily trend filtering for momentum signals

---

## 📊 EXECUTIVE SUMMARY

### Current State
- ✅ **Momentum Scanner:** Detects 15m volume spikes + price changes
- ✅ **Database:** Stores 30+ signal attributes (price, volume, momentum scores)
- ✅ **API System:** FastAPI + MCP + OpenAPI wrapper for AI queries
- ❌ **EMA Data:** **NOT currently calculated or stored**

### Trader's Feedback
> "The signals catch big moves, but often after they're done. Use 21 EMA on Daily chart:
> - Price > 21 EMA Daily → **Long bias** (bullish trend)
> - Price < 21 EMA Daily → **Short bias** (bearish trend)
> 
> This would increase signal quality and help catch trends earlier."

### Recommendation
**✅ IMPLEMENT** - High-value enhancement with moderate implementation effort.

---

## 🔍 DETAILED ANALYSIS

### What Data We Currently Have

#### 1. Database Schema (`momentum_signal_monitor.alerts` table)
```sql
CREATE TABLE alerts (
    -- Core identification
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(50) NOT NULL,
    candle_timestamp BIGINT NOT NULL,
    timeframe VARCHAR(20) NOT NULL,  -- Detection timeframe (15m)
    
    -- Volume metrics
    volume_spike_pct FLOAT,
    volume_building BOOLEAN,
    current_volume DOUBLE,
    avg_volume DOUBLE,
    volume_score FLOAT,
    volume_zscore FLOAT,
    volume_spike_threshold FLOAT,
    
    -- Price metrics (multiple timeframes)
    price_change_pct FLOAT,           -- Best of 3bars or current
    price_change_current_bar FLOAT,
    price_change_1hour FLOAT,         -- 1h price movement
    price_change_2hour FLOAT,         -- 2h price movement  
    price_change_4hour FLOAT,         -- 4h price movement
    current_price DECIMAL(20, 8),
    
    -- Momentum analysis
    momentum_score INT,
    momentum_stage VARCHAR(50),       -- early/developing/mature/none
    trends_aligned BOOLEAN,
    volume_price_sync BOOLEAN,
    volatility FLOAT,
    signal_strength FLOAT,
    atr_normalized_return FLOAT,
    
    -- Score breakdowns
    price_score FLOAT,
    trend_score FLOAT,
    quality_score FLOAT,
    volatility_score FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timeframe, candle_timestamp)
);
```

#### 2. What's MISSING for EMA Filter
- ❌ No `ema_21_daily` field
- ❌ No `ema_50_daily` field  
- ❌ No `price_vs_ema` field (price position relative to EMA)
- ❌ No daily timeframe data collection

### Current Detection Flow

```
1. Scan liquid perpetuals (min $1,000/hr volume)
2. Fetch 15m candlestick data (lookback: 8 periods)
3. Calculate volume spike vs average
4. Calculate price changes (current bar, 1h, 2h, 4h)
5. Calculate momentum score (0-10)
6. Store signal if score ≥ 6
7. Send Discord alert
```

**Key Issue:** Scanner only fetches **15m timeframe data** for detection.  
**No Daily timeframe data** is fetched or analyzed.

---

## 💡 IMPLEMENTATION OPTIONS

### Option 1: Add EMA to Scanner (RECOMMENDED)
**Pros:**
- ✅ Filters bad signals BEFORE storing in database
- ✅ Reduces noise in API/Discord alerts
- ✅ Most efficient (single calculation per scan)

**Cons:**
- ⚠️ Requires modifying core scanner logic
- ⚠️ Adds Daily API calls (rate limit consideration)

**Implementation Steps:**
1. Add EMA calculation function to `momentum.py`
2. Fetch 1D (Daily) klines for each symbol (limit=22 for 21 EMA + 1)
3. Calculate 21 EMA from daily closes
4. Store in `MomentumSignal` dataclass
5. Add filter logic: only alert if `price > ema_21` (or add parameter)
6. Update database schema with new fields
7. Update API models to expose EMA data

**Estimated Effort:** 4-6 hours

---

### Option 2: Add EMA to API Layer (Post-Processing)
**Pros:**
- ✅ No scanner changes
- ✅ Flexible filtering at query time

**Cons:**
- ❌ All signals still stored (database bloat)
- ❌ EMA calculated on every API call (inefficient)
- ❌ Discord alerts still include low-quality signals

**Implementation Steps:**
1. Add EMA calculation to FastAPI service
2. Fetch Daily klines on-demand per query
3. Filter results before returning

**Estimated Effort:** 2-3 hours  
**NOT RECOMMENDED** - Inefficient and doesn't solve Discord alert noise

---

### Option 3: Separate EMA Enrichment Service
**Pros:**
- ✅ Separation of concerns
- ✅ Can backfill existing signals

**Cons:**
- ❌ Increased complexity
- ❌ Eventual consistency issues
- ❌ More infrastructure to maintain

**Estimated Effort:** 8-10 hours  
**NOT RECOMMENDED** - Overengineered for the use case

---

## 📋 RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Database Schema Update

```sql
-- Add EMA fields to alerts table
ALTER TABLE alerts ADD COLUMN ema_21_daily DECIMAL(20, 8) NULL;
ALTER TABLE alerts ADD COLUMN ema_50_daily DECIMAL(20, 8) NULL;
ALTER TABLE alerts ADD COLUMN price_vs_ema_21 ENUM('above', 'below', 'unknown') NULL;
ALTER TABLE alerts ADD COLUMN ema_trend_bias ENUM('bullish', 'bearish', 'neutral') DEFAULT 'neutral';

-- Add index for EMA filtering
CREATE INDEX idx_alerts_ema_bias ON alerts(ema_trend_bias);
```

### Phase 2: Scanner Enhancement

**File:** `binance_momentum_monitor/src/signals/momentum.py`

1. Add EMA calculation method:
```python
def _calculate_ema(self, df: pd.DataFrame, period: int) -> float:
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).iloc[-1]
```

2. Add Daily data fetching:
```python
def _fetch_daily_data(self, symbol: str) -> Optional[pd.DataFrame]:
    """Fetch daily klines for EMA calculation"""
    klines = self.rest_client.get_klines(symbol, '1d', limit=50)
    # Parse and return DataFrame
```

3. Add EMA trend analysis:
```python
def _analyze_ema_trend(self, symbol: str, current_price: float) -> dict:
    """
    Analyze EMA trend bias
    Returns: {
        'ema_21': float,
        'ema_50': float,
        'price_vs_ema_21': str,  # 'above' or 'below'
        'trend_bias': str  # 'bullish' or 'bearish'
    }
    """
    df_daily = self._fetch_daily_data(symbol)
    if df_daily is None:
        return None
    
    ema_21 = df_daily['close'].ewm(span=21, adjust=False).iloc[-1]
    ema_50 = df_daily['close'].ewm(span=50, adjust=False).iloc[-1]
    
    price_vs_ema = 'above' if current_price > ema_21 else 'below'
    trend_bias = 'bullish' if current_price > ema_21 else 'bearish'
    
    return {
        'ema_21': ema_21,
        'ema_50': ema_50,
        'price_vs_ema_21': price_vs_ema,
        'trend_bias': trend_bias
    }
```

4. Integrate into `analyze_symbol()`:
```python
# After existing analysis
ema_analysis = self._analyze_ema_trend(symbol, current_price)

# Optional: Filter by trend (configurable)
if self.config.require_ema_alignment:
    if ema_analysis['trend_bias'] != 'bullish':
        logger.debug(f'Filtered {symbol} - price below 21 EMA')
        return None
```

### Phase 3: Data Model Updates

**File:** `binance_momentum_monitor/src/core/types.py`

```python
@dataclass
class MomentumSignal:
    # ...existing fields...
    
    # EMA trend fields (optional, add at end)
    ema_21_daily: Optional[float] = None
    ema_50_daily: Optional[float] = None
    price_vs_ema_21: Optional[str] = None  # 'above' or 'below'
    ema_trend_bias: str = 'neutral'  # 'bullish' or 'bearish'
```

### Phase 4: Configuration

**File:** `binance_momentum_monitor/config/default.yaml`

```yaml
signals:
  # ...existing config...
  
  # EMA trend filtering
  enable_ema_filter: true          # Enable EMA trend filter
  require_ema_alignment: false     # If true, only alert when price > 21 EMA
  ema_periods: [21, 50]            # EMA periods to calculate
```

### Phase 5: API Updates

**Files:** 
- `binance_momentum_signal_api/models/model.py`
- `binance_momentum_signal_api/service/api.py`

1. Add fields to Pydantic model
2. Add EMA filter parameters to `/alerts/search`:
   - `ema_trend_bias`: Filter by 'bullish' or 'bearish'
   - `min_price_above_ema_pct`: e.g., 5% above 21 EMA

### Phase 6: OpenAPI Wrapper Updates

**File:** `binance_momentum_mcp_server/openapi_wrapper.py`

Add EMA filtering to search requests:
```python
class SearchSignalsRequest(BaseModel):
    # ...existing fields...
    ema_trend_bias: Optional[str] = Field(
        None, 
        description="Filter by EMA trend: 'bullish' (price > 21 EMA) or 'bearish'"
    )
```

---

## 📈 EXPECTED BENEFITS

### 1. Signal Quality Improvement
- **Before:** Catch big moves after they've moved 10-20%
- **After:** Catch trends earlier with confirmation

### 2. Risk Management
- **Trading with the trend** = Higher win rate
- **Price > 21 EMA** = "Tailwind" helping the trade

### 3. Reduced Noise
- **Estimate:** 30-50% fewer signals
- **Quality:** Higher probability setups

### 4. AI Query Enhancement
Users can ask:
- "Show bullish signals with price above 21 EMA"
- "Find signals in strong uptrends"
- "What coins are trending above their 21 EMA?"

---

## ⚠️ CONSIDERATIONS

### 1. Rate Limiting
- **Current:** ~1 API call per symbol per scan (15m data)
- **After EMA:** ~2 API calls per symbol per scan (15m + 1D data)
- **Impact:** 2x API usage
- **Mitigation:** Cache Daily EMA values (update every 24 hours)

### 2. Historical Signals
- Existing database records won't have EMA data
- Options:
  - **Backfill:** Calculate EMA for all existing signals (time-consuming)
  - **Null handling:** Treat NULL EMA as "neutral" bias
  - **Forward only:** Only new signals have EMA data

### 3. Configuration Flexibility
Should EMA filter be:
- **Hard requirement:** Only alert when price > 21 EMA (reduces signals)
- **Soft indicator:** Store EMA but alert all signals (maintain volume)
- **Configurable:** Let user decide via config flag

**Recommendation:** Start with **soft indicator** (store but don't filter), then add filtering after testing.

---

## 🎯 SUCCESS METRICS

After implementing, track:

1. **Signal Count:** How many signals before/after EMA filter?
2. **Win Rate:** Do EMA-filtered signals perform better?
3. **Timing:** Do we catch trends earlier vs mid-move?
4. **API Performance:** Impact on response times?

---

## 🚀 ROLLOUT STRATEGY

### Stage 1: Soft Launch (Week 1)
- Add EMA calculation and storage
- **Do NOT filter** signals yet
- Collect data for analysis

### Stage 2: A/B Testing (Week 2-3)
- Send both filtered and unfiltered alerts
- Compare performance
- Gather trader feedback

### Stage 3: Full Deployment (Week 4)
- Enable EMA filter based on data
- Update documentation
- Train AI on new parameters

---

## 🔧 IMPLEMENTATION CHECKLIST

### Scanner Changes
- [ ] Add `_calculate_ema()` method
- [ ] Add `_fetch_daily_data()` method  
- [ ] Add `_analyze_ema_trend()` method
- [ ] Integrate into `analyze_symbol()`
- [ ] Add configuration options
- [ ] Add unit tests for EMA calculations

### Database Changes
- [ ] Create migration script (ALTER TABLE)
- [ ] Add new columns (ema_21_daily, ema_50_daily, etc.)
- [ ] Add indexes for filtering
- [ ] Test migration on dev database

### Data Model Changes
- [ ] Update `MomentumSignal` dataclass
- [ ] Update `MomentumSignalModel` Pydantic model
- [ ] Update database insertion logic

### API Changes
- [ ] Add EMA fields to response models
- [ ] Add EMA filter parameters to search endpoint
- [ ] Update API documentation
- [ ] Test with sample queries

### OpenAPI Wrapper Changes
- [ ] Add EMA parameters to search request
- [ ] Update OpenAPI schema descriptions
- [ ] Test AI function calling with EMA filters

### Documentation
- [ ] Update README with EMA feature
- [ ] Add EMA configuration guide
- [ ] Create example queries with EMA filters
- [ ] Update Open WebUI setup docs

### Testing
- [ ] Unit tests for EMA calculations
- [ ] Integration tests for filtered queries
- [ ] Load testing for API performance
- [ ] Validate EMA accuracy vs TradingView

---

## 💭 FINAL THOUGHTS

### Why This Matters
The trader's feedback is **spot-on**. Momentum without trend context is like driving fast without knowing the direction. The 21 EMA on Daily provides that directional bias.

### Quick Win Potential
This is a **high-ROI enhancement**:
- Moderate implementation effort (4-6 hours)
- Significant quality improvement
- Uses well-established technical indicator (21 EMA is industry standard)
- No breaking changes to existing system

### Next Steps
1. **Get approval** to proceed with implementation
2. **Prioritize:** Scanner changes → Database → API → Wrapper
3. **Test thoroughly** with historical data
4. **Monitor results** and adjust thresholds

---

## 📚 REFERENCES

- **21 EMA Strategy:** https://www.investopedia.com/articles/trading/08/exponential-moving-average.asp
- **Pandas EMA:** `df['close'].ewm(span=21, adjust=False).mean()`
- **TradingView EMA:** Default formula uses exponential weighting
- **Binance Kline API:** `/fapi/v1/klines?interval=1d&limit=50`

---

**Status:** ✅ Ready for implementation  
**Priority:** High  
**Effort:** 4-6 hours  
**Risk:** Low
