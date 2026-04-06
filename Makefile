.PHONY: help local-up local-down build-all push-all deploy clean

help:
	@echo "PulseShield AI - Available Commands"
	@echo "===================================="
	@echo "make local-up       - Start local development environment"
	@echo "make local-down     - Stop local development environment"
	@echo "make build-all      - Build all Docker images"
	@echo "make push-all       - Push all images to ECR"
	@echo "make deploy         - Deploy to Kubernetes"
	@echo "make clean          - Clean up resources"

local-up:
	docker-compose up -d
	@echo "Services running at:"
	@echo "  Order Service: http://localhost:3000"
	@echo "  Inventory Service: http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3002"

local-down:
	docker-compose down

build-all:
	docker build -t pulseshield/order-service:latest ./services/order-service
	docker build -t pulseshield/inventory-service:latest ./services/inventory-service
	docker build -t pulseshield/notify-service:latest ./services/notify-service
	docker build -t pulseshield/ai-agent-service:latest ./services/ai-agent-service
	docker build -t pulseshield/api-gateway:latest ./services/api-gateway

push-all:
	@echo "Pushing images to ECR..."
	docker push $(ECR_REGISTRY)/pulseshield/order-service:latest
	docker push $(ECR_REGISTRY)/pulseshield/inventory-service:latest
	docker push $(ECR_REGISTRY)/pulseshield/notify-service:latest
	docker push $(ECR_REGISTRY)/pulseshield/ai-agent-service:latest
	docker push $(ECR_REGISTRY)/pulseshield/api-gateway:latest

deploy:
	helm upgrade --install pulseshield ./kubernetes/helm/pulseshield \
		--namespace pulseshield --create-namespace

clean:
	docker-compose down -v
	docker system prune -f
