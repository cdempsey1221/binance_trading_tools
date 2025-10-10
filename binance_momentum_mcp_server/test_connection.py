#!/usr/bin/env python3
"""
Quick test script to verify MCP server can connect to API
and query signals without running full MCP protocol.
"""

import httpx
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_BASE_URL: str = "http://localhost:8000"
    API_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"


def test_api_connection():
    """Test API connection"""
    print("Testing API connection...")
    
    try:
        settings = Settings()
        client = httpx.Client(
            base_url=settings.API_BASE_URL,
            timeout=settings.API_TIMEOUT
        )
        
        # Test health endpoint
        response = client.get("/healthz")
        response.raise_for_status()
        print(f"✅ API health check successful: {response.json()}")
        
        # Get symbols
        response = client.get("/symbols")
        response.raise_for_status()
        symbols = response.json()
        print(f"✅ Found {len(symbols)} monitored trading pairs")
        
        # Get recent signals
        import time
        cutoff = int((time.time() - 3600) * 1000)  # Last hour
        response = client.get("/alerts/search", params={
            "after_ts": cutoff,
            "sort": "momentum_desc",
            "limit": 5
        })
        response.raise_for_status()
        data = response.json()
        signals = data.get("items", [])
        print(f"✅ Found {len(signals)} signals in the last hour")
        
        if signals:
            top = signals[0]
            print(f"✅ Top signal: {top['symbol']} (score: {top['momentum_score']})")
        
        # Test get by ID (if we have signals)
        if signals:
            signal_id = signals[0]["id"]
            response = client.get(f"/alerts/{signal_id}")
            response.raise_for_status()
            print(f"✅ Successfully fetched signal by ID: {signal_id}")
        
        client.close()
        print("\n🎉 All tests passed! MCP server should work correctly.")
        return True
        
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Make sure the FastAPI server is running on {settings.API_BASE_URL}")
        print(f"2. Check .env file has correct API_BASE_URL")
        print(f"3. Verify network connectivity to API server")
        print(f"\nTo start the API server:")
        print(f"   cd ../binance_momentum_signal_api")
        print(f"   docker compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_api_connection()
    exit(0 if success else 1)
