FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .
COPY .env .env

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# For Open WebUI integration
# The MCP server communicates via stdio, so it will be invoked by Open WebUI
CMD ["python", "server.py"]
