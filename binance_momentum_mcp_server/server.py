#!/usr/bin/env python3
"""
Momentum Signals MCP Server

Model Context Protocol server that provides Claude Desktop access to 
cryptocurrency momentum trading signals via REST API.

Tools provided:
- search_momentum_signals: Search signals with filters
- get_signal_by_id: Get specific signal details
- list_symbols: List all monitored trading pairs
- get_recent_high_scores: Get top signals from recent period
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, Any
import httpx

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration from environment variables"""
    # Default is for Docker deployment - override for local development
    API_BASE_URL: str = "http://momentum-signals-api:8000"
    API_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()

# Initialize MCP server
app = Server("momentum-signals-mcp")

# HTTP client for API calls
http_client: httpx.AsyncClient = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            base_url=settings.API_BASE_URL,
            timeout=settings.API_TIMEOUT,
            follow_redirects=True
        )
    return http_client


def format_signal_summary(signal: dict) -> str:
    """Format a signal as a human-readable summary"""
    lines = [
        f"🎯 {signal['symbol']} ({signal['timeframe']}) - Score: {signal['momentum_score']}/10",
        f"   Stage: {signal['momentum_stage']}",
        f"   Price Change: {signal['price_change_pct']:.2f}%",
        f"   Volume Spike: {signal['volume_spike_pct']:.2f}%",
        f"   Volatility: {signal['volatility']:.2f}%",
        "",
        f"   📊 Score Breakdown:",
        f"      Volume: {signal['volume_score']}/2",
        f"      Price: {signal['price_score']}/3",
        f"      Trend: {signal['trend_score']}/3",
        f"      Quality: {signal['quality_score']}/2",
        "",
        f"   Trends Aligned: {'✅' if signal['trends_aligned'] else '❌'}",
        f"   Volume Building: {'✅' if signal['volume_building'] else '❌'}",
        f"   Volume/Price Sync: {'✅' if signal['volume_price_sync'] else '❌'}",
        "",
        f"   Timestamp: {datetime.fromtimestamp(signal['candle_timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')}",
        f"   Current Price: ${signal['current_price']:.8f}",
        f"   ID: {signal['id']}",
    ]
    return "\n".join(lines)


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="search_momentum_signals",
            description=(
                "Search cryptocurrency momentum trading signals with optional filters. "
                "Returns signals sorted by your chosen criteria. Use this to find "
                "trading opportunities based on volume, price action, and momentum."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Filter by trading pair (e.g., 'BTCUSDT', 'ETHUSDT')"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Filter by timeframe (e.g., '15m', '1h', '4h')"
                    },
                    "min_momentum_score": {
                        "type": "integer",
                        "description": "Minimum momentum score (0-10). Higher = stronger signal"
                    },
                    "hours_ago": {
                        "type": "integer",
                        "description": "Only return signals from last N hours (default: 24)",
                        "default": 24
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["momentum_desc", "timestamp_desc", "volume_desc", "price_desc"],
                        "description": "Sort order (default: timestamp_desc)",
                        "default": "timestamp_desc"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (1-100, default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="get_signal_by_id",
            description="Get detailed information about a specific momentum signal by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "signal_id": {
                        "type": "integer",
                        "description": "The ID of the signal to retrieve"
                    }
                },
                "required": ["signal_id"]
            }
        ),
        Tool(
            name="list_symbols",
            description=(
                "List all cryptocurrency trading pairs currently being monitored. "
                "Returns a list of symbols like BTCUSDT, ETHUSDT, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_recent_high_scores",
            description=(
                "Get the highest-scoring momentum signals from the last hour. "
                "Perfect for finding the strongest current trading opportunities."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top signals to return (default: 10)",
                        "default": 10
                    }
                }
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    
    try:
        if name == "search_momentum_signals":
            return await search_momentum_signals(
                symbol=arguments.get("symbol"),
                timeframe=arguments.get("timeframe"),
                min_momentum_score=arguments.get("min_momentum_score"),
                hours_ago=arguments.get("hours_ago", 24),
                sort_by=arguments.get("sort_by", "timestamp_desc"),
                limit=arguments.get("limit", 20)
            )
        
        elif name == "get_signal_by_id":
            return await get_signal_by_id(arguments["signal_id"])
        
        elif name == "list_symbols":
            return await list_symbols()
        
        elif name == "get_recent_high_scores":
            return await get_recent_high_scores(arguments.get("limit", 10))
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def search_momentum_signals(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    min_momentum_score: Optional[int] = None,
    hours_ago: int = 24,
    sort_by: str = "timestamp_desc",
    limit: int = 20
) -> list[TextContent]:
    """Search momentum signals with filters via API"""
    
    client = await get_http_client()
    
    # Build query parameters
    params = {}
    
    # Time filter
    cutoff_timestamp = int((time.time() - (hours_ago * 3600)) * 1000)
    params["after_ts"] = cutoff_timestamp
    
    # Symbol filter
    if symbol:
        params["symbol"] = symbol.upper()
    
    # Timeframe filter
    if timeframe:
        params["timeframe"] = timeframe
    
    # Momentum score filter (API uses min_signal which is signal_strength, not momentum_score)
    # For now, we'll filter after fetching. API could be enhanced to support min_momentum_score
    
    # Sort mapping
    sort_map = {
        "momentum_desc": "momentum_desc",
        "timestamp_desc": "ts_desc",
        "volume_desc": "ts_desc",  # API doesn't have volume sort, use timestamp
        "price_desc": "ts_desc"     # API doesn't have price sort, use timestamp
    }
    params["sort"] = sort_map.get(sort_by, "ts_desc")
    
    # Limit
    params["limit"] = min(max(1, limit), 100)
    
    try:
        # Call API
        response = await client.get("/alerts/search", params=params)
        response.raise_for_status()
        data = response.json()
        
        signals = data.get("items", [])
        
        # Apply momentum score filter if specified (since API doesn't support it directly)
        if min_momentum_score is not None:
            signals = [s for s in signals if s.get("momentum_score", 0) >= min_momentum_score]
        
        # Client-side sorting for volume/price if needed
        if sort_by == "volume_desc":
            signals.sort(key=lambda s: s.get("volume_spike_pct", 0), reverse=True)
        elif sort_by == "price_desc":
            signals.sort(key=lambda s: s.get("price_change_pct", 0), reverse=True)
        
        # Apply limit after filtering
        signals = signals[:limit]
        
    except httpx.HTTPError as e:
        return [TextContent(
            type="text",
            text=f"Error calling API: {str(e)}"
        )]
    
    # Format response
    if not signals:
        filter_desc = []
        if symbol:
            filter_desc.append(f"symbol={symbol}")
        if timeframe:
            filter_desc.append(f"timeframe={timeframe}")
        if min_momentum_score:
            filter_desc.append(f"score>={min_momentum_score}")
        filter_desc.append(f"last {hours_ago}h")
        
        return [TextContent(
            type="text",
            text=f"No momentum signals found matching criteria: {', '.join(filter_desc)}"
        )]
    
    # Build summary
    summary_lines = [
        f"Found {len(signals)} momentum signal(s):",
        f"Timeframe: Last {hours_ago} hours",
        ""
    ]
    
    for signal in signals:
        summary_lines.append(format_signal_summary(signal))
        summary_lines.append("\n" + "="*80 + "\n")
    
    return [TextContent(type="text", text="\n".join(summary_lines))]


async def get_signal_by_id(signal_id: int) -> list[TextContent]:
    """Get a specific signal by ID via API"""
    
    client = await get_http_client()
    
    try:
        response = await client.get(f"/alerts/{signal_id}")
        response.raise_for_status()
        signal = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(type="text", text=f"Signal ID {signal_id} not found")]
        return [TextContent(type="text", text=f"Error fetching signal: {str(e)}")]
    except httpx.HTTPError as e:
        return [TextContent(type="text", text=f"Error calling API: {str(e)}")]
    
    # Detailed format
    output = f"""
📊 Momentum Signal Details - ID: {signal['id']}

Symbol: {signal['symbol']}
Timeframe: {signal['timeframe']}
Momentum Score: {signal['momentum_score']}/10
Stage: {signal['momentum_stage']}

💰 Price Analysis:
   Current Price: ${signal['current_price']:.8f}
   Price Change: {signal['price_change_pct']:.2f}%
   Current Bar: {signal['price_change_current_bar']:.2f}%
   1 Hour: {signal['price_change_1hour']:.2f}%
   2 Hour: {signal['price_change_2hour']:.2f}%
   4 Hour: {signal['price_change_4hour']:.2f}%

📈 Volume Analysis:
   Volume Spike: {signal['volume_spike_pct']:.2f}%
   Volume Building: {'Yes' if signal['volume_building'] else 'No'}
   Current Volume: {signal['current_volume']:,.0f}
   Average Volume: {signal['avg_volume']:,.0f}
   Z-Score: {signal['volume_zscore']:.2f}

📊 Score Breakdown:
   Volume Score: {signal['volume_score']}/2
   Price Score: {signal['price_score']}/3
   Trend Score: {signal['trend_score']}/3
   Quality Score: {signal['quality_score']}/2
   Volatility: {signal['volatility_score']:.2f}%

✅ Quality Indicators:
   Trends Aligned: {'Yes' if signal['trends_aligned'] else 'No'}
   Volume/Price Sync: {'Yes' if signal['volume_price_sync'] else 'No'}
   Volatility: {signal['volatility']:.2f}%

⏰ Timing:
   Candle Time: {datetime.fromtimestamp(signal['candle_timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S UTC')}
   Detected At: {signal['created_at']}
"""
    
    return [TextContent(type="text", text=output.strip())]


