# Binance Momentum Monitor

A modular, production-ready momentum scanner for Binance Futures with WebSocket support and advanced signal detection.

## Features

- **Modular Architecture**: Clean separation of concerns across core, data, signals, alerts, and monitoring modules
- **Configuration Management**: YAML-based configuration with environment variable interpolation
- **Alert Deduplication**: SQLite-based persistence to prevent duplicate alerts
- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **Rate Limiting**: Built-in rate limiting for REST API calls
- **Docker Support**: Production-ready Docker configuration

## Project Structure

```
binance_momentum_monitor/
├── src/
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration management
│   │   ├── universe.py     # Symbol universe management
│   │   └── types.py        # Data types/models
│   ├── data/               # Data layer
│   │   ├── websocket_client.py  # WebSocket connection (Phase 2)
│   │   ├── rest_client.py       # REST API client
│   │   └── cache.py             # Data caching
│   ├── signals/            # Signal detection
│   │   ├── momentum.py     # Momentum calculation
│   │   ├── normalizers.py  # ATR/Z-score normalization (Phase 3)
│   │   └── filters.py      # Signal filtering
│   ├── alerts/             # Alert system
│   │   ├── manager.py      # Alert orchestration
│   │   ├── discord.py      # Discord integration
│   │   └── deduplication.py # SQLite dedup logic
│   └── monitoring/         # Monitoring & observability
│       ├── metrics.py      # Performance metrics (Phase 5)
│       └── logger.py       # Structured logging
├── tests/                  # Unit tests
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── default.yaml        # Default configuration
├── main.py                 # Application entry point
└── requirements.txt
```

## Configuration

### YAML Configuration

Create a `config/default.yaml` file:

```yaml
universe:
  cache_ttl: 3600
  min_hourly_volume: 1000

data:
  websocket:
    max_streams_per_connection: 1024
    max_messages_per_second: 10
    reconnect_delay: 5
  rest:
    rate_limit: 1200

signals:
  timeframe: "15m"
  lookback_periods: 8
  volume_zscore_threshold: 2.0
  price_change_threshold: 0.05
  use_atr_normalization: true

alerts:
  cooldown_minutes: 30
  discord_webhook_url: "${DISCORD_WEBHOOK_URL}"

monitoring:
  metrics_interval: 60
  log_level: "INFO"
```

### Environment Variables

You can override any configuration with environment variables:

- `DISCORD_WEBHOOK_URL` - Discord webhook URL (required)
- `TIMEFRAME` - Candlestick timeframe (default: "15m")
- `LOOKBACK_PERIODS` - Number of periods to analyze (default: 8)
- `VOLUME_ZSCORE_THRESHOLD` - Volume Z-score threshold (default: 2.0)
- `PRICE_CHANGE_THRESHOLD` - Price change threshold (default: 0.05)
- `MIN_HOURLY_VOLUME` - Minimum hourly volume in USD (default: 1000)
- `ALERT_COOLDOWN` - Alert cooldown in minutes (default: 30)
- `LOG_LEVEL` - Logging level (default: "INFO")

## Installation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_WEBHOOK_URL="your_webhook_url"

# Run the scanner
python main.py
```

### Docker Deployment

```bash
# Using docker-compose
cd docker
export DISCORD_WEBHOOK_URL="your_webhook_url"
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Testing

```bash
# Install pytest
pip install pytest

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Phase 1 Implementation Status

✅ **Completed:**
- Project structure refactoring
- Configuration management with YAML and env var interpolation
- SQLite persistence layer for alert deduplication
- Structured JSON logging
- REST API client with rate limiting
- Symbol universe management with caching
- Alert manager with cooldown logic
- Discord notifier
- Momentum detector
- Main application orchestration
- Docker configuration
- Basic unit tests

🔄 **Next Phases:**
- Phase 2: WebSocket infrastructure
- Phase 3: Enhanced signal detection (ATR normalization, volume Z-score)
- Phase 4: Alert system upgrade (enrichment, templating)
- Phase 5: Monitoring & observability (metrics, health checks)
- Phase 6: Testing & deployment automation

## Usage Examples

### Basic Usage

```python
from src.core.config import load_config
from binance_momentum_monitor.main import MomentumScanner

# Load configuration
config = load_config('config/default.yaml')

# Create and run scanner
scanner = MomentumScanner(config)
await scanner.run()
```

### Custom Configuration

```python
from src.core.config import Config, SignalsConfig

# Create custom config
config = Config()
config.signals = SignalsConfig(
    timeframe="5m",
    lookback_periods=12,
    price_change_threshold=0.03
)
config.alerts.discord_webhook_url = "your_webhook"

# Run with custom config
scanner = MomentumScanner(config)
await scanner.run()
```

## Logging

Logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2025-10-01T12:34:56.789Z",
  "level": "INFO",
  "component": "momentum_detector",
  "event": "momentum_detected",
  "symbol": "BTCUSDT",
  "data": {
    "volume_spike_pct": 250.5,
    "price_change_pct": 5.2
  },
  "trace_id": "abc123"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
