# Binance Momentum Monitor - Documentation Index

## 📚 Complete Documentation Guide

### 🚀 Getting Started

1. **[README.md](README.md)** - Start here!
   - Features overview
   - Project structure
   - Configuration guide
   - Installation instructions
   - Docker deployment
   - Testing guide
   - Usage examples

2. **[QUICKREF.md](QUICKREF.md)** - Quick Reference
   - Quick start commands
   - Environment variables
   - Configuration examples
   - Common tasks
   - Troubleshooting
   - API endpoints

3. **[.env.example](.env.example)** - Environment Template
   - All available environment variables
   - Default values
   - Required vs optional settings

### 📖 Implementation Details

4. **[PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)** - Phase 1 Summary
   - Complete implementation details
   - Acceptance criteria status
   - Technical improvements
   - File structure breakdown
   - Performance metrics
   - Next steps

5. **[DELIVERABLES.md](DELIVERABLES.md)** - Complete Deliverables
   - All 35+ files created
   - Line count statistics
   - Feature completion status
   - Quality metrics
   - Validation results

6. **[CHANGELOG.md](CHANGELOG.md)** - Version History
   - Version 1.0.0 details
   - Added features
   - Changed components
   - Technical improvements
   - Future releases planned

### 🔄 Migration & Upgrade

7. **[MIGRATION.md](MIGRATION.md)** - Migration Guide
   - Original → new structure mapping
   - Key differences explained
   - Step-by-step migration
   - Backward compatibility
   - New features available
   - Troubleshooting tips

### 📋 Configuration Files

8. **[config/default.yaml](config/default.yaml)** - Default Configuration
   - Universe settings
   - Data layer settings
   - Signal detection parameters
   - Alert configuration
   - Monitoring settings

### 🐳 Docker Files

9. **[docker/Dockerfile](docker/Dockerfile)** - Docker Build
   - Multi-stage build
   - Non-root user setup
   - Health checks

10. **[docker/docker-compose.yml](docker/docker-compose.yml)** - Docker Compose
    - Service configuration
    - Environment variables
    - Volume mounts
    - Logging configuration

### 🧪 Testing & Validation

11. **[tests/test_config.py](tests/test_config.py)** - Configuration Tests
    - YAML loading tests
    - Environment variable tests
    - Validation tests

12. **[tests/test_deduplication.py](tests/test_deduplication.py)** - Database Tests
    - Alert storage tests
    - Duplicate prevention tests
    - Cleanup tests

13. **[validate.py](validate.py)** - Validation Script
    - Comprehensive validation
    - All component checks
    - Summary report

### 🔧 Scripts

14. **[start.sh](start.sh)** - Quick Start Script
    - Dependency installation
    - Test execution
    - Configuration display
    - Scanner startup

15. **[main.py](main.py)** - Main Application
    - Entry point
    - Component orchestration
    - Scan cycle management

---

## 📦 Module Documentation

### Core Module (`src/core/`)

#### [src/core/config.py](src/core/config.py)
**Configuration Management System**
- YAML configuration loading
- Environment variable interpolation
- Configuration validation
- Type-safe dataclasses
- Hot-reload support

**Key Classes:**
- `Config` - Main configuration
- `UniverseConfig` - Universe settings
- `DataConfig` - Data layer settings
- `SignalsConfig` - Signal parameters
- `AlertsConfig` - Alert settings
- `MonitoringConfig` - Monitoring settings

**Key Functions:**
- `load_config(path)` - Load and validate config
- `Config.from_yaml(path)` - Load from YAML
- `Config.from_env()` - Load from environment

#### [src/core/types.py](src/core/types.py)
**Core Data Models**
- `KlineBar` - Candlestick data
- `MomentumSignal` - Signal with enrichment fields
- `SymbolInfo` - Symbol metadata
- `AlertRecord` - Alert tracking

#### [src/core/universe.py](src/core/universe.py)
**Symbol Universe Management**
- Liquid perpetual filtering
- Symbol caching (TTL-based)
- Thread-safe operations
- Force refresh capability

**Key Class:**
- `SymbolUniverse`

**Key Methods:**
- `get_liquid_perpetuals(force_refresh)` - Get liquid symbols
- `get_symbol_info(symbol)` - Get symbol details
- `is_liquid(symbol)` - Check liquidity

### Data Module (`src/data/`)

#### [src/data/rest_client.py](src/data/rest_client.py)
**REST API Client**
- Binance Futures API integration
- Automatic rate limiting
- Connection pooling
- Error handling

**Key Class:**
- `BinanceRestClient`

**Key Methods:**
- `get_24hr_tickers()` - Get all tickers
- `get_exchange_info()` - Get exchange info
- `get_klines(symbol, interval, limit)` - Get candlesticks

#### [src/data/websocket_client.py](src/data/websocket_client.py)
**WebSocket Client** (Placeholder for Phase 2)

