# Momentum Signals MCP Server

Model Context Protocol (MCP) server that provides Claude Desktop with direct access to cryptocurrency momentum trading signals stored in your MySQL database.

## Features

🔧 **MCP Tools for Claude:**
- `search_momentum_signals` - Search signals with flexible filters
- `get_signal_by_id` - Get detailed signal information
- `list_symbols` - List all monitored trading pairs
- `get_recent_high_scores` - Get top signals from last hour

📊 **Rich Signal Data:**
- Momentum scores and stage analysis
- Volume spike detection and z-scores
- Price action across multiple timeframes
- Score breakdowns (volume, price, trend, quality)
- Trend alignment and quality indicators

## Prerequisites

- Python 3.11+
- **Momentum Signals FastAPI** (from `binance_momentum_signal_api`) running on http://localhost:8000
- Claude Desktop (for MCP integration)

## Architecture

The MCP server acts as a client to the FastAPI REST API:

```
Claude Desktop → MCP Server → FastAPI REST API → MySQL Database
```

**Why this design?**
- ✅ Single source of truth (API layer)
- ✅ No direct database credentials needed in MCP
- ✅ Easier to maintain and update
- ✅ Better separation of concerns

## Setup

### 1. Start the FastAPI Server

First, make sure the REST API is running:

```bash
cd ../binance_momentum_signal_api
docker compose up -d

# Verify it's working
curl http://localhost:8000/healthz
```

### 2. Install MCP Dependencies

```bash
cd ../binance_momentum_mcp_server
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if your API runs on a different URL:
```env
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
```

### 4. Test the Connection

```bash
python test_connection.py
```

You should see:
```
✅ API health check successful
✅ Found X monitored trading pairs
✅ Found Y signals in the last hour
✅ Top signal: BTCUSDT (score: 7)
🎉 All tests passed!
```

## Claude Desktop Integration

### Configure Claude Desktop

Edit your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the MCP server:

```json
{
  "mcpServers": {
    "momentum-signals": {
      "command": "python",
      "args": [
        "c:/Home/Dempsey/Development/github/binance_trading_tools/binance_momentum_mcp_server/server.py"
      ],
      "env": {
        "API_BASE_URL": "http://localhost:8000",
        "API_TIMEOUT": "30"
      }
    }
  }
}
```

**Important:** Use absolute paths. If your API runs on a different host/port, update `API_BASE_URL`.

### Restart Claude Desktop

After saving the config, restart Claude Desktop. You should see the MCP server tools available in the chat.

## Usage Examples

### In Claude Desktop

Once configured, you can ask Claude natural language questions:

**"What are the strongest momentum signals right now?"**
- Claude will use `get_recent_high_scores` tool

**"Show me all BTCUSDT signals from the last 24 hours"**
- Claude will use `search_momentum_signals` with symbol filter

**"What trading pairs are being monitored?"**
- Claude will use `list_symbols` tool

**"Get details for signal ID 75"**
- Claude will use `get_signal_by_id` tool

**"Find all signals with momentum score 8 or higher from the last 6 hours"**
- Claude will use `search_momentum_signals` with filters

## Docker Deployment (Optional)

Docker isn't typically used for MCP servers since they run via stdio with Claude Desktop. However, you can test locally if needed.

## Architecture

```
┌──────────────────────────────┐
│   Claude Desktop (User)      │
└──────────────┬───────────────┘
               │ MCP (stdio)
               ▼
┌──────────────────────────────┐
│   MCP Server (server.py)     │
└──────────────┬───────────────┘
               │ HTTP REST API
               ▼
┌──────────────────────────────┐
│   FastAPI Server             │
│   (momentum-signals-api)     │
└──────────────┬───────────────┘
               │ SQL Queries
               ▼
┌──────────────────────────────┐
│   MySQL Database             │
│   momentum_signal_monitor    │
└──────────────────────────────┘
```

**Benefits of this architecture:**
- MCP doesn't need database credentials
- API handles all data access logic
- Changes to API don't require MCP updates
- Better separation of concerns

## Tool Details

### search_momentum_signals

Search for trading signals with optional filters.

**Parameters:**
- `symbol` (optional): Trading pair (e.g., "BTCUSDT")
- `timeframe` (optional): Candle timeframe (e.g., "15m", "1h")
- `min_momentum_score` (optional): Minimum score 0-10
- `hours_ago` (optional): Look back period (default: 24)
- `sort_by` (optional): Sort order - momentum_desc, timestamp_desc, volume_desc, price_desc
- `limit` (optional): Max results 1-100 (default: 20)

**Returns:** Formatted list of matching signals with full details

### get_signal_by_id

Get complete details for a specific signal.

**Parameters:**
- `signal_id` (required): Database ID of the signal

**Returns:** Detailed breakdown including price analysis, volume metrics, score components

### list_symbols

Get all monitored trading pairs.

**Parameters:** None

**Returns:** List of symbols (e.g., BTCUSDT, ETHUSDT, etc.)

### get_recent_high_scores

Get top-scoring signals from the last hour.

**Parameters:**
- `limit` (optional): Number of results (default: 10, max: 50)

**Returns:** Top signals sorted by momentum score and volume

## Troubleshooting

### MCP Server Not Showing in Claude

1. Check Claude Desktop config file syntax (valid JSON)
2. Verify absolute path to `server.py` is correct
3. Check that Python is in your PATH
4. Restart Claude Desktop completely (quit, don't just close window)

### API Connection Errors

**Error:** "Connection refused" or "Cannot connect to API"

**Solution:**
1. Make sure FastAPI server is running:
   ```bash
   cd ../binance_momentum_signal_api
   docker compose ps
   ```
2. Test API directly:
   ```bash
   curl http://localhost:8000/healthz
   ```
3. Check `API_BASE_URL` in your `.env` file
4. If API runs on different host, update the URL (e.g., `http://app-greyjoy-01:8000`)

### No Signals Returned

**Error:** "No momentum signals found"

**Solution:**
1. Check if momentum scanner is running and generating signals
2. Verify API has data:
   ```bash
   curl "http://localhost:8000/alerts/search?limit=5"
   ```
3. Check database has recent data (via API container):
   ```bash
   docker exec momentum-signals-api curl http://localhost:8000/symbols
   ```

## Development

### Testing Tools Locally

You can test the MCP tools using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python server.py
```

This opens a web UI to test tool execution.

### Adding New Tools

1. Add tool definition to `handle_list_tools()`
2. Implement tool function
3. Add case to `handle_call_tool()`
4. Test with MCP Inspector

## Security Notes

- MCP server runs locally on your machine
- Database credentials stored in environment variables
- No network exposure (stdio only)
- Runs with non-root user in Docker

## Version

Current version: **0.1.0**

## License

Same as parent project.
