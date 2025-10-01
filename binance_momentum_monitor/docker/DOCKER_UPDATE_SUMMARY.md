# Docker Integration - Update Summary

## Changes Made for Docker + NordVPN Integration

### Files Updated

#### 1. **docker/Dockerfile** ✅
**Changes:**
- Updated to copy new modular structure (`src/`, `config/`, `main.py`)
- Removed old `momentum_scanner.py` reference
- Added non-root user creation with sudo permissions for NordVPN
- Added proper ownership changes for non-root user
- Updated health check to validate new imports
- Improved layer caching (requirements first, then code)

**Key Sections:**
```dockerfile
# Create non-root user with sudo for nordvpnd
RUN useradd -m -u 1000 scanner && \
    echo "scanner ALL=(ALL) NOPASSWD: /usr/sbin/nordvpnd" >> /etc/sudoers

# Copy modular structure
COPY src/ ./src/
COPY config/ ./config/
COPY main.py .

# Health check validates new imports
HEALTHCHECK ... CMD ./venv/bin/python3 -c "from src.core.config import Config; ..."
```

#### 2. **docker/entrypoint.sh** ✅
**Changes:**
- Added comprehensive startup logging with emojis
- Added validation checks for required environment variables
- Added Python import validation before starting app
- Added configuration display
- Added VPN status display
- Removed test execution (not needed in production entrypoint)
- Better error handling and exit codes

**Key Sections:**
```bash
# Validate environment
if [ -z "${NORDVPN_TOKEN}" ]; then
  echo "❌ Error: NORDVPN_TOKEN environment variable is not set"
  exit 1
fi

# Verify Python environment
./venv/bin/python3 -c "from src.core.config import Config; print('✅ Imports successful')"

# Start application
exec ./venv/bin/python3 main.py
```

#### 3. **docker/docker-compose.yml** ✅
**Changes:**
- Added `cap_add: NET_ADMIN` for VPN
- Added `/dev/net/tun` device for VPN tunnel
- Added `NORDVPN_TOKEN` environment variable (required)
- Organized environment variables with comments
- Added persistent volume `scanner-data` for database
- Added `sysctls` to disable IPv6 for VPN stability
- Enhanced documentation in comments

**Key Sections:**
```yaml
cap_add:
  - NET_ADMIN  # Required for NordVPN
devices:
  - /dev/net/tun  # Required for VPN tunnel

environment:
  - NORDVPN_TOKEN=${NORDVPN_TOKEN}  # Required!
  - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}  # Required!

volumes:
  scanner-data:
    driver: local
```

#### 4. **docker/DOCKER_DEPLOYMENT.md** ✅ (New File)
**Created comprehensive deployment guide covering:**
- Prerequisites and system requirements
- Quick start guide
- Detailed configuration
- Environment variables reference
- Build process
- Startup sequence
- Health checks
- Persistent data management
- Logs and monitoring
- VPN management
- Troubleshooting guide
- Production deployment recommendations

#### 5. **.dockerignore** ✅ (New File)
**Created to exclude:**
- Python bytecode and cache
- Virtual environments
- Test files and coverage
- IDE files
- Git files
- Temporary files
- Documentation (except README)

---

## Required Environment Variables

### Production Deployment

```bash
# Required
export NORDVPN_TOKEN="your_nordvpn_token_here"
export DISCORD_WEBHOOK_URL="your_discord_webhook_url"

# Optional (with defaults)
export TIMEFRAME="15m"
export LOOKBACK_PERIODS=8
export MIN_HOURLY_VOLUME=1000
export ALERT_COOLDOWN=30
export LOG_LEVEL="INFO"
```

---

## Deployment Commands

### Build and Start
```bash
cd /workspaces/binance_trading_tools/binance_momentum_monitor/docker

# Set required variables
export NORDVPN_TOKEN="your_token"
export DISCORD_WEBHOOK_URL="your_webhook"

# Start
docker-compose up -d

# View logs
docker-compose logs -f
```

### Stop
```bash
docker-compose down
```