#### [src/data/cache.py](src/data/cache.py)
**Data Caching** (Placeholder for Phase 2)

### Signals Module (`src/signals/`)

#### [src/signals/momentum.py](src/signals/momentum.py)
**Momentum Detection**
- Volume spike detection
- Price change detection
- Dynamic thresholds
- Historical analysis

**Key Class:**
- `MomentumDetector`

**Key Methods:**
- `analyze_symbol(symbol, avg_volume)` - Analyze for signals
- `get_kline_dataframe(symbol, limit)` - Get historical data

#### [src/signals/normalizers.py](src/signals/normalizers.py)
**ATR/Z-Score Normalization** (Placeholder for Phase 3)

#### [src/signals/filters.py](src/signals/filters.py)
**Signal Filtering** (Placeholder for Phase 3)

### Alerts Module (`src/alerts/`)

#### [src/alerts/manager.py](src/alerts/manager.py)
**Alert Manager**
- Alert orchestration
- Cooldown management
- Database deduplication
- Context-aware delivery

**Key Class:**
- `AlertManager`

**Key Methods:**
- `can_alert(symbol, timeframe, bar_time)` - Check if can alert
- `send_alert(signal, context)` - Send alert
- `cleanup_old_alerts(days)` - Clean old records

#### [src/alerts/discord.py](src/alerts/discord.py)
**Discord Integration**
- Webhook notifications
- Basic alert formatting
- Enriched alerts with context
- Error handling

**Key Class:**
- `DiscordNotifier`

**Key Methods:**
- `send_alert(signal)` - Send basic alert
- `send_enriched_alert(signal, context)` - Send enriched alert

#### [src/alerts/deduplication.py](src/alerts/deduplication.py)
**SQLite Deduplication**
- Alert persistence
- Duplicate prevention
- Thread-safe operations
- Automatic cleanup

**Key Class:**
- `AlertDeduplicationDB`

**Key Methods:**
- `store_alert(symbol, timeframe, bar_time, sig)` - Store alert
- `alert_exists(symbol, timeframe, bar_time)` - Check existence
- `cleanup_old(days)` - Remove old alerts

### Monitoring Module (`src/monitoring/`)

#### [src/monitoring/logger.py](src/monitoring/logger.py)
**Structured Logging**
- JSON-formatted logs
- Configurable levels
- Trace ID tracking
- Event-driven logging
- Component isolation

**Key Class:**
- `StructuredLogger`

**Key Function:**
- `get_logger(component, level)` - Get logger instance

**Log Methods:**
- `info(event, message, data, trace_id)`
- `warning(event, message, data, trace_id)`
- `error(event, message, data, trace_id, exc_info)`
- `debug(event, message, data, trace_id)`

#### [src/monitoring/metrics.py](src/monitoring/metrics.py)
**Performance Metrics** (Placeholder for Phase 5)

---

## 🎯 Quick Navigation

### For First-Time Users
1. Read [README.md](README.md)
2. Copy [.env.example](.env.example) to `.env`
3. Follow [QUICKREF.md](QUICKREF.md) quick start

### For Migration from Old Version
1. Read [MIGRATION.md](MIGRATION.md)
2. Check [CHANGELOG.md](CHANGELOG.md) for changes
3. Test with [validate.py](validate.py)

### For Developers
1. Read [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)
2. Check [DELIVERABLES.md](DELIVERABLES.md)
3. Review module documentation above

### For Operators
1. Use [QUICKREF.md](QUICKREF.md) for commands
2. Check [docker/](docker/) for deployment
3. Monitor using structured logs

### For Troubleshooting
1. Check [QUICKREF.md](QUICKREF.md) troubleshooting section
2. Review [MIGRATION.md](MIGRATION.md) for common issues
3. Run [validate.py](validate.py) for diagnostics

---

## 📊 Implementation Status

### ✅ Phase 1: Foundation & Infrastructure (COMPLETE)
- All 35+ files delivered
- 7/7 tests passing
- 6/6 validation checks passing
- Documentation complete

### 🔄 Phase 2: WebSocket Infrastructure (READY)
- Placeholder files created
- Architecture ready
- No refactoring needed

### 🔄 Phase 3: Enhanced Signals (READY)
- Placeholder files created
- Integration points defined

### 🔄 Phase 4: Alert System Upgrade (READY)
- Foundation in place
- Extensible design

### 🔄 Phase 5: Monitoring (READY)
- Logger complete
- Metrics placeholder ready

### 🔄 Phase 6: Testing & Deployment (READY)
- Test framework in place
- Docker ready

---

## 📞 Support & Resources

- **GitHub Issues:** Report bugs and request features
- **README.md:** Complete documentation
- **QUICKREF.md:** Quick answers
- **validate.py:** Diagnostic tool

---

## 📄 License

MIT License - See project root for details

---

**Last Updated:** October 1, 2025  
**Version:** 1.0.0  
**Status:** Phase 1 Complete ✅
