# CostMinimizer Web Interface - Deployment Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Options](#deployment-options)
4. [Configuration](#configuration)
5. [Security](#security)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/aws-samples/sample-costminimizer.git
cd sample-costminimizer
```

### 2. Start Web Interface
```bash
# Linux/Mac
./start-web-interface.sh

# Windows PowerShell
.\start-web-interface.ps1
```

### 3. Access Application
- HTTP: http://localhost:6000
- HTTPS: https://localhost:6001

That's it! The startup script handles:
- Environment configuration
- SSL certificate generation
- Docker network creation
- Service deployment

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                        Internet                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Nginx (Port 443)   │
              │   - SSL Termination  │
              │   - Reverse Proxy    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Flask App (Port 8000)│
              │  - Web Interface     │
              │  - API Endpoints     │
              │  - Session Management│
              └──────────┬───────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ CostMinimizer    │  │   MCP Tools      │
    │ Core Engine      │  │   AI Assistant   │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │      AWS APIs        │
              │  - Cost Explorer     │
              │  - Trusted Advisor   │
              │  - Compute Optimizer │
              │  - Bedrock (AI)      │
              └──────────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

**Best for:** Production deployments, multi-container setups

**Steps:**
```bash
# 1. Configure environment
cat > .env << EOF
HTTP_PORT=6000
HTTPS_PORT=6001
SECRET_KEY=$(openssl rand -hex 32)
USER_ID=1
EOF

# 2. Generate SSL certificates
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem -out ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=CostMinimizer/CN=localhost"

# 3. Create Docker network
docker network create costminimizer-network-1

# 4. Start services
docker-compose up -d

# 5. Verify deployment
./test-web-interface.sh
```

**Services:**
- `ai-costminimizer`: Flask web application
- `nginx`: Reverse proxy with SSL

### Option 2: Standalone Docker

**Best for:** Simple deployments, testing

**Steps:**
```bash
# Build image
docker build -t costminimizer .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $HOME/cow:/root/cow \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  --name costminimizer-web \
  costminimizer

# Access at http://localhost:8000
```

### Option 3: Local Development

**Best for:** Development, debugging

**Steps:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Set environment variables
export FLASK_APP=src/CostMinimizer/web/app.py
export SECRET_KEY=$(openssl rand -hex 32)
export FLASK_ENV=development

# Run development server
flask run --host=0.0.0.0 --port=8000 --debug
```

### Option 4: AWS ECS/Fargate

**Best for:** Production AWS deployments

**Steps:**

1. **Build and push to ECR:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name costminimizer

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t costminimizer .
docker tag costminimizer:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/costminimizer:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/costminimizer:latest
```

2. **Create ECS Task Definition:**
```json
{
  "family": "costminimizer-web",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "costminimizer",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/costminimizer:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/costminimizer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create ECS Service with ALB**

### Option 5: Kubernetes

**Best for:** Large-scale deployments, multi-region

**Deployment manifest:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: costminimizer-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: costminimizer
  template:
    metadata:
      labels:
        app: costminimizer
    spec:
      containers:
      - name: costminimizer
        image: costminimizer:latest
        ports:
        - containerPort: 8000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: costminimizer-secrets
              key: secret-key
        volumeMounts:
        - name: cow-data
          mountPath: /root/cow
      volumes:
      - name: cow-data
        persistentVolumeClaim:
          claimName: cow-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: costminimizer-service
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 8000
  selector:
    app: costminimizer
```

## Configuration

### Environment Variables

**Required:**
- `SECRET_KEY`: Flask session encryption key (generate with `openssl rand -hex 32`)

**Optional:**
- `FLASK_ENV`: `production` or `development` (default: `production`)
- `HTTP_PORT`: HTTP port for Flask app (default: `6000`)
- `HTTPS_PORT`: HTTPS port for nginx (default: `6001`)
- `USER_ID`: User identifier for multi-user deployments (default: `0`)

### Docker Compose Configuration

**File: `.env`**
```bash
HTTP_PORT=6000
HTTPS_PORT=6001
SECRET_KEY=your-secret-key-here
USER_ID=1
```

**File: `docker-compose.yml`**
```yaml
services:
  ai-costminimizer:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${HTTP_PORT:-6000}:8000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - cow_data:/root/cow
    restart: unless-stopped
```

### SSL Certificates

**Self-signed (Development):**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem -out ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=CostMinimizer/CN=localhost"
```

**Let's Encrypt (Production):**
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to ssl directory
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
```

## Security

### Best Practices

1. **Strong Secret Key**
   ```bash
   # Generate strong key
   SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **HTTPS Only**
   - Always use HTTPS in production
   - Redirect HTTP to HTTPS
   - Use valid SSL certificates

3. **Credential Management**
   - Never store credentials in code
   - Use environment variables or AWS Secrets Manager
   - Rotate credentials regularly

4. **Network Security**
   - Use security groups to restrict access
   - Enable VPC for ECS/Fargate deployments
   - Use AWS WAF for additional protection

5. **IAM Permissions**
   - Follow principle of least privilege
   - Use IAM roles instead of access keys when possible
   - Enable MFA for sensitive operations

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetReservation*",
        "support:DescribeTrustedAdvisor*",
        "compute-optimizer:Get*",
        "athena:*",
        "s3:GetObject",
        "s3:ListBucket",
        "sts:GetCallerIdentity",
        "bedrock:Converse"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
lsof -i :6000  # Linux/Mac
netstat -ano | findstr :6000  # Windows

# Kill process or change port in .env
```

#### 2. SSL Certificate Errors
```bash
# Regenerate certificates
rm -rf ssl/*
./start-web-interface.sh
```

#### 3. Docker Network Issues
```bash
# Remove and recreate network
docker network rm costminimizer-network-1
docker network create costminimizer-network-1
```

#### 4. Container Won't Start
```bash
# Check logs
docker-compose logs -f

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

#### 5. AWS Credentials Not Working
- Verify credentials with: `aws sts get-caller-identity`
- Check IAM permissions
- Ensure credentials are not expired

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export FLASK_ENV=development

# Or in docker-compose.yml
environment:
  - FLASK_ENV=development
```

View logs:
```bash
# Docker Compose
docker-compose logs -f

# Standalone Docker
docker logs -f costminimizer-web

# Local development
# Logs appear in terminal
```

## Maintenance

### Backup

**Report Data:**
```bash
# Backup cow directory
tar -czf cow-backup-$(date +%Y%m%d).tar.gz ~/cow/

# Or with Docker volume
docker run --rm -v cow_data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/cow-backup-$(date +%Y%m%d).tar.gz /data
```

**Configuration:**
```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml ssl/
```

### Updates

**Update Application:**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

**Update Dependencies:**
```bash
# Update requirements.txt
pip install --upgrade -r requirements.txt

# Rebuild Docker image
docker-compose build --no-cache
```

### Monitoring

**Health Checks:**
```bash
# Manual check
curl http://localhost:6000/health

# Automated monitoring (add to cron)
*/5 * * * * curl -f http://localhost:6000/health || systemctl restart docker-compose
```

**Resource Usage:**
```bash
# Docker stats
docker stats

# Container logs
docker-compose logs --tail=100 -f
```

### Scaling

**Horizontal Scaling (Multiple Instances):**
```yaml
# docker-compose.yml
services:
  ai-costminimizer:
    deploy:
      replicas: 3
```

**Vertical Scaling (More Resources):**
```yaml
# docker-compose.yml
services:
  ai-costminimizer:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Support

- **Documentation**: See README.md and WEB_INTERFACE.md
- **Issues**: https://github.com/aws-samples/sample-costminimizer/issues
- **AWS Support**: For AWS-specific issues

## License

Apache-2.0 License - See LICENSE file for details
