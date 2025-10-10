# Momentum Signals API

REST API for querying momentum trading signals stored in MySQL database.

## Features

- 📊 **Signal Search** - Query alerts by symbol, timeframe, score, etc.
- 🔄 **Cursor Pagination** - Efficient pagination for large datasets
- 🏥 **Health Checks** - Built-in `/healthz` endpoint
- 🐳 **Docker Ready** - Complete containerization setup
- 🔌 **MySQL Pool** - Connection pooling for performance

## API Endpoints

### Health Check
```
GET /healthz
```
Returns: `{"status": "ok"}`

### List All Symbols
```
GET /symbols
```
Returns: `["BTCUSDT", "ETHUSDT", ...]`

### Get Alert by ID
```
GET /alerts/{id}
```
Returns: Full `MomentumSignalModel` object

### Search Alerts
```
GET /alerts/search?symbol=BTCUSDT&timeframe=15m&min_signal=5.0&limit=50
```

**Query Parameters:**
- `symbol` (optional): Filter by trading pair (e.g., "BTCUSDT")
- `timeframe` (optional): Filter by timeframe (e.g., "15m", "1h")
- `after_ts` (optional): Unix timestamp - only return signals after this time
- `min_signal` (optional): Minimum signal_strength score
- `sort` (optional): Sort order - `ts_desc`, `signal_desc`, `momentum_desc`, `created_desc` (default: `ts_desc`)
- `limit` (optional): Results per page (1-500, default: 50)
- `cursor` (optional): Pagination cursor (use `next_cursor` from previous response)

**Returns:**
```json
{
  "items": [...],
  "next_cursor": 123
}
```

## Setup

### 1. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
MYSQL_DSN=mysql+pymysql://root:password@172.21.0.3:3306/momentum_signal_monitor
API_PORT=8000
```

### 2. Build and Run with Docker Compose

```bash
# Build the image
docker compose build

# Start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/healthz

# Get symbols
curl http://localhost:8000/symbols

# Search alerts
curl "http://localhost:8000/alerts/search?symbol=BTCUSDT&limit=10"
```

## Local Development (Without Docker)

### 1. Install Dependencies
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Windows PowerShell
$env:MYSQL_DSN="mysql+pymysql://root:password@localhost:3306/momentum_signal_monitor"

# Linux/Mac
export MYSQL_DSN="mysql+pymysql://root:password@localhost:3306/momentum_signal_monitor"
```

### 3. Run the Server
```bash
uvicorn service.api:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Database Connection

The API connects to the same MySQL database used by the momentum scanner (`momentum_signal_monitor` database). Make sure:

1. The database exists and has the `alerts` table
2. If running in Docker, the API container is on the same network as the MySQL container
3. Use the correct database credentials in your `.env` file

### Docker Network Setup

The `docker-compose.yml` connects to the `azerothcore-wotlk_ac-network` to access the shared MySQL database. If your MySQL is on a different network:

```yaml
networks:
  - your-mysql-network
```

Or use the direct IP address in `MYSQL_DSN`:
```env
MYSQL_DSN=mysql+pymysql://root:password@172.21.0.3:3306/momentum_signal_monitor
```

## Production Deployment

### On Your Server

```bash
# Navigate to the API directory
cd /path/to/binance_momentum_signal_api

# Create .env file
nano .env  # Add your production credentials

# Build and start
docker compose up -d --build

# Verify it's running
docker ps | grep momentum-signals-api
curl http://localhost:8000/healthz
```

### Accessing from External Applications

If you need to expose the API externally:

1. **Update docker-compose.yml ports:**
   ```yaml
   ports:
     - "8000:8000"  # Accessible on host machine
   ```

2. **Use a reverse proxy (recommended):**
   ```nginx
   location /api/ {
       proxy_pass http://localhost:8000/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. **Add HTTPS with Caddy/Nginx:**
   ```
   momentum-api.yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```

## Architecture

```
binance_momentum_signal_api/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Orchestration config
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
├── models/
│   ├── __init__.py
│   └── model.py           # Pydantic data models
└── service/
    ├── __init__.py
    └── api.py             # FastAPI application
```

## Monitoring

### Check Container Status
```bash
docker compose ps
```

### View Logs
```bash
docker compose logs -f momentum-api
```

### Health Check
```bash
docker exec momentum-signals-api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
```

## Troubleshooting

### Database Connection Errors

**Error:** `Can't connect to MySQL server`

**Solutions:**
1. Verify MySQL container is running: `docker ps | grep ac-database`
2. Check network connection: `docker network inspect azerothcore-wotlk_ac-network`
3. Test connection from API container:
   ```bash
   docker exec momentum-signals-api ping ac-database
   ```
4. Verify credentials in `.env` file

### Port Already in Use

**Error:** `Port 8000 is already allocated`

**Solution:** Change the port in `.env`:
```env
API_PORT=8001
```

## Performance Tuning

### Connection Pooling
Adjust in `service/api.py`:
```python
engine = create_engine(
    settings.MYSQL_DSN, 
    pool_pre_ping=True,
    pool_size=10,        # Increase for more concurrent connections
    max_overflow=20      # Increase for burst traffic
)
```

### Uvicorn Workers
Adjust in `Dockerfile`:
```dockerfile
CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## License

Same as parent project.
