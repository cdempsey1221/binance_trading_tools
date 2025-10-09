#!/bin/sh

set -e

echo "=========================================="
echo "Binance Momentum Monitor - Docker Startup"
echo "=========================================="
echo ""

# Start the NordVPN background service
echo "🔒 Starting NordVPN service..."
sudo /usr/sbin/nordvpnd &

# Wait for the service to start up and create its socket
echo "⏳ Waiting for NordVPN daemon to initialize..."
sleep 15

# Check if NORDVPN_TOKEN is set
if [ -z "${NORDVPN_TOKEN}" ]; then
  echo "❌ Error: NORDVPN_TOKEN environment variable is not set"
  exit 1
fi

# Login to NordVPN
echo "🔐 Logging into NordVPN..."
if ! nordvpn login --token "${NORDVPN_TOKEN}"; then
  echo "❌ Error: NordVPN login failed"
  exit 1
fi

# Configure VPN settings
echo "⚙️  Configuring VPN settings..."
nordvpn set technology OpenVPN
nordvpn set protocol tcp

# Enable LAN discovery for Docker network
# echo "🔧 Enabling LAN discovery..."
# nordvpn set lan-discovery enable

# Whitelist Docker network subnet so it bypasses VPN
echo "🔧 Whitelisting Docker network (172.21.0.0/16)..."
nordvpn whitelist add subnet 172.21.0.0/16
echo "✅ Docker network (172.21.0.0/16) whitelisted - bypassing VPN"

# Connect to a NordVPN server in Portugal
echo "🌐 Connecting to NordVPN (Portugal - pt125)..."
if ! nordvpn connect pt125; then
  echo "❌ Error: NordVPN connection failed"
  exit 1
fi

# Verify connection
echo "✅ Successfully connected to NordVPN"
echo ""

# Display VPN status
echo "📊 VPN Status:"
nordvpn status
echo ""

# Check if DISCORD_WEBHOOK_URL is set
if [ -z "${DISCORD_WEBHOOK_URL}" ]; then
  echo "⚠️  Warning: DISCORD_WEBHOOK_URL environment variable is not set"
  echo "   Alerts will not be sent to Discord"
fi

# Display configuration
echo "=========================================="
echo "📋 Application Configuration:"
echo "   Timeframe: ${TIMEFRAME:-15m}"
echo "   Lookback Periods: ${LOOKBACK_PERIODS:-8}"
echo "   Volume Window: ${VOLUME_WINDOW_HOURS:-8} hours"
echo "   Volume Spike Threshold: ${VOLUME_SPIKE_THRESHOLD:-150.0}%"

# Calculate price change percentage for display (portable shell calculation)
PRICE_CHANGE_DECIMAL=${PRICE_CHANGE_THRESHOLD:-0.05}
PRICE_CHANGE_PERCENT=$(echo "$PRICE_CHANGE_DECIMAL" | awk '{printf "%.1f", $1 * 100}')
echo "   Price Change Threshold: ${PRICE_CHANGE_DECIMAL} (${PRICE_CHANGE_PERCENT}%)"

echo "   Min Hourly Volume: ${MIN_HOURLY_VOLUME:-1000} USD"
echo "   Alert Cooldown: ${ALERT_COOLDOWN:-30} minutes"
echo "   Log Level: ${LOG_LEVEL:-INFO}"
echo "=========================================="
echo ""

# Verify Python and dependencies
echo "🔍 Verifying Python environment..."
if ! ./venv/bin/python3 -c "from src.core.config import Config; print('✅ Imports successful')"; then
  echo "❌ Error: Python import validation failed"
  exit 1
fi

# Run the momentum scanner
echo "🚀 Starting Binance Momentum Monitor..."
echo "=========================================="
echo ""

# Execute main application (replaces this process)
exec ./venv/bin/python3 main.py
