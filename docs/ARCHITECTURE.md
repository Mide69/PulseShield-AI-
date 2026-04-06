# PulseShield AI - Architecture

## System Overview

PulseShield AI is an AI-powered microservices monitoring and auto-remediation platform that continuously monitors service health and automatically resolves issues using Claude AI.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    EKS Cluster                         │ │
│  │                                                        │ │
│  │  ┌──────────────┐      ┌──────────────┐             │ │
│  │  │ API Gateway  │─────▶│ Order Service│             │ │
│  │  │   (Nginx)    │      │   (Node.js)  │             │ │
│  │  └──────────────┘      └──────────────┘             │ │
│  │         │                      │                      │ │
│  │         │              ┌──────────────┐             │ │
│  │         └─────────────▶│  Inventory   │             │ │
│  │                        │   Service    │             │ │
│  │                        │  (Python)    │             │ │
│  │                        └──────────────┘             │ │
│  │                                                      │ │
│  │  ┌──────────────┐      ┌──────────────┐           │ │
│  │  │ AI Agent     │─────▶│   Notify     │           │ │
│  │  │  Service     │      │   Service    │           │ │
│  │  │  (Python)    │      │  (Node.js)   │           │ │
│  │  └──────────────┘      └──────────────┘           │ │
│  │         │                                           │ │
│  │         │                                           │ │
│  │         ▼                                           │ │
│  │  ┌──────────────┐                                  │ │
│  │  │  Prometheus  │                                  │ │
│  │  │   Metrics    │                                  │ │
│  │  └──────────────┘                                  │ │
│  │         │                                           │ │
│  │         ▼                                           │ │
│  │  ┌──────────────┐                                  │ │
│  │  │   Grafana    │                                  │ │
│  │  │  Dashboard   │                                  │ │
│  │  └──────────────┘                                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │     RDS      │         │     ECR      │            │
│  │  PostgreSQL  │         │  Container   │            │
│  │              │         │  Registry    │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │   Claude API     │
         │  (Anthropic)     │
         └──────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  Slack Webhook   │
         └──────────────────┘
```

## Component Details

### Microservices

**API Gateway (Nginx)**
- Entry point for external traffic
- Routes requests to backend services
- Load balancing

**Order Service (Node.js)**
- Manages customer orders
- PostgreSQL database integration
- Exposes Prometheus metrics
- REST API endpoints

**Inventory Service (Python FastAPI)**
- Manages product inventory
- In-memory data store
- Prometheus metrics
- High-performance async API

**Notify Service (Node.js)**
- Handles notifications
- Slack integration
- Email simulation

**AI Agent Service (Python)**
- Core intelligence component
- Monitors Prometheus metrics every 60s
- Detects anomalies (error rate, latency, restarts, resource usage)
- Calls Claude API for diagnosis
- Executes remediation via Kubernetes API
- Logs incidents to PostgreSQL
- Sends Slack notifications

### Infrastructure

**AWS EKS**
- Managed Kubernetes cluster
- Auto-scaling node groups
- High availability across AZs

**AWS RDS PostgreSQL**
- Managed database service
- Stores orders and incident logs
- Automated backups

**AWS ECR**
- Private container registry
- Image scanning enabled
- Lifecycle policies

**AWS Secrets Manager**
- Secure credential storage
- API keys and passwords

### Observability

**Prometheus**
- Metrics collection
- Service discovery
- Alert rules

**Grafana**
- Visualization dashboards
- Real-time monitoring
- Custom queries

### CI/CD

**GitHub Actions**
- Automated testing
- Docker image builds
- ECR push
- Helm deployment
- Rollout verification

## Data Flow

1. **Request Flow**
   - Client → API Gateway → Service → Database
   - Response back through same path

2. **Monitoring Flow**
   - Services expose /metrics endpoint
   - Prometheus scrapes metrics every 15s
   - Grafana queries Prometheus for visualization

3. **AI Remediation Flow**
   - AI Agent queries Prometheus
   - Detects anomaly threshold breach
   - Sends metrics snapshot to Claude API
   - Receives remediation recommendation
   - Executes action via Kubernetes API
   - Logs incident to PostgreSQL
   - Sends Slack notification

## Security

- Non-root containers
- RBAC for Kubernetes access
- Secrets stored in AWS Secrets Manager
- Network policies for pod communication
- Image scanning in ECR
- Encrypted RDS storage

## Scalability

- Horizontal Pod Autoscaler (HPA)
- EKS node auto-scaling
- Stateless service design
- Database connection pooling

## High Availability

- Multi-AZ deployment
- Pod replicas (minimum 2)
- Health checks and readiness probes
- Automatic pod restart on failure
- RDS Multi-AZ option
