#!/bin/bash
# ============================================================
#  PulseShield-AI — Service Health Test (Git Bash / Windows)
#  Run with:  bash test_pulseshield_gitbash.sh
# ============================================================

PASS="[PASS]"
FAIL="[FAIL]"
WARN="[WARN]"

check_http() {
  local name="$1"
  local url="$2"

  result=$(curl -s -o /tmp/ps_resp.txt -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
  body=$(cat /tmp/ps_resp.txt 2>/dev/null | tr -d '\r\n' | cut -c1-150)

  if [[ "$result" =~ ^(200|301|302|303)$ ]]; then
    echo "$PASS  $name"
    echo "       URL   : $url"
    echo "       HTTP  : $result"
    echo "       Body  : ${body:0:120}"
  elif [[ "$result" == "000" ]]; then
    echo "$FAIL  $name"
    echo "       URL   : $url"
    echo "       ERROR : No connection / timeout"
  else
    echo "$WARN  $name"
    echo "       URL   : $url"
    echo "       HTTP  : $result"
    echo "       Body  : ${body:0:120}"
  fi
  echo ""
}

check_tcp() {
  local name="$1"
  local port="$2"

  if curl -s --max-time 3 "telnet://localhost:$port" > /dev/null 2>&1; then
    echo "$PASS  $name (localhost:$port) — TCP OPEN"
  else
    curl -s --connect-timeout 3 "http://localhost:$port" > /dev/null 2>&1
    code=$?
    if [[ $code -eq 7 ]]; then
      echo "$FAIL  $name (localhost:$port) — Connection refused"
    elif [[ $code -eq 28 ]]; then
      echo "$FAIL  $name (localhost:$port) — Timeout"
    else
      echo "$PASS  $name (localhost:$port) — TCP OPEN (HTTP responded)"
    fi
  fi
  echo ""
}

echo ""
echo "============================================="
echo "   PulseShield-AI  —  Health Check"
echo "   $(date)"
echo "============================================="
echo ""

echo "----------------------------------------------"
echo " API GATEWAY (port 80)"
echo "----------------------------------------------"
check_http "API Gateway root"         "http://localhost:80"
check_http "API Gateway /health"      "http://localhost:80/health"
check_http "Gateway → /orders"        "http://localhost:80/orders"
check_http "Gateway → /inventory"     "http://localhost:80/inventory"
check_http "Gateway → /notify"        "http://localhost:80/notify"

echo "----------------------------------------------"
echo " ORDER SERVICE (port 3000)"
echo "----------------------------------------------"
check_http "Order Service root"       "http://localhost:3000"
check_http "Order Service /health"    "http://localhost:3000/health"
check_http "Order Service /orders"    "http://localhost:3000/orders"

echo "----------------------------------------------"
echo " NOTIFY SERVICE (port 3001)"
echo "----------------------------------------------"
check_http "Notify Service root"      "http://localhost:3001"
check_http "Notify Service /health"   "http://localhost:3001/health"

echo "----------------------------------------------"
echo " INVENTORY SERVICE (port 8000)"
echo "----------------------------------------------"
check_http "Inventory root"           "http://localhost:8000"
check_http "Inventory /health"        "http://localhost:8000/health"
check_http "Inventory /docs"          "http://localhost:8000/docs"
check_http "Inventory /items"         "http://localhost:8000/items"

echo "----------------------------------------------"
echo " GRAFANA (port 3002)"
echo "----------------------------------------------"
check_http "Grafana UI"               "http://localhost:3002"
check_http "Grafana /login"           "http://localhost:3002/login"
check_http "Grafana /api/health"      "http://localhost:3002/api/health"

echo "----------------------------------------------"
echo " PROMETHEUS (port 9090)"
echo "----------------------------------------------"
check_http "Prometheus UI"            "http://localhost:9090"
check_http "Prometheus /metrics"      "http://localhost:9090/metrics"
check_http "Prometheus /api/v1/targets"        "http://localhost:9090/api/v1/targets"
check_http "Prometheus /api/v1/query?query=up" "http://localhost:9090/api/v1/query?query=up"

echo "----------------------------------------------"
echo " POSTGRESQL (port 5432)"
echo "----------------------------------------------"
check_tcp "PostgreSQL" "5432"

echo "============================================="
echo "  Done. Check [FAIL] items above."
echo "  Tip: docker-compose logs <service> for details"
echo "============================================="
