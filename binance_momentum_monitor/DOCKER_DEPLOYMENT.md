# Docker Deployment Guide

## Overview

This guide covers deploying the Binance Momentum Monitor with NordVPN in Docker.

## Prerequisites

### Required
- Docker Engine 20.10+
- Docker Compose v2.0+
- NordVPN subscription with access token
- Discord webhook URL

### System Requirements
- NET_ADMIN capability (for VPN)
- /dev/net/tun device access
- 512MB RAM minimum
- 1GB disk space

## Quick Start

### 1. Set Required Environment Variables

```bash
# Required: NordVPN authentication token
export NORDVPN_TOKEN="your_nordvpn_token_here"

# Required: Discord webhook for alerts
export DISCORD_WEBHOOK_URL="your_discord_webhook_url"
```

### 2. Build and Start

```bash
cd docker
docker-compose up -d
```

### 3. View Logs

```bash
docker-compose logs -f
```

### 4. Stop

```bash
docker-compose down
```

## Detailed Configuration

### Environment Variables

#### Required Variables

```bash
# NordVPN authentication
NORDVPN_TOKEN="your_token_here"

# Discord alerts
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

#### Optional Variables

```bash
# Signal Detection
TIMEFRAME="15m"                    # Candlestick timeframe
LOOKBACK_PERIODS=8                 # Historical periods to analyze
VOLUME_ZSCORE_THRESHOLD=2.0        # Volume spike threshold
PRICE_CHANGE_THRESHOLD=0.05        # Price change threshold (5%)

# Universe Filtering
MIN_HOURLY_VOLUME=1000             # Min USD volume per hour
UNIVERSE_CACHE_TTL=3600            # Symbol cache duration (seconds)

# Alert Management
ALERT_COOLDOWN=30                  # Minutes between alerts per symbol

# Monitoring
LOG_LEVEL="INFO"                   # DEBUG, INFO, WARNING, ERROR
METRICS_INTERVAL=60                # Metrics collection interval (seconds)

# Configuration File
CONFIG_PATH=""                     # Path to custom YAML config (optional)
```

### Docker Compose Configuration

The `docker-compose.yml` includes:

- **NET_ADMIN capability**: Required for VPN routing
- **TUN device**: Required for VPN tunnel
- **Persistent volumes**: Alert database persistence
- **Log rotation**: 10MB max, 3 files
- **IPv6 disabled**: For VPN stability

## Build Process

### What Gets Copied

The Dockerfile copies these files/directories:

```
/app/
├── venv/                  # Python virtual environment
├── src/                   # Application source code
│   ├── core/
│   ├── data/
│   ├── signals/
│   ├── alerts/
│   └── monitoring/
├── config/                # Configuration files
│   └── default.yaml
├── main.py               # Application entry point
├── validate.py           # Validation script
├── requirements.txt      # Python dependencies
└── entrypoint.sh        # Docker entrypoint
```

### Build Command

```bash
# From the docker/ directory
docker-compose build

# Or from project root
cd binance_momentum_monitor
docker build -f docker/Dockerfile -t binance-momentum-monitor .
```

## Startup Sequence

The entrypoint script (`entrypoint.sh`) performs the following:

1. **Start NordVPN daemon** (`nordvpnd`)
2. **Wait 10s** for daemon initialization
3. **Login to NordVPN** using `NORDVPN_TOKEN`
4. **Configure VPN**:
   - Technology: OpenVPN
   - Protocol: TCP
5. **Connect to VPN**: Portugal server (pt125)
6. **Verify connection**: Display VPN status
7. **Validate environment**: Check Python imports
8. **Start application**: Launch `main.py`

## Health Checks

The container includes a health check that:

- Runs every 60 seconds
- Times out after 10 seconds
- Waits 60 seconds before first check
- Retries 3 times before marking unhealthy

**Health check command:**
```bash
./venv/bin/python3 -c "from src.core.config import Config; import sys; sys.exit(0)"
```

## Persistent Data

### Alert Database

Alert deduplication data persists in a Docker volume:

```bash
# Volume name: scanner-data
# Mount point: /app/data
# Contains: alerts.db (SQLite database)
```

### Backup Database

```bash
# Find volume location
docker volume inspect scanner-data

# Copy database out
docker cp binance-momentum-scanner:/app/data/alerts.db ./backup/

# Restore database
docker cp ./backup/alerts.db binance-momentum-scanner:/app/data/
```

## Logs

### Viewing Logs

```bash
# Follow all logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs from specific time
docker-compose logs --since=10m
```

### Log Format

Logs are JSON-formatted for easy parsing:

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

### Parsing Logs

```bash
# Filter by component
docker-compose logs | jq 'select(.component == "momentum_detector")'

