# Quick Start Guide - Momentum Signals MCP Server

## 🚀 Get Started in 5 Minutes

### Step 1: Start the FastAPI Server

First, make sure the REST API is running:

```powershell
cd c:\Home\Dempsey\Development\github\binance_trading_tools\binance_momentum_signal_api
docker compose up -d

# Verify it's working
curl http://localhost:8000/healthz
```

You should see: `{"status":"ok"}`

### Step 2: Install MCP Dependencies

```powershell
cd c:\Home\Dempsey\Development\github\binance_trading_tools\binance_momentum_mcp_server
pip install -r requirements.txt
```

### Step 3: Configure Environment

The `.env` file is already created with defaults. Only edit if your API runs elsewhere:

```env
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
```

### Step 4: Test API Connection

```powershell
python test_connection.py
```

You should see:
```
✅ API health check successful: {'status': 'ok'}
✅ Found 45 monitored trading pairs
✅ Found 10 signals in the last hour
✅ Top signal: BTCUSDT (score: 7)
✅ Successfully fetched signal by ID: 75
🎉 All tests passed!
```

### Step 5: Configure Claude Desktop

1. Open Claude Desktop config file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Create it if it doesn't exist

2. Copy the contents from `claude_desktop_config.json` in this directory

3. **Optional:** Change `API_BASE_URL` if your API runs on a different host/port

4. Save and restart Claude Desktop

### Step 6: Test in Claude

Open Claude Desktop and try asking:

**"What are the top momentum signals right now?"**

Claude should use the MCP tools and respond with real trading signals from your API! 🎉

## 🔧 Available Commands in Claude

Once configured, you can ask Claude:

- **"Show me the strongest momentum signals from the last hour"**
- **"What's the latest signal for BTCUSDT?"**
- **"List all trading pairs being monitored"**
- **"Find signals with momentum score 8 or higher"**
- **"Show me details for signal ID 75"**
- **"What are the highest volume spikes in the last 24 hours?"**

## 🐛 Troubleshooting

### MCP Tools Not Showing in Claude

1. Check config file is valid JSON (no trailing commas)
2. Verify absolute path to `server.py` 
3. Make sure Python is in your PATH
4. Completely quit and restart Claude Desktop (not just close window)

### API Connection Fails

1. Test manually: `python test_connection.py`
2. Check FastAPI is running:
   ```powershell
   cd ..\binance_momentum_signal_api
   docker compose ps
   ```
3. Test API directly: `curl http://localhost:8000/healthz`
4. Verify `API_BASE_URL` in `.env` is correct

### "No Signals Found"

1. Make sure momentum scanner is running and generating signals
2. Check API has data:
   ```powershell
   curl "http://localhost:8000/alerts/search?limit=5"
   ```
3. Check that signals are recent (use `after_ts` parameter)

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Learn about each MCP tool and its parameters
- Customize the server for your specific needs

## 🎯 Architecture

```
You ask Claude → Claude uses MCP → MCP calls FastAPI → API queries MySQL → Returns signals → Claude formats response
```

**Benefits:**
- ✅ MCP doesn't need database credentials
- ✅ API is the single source of truth
- ✅ Changes to API don't break MCP
- ✅ Better separation of concerns

That's it! You now have AI-powered access to your trading signals through a clean API architecture! 🚀
