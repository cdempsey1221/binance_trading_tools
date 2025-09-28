#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Start the NordVPN background service directly and run it in the background
echo "Starting NordVPN service..."
sudo /usr/sbin/nordvpnd &

# Wait for the service to start up and create its socket
sleep 5

#Login and set connection to OpenVPN
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

# Run your Python application using the virtual environment's Python executable
echo "Starting Python script..."
exec ./venv/bin/python3 binance_perp_notification.py
