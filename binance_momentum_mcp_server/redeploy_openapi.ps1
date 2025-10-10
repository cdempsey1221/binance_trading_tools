# Redeploy both FastAPI and OpenAPI wrapper with healthchecks in Dockerfiles
Write-Host "Redeploying Momentum Signal services..." -ForegroundColor Cyan

# SSH and redeploy both services
ssh dempsey@app-greyjoy-01.poolspot.app @"
echo '=== Rebuilding FastAPI service ===' && \
cd /opt/deployment/momentum-signals-api && \
docker compose down && \
docker compose build && \
docker compose up -d && \
sleep 5 && \
echo '' && \
echo '=== Rebuilding OpenAPI wrapper ===' && \
cd /opt/deployment/momentum-mcp-server && \
docker compose -f docker-compose.openapi.yml down && \
docker compose -f docker-compose.openapi.yml build && \
docker compose -f docker-compose.openapi.yml up -d && \
sleep 5 && \
echo '' && \
echo '=== Container Status ===' && \
docker ps | grep momentum && \
echo '' && \
echo '=== FastAPI Health Check ===' && \
curl -s http://localhost:8000/healthz | python3 -m json.tool && \
echo '' && \
echo '=== OpenAPI Wrapper Health Check ===' && \
curl -s http://localhost:8001/healthz | python3 -m json.tool && \
echo '' && \
echo '=== OpenAPI Spec Test ===' && \
curl -s http://localhost:8001/openapi.json | python3 -c 'import json,sys; spec=json.load(sys.stdin); print(f\"Title: {spec[\"info\"][\"title\"]}\"); print(f\"Paths: {len(spec[\"paths\"])} endpoints\"); print(\"Endpoints:\"); [print(f\"  - {method.upper()} {path}\") for path,methods in spec[\"paths\"].items() for method in methods.keys()]' && \
echo '' && \
echo '=== Test Price Filter (signals under \$1) ===' && \
curl -s 'http://localhost:8001/search' -X POST -H 'Content-Type: application/json' -d '{\"max_current_price\": 1.0, \"hours_ago\": 24, \"limit\": 5}' | python3 -c 'import json,sys; data=json.load(sys.stdin); print(f\"Found {data[\"count\"]} signals under \$1\"); [print(f\"  - {s[\"symbol\"]}: \${s[\"current_price\"]:.8f}\") for s in data[\"signals\"][:3]]'
"@

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "`nNext steps for Open WebUI:" -ForegroundColor Yellow
Write-Host "1. Go to Settings → Functions" -ForegroundColor White
Write-Host "2. Delete existing 'Momentum Signals' function if present" -ForegroundColor White
Write-Host "3. Add new function with URL: http://momentum-mcp-server-openapi:8001/openapi.json" -ForegroundColor White
Write-Host "4. Go to Settings → Models → qwen2.5:7b" -ForegroundColor White
Write-Host "5. Enable the 'Momentum Signals' function toggle for this model" -ForegroundColor White
