# PulseShield AI - Deployment Guide

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Docker installed
- kubectl installed
- Helm 3.x installed
- Terraform 1.0+ installed
- Claude API key
- Slack webhook URL

## Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd pulseshield-ai
```

2. **Set environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Start services locally**
```bash
docker-compose up -d
```

4. **Access services**
- Order Service: http://localhost:3000
- Inventory Service: http://localhost:8000
- Notify Service: http://localhost:3001
- AI Agent: http://localhost:8001
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3002 (admin/admin)

## AWS Infrastructure Deployment

1. **Navigate to Terraform directory**
```bash
cd infrastructure/environments/dev
```

2. **Create terraform.tfvars**
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit with your values
```

3. **Initialize and apply Terraform**
```bash
terraform init
terraform plan
terraform apply
```

4. **Configure kubectl**
```bash
aws eks update-kubeconfig --name pulseshield-eks --region us-east-1
```

## Application Deployment

1. **Build and push Docker images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push each service
cd services/order-service
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/pulseshield/order-service:latest .
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/pulseshield/order-service:latest

# Repeat for other services
```

2. **Create Kubernetes secrets**
```bash
kubectl create namespace pulseshield

kubectl create secret generic pulseshield-secrets \
  --from-literal=db-password=<your-password> \
  --from-literal=claude-api-key=<your-key> \
  --from-literal=slack-webhook-url=<your-url> \
  -n pulseshield
```

3. **Deploy with Helm**
```bash
cd kubernetes/helm

# Update values.yaml with your ECR registry and RDS endpoint

helm install pulseshield ./pulseshield -n pulseshield
```

4. **Verify deployment**
```bash
kubectl get pods -n pulseshield
kubectl get svc -n pulseshield
```

## Monitoring Setup

1. **Install Prometheus**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -n pulseshield
```

2. **Install Grafana**
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -n pulseshield
```

3. **Access Grafana**
```bash
kubectl port-forward svc/grafana 3000:80 -n pulseshield
```

## CI/CD Setup

1. **Configure GitHub Secrets**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- ECR_REGISTRY

2. **Push to main branch to trigger deployment**
```bash
git push origin main
```

## Testing the Platform

1. **Create an order**
```bash
curl -X POST http://<api-gateway-url>/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"John","product":"laptop","quantity":1}'
```

2. **Check inventory**
```bash
curl http://<api-gateway-url>/inventory/laptop
```

3. **View metrics**
```bash
curl http://<order-service-url>:3000/metrics
```

## Troubleshooting

**Pods not starting**
```bash
kubectl describe pod <pod-name> -n pulseshield
kubectl logs <pod-name> -n pulseshield
```

**Database connection issues**
- Verify RDS security group allows traffic from EKS
- Check database credentials in secrets

**AI Agent not working**
- Verify Claude API key is valid
- Check Prometheus URL is accessible
- Verify RBAC permissions for service account

## Cleanup

```bash
# Delete Helm release
helm uninstall pulseshield -n pulseshield

# Destroy infrastructure
cd infrastructure/environments/dev
terraform destroy
```
