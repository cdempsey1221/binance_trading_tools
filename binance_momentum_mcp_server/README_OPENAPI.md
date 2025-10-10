# OpenAPI Wrapper for Momentum Signals MCP

## What is this?

This is a **REST API wrapper** that makes the Momentum Signals MCP server accessible via HTTP endpoints. It's specifically designed for **Open WebUI integration**, which requires OpenAPI/REST interfaces rather than stdio-based MCP servers.

## Why do we need this?

- **MCP servers** use stdio (standard input/output) for communication
- **Open WebUI** expects REST APIs with OpenAPI specifications
- This wrapper **bridges the gap** by translating HTTP requests into MCP tool calls

## Quick Start

### Build and Run

```bash
# Build the Docker image
docker compose -f docker-compose.openapi.yml build

# Start the service
docker compose -f docker-compose.openapi.yml up -d

# Check health
curl http://localhost:8001/healthz
```

### Test Endpoints

```bash
# List symbols
curl http://localhost:8001/symbols

# Search for signals
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"hours_ago": 24, "limit": 5}'

# Get OpenAPI spec
curl http://localhost:8001/openapi.json
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API information |
| `GET` | `/openapi.json` | OpenAPI 3.0 specification |
| `POST` | `/search` | Search momentum signals with filters |
| `GET` | `/signal/{id}` | Get specific signal by ID |
| `GET` | `/symbols` | List monitored trading pairs |
| `POST` | `/top-signals` | Get recent high-scoring signals |
| `GET` | `/healthz` | Health check |

## Configuration

Environment variables (set in `docker-compose.openapi.yml`):

```env
API_BASE_URL=http://momentum-signals-api:8000
API_TIMEOUT=30
```

## Open WebUI Integration

See [OPEN_WEBUI_SETUP.md](./OPEN_WEBUI_SETUP.md) for complete setup instructions.

**Quick version**:

1. Deploy this wrapper: `docker compose -f docker-compose.openapi.yml up -d`
2. In Open WebUI: Settings → Connections → Add Connection
3. Type: **OpenAPI**
4. URL: `http://momentum-mcp-openapi:8001/openapi.json`
5. Save and test!

## Architecture

```
┌─────────────────┐
│   Open WebUI    │
│   (Browser)     │
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│ OpenAPI Wrapper │  ← YOU ARE HERE
│    Port 8001    │
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│  FastAPI API    │
│    Port 8000    │
└────────┬────────┘
         │ SQL
         ↓
┌─────────────────┐
│  MySQL Database │
└─────────────────┘
```

## Files

- `openapi_wrapper.py` - FastAPI application
- `Dockerfile.openapi` - Container definition
- `docker-compose.openapi.yml` - Deployment config
- `OPEN_WEBUI_SETUP.md` - Complete integration guide

## Development

### Local Testing

```bash
# Install dependencies
pip install fastapi uvicorn httpx pydantic pydantic-settings

# Run locally (requires API at localhost:8000)
python openapi_wrapper.py

# Access at http://localhost:8001
```

### Docker Testing

```bash
# Build
docker build -f Dockerfile.openapi -t momentum-mcp-openapi:dev .

# Run
docker run --rm -p 8001:8001 \
  --network azerothcore-wotlk_ac-network \
  -e API_BASE_URL=http://momentum-signals-api:8000 \
  momentum-mcp-openapi:dev

# Test
curl http://localhost:8001/healthz
```

## Comparison: Original MCP vs OpenAPI Wrapper

| Feature | Original MCP Server | OpenAPI Wrapper |
|---------|-------------------|-----------------|
| **Protocol** | stdio (stdin/stdout) | HTTP REST |
| **Client** | Claude Desktop, MCP clients | Any HTTP client, Open WebUI |
| **Spec** | MCP protocol | OpenAPI 3.0 |
| **Authentication** | N/A | Can add Bearer tokens |
| **Use Case** | AI assistants with MCP support | Web UIs, API integrations |
| **Port** | N/A (stdio) | 8001 |

**Both connect to the same underlying FastAPI service** at port 8000.

## Troubleshooting

**Wrapper not starting:**
```bash
docker logs momentum-mcp-openapi
```

**Can't reach API service:**
```bash
docker exec momentum-mcp-openapi curl http://momentum-signals-api:8000/healthz
```

**OpenAPI spec issues:**
```bash
# View the spec
curl http://localhost:8001/openapi.json | jq

# Validate with Swagger Editor
open https://editor.swagger.io/
# Paste the spec
```

## License

Same as parent project.