# Filter by log level
docker-compose logs | jq 'select(.level == "ERROR")'

# Extract specific data
docker-compose logs | jq '.data.symbol'
```

## VPN Management

### VPN Server Selection

The default server is `pt125` (Portugal). To change:

1. Edit `entrypoint.sh`
2. Change `nordvpn connect pt125` to your preferred server
3. Rebuild container

### VPN Status

```bash
# Check VPN status inside container
docker exec binance-momentum-scanner nordvpn status

# Check connection
docker exec binance-momentum-scanner curl -s ifconfig.me
```

### VPN Troubleshooting

If VPN connection fails:

1. **Check token**: Ensure `NORDVPN_TOKEN` is valid
2. **Check logs**: Look for VPN error messages
3. **Restart service**: `docker-compose restart`
4. **Try different server**: Edit entrypoint.sh

## Troubleshooting

### Container Won't Start

**Problem**: Container exits immediately

**Solution**:
```bash
# Check logs
docker-compose logs

# Common issues:
# 1. Missing NORDVPN_TOKEN
# 2. Missing DISCORD_WEBHOOK_URL
# 3. VPN connection failed
# 4. Import errors
```

### VPN Connection Fails

**Problem**: "NordVPN connection failed" error

**Solution**:
```bash
# 1. Verify token is valid
echo $NORDVPN_TOKEN

# 2. Check NordVPN status
docker logs binance-momentum-scanner | grep -i nordvpn

# 3. Try manual connection
docker exec -it binance-momentum-scanner sh
nordvpn status
nordvpn connect
```

### Permission Denied Errors

**Problem**: Permission errors in logs

**Solution**:
```bash
# Ensure proper permissions on entrypoint
chmod +x docker/entrypoint.sh

# Rebuild container
docker-compose build --no-cache
```

### Python Import Errors

**Problem**: "No module named 'src'" errors

**Solution**:
```bash
# Verify all files were copied
docker exec binance-momentum-scanner ls -la

# Check if src/ directory exists
docker exec binance-momentum-scanner ls -la src/

# Rebuild if missing
docker-compose build --no-cache
```

### Database Locked

**Problem**: SQLite database locked errors

**Solution**:
```bash
# Stop container
docker-compose down

# Remove database volume
docker volume rm scanner-data

# Restart (will create new database)
docker-compose up -d
```

## Monitoring

### Container Stats

```bash
# View resource usage
docker stats binance-momentum-scanner

# View detailed info
docker inspect binance-momentum-scanner
```

### Health Status

```bash
# Check health status
docker ps --filter "name=binance-momentum-scanner"

# View health check logs
docker inspect --format='{{json .State.Health}}' binance-momentum-scanner | jq
```

## Updates and Maintenance

### Updating Application

```bash
# 1. Pull latest code
git pull

# 2. Rebuild container
cd docker
docker-compose build --no-cache

# 3. Restart with new image
docker-compose up -d
```

### Updating Dependencies

```bash
# 1. Update requirements.txt
# 2. Rebuild container
docker-compose build --no-cache

# 3. Restart
docker-compose up -d
```

### Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove with volumes
docker-compose down -v

# Remove unused images
docker image prune -a

# Full cleanup
docker system prune -a --volumes
```

## Production Deployment

### Recommended Settings

```yaml
# docker-compose.yml additions for production
services:
  momentum-scanner:
    # ... existing config ...
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # Auto-restart policy
    restart: always
    
    # Multiple replicas (optional)
    deploy:
      replicas: 1
```

### Security Best Practices

1. **Use secrets** instead of environment variables:
   ```yaml
   secrets:
     - nordvpn_token
     - discord_webhook
   ```

2. **Read-only filesystem**:
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
     - /app/data
   ```

3. **Drop capabilities**:
   ```yaml
   cap_drop:
     - ALL
   cap_add:
     - NET_ADMIN  # Only what's needed
   ```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Run validation: `docker exec binance-momentum-scanner ./venv/bin/python3 validate.py`
3. Check GitHub issues
4. Review QUICKREF.md for common problems

## Related Documentation

- [README.md](../README.md) - Main project documentation
- [QUICKREF.md](../QUICKREF.md) - Quick reference guide
- [MIGRATION.md](../MIGRATION.md) - Migration from old version
- [docker-compose.yml](docker-compose.yml) - Docker Compose configuration