async def list_symbols() -> list[TextContent]:
    """List all monitored trading pairs via API"""
    
    client = await get_http_client()
    
    try:
        response = await client.get("/symbols")
        response.raise_for_status()
        symbols = response.json()
    except httpx.HTTPError as e:
        return [TextContent(type="text", text=f"Error calling API: {str(e)}")]
    
    if not symbols:
        return [TextContent(type="text", text="No trading pairs currently monitored")]
    
    output = f"📊 Monitored Trading Pairs ({len(symbols)} total):\n\n"
    output += ", ".join(symbols)
    
    return [TextContent(type="text", text=output)]


async def get_recent_high_scores(limit: int = 10) -> list[TextContent]:
    """Get highest-scoring signals from the last hour via API"""
    
    client = await get_http_client()
    
    # Last 1 hour
    cutoff_timestamp = int((time.time() - 3600) * 1000)
    limit = min(max(1, limit), 50)  # Clamp between 1 and 50
    
    try:
        response = await client.get("/alerts/search", params={
            "after_ts": cutoff_timestamp,
            "sort": "momentum_desc",
            "limit": limit
        })
        response.raise_for_status()
        data = response.json()
        signals = data.get("items", [])
    except httpx.HTTPError as e:
        return [TextContent(
            type="text",
            text=f"Error calling API: {str(e)}"
        )]
    
    if not signals:
        return [TextContent(
            type="text",
            text="No momentum signals detected in the last hour"
        )]
    
    summary_lines = [
        f"🔥 Top {len(signals)} Momentum Signals (Last Hour):",
        ""
    ]
    
    for i, signal in enumerate(signals, 1):
        summary_lines.append(f"\n#{i}")
        summary_lines.append(format_signal_summary(signal))
        summary_lines.append("="*80)
    
    return [TextContent(type="text", text="\n".join(summary_lines))]


async def main():
    """Run the MCP server"""
    global http_client
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="momentum-signals-mcp",
                    server_version="0.1.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )
    finally:
        # Cleanup HTTP client
        if http_client is not None:
            await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
