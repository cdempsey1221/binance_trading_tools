# Quick Reference Guide

## Quick Start

```bash
# 1. Set environment variable
export DISCORD_WEBHOOK_URL="your_webhook_url"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
pytest tests/ -v

# 4. Start scanner
python main.py
```

## Environment Variables

```bash
# Required
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Optional (with defaults)
TIMEFRAME="15m"
LOOKBACK_PERIODS=8
MIN_HOURLY_VOLUME=1000
ALERT_COOLDOWN=30
LOG_LEVEL="INFO"
CONFIG_PATH="/path/to/config.yaml"
```

## Configuration File (config/default.yaml)

```yaml
universe:
  cache_ttl: 3600              # Symbol cache duration (seconds)
  min_hourly_volume: 1000      # Min USD volume per hour

data:
  websocket:
    max_streams_per_connection: 1024
    max_messages_per_second: 10
    reconnect_delay: 5
  rest:
    rate_limit: 1200           # Requests per minute

signals:
  timeframe: "15m"             # Candlestick timeframe
  lookback_periods: 8          # Periods to analyze
  volume_zscore_threshold: 2.0
  price_change_threshold: 0.05 # 5%
  use_atr_normalization: true

alerts:
  cooldown_minutes: 30         # Min time between alerts
  discord_webhook_url: "${DISCORD_WEBHOOK_URL}"

monitoring:
  metrics_interval: 60         # Seconds
  log_level: "INFO"            # DEBUG, INFO, WARNING, ERROR
```

## Docker Commands

```bash
# Build and run
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

## Common Tasks

### Run Tests
```bash
pytest tests/                    # All tests
pytest tests/test_config.py     # Specific test
pytest -v                        # Verbose
pytest --cov=src tests/         # With coverage
```

### Validate Installation
```bash
python validate.py              # Run all checks
```

### Check Configuration
```python
from src.core.config import load_config

config = load_config('config/default.yaml')
config.validate()
print(config.signals.timeframe)
```

### Manual Alert Test
```python
from src.alerts.discord import DiscordNotifier
from src.core.types import MomentumSignal

notifier = DiscordNotifier("your_webhook_url")
signal = MomentumSignal(
    symbol="BTCUSDT",
    volume_spike_pct=250.0,
    price_change_pct=5.0,
    candle_timestamp=1234567890,
    timeframe="15m"
)
notifier.send_alert(signal)
```

### Database Operations
```python
from src.alerts.deduplication import AlertDeduplicationDB

db = AlertDeduplicationDB()

# Store alert
db.store_alert('BTCUSDT', '15m', 1234567890, 'sig123')

# Check if exists
exists = db.alert_exists('BTCUSDT', '15m', 1234567890)

# Cleanup old (>7 days)
db.cleanup_old(days=7)
```

### Structured Logging
```python
from src.monitoring.logger import get_logger

logger = get_logger('my_component', 'INFO')

# Log with data
logger.info(
    event='symbol_analyzed',
    message='Analysis complete',
    data={'symbol': 'BTCUSDT', 'result': 'signal'}
)

# Log error
logger.error(
    event='api_error',
    message='Failed to fetch data',
    data={'error': str(e)},
    exc_info=True
)
```

### Symbol Universe
```python
from src.core.universe import SymbolUniverse
from src.data.rest_client import BinanceRestClient

rest_client = BinanceRestClient()
universe = SymbolUniverse(
    rest_client=rest_client,
    min_hourly_volume=1000,
    cache_ttl=3600
)

# Get liquid symbols
symbols = universe.get_liquid_perpetuals()

# Force refresh
symbols = universe.get_liquid_perpetuals(force_refresh=True)

# Check specific symbol
is_liquid = universe.is_liquid('BTCUSDT')
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the project root
cd /workspaces/binance_trading_tools/binance_momentum_monitor
python main.py
```

### Configuration Not Found
```bash
# Set explicit path
export CONFIG_PATH="/path/to/config.yaml"
```

### Database Locked
```bash
# Remove and restart
rm alerts.db
python main.py
```

### Rate Limit Errors
```yaml
# In config.yaml, reduce rate limit
data:
  rest:
    rate_limit: 600  # Instead of 1200
```

### Memory Issues
```bash
# Monitor memory
docker stats  # If using Docker

# Check logs
grep -i "memory" logs/*.log
```

## File Locations

```
Project Root: /workspaces/binance_trading_tools/binance_momentum_monitor/
Config:       config/default.yaml
Database:     alerts.db (auto-created)
Logs:         stdout (JSON format)
Docker:       docker/
Tests:        tests/
Main:         main.py
```

## API Endpoints Used

```
Exchange Info:  https://fapi.binance.com/fapi/v1/exchangeInfo
24hr Tickers:   https://fapi.binance.com/fapi/v1/ticker/24hr
Klines:         https://fapi.binance.com/fapi/v1/klines
```

## Log Format

```json
{
  "timestamp": "2025-10-01T12:34:56.789Z",
  "level": "INFO",
  "component": "momentum_detector",
  "event": "momentum_detected",
  "message": "Momentum signal for BTCUSDT",
  "data": {
    "symbol": "BTCUSDT",
    "volume_spike_pct": 250.5,
    "price_change_pct": 5.2
  },
  "trace_id": "abc123"
}
```

## Discord Alert Format

```
🚨 **MOMENTUM ALERT** 🚨
**BTCUSDT**
Volume: +250.0%
Price: +5.0%
Timeframe: 15m
```

## Next Steps

For Phase 2 (WebSocket implementation):
- See `src/data/websocket_client.py` (placeholder)
- See implementation plan in main README

For Phase 3 (Advanced signals):
- See `src/signals/normalizers.py` (placeholder)
- ATR normalization ready to implement
- Volume Z-score ready to implement

## Support

- README.md - Full documentation
- MIGRATION.md - Migration guide
- PHASE1_SUMMARY.md - Implementation details
- GitHub Issues - Bug reports and features
