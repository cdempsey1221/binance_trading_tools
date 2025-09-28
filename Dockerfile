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

# Update the package list and install the NordVPN package with the -y flag
RUN apt-get update && \
    apt-get install -y --no-install-recommends nordvpn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies in a virtual environment
COPY requirements.txt .
RUN python3 -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

COPY binance_perp_notification.py .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
