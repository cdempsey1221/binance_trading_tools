FROM ubuntu:24.04

# Install Python, curl, and the necessary tools for NordVPN.
# Also install python3-venv to create a virtual environment.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    sudo \
    wget \
    gnupg \
    apt-transport-https \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Manually add the NordVPN repository and public key
RUN wget -qO- https://repo.nordvpn.com/gpg/nordvpn_public.asc | gpg --dearmor | sudo tee /usr/share/keyrings/nordvpn-archive-keyring.gpg > /dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/nordvpn-archive-keyring.gpg] https://repo.nordvpn.com/deb/nordvpn/debian stable main" | sudo tee /etc/apt/sources.list.d/nordvpn.list

# Update the package list and install the NordVPN package
RUN apt-get update && \
    apt-get install -y --no-install-recommends nordvpn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python3 -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy all application files and directories
COPY src/ ./src/
COPY config/ ./config/
COPY main.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Health check - verify Python and core imports work
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD ./venv/bin/python3 -c "from src.core.config import Config; import sys; sys.exit(0)" || exit 1

# Run application via entrypoint (handles NordVPN + app startup)
ENTRYPOINT ["/app/entrypoint.sh"]
