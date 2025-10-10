# Deployment Guide - Momentum Signals API

## Quick Deployment on Your Server

### 1. Upload Files to Server

From your local machine:

```powershell
# Navigate to the API directory
cd c:\Home\Dempsey\Development\github\binance_trading_tools\binance_momentum_signal_api

# Upload to server (adjust path as needed)
scp -r . dempsey@app-greyjoy-01:/opt/deployment/momentum-signals-api/
```

Or use Git if you've committed the changes:
```bash
# On server
cd /opt/deployment
git clone <your-repo> momentum-signals-api
cd momentum-signals-api
```

### 2. Create Environment File on Server

```bash
# SSH into server
ssh dempsey@app-greyjoy-01

# Navigate to API directory
cd /opt/deployment/momentum-signals-api

# Create .env file
nano .env
```

Add the following (adjust credentials):
```env
MYSQL_DSN=mysql+pymysql://root:password@172.21.0.3:3306/momentum_signal_monitor
API_PORT=8000
```

**Important:** Replace `password` with your actual MySQL root password (same as `DOCKER_DB_ROOT_PASSWORD` from AzerothCore).

### 3. Deploy with Docker Compose

```bash
# Build the image
docker compose build

# Start the service
docker compose up -d

# Check if it's running
docker ps | grep momentum-signals-api

# View logs
docker logs -f momentum-signals-api
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8000/healthz

# Test API
curl http://localhost:8000/symbols
```

### 5. Check Network Connectivity

Verify the API can reach the database:

```bash
# Check network
docker network inspect azerothcore-wotlk_ac-network | grep momentum-signals-api

# Test database connection from container
docker exec momentum-signals-api python -c "
from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://root:password@172.21.0.3:3306/momentum_signal_monitor')
with engine.connect() as conn:
    result = conn.execute('SELECT COUNT(*) FROM alerts')
    print(f'Alerts in database: {result.scalar()}')
"
```

## Accessing the API

### From Your Server
```bash
curl http://localhost:8000/healthz
```

### From External Machine
```bash
# Replace with your server's IP
curl http://app-greyjoy-01:8000/healthz
```

### Interactive Documentation
Open in browser: `http://app-greyjoy-01:8000/docs`

## Common Operations

### Restart Service
```bash
cd /opt/deployment/momentum-signals-api
docker compose restart
```

### View Logs
```bash
docker logs -f momentum-signals-api
```

### Update Service
```bash
cd /opt/deployment/momentum-signals-api

# Pull latest code (if using Git)
git pull

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Stop Service
```bash
cd /opt/deployment/momentum-signals-api
docker compose down
```

## Example API Calls

### Get All Symbols
```bash
curl http://localhost:8000/symbols
```

### Search Recent Alerts
```bash
curl "http://localhost:8000/alerts/search?limit=10&sort=created_desc"
```

### Get BTCUSDT Alerts
```bash
curl "http://localhost:8000/alerts/search?symbol=BTCUSDT&timeframe=15m"
```

### Get High-Score Signals
```bash
curl "http://localhost:8000/alerts/search?min_signal=7&sort=signal_desc"
```

## Integration with External Services

### Example: Query from Python Script
```python
import requests

API_URL = "http://app-greyjoy-01:8000"

# Get recent alerts
response = requests.get(
    f"{API_URL}/alerts/search",
    params={"limit": 50, "sort": "created_desc"}
)

alerts = response.json()["items"]
for alert in alerts:
    print(f"{alert['symbol']} - Score: {alert['momentum_score']}")
```

### Example: Query from Trading Bot
```python
def get_recent_signals(symbol: str = None, min_score: int = 6):
    """Get recent high-quality signals"""
    params = {
        "min_signal": min_score,
        "sort": "created_desc",
        "limit": 20
    }
    
    if symbol:
        params["symbol"] = symbol
    
    response = requests.get(
        f"{API_URL}/alerts/search",
        params=params
    )
    
    return response.json()["items"]
```

## Troubleshooting

### Can't Connect to Database
```bash
# Check if MySQL is running
docker ps | grep ac-database

# Check if API is on the correct network
docker network inspect azerothcore-wotlk_ac-network

# Test connection
docker exec momentum-signals-api ping 172.21.0.3
```

### API Returns Empty Results
```bash
# Check database has data
docker exec -it ac-database mysql -uroot -p -e "SELECT COUNT(*) FROM momentum_signal_monitor.alerts;"

# Check API logs
docker logs momentum-signals-api
```

### Port Conflict
If port 8000 is already in use, change it in `.env`:
```env
API_PORT=8001
```

Then restart:
```bash
docker compose down
docker compose up -d
```

## Security Notes

1. **Never Commit .env**: Never commit `.env` file to Git (contains database credentials)
2. **Use Firewall**: Only expose port 8000 if needed externally
3. **Use HTTPS**: In production, put behind reverse proxy with SSL
4. **Restrict Network**: Keep API on private Docker network

## Monitoring

### Container Health
```bash
docker inspect --format='{{.State.Health.Status}}' momentum-signals-api
```

### Resource Usage
```bash
docker stats momentum-signals-api
```

### Database Connection Status
```bash
docker logs momentum-signals-api | grep -i "database\|mysql\|connection"
```
