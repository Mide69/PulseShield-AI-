terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "cluster_name" {
  default = "pulseshield-eks"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "claude_api_key" {
  type      = string
  sensitive = true
}

variable "slack_webhook_url" {
  type      = string
  sensitive = true
}

data "aws_availability_zones" "available" {}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.cluster_name}-private-${count.index + 1}"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 101}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

module "eks" {
  source      = "../../modules/eks"
  cluster_name = var.cluster_name
  vpc_id      = aws_vpc.main.id
  subnet_ids  = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
}

module "ecr" {
  source = "../../modules/ecr"
  repository_names = [
    "pulseshield/order-service",
    "pulseshield/inventory-service",
    "pulseshield/notify-service",
    "pulseshield/ai-agent-service",
    "pulseshield/api-gateway"
  ]
}

module "rds" {
  source      = "../../modules/rds"
  db_name     = "pulseshield"
  db_username = "postgres"
  db_password = var.db_password
  subnet_ids  = aws_subnet.private[*].id
  vpc_id      = aws_vpc.main.id
}

module "secrets" {
  source = "../../modules/secrets"
  secrets = {
    "pulseshield/claude-api-key"    = var.claude_api_key
    "pulseshield/slack-webhook-url" = var.slack_webhook_url
    "pulseshield/db-password"       = var.db_password
  }
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repositories" {
  value = module.ecr.repository_urls
}

output "rds_endpoint" {
  value = module.rds.db_endpoint
}
