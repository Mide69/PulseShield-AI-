# PulseShield AI

AI-Powered Microservices Health Monitoring & Auto-Remediation Platform

## Overview

PulseShield AI is a production-grade DevOps platform that monitors microservices health, detects anomalies using Prometheus metrics, and automatically triggers remediation actions using AI-driven decision making.

## Architecture

- **Microservices**: order-service, inventory-service, notify-service
- **AI Agent**: Monitors metrics and performs auto-remediation
- **Infrastructure**: AWS EKS, RDS PostgreSQL, ECR
- **Observability**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

## Tech Stack

- Cloud: AWS (EKS, RDS, ECR)
- Container: Docker, Kubernetes
- IaC: Terraform
- Languages: Node.js, Python
- Monitoring: Prometheus, Grafana
- AI: Claude API
- Notifications: Slack

## Quick Start

### Local Development

```bash
docker-compose up -d
```

### Deploy to AWS

```bash
cd infrastructure/environments/dev
terraform init
terraform apply

cd ../../../kubernetes
helm install pulseshield ./helm/pulseshield
```

## Services

- **api-gateway**: Nginx reverse proxy (Port 80)
- **order-service**: Order management API (Port 3000)
- **inventory-service**: Inventory management API (Port 8000)
- **notify-service**: Notification handler (Port 3001)
- **ai-agent-service**: AI-powered monitoring agent (Port 8001)

## Project Structure

```
pulseshield-ai/
├── services/              # Microservices
├── infrastructure/        # Terraform IaC
├── kubernetes/           # K8s manifests & Helm
├── monitoring/           # Prometheus & Grafana
├── .github/workflows/    # CI/CD pipelines
└── docs/                 # Documentation
```

## Environment Variables

See `.env.example` in each service directory.

## License

MIT
