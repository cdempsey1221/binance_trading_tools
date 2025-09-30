#!/bin/sh

set -e

# Start the NordVPN background service directly and run it in the background
echo "Starting NordVPN service..."
sudo /usr/sbin/nordvpnd &

# Wait for the service to start up and create its socket
sleep 5

echo "Logging into NordVPN..."
nordvpn login --token "${NORDVPN_TOKEN}"

echo "Using TCP and Setting VPN technology to OpenVPN..."
nordvpn set technology OpenVPN
nordvpn set protocol tcp

# Connect to a NordVPN server in Portugal
echo "Connecting to NordVPN..."
if ! nordvpn connect pt125; then
  echo "Error: NordVPN connection failed. Exiting."
  exit 1
fi

echo "Successfully connected to NordVPN."

# Run the momentum scanner script using the virtual environment
echo "Starting momentum_scanner.py script..."
exec ./venv/bin/python3 momentum_scanner.py
