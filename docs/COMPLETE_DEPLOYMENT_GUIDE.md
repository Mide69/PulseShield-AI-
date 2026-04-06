# PulseShield AI - Complete Deployment Guide for Junior Engineers

## 📋 Table of Contents
1. [Prerequisites Setup](#prerequisites-setup)
2. [Local Development](#local-development)
3. [AWS Account Setup](#aws-account-setup)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Testing & Verification](#testing--verification)
8. [Troubleshooting](#troubleshooting)
9. [Cleanup](#cleanup)

---

## Prerequisites Setup

### Step 1: Install Required Tools

#### Windows Users:

**Install WSL2 (Windows Subsystem for Linux)**
```powershell
# Open PowerShell as Administrator
wsl --install
# Restart your computer
```

**Install Docker Desktop**
1. Download from https://www.docker.com/products/docker-desktop
2. Install and restart
3. Verify: Open terminal and run `docker --version`

**Install AWS CLI**
```powershell
# Download installer from https://aws.amazon.com/cli/
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

**Install kubectl**
```powershell
curl -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"
# Move kubectl.exe to C:\Windows\System32\
```

**Install Helm**
```powershell
choco install kubernetes-helm
# Or download from https://github.com/helm/helm/releases
```

**Install Terraform**
```powershell
choco install terraform
# Or download from https://www.terraform.io/downloads
```

#### Mac Users:

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all tools
brew install awscli kubectl helm terraform docker
```

#### Linux Users:

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Step 2: Verify Installations

```bash
docker --version          # Should show: Docker version 24.x.x
aws --version            # Should show: aws-cli/2.x.x
kubectl version --client # Should show: Client Version: v1.28.x
helm version             # Should show: version.BuildInfo{Version:"v3.x.x"}
terraform --version      # Should show: Terraform v1.x.x
```

### Step 3: Get API Keys and Credentials

**Claude API Key**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy and save the key (starts with `sk-ant-`)

**Slack Webhook URL**
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "PulseShield AI" and select your workspace
4. Go to "Incoming Webhooks" → Enable it
5. Click "Add New Webhook to Workspace"
6. Select a channel and authorize
7. Copy the webhook URL (starts with `https://hooks.slack.com/`)

---

## Local Development

### Step 1: Clone the Repository

```bash
# Navigate to your projects folder
cd ~/projects  # or C:\Users\YourName\projects on Windows

# Clone the repository
git clone https://github.com/your-username/pulseshield-ai.git
cd pulseshield-ai
```

### Step 2: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit the file (use nano, vim, or any text editor)
nano .env
```

**Add these values to .env:**
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012  # Replace with your AWS account ID

# Database
DB_PASSWORD=MySecurePassword123!

# AI Configuration
CLAUDE_API_KEY=sk-ant-your-key-here

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Kubernetes
EKS_CLUSTER_NAME=pulseshield-eks
```

**Save and exit** (Ctrl+X, then Y, then Enter in nano)

### Step 3: Start Local Environment

```bash
# Start all services
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Check if services are running
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
order-service           Up                  0.0.0.0:3000->3000/tcp
inventory-service       Up                  0.0.0.0:8000->8000/tcp
notify-service          Up                  0.0.0.0:3001->3001/tcp
ai-agent-service        Up                  0.0.0.0:8001->8001/tcp
prometheus              Up                  0.0.0.0:9090->9090/tcp
grafana                 Up                  0.0.0.0:3002->3000/tcp
postgres                Up                  0.0.0.0:5432->5432/tcp
```

### Step 4: Test Local Services

```bash
# Test order service
curl http://localhost:3000/health
# Expected: {"status":"healthy","service":"order-service"}

# Test inventory service
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"inventory-service"}

# Create a test order
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"John Doe","product":"laptop","quantity":1}'
# Expected: JSON with order details

# Check inventory
curl http://localhost:8000/inventory/laptop
# Expected: {"stock":50,"price":999.99}
```

### Step 5: Access Monitoring Tools

**Prometheus:**
- Open browser: http://localhost:9090
- Go to Status → Targets
- Verify order-service and inventory-service are "UP"

**Grafana:**
- Open browser: http://localhost:3002
- Login: admin / admin
- Skip password change or set new password
- Add Prometheus data source:
  - Click "Add data source"
  - Select "Prometheus"
  - URL: http://prometheus:9090
  - Click "Save & Test"

### Step 6: Stop Local Environment (when done testing)
doc
```bash
docker-compose down
```

---

## AWS Account Setup

### Step 1: Create AWS Account

1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Follow the registration process
4. Add payment method (required, but we'll use free tier)

### Step 2: Create IAM User

1. Log into AWS Console: https://console.aws.amazon.com/
2. Search for "IAM" in the top search bar
3. Click "Users" → "Create user"
4. Username: `pulseshield-deployer`
5. Check "Provide user access to AWS Management Console"
6. Click "Next"
7. Select "Attach policies directly"
8. Add these policies:
   - `AdministratorAccess` (for learning; use restricted policies in production)
9. Click "Next" → "Create user"

### Step 3: Create Access Keys

1. Click on the user you just created
2. Go to "Security credentials" tab
3. Scroll to "Access keys"
4. Click "Create access key"
5. Select "Command Line Interface (CLI)"
6. Check the confirmation box
7. Click "Next" → "Create access key"
8. **IMPORTANT:** Copy both:
   - Access key ID (starts with `AKIA`)
   - Secret access key (long random string)
9. Save these securely!

### Step 4: Configure AWS CLI

```bash
# Run AWS configure
aws configure

# Enter when prompted:
AWS Access Key ID: AKIA... (paste your key)
AWS Secret Access Key: ... (paste your secret)
Default region name: us-east-1
Default output format: json
```

**Verify configuration:**
```bash
aws sts get-caller-identity
```

**Expected output:**
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/pulseshield-deployer"
}
```

**Save your Account ID** - you'll need it later!

---

## Infrastructure Deployment

### Step 1: Prepare Terraform Configuration

```bash
# Navigate to Terraform directory
cd infrastructure/environments/dev

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit the file
nano terraform.tfvars
```

**Update terraform.tfvars:**
```hcl
aws_region        = "us-east-1"
cluster_name      = "pulseshield-eks"
db_password       = "MySecurePassword123!"
claude_api_key    = "sk-ant-your-key-here"
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Step 2: Initialize Terraform

```bash
# Initialize Terraform (downloads providers)
terraform init
```

**Expected output:**
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 3: Plan Infrastructure

```bash
# See what will be created
terraform plan
```

**Review the output** - it will show:
- VPC and subnets
- EKS cluster
- RDS database
- ECR repositories
- Security groups
- IAM roles

**This will create approximately 30-40 resources.**

### Step 4: Deploy Infrastructure

```bash
# Apply the configuration
terraform apply
```

**When prompted:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**⏱️ This takes 15-20 minutes!** Go get coffee ☕

**Expected final output:**
```
Apply complete! Resources: 38 added, 0 changed, 0 destroyed.

Outputs:

ecr_repositories = {
  "pulseshield/ai-agent-service" = "123456789012.dkr.ecr.us-east-1.amazonaws.com/pulseshield/ai-agent-service"
  "pulseshield/api-gateway" = "123456789012.dkr.ecr.us-east-1.amazonaws.com/pulseshield/api-gateway"
  ...
}
eks_cluster_endpoint = "https://ABC123.gr7.us-east-1.eks.amazonaws.com"
rds_endpoint = "pulseshield.abc123.us-east-1.rds.amazonaws.com:5432"
```

**📝 SAVE THESE OUTPUTS!** You'll need them.

### Step 5: Configure kubectl

```bash
# Update kubeconfig to connect to your EKS cluster
aws eks update-kubeconfig --name pulseshield-eks --region us-east-1
```

**Verify connection:**
```bash
kubectl get nodes
```

**Expected output:**
```
NAME                          STATUS   ROLES    AGE   VERSION
ip-10-0-1-123.ec2.internal   Ready    <none>   5m    v1.28.x
ip-10-0-2-456.ec2.internal   Ready    <none>   5m    v1.28.x
```

---

## Application Deployment

### Step 1: Login to ECR

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Your AWS Account ID: $AWS_ACCOUNT_ID"

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

**Expected output:**
```
Login Succeeded
```

### Step 2: Build and Push Docker Images

```bash
# Navigate back to project root
cd ../../../

# Set ECR registry variable
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"

# Build and push order-service
echo "Building order-service..."
cd services/order-service
docker build -t $ECR_REGISTRY/pulseshield/order-service:latest .
docker push $ECR_REGISTRY/pulseshield/order-service:latest
cd ../..

# Build and push inventory-service
echo "Building inventory-service..."
cd services/inventory-service
docker build -t $ECR_REGISTRY/pulseshield/inventory-service:latest .
docker push $ECR_REGISTRY/pulseshield/inventory-service:latest
cd ../..

# Build and push notify-service
echo "Building notify-service..."
cd services/notify-service
docker build -t $ECR_REGISTRY/pulseshield/notify-service:latest .
docker push $ECR_REGISTRY/pulseshield/notify-service:latest
cd ../..

# Build and push ai-agent-service
echo "Building ai-agent-service..."
cd services/ai-agent-service
docker build -t $ECR_REGISTRY/pulseshield/ai-agent-service:latest .
docker push $ECR_REGISTRY/pulseshield/ai-agent-service:latest
cd ../..

# Build and push api-gateway
echo "Building api-gateway..."
cd services/api-gateway
docker build -t $ECR_REGISTRY/pulseshield/api-gateway:latest .
docker push $ECR_REGISTRY/pulseshield/api-gateway:latest
cd ../..
```

**⏱️ This takes 10-15 minutes** depending on your internet speed.

### Step 3: Create Kubernetes Namespace

```bash
kubectl create namespace pulseshield
```

### Step 4: Create Kubernetes Secrets

```bash
# Get RDS endpoint from Terraform output
cd infrastructure/environments/dev
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
cd ../../../

# Create secrets
kubectl create secret generic pulseshield-secrets \
  --from-literal=db-password='MySecurePassword123!' \
  --from-literal=claude-api-key='sk-ant-your-key-here' \
  --from-literal=slack-webhook-url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL' \
  -n pulseshield

# Verify secret was created
kubectl get secrets -n pulseshield
```

### Step 5: Update Helm Values

```bash
# Edit Helm values
cd kubernetes/helm/pulseshield
nano values.yaml
```

**Update these lines:**
```yaml
global:
  registry: 123456789012.dkr.ecr.us-east-1.amazonaws.com  # Your ECR registry
  namespace: pulseshield

# ... scroll down to database section ...

database:
  host: pulseshield.abc123.us-east-1.rds.amazonaws.com  # Your RDS endpoint (without :5432)
  name: pulseshield
  user: postgres

prometheus:
  url: http://prometheus-server:80  # We'll install Prometheus next
```

**Save and exit**

### Step 6: Deploy with Helm

```bash
# Install the application
helm install pulseshield . -n pulseshield

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment --all -n pulseshield
```

**Expected output:**
```
deployment.apps/order-service condition met
deployment.apps/inventory-service condition met
deployment.apps/notify-service condition met
deployment.apps/ai-agent-service condition met
deployment.apps/api-gateway condition met
```

### Step 7: Verify Deployment

```bash
# Check pods
kubectl get pods -n pulseshield
```

**Expected output (all should be Running):**
```
NAME                                 READY   STATUS    RESTARTS   AGE
order-service-xxx-yyy               1/1     Running   0          2m
order-service-xxx-zzz               1/1     Running   0          2m
inventory-service-xxx-yyy           1/1     Running   0          2m
inventory-service-xxx-zzz           1/1     Running   0          2m
notify-service-xxx-yyy              1/1     Running   0          2m
ai-agent-service-xxx-yyy            1/1     Running   0          2m
api-gateway-xxx-yyy                 1/1     Running   0          2m
```

**If any pod is not Running:**
```bash
# Check pod details
kubectl describe pod <pod-name> -n pulseshield

# Check logs
kubectl logs <pod-name> -n pulseshield
```

---

## Monitoring Setup

### Step 1: Install Prometheus

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace pulseshield \
  --set server.service.type=LoadBalancer
```

**Wait for LoadBalancer:**
```bash
kubectl get svc -n pulseshield -w
# Press Ctrl+C when prometheus-server shows EXTERNAL-IP
```

### Step 2: Install Grafana

```bash
# Add Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Grafana
helm install grafana grafana/grafana \
  --namespace pulseshield \
  --set service.type=LoadBalancer \
  --set adminPassword=admin
```

### Step 3: Access Grafana

```bash
# Get Grafana URL
kubectl get svc grafana -n pulseshield

# Note the EXTERNAL-IP
# Open browser: http://<EXTERNAL-IP>
# Login: admin / admin
```

### Step 4: Configure Grafana

1. **Add Prometheus Data Source:**
   - Click "⚙️" (Settings) → "Data sources"
   - Click "Add data source"
   - Select "Prometheus"
   - URL: `http://prometheus-server:80`
   - Click "Save & Test" (should show green checkmark)

2. **Import Dashboard:**
   - Click "+" → "Import"
   - Upload `monitoring/grafana/pulseshield-dashboard.json`
   - Select Prometheus data source
   - Click "Import"

---

## Testing & Verification

### Step 1: Get API Gateway URL

```bash
# Get the LoadBalancer URL
kubectl get svc api-gateway -n pulseshield

# Save the EXTERNAL-IP
API_URL=<EXTERNAL-IP>
```

### Step 2: Test Order Service

```bash
# Create an order
curl -X POST http://$API_URL/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Alice Johnson",
    "product": "laptop",
    "quantity": 2
  }'
```

**Expected response:**
```json
{
  "id": 1,
  "customer_name": "Alice Johnson",
  "product": "laptop",
  "quantity": 2,
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

### Step 3: Test Inventory Service

```bash
# Check inventory
curl http://$API_URL/inventory/laptop
```

**Expected response:**
```json
{
  "stock": 50,
  "price": 999.99
}
```

### Step 4: Verify Metrics

```bash
# Get Prometheus URL
PROM_URL=$(kubectl get svc prometheus-server -n pulseshield -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Check if metrics are being collected
curl "http://$PROM_URL/api/v1/query?query=up"
```

### Step 5: Test AI Agent (Trigger Anomaly)

```bash
# Generate high load to trigger anomaly detection
for i in {1..100}; do
  curl -X POST http://$API_URL/orders \
    -H "Content-Type: application/json" \
    -d '{"customer_name":"Test","product":"phone","quantity":1}' &
done

# Wait 2 minutes for AI agent to detect and remediate
sleep 120

# Check AI agent logs
kubectl logs -l app=ai-agent-service -n pulseshield --tail=50
```

**Check Slack** - you should receive an alert!

### Step 6: Verify Auto-Scaling

```bash
# Check HPA status
kubectl get hpa -n pulseshield

# Generate more load
for i in {1..500}; do
  curl http://$API_URL/orders &
done

# Watch pods scale up
kubectl get pods -n pulseshield -w
```

---

## Troubleshooting

### Problem: Pods are in CrashLoopBackOff

**Solution:**
```bash
# Check pod logs
kubectl logs <pod-name> -n pulseshield

# Common issues:
# 1. Database connection failed
kubectl get secret pulseshield-secrets -n pulseshield -o yaml
# Verify db-password is correct

# 2. Image pull error
kubectl describe pod <pod-name> -n pulseshield
# Check ECR permissions

# 3. Resource limits
kubectl describe pod <pod-name> -n pulseshield
# Look for OOMKilled or resource issues
```

### Problem: Cannot connect to RDS

**Solution:**
```bash
# Check security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=*rds*" \
  --query 'SecurityGroups[*].[GroupId,GroupName,IpPermissions]'

# Security group should allow port 5432 from EKS nodes
# Fix in AWS Console: EC2 → Security Groups → Edit inbound rules
```

### Problem: AI Agent not detecting anomalies

**Solution:**
```bash
# Check AI agent logs
kubectl logs -l app=ai-agent-service -n pulseshield

# Verify Claude API key
kubectl get secret pulseshield-secrets -n pulseshield -o jsonpath='{.data.claude-api-key}' | base64 -d

# Check Prometheus connectivity
kubectl exec -it <ai-agent-pod> -n pulseshield -- curl http://prometheus-server:80/api/v1/query?query=up
```

### Problem: High AWS costs

**Solution:**
```bash
# Check running resources
aws eks list-clusters
aws rds describe-db-instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# Stop RDS when not in use
aws rds stop-db-instance --db-instance-identifier pulseshield

# Scale down EKS nodes
kubectl scale deployment --all --replicas=1 -n pulseshield
```

---

## Cleanup

### Step 1: Delete Kubernetes Resources

```bash
# Delete Helm releases
helm uninstall pulseshield -n pulseshield
helm uninstall prometheus -n pulseshield
helm uninstall grafana -n pulseshield

# Delete namespace
kubectl delete namespace pulseshield
```

### Step 2: Destroy Infrastructure

```bash
# Navigate to Terraform directory
cd infrastructure/environments/dev

# Destroy all resources
terraform destroy

# When prompted, type: yes
```

**⏱️ This takes 10-15 minutes**

### Step 3: Verify Cleanup

```bash
# Check EKS clusters
aws eks list-clusters

# Check RDS instances
aws rds describe-db-instances

# Check ECR repositories
aws ecr describe-repositories
```

### Step 4: Delete ECR Images (optional)

```bash
# List repositories
aws ecr describe-repositories --query 'repositories[*].repositoryName'

# Delete each repository
aws ecr delete-repository --repository-name pulseshield/order-service --force
aws ecr delete-repository --repository-name pulseshield/inventory-service --force
aws ecr delete-repository --repository-name pulseshield/notify-service --force
aws ecr delete-repository --repository-name pulseshield/ai-agent-service --force
aws ecr delete-repository --repository-name pulseshield/api-gateway --force
```

---

## 🎉 Congratulations!

You've successfully deployed PulseShield AI from start to finish!

### What You've Learned:
✅ Docker containerization
✅ Kubernetes orchestration
✅ Terraform infrastructure as code
✅ Helm package management
✅ AWS cloud services (EKS, RDS, ECR)
✅ Prometheus monitoring
✅ Grafana dashboards
✅ CI/CD concepts
✅ Microservices architecture

### Next Steps:
1. Customize the services for your use case
2. Add more monitoring dashboards
3. Implement additional AI remediation rules
4. Set up CI/CD with GitHub Actions
5. Add more microservices

### Need Help?
- Check logs: `kubectl logs <pod-name> -n pulseshield`
- Describe resources: `kubectl describe <resource> <name> -n pulseshield`
- AWS documentation: https://docs.aws.amazon.com/
- Kubernetes docs: https://kubernetes.io/docs/

**Happy deploying! 🚀**