### Rebuild After Changes
```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## File Structure in Container

```
/app/
├── venv/                    # Python virtual environment
│   ├── bin/
│   │   └── python3         # Python interpreter
│   └── lib/
├── src/                     # Application source
│   ├── core/
│   │   ├── config.py
│   │   ├── types.py
│   │   └── universe.py
│   ├── data/
│   │   └── rest_client.py
│   ├── signals/
│   │   └── momentum.py
│   ├── alerts/
│   │   ├── manager.py
│   │   ├── discord.py
│   │   └── deduplication.py
│   └── monitoring/
│       └── logger.py
├── config/
│   └── default.yaml         # Default configuration
├── data/                    # Persistent volume mount
│   └── alerts.db           # SQLite database (auto-created)
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── entrypoint.sh           # Docker entrypoint script
```

---

## Startup Sequence

1. **Container starts** → `entrypoint.sh` begins
2. **Start NordVPN daemon** → `sudo /usr/sbin/nordvpnd &`
3. **Wait 10s** → Daemon initialization
4. **Login to NordVPN** → Using `$NORDVPN_TOKEN`
5. **Configure VPN** → OpenVPN + TCP
6. **Connect to VPN** → Portugal server (pt125)
7. **Verify VPN** → Display status
8. **Validate Python** → Import checks
9. **Start application** → `exec ./venv/bin/python3 main.py`

---

## Health Check

The Docker health check runs every 60 seconds:

```bash
./venv/bin/python3 -c "from src.core.config import Config; import sys; sys.exit(0)"
```

**Status indicators:**
- ✅ **Healthy**: Imports work, app running
- ⚠️ **Starting**: Within 60s startup period
- ❌ **Unhealthy**: Failed 3 times

---

## Troubleshooting

### Issue: Container exits immediately

**Check:**
1. `docker-compose logs` - View error messages
2. Environment variables set? (`NORDVPN_TOKEN`, `DISCORD_WEBHOOK_URL`)
3. VPN connection successful?

**Solution:**
```bash
# View logs
docker-compose logs

# Check environment
docker exec binance-momentum-scanner env | grep -E "NORDVPN|DISCORD"

# Manual debug
docker run -it --rm \
  -e NORDVPN_TOKEN="$NORDVPN_TOKEN" \
  -e DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL" \
  --cap-add=NET_ADMIN \
  --device=/dev/net/tun \
  binance-momentum-monitor sh
```

### Issue: Import errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Verify files copied correctly
docker exec binance-momentum-scanner ls -la /app/src/

# If missing, rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Issue: VPN connection fails

**Problem:** "NordVPN connection failed"

**Solution:**
```bash
# Check token validity
echo $NORDVPN_TOKEN

# View VPN logs
docker-compose logs | grep -i nordvpn

# Try different server in entrypoint.sh:
# Change: nordvpn connect pt125
# To: nordvpn connect portugal  (or any other country/server)
```

---

## Testing the Docker Build

### Test Build Locally

```bash
cd /workspaces/binance_trading_tools/binance_momentum_monitor

# Build image
docker build -f docker/Dockerfile -t test-momentum .

# Run with minimal config
docker run --rm \
  -e NORDVPN_TOKEN="test_token" \
  -e DISCORD_WEBHOOK_URL="https://test.webhook" \
  --cap-add=NET_ADMIN \
  --device=/dev/net/tun \
  test-momentum
```

### Verify Files Are Copied

```bash
# Start container in background
docker-compose up -d

# Check file structure
docker exec binance-momentum-scanner ls -la
docker exec binance-momentum-scanner ls -la src/
docker exec binance-momentum-scanner ls -la config/

# Check Python can import
docker exec binance-momentum-scanner ./venv/bin/python3 -c "from src.core.config import Config; print('OK')"

# Stop
docker-compose down
```

---

## Differences from Development

| Aspect | Development | Docker Production |
|--------|-------------|-------------------|
| Python | System Python | Virtual environment (`venv/`) |
| Tests | Run via `pytest` | Not run in entrypoint |
| Validation | `validate.py` before start | Import check only |
| Startup | `python main.py` | `./venv/bin/python3 main.py` |
| VPN | Manual or none | Automatic via entrypoint |
| Config | `config/default.yaml` or env | Environment variables preferred |
| User | Current user | Non-root `scanner` user |
| Logging | Console | JSON to Docker logs |

---

## Production Checklist

Before deploying to production:

- [ ] `NORDVPN_TOKEN` is set and valid
- [ ] `DISCORD_WEBHOOK_URL` is set and valid
- [ ] VPN server location is correct (pt125 or change in entrypoint.sh)
- [ ] Environment variables configured (timeframe, thresholds, etc.)
- [ ] Docker host has NET_ADMIN capability
- [ ] Docker host has /dev/net/tun device
- [ ] Persistent volume configured for database
- [ ] Log rotation configured (10MB max, 3 files)
- [ ] Resource limits set if needed
- [ ] Health check working
- [ ] Tested build and startup

---

## Summary

✅ **Dockerfile**: Updated to copy modular structure, proper user setup
✅ **entrypoint.sh**: Enhanced with validation, logging, error handling
✅ **docker-compose.yml**: Added VPN requirements, persistent storage
✅ **DOCKER_DEPLOYMENT.md**: Comprehensive deployment guide
✅ **.dockerignore**: Exclude unnecessary files

**Ready for deployment!** 🚀

The Docker setup now:
- Properly copies all new modular files
- Validates environment and imports before starting
- Provides detailed logging during startup
- Handles VPN connection automatically
- Persists alert database across restarts
- Runs as non-root user for security
- Includes health checks for monitoring
