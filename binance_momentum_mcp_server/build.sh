#!/bin/bash

# Build and push script for Momentum MCP Server OpenAPI Wrapper
set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default version from docker-compose.openapi.yml
DEFAULT_VERSION="0.1.0"
VERSION="${1:-$DEFAULT_VERSION}"

REPO="cdempsey1221/momentum-mcp-server-openapi"
IMAGE_NAME="$REPO:$VERSION"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MCP Server OpenAPI Wrapper - Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Version: ${YELLOW}$VERSION${NC}"
echo -e "Image: ${YELLOW}$IMAGE_NAME${NC}"
echo ""

# Step 1: Build with docker compose
echo -e "${GREEN}[1/2] Building Docker image...${NC}"
docker compose -f docker-compose.openapi.yml build
echo -e "Built: ${YELLOW}$IMAGE_NAME${NC}"

# Step 2: Push to Docker Hub
echo -e "${GREEN}[2/2] Pushing to Docker Hub...${NC}"
docker push "$IMAGE_NAME"
echo -e "${GREEN}✓ Pushed: $IMAGE_NAME${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "To deploy on server:"
echo -e "  ${YELLOW}docker pull $IMAGE_NAME${NC}"
echo -e "  ${YELLOW}docker compose -f docker-compose.openapi.yml up -d${NC}"
echo ""
