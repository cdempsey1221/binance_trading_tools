# Migration Guide: From momentum_scanner.py to Modular Structure

This guide explains how to migrate from the original `momentum_scanner.py` to the new modular architecture.

## Overview of Changes

### Phase 1 Completed ✅

The codebase has been refactored into a modular architecture with the following improvements:

1. **Configuration Management**: YAML-based configuration with environment variable support
2. **Structured Logging**: JSON-formatted logs for better observability
3. **Alert Deduplication**: SQLite-based persistence to prevent duplicates
4. **Modular Design**: Clear separation of concerns across modules
5. **Type Safety**: Dataclasses for all data structures
6. **Docker Support**: Production-ready containerization

## Module Mapping

### Original → New Structure

| Original Location | New Location | Notes |
|------------------|--------------|-------|
| `Config` class | `src/core/config.py` | Enhanced with YAML support |
| `MomentumSignal` | `src/core/types.py` | Extended with optional fields |
| `AlertManager` | `src/alerts/manager.py` | Added DB deduplication |
| `BinanceAPI` | `src/data/rest_client.py` | Added rate limiting |
| `SymbolFilter` | `src/core/universe.py` | Added caching |
| `MomentumDetector` | `src/signals/momentum.py` | Restructured |
| `DiscordNotifier` | `src/alerts/discord.py` | Added enrichment |
| `MomentumScanner` | `main.py` | Simplified orchestration |
| Logging | `src/monitoring/logger.py` | Structured JSON logging |
| N/A | `src/alerts/deduplication.py` | New SQLite persistence |

## Key Differences

### 1. Configuration

**Old:**
```python
config = Config.from_env()
```

**New:**
```python
from src.core.config import load_config

# From YAML file
config = load_config('config/default.yaml')

# Or from environment
config = load_config()  # Uses env vars if no file
```

### 2. Logging

**Old:**
```python
logger.info(f"Found {count} symbols")
```

**New:**
```python
from src.monitoring.logger import get_logger

logger = get_logger('component_name')
logger.info('symbols_found', f'Found {count} symbols', data={'count': count})
```

### 3. Alert Deduplication

**Old:**
```python
# In-memory only with cooldown
if self.can_alert(symbol):
    send_alert(signal)
```

**New:**
```python
# Database-backed with exact bar tracking
from src.alerts.deduplication import AlertDeduplicationDB

dedup_db = AlertDeduplicationDB()
if not dedup_db.alert_exists(symbol, timeframe, bar_close_time):
    send_alert(signal)
    dedup_db.store_alert(symbol, timeframe, bar_close_time, signature)
```

### 4. Component Initialization

**Old:**
```python
scanner = MomentumScanner(config)
```

**New:**
```python
# More explicit initialization with dependency injection
rest_client = BinanceRestClient(rate_limit=1200)
universe = SymbolUniverse(rest_client, min_volume=1000)
detector = MomentumDetector(rest_client, timeframe='15m', ...)
alert_manager = AlertManager(notifier, dedup_db, cooldown=30)

scanner = MomentumScanner(config)  # Scanner creates components internally
```

## Migration Steps

### Step 1: Update Configuration

Create `config/default.yaml`:

```yaml
universe:
  cache_ttl: 3600
  min_hourly_volume: 1000

signals:
  timeframe: "15m"
  lookback_periods: 8
  volume_zscore_threshold: 2.0
  price_change_threshold: 0.05

alerts:
  cooldown_minutes: 30
  discord_webhook_url: "${DISCORD_WEBHOOK_URL}"

monitoring:
  log_level: "INFO"
```

### Step 2: Set Environment Variables

```bash
export DISCORD_WEBHOOK_URL="your_webhook_url"
export TIMEFRAME="15m"
export LOG_LEVEL="INFO"
```

Or create a `.env` file (copy from `.env.example`).

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run Tests

```bash
pytest tests/ -v
```

### Step 5: Run the Scanner

```bash
# Using the start script
./start.sh

# Or directly
python main.py
```

## Backward Compatibility

The new system maintains functional compatibility with the original:

- ✅ Same Binance API endpoints
- ✅ Same momentum detection logic
- ✅ Same Discord alert format (with optional enhancements)
- ✅ Same environment variable names (extended)
- ✅ Same scan intervals and thresholds

## New Features Available

### 1. Database Deduplication

Alerts are now tracked in SQLite to prevent duplicates:

```python
from src.alerts.deduplication import AlertDeduplicationDB

db = AlertDeduplicationDB()
db.store_alert('BTCUSDT', '15m', 1234567890, 'signature')
db.alert_exists('BTCUSDT', '15m', 1234567890)  # True
db.cleanup_old(days=7)  # Remove old alerts
```

### 2. Structured Logging

JSON logs for better parsing:

```python
from src.monitoring.logger import get_logger

logger = get_logger('my_component')
logger.info('event_name', 'Human message', data={'key': 'value'})
```

### 3. Configuration Hot-Reload

Change config without restart (non-critical settings):

```python
config = load_config('config.yaml')
# Modify config.yaml
config = load_config('config.yaml')  # Reload
```

### 4. Rate Limiting

Automatic rate limiting for REST API:

```python
rest_client = BinanceRestClient(rate_limit=1200)
# Automatically enforces 1200 requests/minute
```

### 5. Symbol Universe Caching

Cached symbol lists to reduce API calls:

```python
universe = SymbolUniverse(rest_client, min_volume=1000, cache_ttl=3600)
symbols = universe.get_liquid_perpetuals()  # Uses cache if fresh
symbols = universe.get_liquid_perpetuals(force_refresh=True)  # Force update
```

## Docker Deployment

### Build and Run

```bash
cd docker
export DISCORD_WEBHOOK_URL="your_webhook_url"
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Stop

```bash
docker-compose down
```

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running from the project root:

```bash
cd /workspaces/binance_trading_tools/binance_momentum_monitor
python main.py
```

### Configuration Not Found

If config is not found, set `CONFIG_PATH`:

```bash
export CONFIG_PATH="/path/to/config.yaml"
python main.py
```

### Database Locked

If SQLite database is locked:

```bash
rm alerts.db  # Delete and restart (alerts will be recreated)
```

### Rate Limit Errors

If hitting rate limits, adjust in config:

```yaml
data:
  rest:
    rate_limit: 600  # Reduce from 1200
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_config.py -v
```

### Run with Coverage

```bash
pytest --cov=src tests/
```

## Next Phases

The modular structure is ready for Phase 2+ enhancements:

- **Phase 2**: WebSocket support (see `src/data/websocket_client.py`)
- **Phase 3**: ATR normalization and volume Z-scores (see `src/signals/normalizers.py`)
- **Phase 4**: Enhanced alerts (see `src/alerts/discord.py` enrichment methods)
- **Phase 5**: Metrics and monitoring (see `src/monitoring/metrics.py`)

## Support

For issues or questions:
1. Check the README.md
2. Review test files for usage examples
3. Open a GitHub issue

## Rollback

To rollback to the original:

```bash
cd /workspaces/binance_trading_tools
python momentum_scanner.py
```

The original file remains unchanged and functional.
