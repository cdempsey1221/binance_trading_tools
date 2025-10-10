# MCP Server - Deployment Configuration Summary

## ✅ Updated for Open WebUI on Docker Server

The MCP server has been configured for deployment on your Docker server (app-greyjoy-01) to work with Open WebUI.

## 🔧 Key Configuration Changes

### API Base URL

**Changed from:**
```env
API_BASE_URL=http://localhost:8000
```

**Changed to:**
```env
API_BASE_URL=http://momentum-signals-api:8000
```

**Why:** 
- MCP server runs in Docker container on same network as API
- Containers use service names for DNS resolution
- `localhost` would refer to the MCP container itself, not the API
- `momentum-signals-api` is the container name from FastAPI docker-compose.yml

## 📁 Files Ready for Deployment

Upload to `/opt/deployment/momentum-mcp-server/`:

```
momentum-mcp-server/
├── server.py                      # MCP server (API-based)
├── requirements.txt               # httpx, mcp, pydantic-settings
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Docker orchestration
├── .env                          # API_BASE_URL=http://momentum-signals-api:8000
├── .dockerignore                  # Build optimization
├── README.md                      # General documentation
├── OPEN_WEBUI_DEPLOYMENT.md      # Open WebUI specific guide
├── QUICKSTART.md                  # Quick setup (for local Claude Desktop)
└── REFACTORING_SUMMARY.md        # Technical details of API refactor
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Open WebUI Container (app-greyjoy-01)             │
│  - Invokes MCP tools                                │
└────────────────┬────────────────────────────────────┘
                 │ Docker exec or spawn
                 ▼
┌─────────────────────────────────────────────────────┐
│  Momentum MCP Server Container                      │
│  - Image: momentum-mcp-server:0.1.0                 │
│  - Network: azerothcore-wotlk_ac-network            │
│  - Tools: search, get_by_id, list_symbols, etc.     │
└────────────────┬────────────────────────────────────┘
                 │ HTTP API calls
                 │ http://momentum-signals-api:8000
                 ▼
┌─────────────────────────────────────────────────────┐
│  Momentum Signals API Container                     │
│  - Container: momentum-signals-api                  │
│  - Port: 8000 (internal)                            │
│  - Network: azerothcore-wotlk_ac-network            │
└────────────────┬────────────────────────────────────┘
                 │ SQL queries
                 │ mysql://172.21.0.3:3306
                 ▼
┌─────────────────────────────────────────────────────┐
│  MySQL Database Container                           │
│  - Container: ac-database                           │
│  - Database: momentum_signal_monitor                │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Deployment Commands

```bash
# On app-greyjoy-01 server

# 1. Upload files
cd /opt/deployment/momentum-mcp-server

# 2. Build image
docker compose build

# 3. Test connectivity
docker run --rm \
  --network azerothcore-wotlk_ac-network \
  momentum-mcp-server:0.1.0 \
  python -c "import httpx; print(httpx.get('http://momentum-signals-api:8000/healthz').json())"

# Should output: {'status': 'ok'}

# 4. Configure Open WebUI (see OPEN_WEBUI_DEPLOYMENT.md for details)
```

## 📊 Network Configuration

All containers must be on the same Docker network:

```yaml
networks:
  azerothcore-wotlk_ac-network:
    external: true
```

**Containers on this network:**
- `momentum-mcp-server` (MCP server)
- `momentum-signals-api` (FastAPI REST API)
- `ac-database` (MySQL)
- `momentum-scanner` (signal generator)

## 🎯 MCP Tools Available

Once integrated with Open WebUI:

1. **search_momentum_signals**
   - Parameters: symbol, timeframe, min_momentum_score, hours_ago, sort_by, limit
   - Returns: Filtered signals with full details

2. **get_signal_by_id**
   - Parameters: signal_id
   - Returns: Complete signal breakdown

3. **list_symbols**
   - Parameters: None
   - Returns: All monitored trading pairs

4. **get_recent_high_scores**
   - Parameters: limit
   - Returns: Top signals from last hour

## 🔑 Key Differences from Local Setup

| Aspect | Local (Claude Desktop) | Server (Open WebUI) |
|--------|----------------------|---------------------|
| **API URL** | `http://localhost:8000` | `http://momentum-signals-api:8000` |
| **MCP Location** | Python subprocess | Docker container |
| **Network** | Host network | Docker network |
| **Invocation** | Claude Desktop spawns process | Open WebUI spawns/execs container |
| **Configuration** | `claude_desktop_config.json` | Open WebUI MCP config |

## ✅ Deployment Checklist

- [x] Updated `API_BASE_URL` to use container name
- [x] Created `docker-compose.yml` with correct network
- [x] Updated `.env.example` with Docker config
- [x] Created `.dockerignore` for efficient builds
- [x] Created `OPEN_WEBUI_DEPLOYMENT.md` guide
- [ ] Upload files to server
- [ ] Build Docker image
- [ ] Test API connectivity
- [ ] Configure Open WebUI integration
- [ ] Test MCP tools

## 📝 Environment Variables

```env
# For Docker deployment (container-to-container)
API_BASE_URL=http://momentum-signals-api:8000
API_TIMEOUT=30

# For local development (host-to-container)
# API_BASE_URL=http://localhost:8000
# API_TIMEOUT=30
```

## 🎉 Result

Once deployed, you can ask Open WebUI natural language questions like:

- "What are the strongest momentum signals right now?"
- "Show me all BTCUSDT signals from the last 6 hours"
- "List all trading pairs being monitored"
- "Get details for signal ID 75"

Open WebUI will invoke the MCP tools, which call your FastAPI, which queries MySQL, and return beautifully formatted trading signals! 🚀

## 📚 Documentation Files

- **`README.md`** - General documentation (covers both local and Docker)
- **`OPEN_WEBUI_DEPLOYMENT.md`** - **START HERE** for Open WebUI deployment
- **`QUICKSTART.md`** - For local Claude Desktop setup (not your use case)
- **`REFACTORING_SUMMARY.md`** - Technical details of DB→API refactor

---

**Next step:** See `OPEN_WEBUI_DEPLOYMENT.md` for detailed deployment instructions! 🚀
