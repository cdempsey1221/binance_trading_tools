#!/bin/bash

# Binance Momentum Monitor - Quick Start Script

set -e

echo "🚀 Binance Momentum Monitor - Quick Start"
echo "=========================================="
echo ""

# Check if DISCORD_WEBHOOK_URL is set
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "❌ Error: DISCORD_WEBHOOK_URL environment variable is not set"
    echo ""
    echo "Please set your Discord webhook URL:"
    echo "  export DISCORD_WEBHOOK_URL='your_webhook_url'"
    echo ""
    echo "Or create a .env file with the required configuration"
    exit 1
fi

echo "✓ Discord webhook URL configured"
echo ""

# Check if dependencies are installed
if ! python -c "import pandas, requests, yaml" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
    echo ""
fi

# Check if pytest is available for testing
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest for testing..."
    pip install pytest
    echo "✓ Pytest installed"
    echo ""
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short
if [ $? -eq 0 ]; then
    echo "✓ All tests passed"
    echo ""
else
    echo "❌ Tests failed"
    exit 1
fi

# Display configuration
echo "📋 Configuration:"
echo "  Timeframe: ${TIMEFRAME:-15m}"
echo "  Lookback Periods: ${LOOKBACK_PERIODS:-8}"
echo "  Min Hourly Volume: ${MIN_HOURLY_VOLUME:-1000} USD"
echo "  Alert Cooldown: ${ALERT_COOLDOWN:-30} minutes"
echo "  Log Level: ${LOG_LEVEL:-INFO}"
echo ""

# Start the scanner
echo "🎯 Starting Momentum Scanner..."
echo ""
python main.py
