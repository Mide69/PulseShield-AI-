#!/bin/bash

echo "🚀 PulseShield AI - Quick Start"
echo "================================"

if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials"
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Services started!"
echo ""
echo "📊 Access Points:"
echo "  Order Service:     http://localhost:3000/health"
echo "  Inventory Service: http://localhost:8000/health"
echo "  Notify Service:    http://localhost:3001/health"
echo "  AI Agent:          http://localhost:8001/health"
echo "  Prometheus:        http://localhost:9090"
echo "  Grafana:           http://localhost:3002 (admin/admin)"
echo ""
echo "🧪 Test the API:"
echo "  curl -X POST http://localhost:3000/orders \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"customer_name\":\"John\",\"product\":\"laptop\",\"quantity\":1}'"
