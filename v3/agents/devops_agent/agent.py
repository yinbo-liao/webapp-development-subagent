from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from ecc_tools.core.engine import ECCEngine


class DevOpsAgent:
    """Specialized agent for Docker, K8s, Terraform, CI/CD infrastructure."""

    def __init__(self, config: Dict = None, ecc: Optional[ECCEngine] = None):
        self.config = config or {}
        self.ecc = ecc or ECCEngine.get_instance("config")

        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = None
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def setup(self, deployment_spec: Dict, project_path: str) -> Dict:
        """Setup deployment infrastructure"""
        print(f"[DEVOPS AGENT] Setting up deployment infrastructure...")

        results = {
            "status": "success",
            "generated_files": [],
            "validation": {}
        }

        # Generate Dockerfile
        files = self._generate_dockerfile(project_path)
        results["generated_files"].extend(files)

        # Generate docker-compose
        files = self._generate_docker_compose(project_path)
        results["generated_files"].extend(files)

        # Generate CI/CD pipeline
        files = self._generate_ci_cd(project_path)
        results["generated_files"].extend(files)

        # Generate Kubernetes manifests
        files = self._generate_k8s_manifests(project_path)
        results["generated_files"].extend(files)

        # Generate Terraform configuration
        files = self._generate_terraform(project_path)
        results["generated_files"].extend(files)

        # Validate with ECC
        results["validation"] = self.validate_output(project_path)

        return results

    def deploy(self, project_path: str) -> Dict:
        """Deploy application"""
        print(f"[DEVOPS AGENT] Deploying application...")
        return {
            "status": "success",
            "message": "Deployment configuration generated. Run 'docker-compose up' or 'kubectl apply' to deploy.",
            "commands": [
                "docker-compose -f docker-compose.yml up -d",
                "kubectl apply -f k8s/"
            ]
        }

    def validate_output(self, output_path: str) -> Dict:
        """Validate via shared ECC engine."""
        report = self.ecc.full_scan(output_path)
        sec_ok = report.security.critical_count == 0 if report.security else True
        stab_ok = len([i for i in report.stability if i.severity == 'critical']) == 0
        return {
            "passed": sec_ok and stab_ok,
            "security": report.security,
            "stability": report.stability,
            "performance": report.performance,
            "maintainability": report.maintainability,
        }

    def _generate_dockerfile(self, project_path: str) -> List[str]:
        """Generate production Dockerfile"""
        dockerfile = Path(project_path) / "Dockerfile"

        code = """# Multi-stage build for production
FROM python:3.11-slim as builder

# Security: Run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Security: Copy non-root user from builder
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup . .

# Security: Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        dockerfile.write_text(code)
        return [str(dockerfile)]

    def _generate_docker_compose(self, project_path: str) -> List[str]:
        """Generate docker-compose configuration"""
        compose_file = Path(project_path) / "docker-compose.yml"

        code = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/enterprise_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      - db
      - redis
    networks:
      - enterprise-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=enterprise_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - enterprise-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - enterprise-network
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - enterprise-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  enterprise-network:
    driver: bridge
"""
        compose_file.write_text(code)
        return [str(compose_file)]

    def _generate_ci_cd(self, project_path: str) -> List[str]:
        """Generate GitHub Actions CI/CD pipeline"""
        github_dir = Path(project_path) / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)

        ci_file = github_dir / "ci-cd.yml"

        code = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run ECC Security Scan
      run: |
        python -m ecc_tools.security.sast_engine --path . --output sarif

    - name: Run ECC Stability Analysis
      run: |
        python -m ecc_tools.stability.static_analyzer --path .

    - name: Run ECC Performance Profiling
      run: |
        python -m ecc_tools.performance.profiler --path .

    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to Kubernetes
      run: |
        echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}
        kubectl rollout status deployment/app
"""
        ci_file.write_text(code)
        return [str(ci_file)]

    def _generate_k8s_manifests(self, project_path: str) -> List[str]:
        """Generate Kubernetes manifests"""
        k8s_dir = Path(project_path) / "k8s"
        k8s_dir.mkdir(parents=True, exist_ok=True)

        files = []

        # Deployment
        deployment = k8s_dir / "deployment.yaml"
        deployment_code = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: enterprise-app
  labels:
    app: enterprise-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: enterprise-app
  template:
    metadata:
      labels:
        app: enterprise-app
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: ghcr.io/enterprise/app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
"""
        deployment.write_text(deployment_code)
        files.append(str(deployment))

        # Service
        service = k8s_dir / "service.yaml"
        service_code = """apiVersion: v1
kind: Service
metadata:
  name: enterprise-app
spec:
  selector:
    app: enterprise-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
"""
        service.write_text(service_code)
        files.append(str(service))

        # Ingress
        ingress = k8s_dir / "ingress.yaml"
        ingress_code = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: enterprise-app
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.enterprise.com
    secretName: enterprise-tls
  rules:
  - host: api.enterprise.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: enterprise-app
            port:
              number: 80
"""
        ingress.write_text(ingress_code)
        files.append(str(ingress))

        # HPA
        hpa = k8s_dir / "hpa.yaml"
        hpa_code = """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: enterprise-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: enterprise-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""
        hpa.write_text(hpa_code)
        files.append(str(hpa))

        return files

    def _generate_terraform(self, project_path: str) -> List[str]:
        """Generate Terraform infrastructure configuration"""
        tf_dir = Path(project_path) / "terraform"
        tf_dir.mkdir(parents=True, exist_ok=True)

        main_tf = tf_dir / "main.tf"
        main_code = """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "enterprise-terraform-state"
    key    = "web-app/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "enterprise-web-app"
      ManagedBy   = "terraform"
    }
  }
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false

  tags = {
    Terraform = "true"
    Environment = var.environment
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "general"
      }

      update_config = {
        max_unavailable_percentage = 25
      }
    }
  }

  tags = {
    Environment = var.environment
  }
}

# RDS PostgreSQL
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-${var.environment}"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.t3.medium"

  allocated_storage     = 20
  max_allocated_storage = 100

  db_name  = "enterprise_db"
  username = "admin"
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  deletion_protection = true

  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Environment = var.environment
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = {
    Name = "${var.project_name}-rds"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = {
    Name = "${var.project_name}-redis"
  }
}
"""
        main_tf.write_text(main_code)

        variables_tf = tf_dir / "variables.tf"
        variables_code = """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "enterprise-web-app"
}
"""
        variables_tf.write_text(variables_code)

        outputs_tf = tf_dir / "outputs.tf"
        outputs_code = """output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_address
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}
"""
        outputs_tf.write_text(outputs_code)

        return [str(main_tf), str(variables_tf), str(outputs_tf)]
