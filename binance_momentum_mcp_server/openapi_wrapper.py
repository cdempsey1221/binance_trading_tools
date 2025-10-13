#!/usr/bin/env python3
"""
OpenAPI Wrapper for MCP Server

This FastAPI service wraps the MCP server tools as HTTP endpoints,
allowing Open WebUI to call them via standard REST API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
from datetime import datetime
import os

app = FastAPI(
    title="Momentum Signals API",
    description="Search and analyze cryptocurrency momentum trading signals. Query real-time market data including volume spikes, price movements, and momentum scores for Bitcoin, Ethereum, and other trading pairs.",
    version="0.1.0",
    servers=[
        {
            "url": "http://momentum-mcp-server-openapi:8001",
            "description": "Docker deployment"
        }
    ]
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://momentum-signals-api:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# HTTP client
http_client = httpx.AsyncClient(
    base_url=API_BASE_URL,
    timeout=API_TIMEOUT,
    follow_redirects=True
)


class SearchSignalsRequest(BaseModel):
    """Request parameters for searching momentum signals. Results include score breakdowns: volume_score, price_score, trend_score, quality_score, volatility_score."""
    symbol: Optional[str | list[str]] = Field(None, description="Filter by trading pair symbol. Can be a single symbol ('BTCUSDT') or a list of symbols (['BTCUSDT', 'ETHUSDT']). Leave empty to search all pairs.", examples=["BTCUSDT", ["BTCUSDT", "ETHUSDT"]])
    timeframe: Optional[str] = Field(None, description="Filter by detection timeframe (e.g., '15m', '1h', '4h'). This is the candle period the signal was detected on, not the price change period.", examples=["15m", "1h"])
    min_momentum_score: Optional[float] = Field(None, ge=0, le=10, description="Minimum momentum score from 0-10. Returns signals with score >= this value. Higher scores indicate stronger signals. Use integers: 7, 8, 9, or 10 for high-quality signals. Response includes volume_score, price_score, trend_score, quality_score breakdown.", examples=[7, 8, 9])
    min_price_change_1h: Optional[float] = Field(None, description="Minimum 1-hour price change percentage. Use positive values for upward moves (e.g., 1.5 = +1.5%). Use to find significant short-term price moves.", examples=[1.0, 2.0])
    min_price_change_4h: Optional[float] = Field(None, description="Minimum 4-hour price change percentage. Use positive values for upward moves (e.g., 2.0 = +2.0%). Use to find significant medium-term price moves.", examples=[2.0, 3.0])
    min_current_price: Optional[float] = Field(None, description="Minimum current price in USD. Use this to filter out very cheap coins (e.g., 0.01 to exclude coins under $0.01) or focus on higher-priced assets (e.g., 1.0 for coins over $1).", examples=[0.01, 1.0, 10.0])
    max_current_price: Optional[float] = Field(None, description="Maximum current price in USD. Use this to filter out expensive coins (e.g., 100 to exclude coins over $100) or focus on lower-priced assets (e.g., 1.0 for coins under $1).", examples=[1.0, 10.0, 100.0])
    price_vs_ema_21: Optional[str] = Field(None, description="Filter by price position relative to 21-day EMA. Use 'above' to find coins trading above their 21 EMA (bullish positioning), 'below' for coins under 21 EMA (bearish positioning), or 'at' for coins exactly at EMA. The 21 EMA is calculated from DAILY candles, not the detection timeframe. This helps identify trend alignment - momentum signals that occur while price is above the 21 EMA tend to be stronger. Example: Use 'above' to find momentum signals with bullish trend support.", examples=["above", "below", "at"])
    ema_trend_bias: Optional[str] = Field(None, description="Filter by overall EMA trend bias. Use 'bullish' to find signals where current price is ABOVE the 21-day EMA (uptrend support), 'bearish' for price BELOW 21 EMA (downtrend), or 'neutral' for price exactly at EMA. This is the same as price_vs_ema_21 but uses clearer terminology. The trend bias is determined from DAILY timeframe data. Example: Use 'bullish' to find momentum signals that align with the daily uptrend, or 'bearish' to find contrarian signals (momentum against the trend).", examples=["bullish", "bearish", "neutral"])
    min_tbqr: Optional[float] = Field(None, ge=0, le=1, description="Filter by minimum TBQR (Taker Buy Quote Ratio). TBQR measures buying pressure: 0-1 scale where >0.5 = bullish (more buyers hitting ask), <0.5 = bearish (more sellers hitting bid). Use 0.55+ to find signals with strong buying pressure. Use 0.6+ for very aggressive buying. Example: min_tbqr=0.6 finds signals where 60%+ of volume is from aggressive buyers.", examples=[0.5, 0.55, 0.6])
    min_tbqr_zscore: Optional[float] = Field(None, description="Filter by minimum TBQR Z-score (statistical significance). Z-score measures how unusual the buying pressure is vs recent 20-bar average. Use 1.0+ for above-average buying, 2.0+ for statistically significant buying pressure (95% confidence). Negative values indicate selling pressure. Example: min_tbqr_zscore=1.5 finds signals with unusually strong buying activity.", examples=[1.0, 1.5, 2.0])
    hours_ago: int = Field(24, ge=1, le=168, description="Only return signals from the last N hours. Default is 24 hours (last day).", examples=[1, 24, 48])
    sort_by: str = Field("timestamp_desc", description="Sort order: 'momentum_desc' (highest score first), 'timestamp_desc' (most recent first), 'volume_desc', or 'price_desc'", examples=["momentum_desc", "timestamp_desc"])
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results to return. Default 20, max 100.", examples=[5, 10, 20])

class HighScoresRequest(BaseModel):
    """Request parameters for getting top-scoring signals"""
    limit: int = Field(10, ge=1, le=50, description="Number of top signals to return. Gets the highest-scoring signals from the last hour. Default 10, max 50.", examples=[5, 10, 20])

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Momentum Signals MCP API",
        "version": "0.1.0",
        "description": "OpenAPI wrapper for MCP tools",
        "endpoints": {
            "/search": "Search momentum signals with filters",
            "/signal/{id}": "Get signal by ID",
            "/symbols": "List monitored trading pairs",
            "/top-signals": "Get recent high-scoring signals"
        }
    }


@app.get("/openapi.json")
async def get_openapi_spec():
    """Return OpenAPI specification"""
    return app.openapi()


@app.post("/search",
    summary="Search Momentum Signals",
    description="""Search for cryptocurrency momentum trading signals with filters for symbol, timeframe, score, time range, EMA trend alignment, and buying pressure (TBQR).
    
    Example queries:
    - Find signals with momentum_score >= 8 from last 4 hours
    - Find BTCUSDT signals with price_change_4hour > 2%
    - Get top 10 signals sorted by momentum_score
    - Find bullish momentum signals where price is ABOVE 21-day EMA (ema_trend_bias='bullish')
    - Find contrarian signals: momentum while price is BELOW 21 EMA (ema_trend_bias='bearish')
    - Combine filters: High-score signals with bullish EMA trend (min_momentum_score=8, ema_trend_bias='bullish')
    - Find signals with strong buying pressure (min_tbqr=0.6 means 60%+ aggressive buyers)
    - Find statistically significant buying pressure (min_tbqr_zscore=2.0 means 95% confidence)
    
    EMA Filters (Stage 1 - Data Collection):
    - price_vs_ema_21: Filter by price position ('above', 'below', 'at' the 21-day EMA from DAILY candles)
    - ema_trend_bias: Same as price_vs_ema_21 but uses clearer terms ('bullish', 'bearish', 'neutral')
    
    TBQR Filters (Buying Pressure - Data Collection):
    - min_tbqr: Filter by minimum taker buy ratio (0-1 scale, >0.5 = bullish buying pressure)
    - min_tbqr_zscore: Filter by statistical significance (>2.0 = highly significant buying)
    
    Returns: Full signal details including volume_score, price_score, trend_score, quality_score, volatility_score breakdown, plus EMA data (ema_21_daily, ema_50_daily, price_vs_ema_21, ema_trend_bias), and TBQR buying pressure metrics (tbqr_current, tbqr_zscore, tbqr_delta, quote_volume_zscore).""",
    response_description="List of matching momentum signals with detailed metrics including score breakdowns, EMA trend data, and TBQR buying pressure analysis",
    tags=["Signals"],
    responses={
        200: {"description": "Successful search, returns list of signals with EMA data"},
        422: {"description": "Invalid parameters - check that limit is a valid integer between 1-100, hours_ago is 1-168, ema_trend_bias is 'bullish'/'bearish'/'neutral', etc."}
    }
)
async def search_signals(request: SearchSignalsRequest):
    """
    Search momentum signals with optional filters.
    Returns signals sorted by your chosen criteria.
    """
    try:
        # Build query parameters
        params = {}
        
        # Time filter
        import time
        cutoff_timestamp = int((time.time() - (request.hours_ago * 3600)) * 1000)
        params["after_ts"] = cutoff_timestamp
        
        # Handle symbol filter - store for client-side filtering if list
        symbol_filter = None
        if request.symbol:
            if isinstance(request.symbol, str):
                # Single symbol - pass to API
                params["symbol"] = request.symbol.upper()
            else:
                # Multiple symbols - filter client-side
                symbol_filter = [s.upper() for s in request.symbol]
        
        if request.timeframe:
            params["timeframe"] = request.timeframe
        
        if request.min_current_price is not None:
            params["min_price"] = request.min_current_price
        
        if request.max_current_price is not None:
            params["max_price"] = request.max_current_price
        
        if request.price_vs_ema_21:
            params["price_vs_ema_21"] = request.price_vs_ema_21
        
        if request.ema_trend_bias:
            params["ema_trend_bias"] = request.ema_trend_bias
        
        if request.min_tbqr is not None:
            params["min_tbqr"] = request.min_tbqr
        
        if request.min_tbqr_zscore is not None:
            params["min_tbqr_zscore"] = request.min_tbqr_zscore
        
        # Sort mapping
        sort_map = {
            "momentum_desc": "momentum_desc",
            "timestamp_desc": "ts_desc",
            "volume_desc": "ts_desc",
            "price_desc": "ts_desc"
        }
        
        params["sort"] = sort_map.get(request.sort_by, "ts_desc")
        params["limit"] = request.limit
        
        # Call API
        response = await http_client.get("/alerts/search", params=params)
        response.raise_for_status()
        data = response.json()
        signals = data.get("items", [])
        
        # Apply symbol filter if multiple symbols requested
        if symbol_filter:
            signals = [s for s in signals if s.get("symbol", "").upper() in symbol_filter]
        
        # Apply momentum score filter (convert to int for comparison with database scores)
        if request.min_momentum_score is not None:
            min_score = int(request.min_momentum_score)
            signals = [s for s in signals if s.get("momentum_score", 0) >= min_score]
        
        # Apply price change filters (NEW!)
        if request.min_price_change_1h is not None:
            signals = [s for s in signals if s.get("price_change_1hour", 0) >= request.min_price_change_1h]
        
        if request.min_price_change_4h is not None:
            signals = [s for s in signals if s.get("price_change_4hour", 0) >= request.min_price_change_4h]
        
        # Client-side sorting for volume/price
        if request.sort_by == "volume_desc":
            signals.sort(key=lambda s: s.get("volume_spike_pct", 0), reverse=True)
        elif request.sort_by == "price_desc":
            signals.sort(key=lambda s: s.get("price_change_pct", 0), reverse=True)
        
        signals = signals[:request.limit]
        
        return {
            "count": len(signals),
            "timeframe_hours": request.hours_ago,
            "signals": signals
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")


@app.get("/signal/{signal_id}",
    summary="Get Signal by ID",
    description="Retrieve detailed information about a specific momentum signal including price analysis, volume metrics, and quality indicators.",
    response_description="Detailed signal information",
    tags=["Signals"]
)
async def get_signal(signal_id: int):
    """
    Get detailed information about a specific momentum signal by its ID.
    """
    try:
        response = await http_client.get(f"/alerts/{signal_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Signal ID {signal_id} not found")
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")


@app.get("/symbols",
    summary="List Trading Pairs",
    description="Get a list of all cryptocurrency trading pairs currently being monitored for momentum signals (e.g., BTCUSDT, ETHUSDT).",
    response_description="Array of trading pair symbols",
    tags=["Reference"]
)
async def list_symbols():
    """
    List all cryptocurrency trading pairs currently being monitored.
    """
    try:
        response = await http_client.get("/symbols")
        response.raise_for_status()
        symbols = response.json()
        return {
            "count": len(symbols),
            "symbols": symbols
        }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")


@app.post("/top-signals",
    summary="Get Top Signals",
    description="Get the highest-scoring momentum signals from the last hour. Use this to quickly find the strongest current trading opportunities.",
    response_description="Top-ranked momentum signals",
    tags=["Signals"]
)
async def get_top_signals(request: HighScoresRequest):
    """
    Get the highest-scoring momentum signals from the last hour.
    Perfect for finding the strongest current trading opportunities.
    """
    try:
        import time
        cutoff_timestamp = int((time.time() - 3600) * 1000)
        
        response = await http_client.get("/alerts/search", params={
            "after_ts": cutoff_timestamp,
            "sort": "momentum_desc",
            "limit": request.limit
        })
        response.raise_for_status()
        data = response.json()
        
        return {
            "count": len(data.get("items", [])),
            "signals": data.get("items", [])
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    try:
        # Test connection to underlying API
        response = await http_client.get("/healthz")
        response.raise_for_status()
        return {
            "status": "healthy",
            "api_connection": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "api_connection": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
