#!/bin/bash

set -e

echo "☁️  PulseShield AI - AWS Deployment"
echo "===================================="

read -p "AWS Region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Cluster Name [pulseshield-eks]: " CLUSTER_NAME
CLUSTER_NAME=${CLUSTER_NAME:-pulseshield-eks}

echo ""
echo "📦 Step 1: Deploying Infrastructure..."
cd infrastructure/environments/dev
terraform init
terraform apply -auto-approve

echo ""
echo "🔧 Step 2: Configuring kubectl..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

echo ""
echo "🐳 Step 3: Building and pushing Docker images..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

cd ../../../

for service in order-service inventory-service notify-service ai-agent-service api-gateway; do
    echo "Building $service..."
    docker build -t $ECR_REGISTRY/pulseshield/$service:latest ./services/$service
    docker push $ECR_REGISTRY/pulseshield/$service:latest
done

echo ""
echo "☸️  Step 4: Deploying to Kubernetes..."
helm upgrade --install pulseshield ./kubernetes/helm/pulseshield \
    --namespace pulseshield --create-namespace \
    --set global.registry=$ECR_REGISTRY

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Check status:"
echo "  kubectl get pods -n pulseshield"
echo "  kubectl get svc -n pulseshield"
