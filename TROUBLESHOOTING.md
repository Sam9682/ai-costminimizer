# CostMinimizer Web Interface - Troubleshooting Guide

## Common Issues and Solutions

### 1. Network Configuration Error

**Error:**
```
[ERROR] Some services failed to start
service "nginx" refers to undefined network costminimizer-network-0: invalid compose project
```

**Cause:** Docker Compose network configuration mismatch.

**Solution:**
```bash
# Stop all containers
docker-compose down

# Remove old containers
docker rm -f $(docker ps -aq --filter name=ai-costminimizer) 2>/dev/null || true

# Remove old networks
docker network rm costminimizer-network-1 2>/dev/null || true

# Restart
./start-web-interface.sh
```

### 2. Port Already in Use

**Error:**
```
Error response from daemon: failed to bind host port 0.0.0.0:6000/tcp: address already in use
```

**Solution Option 1 - Change Ports:**
```bash
# Edit .env file
nano .env

# Change ports
HTTP_PORT=7000
HTTPS_PORT=7001

# Restart
docker-compose down
docker-compose up -d
```

**Solution Option 2 - Find and Stop Conflicting Process:**
```bash
# Find process using port
lsof -i :6000  # Linux/Mac
netstat -ano | findstr :6000  # Windows

# Kill the process or stop the service
```

### 3. Container Name Conflict

**Error:**
```
Error response from daemon: Conflict. The container name "/ai-costminimizer-1" is already in use
```

**Solution:**
```bash
# Remove conflicting containers
docker rm -f ai-costminimizer-1 ai-costminimizer-nginx-1

# Restart
./start-web-interface.sh
```

### 4. SSL Certificate Errors

**Error:**
```
SSL certificate problem: self signed certificate
```

**Solution Option 1 - Accept Self-Signed Certificate:**
- In browser, click "Advanced" and "Proceed to localhost (unsafe)"
- This is safe for local development

**Solution Option 2 - Use HTTP Instead:**
```
http://localhost:6000
```

**Solution Option 3 - Regenerate Certificates:**
```bash
rm -rf ssl/*
./start-web-interface.sh
```

### 5. Services Not Starting

**Error:**
```
❌ Failed to start CostMinimizer web service
```

**Solution:**
```bash
# Check logs
docker-compose logs -f

# Common fixes:
# 1. Rebuild containers
docker-compose down
docker-compose up -d --build

# 2. Check Docker is running
docker ps

# 3. Check disk space
df -h

# 4. Restart Docker daemon
sudo systemctl restart docker  # Linux
# or restart Docker Desktop on Mac/Windows
```

### 6. AWS Credentials Not Working

**Error in Web Interface:**
```
Unable to validate credentials
```

**Solution:**
1. Verify credentials are correct
2. Check IAM permissions (see Required IAM Permissions below)
3. Ensure credentials are not expired
4. Test with AWS CLI:
   ```bash
   aws sts get-caller-identity --profile your-profile
   ```

### 7. Reports Taking Too Long

**Issue:** Reports seem stuck or taking forever

**Solution:**
This is normal behavior! Reports can take:
- Cost Explorer (CE): 2-5 minutes
- Trusted Advisor (TA): 1-3 minutes
- Compute Optimizer (CO): 3-10 minutes
- Cost & Usage Report (CUR): 5-15 minutes

**Check Progress:**
```bash
# View real-time logs
docker-compose logs -f ai-costminimizer-1
```

### 8. Chat Not Responding

**Error:**
```
Error processing question
```

**Solution:**
1. Ensure AWS Bedrock is enabled in your account
2. Check IAM permissions include `bedrock:Converse`
3. Verify credentials in session (re-validate if needed)
4. Check logs:
   ```bash
   docker-compose logs -f ai-costminimizer-1
   ```

### 9. EOF When Reading a Line Error

**Error:**
```
❌ Error: EOF when reading a line
```

**Cause:** The application tries to read user input interactively but there's no terminal attached (common in Docker containers).

**Solution:**
This has been fixed in the latest version. The application now:
- Automatically detects non-interactive mode
- Uses `--auto-update-conf` flag when running from web interface
- Sets `COSTMINIMIZER_NON_INTERACTIVE=1` environment variable
- Handles EOFError exceptions gracefully

If you still encounter this error:
```bash
# Rebuild containers with latest code
docker-compose down
docker-compose up -d --build

# Or manually set environment variable
docker-compose down
echo "COSTMINIMIZER_NON_INTERACTIVE=1" >> .env
docker-compose up -d
```

### 10. Cannot Access Web Interface

**Issue:** Browser shows "Connection refused" or "Cannot connect"

**Solution:**
```bash
# 1. Check if containers are running
docker ps --filter name=ai-costminimizer

# 2. Check if ports are exposed
docker port ai-costminimizer-1
docker port ai-costminimizer-nginx-1

# 3. Try different URL
http://localhost:6000  # Direct to Flask
https://localhost:6001  # Through Nginx

# 4. Check firewall
sudo ufw status  # Linux
# Ensure ports 6000 and 6001 are allowed
```

### 11. Docker Build Fails

**Error:**
```
ERROR [internal] load metadata for public.ecr.aws/docker/library/python:3.12
```

**Solution:**
```bash
# 1. Check internet connection
ping google.com

# 2. Check Docker daemon
docker info

# 3. Clear Docker cache
docker system prune -a

# 4. Retry build
docker-compose build --no-cache
```

## Required IAM Permissions

For the web interface to work properly, AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "ce:GetCostAndUsage",
        "ce:GetReservation*",
        "support:DescribeTrustedAdvisor*",
        "compute-optimizer:Get*",
        "athena:*",
        "s3:GetObject",
        "s3:ListBucket",
        "bedrock:Converse"
      ],
      "Resource": "*"
    }
  ]
}
```

## Diagnostic Commands

### Check Service Status
```bash
# View all containers
docker ps -a

# View specific containers
docker ps --filter name=ai-costminimizer

# Check container logs
docker-compose logs -f

# Check specific service logs
docker-compose logs -f ai-costminimizer-1
docker-compose logs -f nginx
```

### Check Network Configuration
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect ai-costminimizer_costminimizer-network

# Check container network
docker inspect ai-costminimizer-1 | grep -A 10 Networks
```

### Check Volumes
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ai-costminimizer_cow_data

# Check volume contents
docker run --rm -v ai-costminimizer_cow_data:/data alpine ls -la /data
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:6000/health

# Available reports
curl http://localhost:6000/api/available-reports

# Validate credentials (replace with your credentials)
curl -X POST http://localhost:6000/api/validate-credentials \
  -H "Content-Type: application/json" \
  -d '{"access_key":"YOUR_KEY","secret_key":"YOUR_SECRET","region":"us-east-1"}'
```

## Clean Slate Restart

If all else fails, start fresh:

```bash
# 1. Stop everything
docker-compose down

# 2. Remove all containers
docker rm -f $(docker ps -aq --filter name=ai-costminimizer) 2>/dev/null || true

# 3. Remove networks
docker network rm $(docker network ls --filter name=costminimizer -q) 2>/dev/null || true

# 4. Remove volumes (WARNING: This deletes report data!)
docker volume rm ai-costminimizer_app_data ai-costminimizer_cow_data 2>/dev/null || true

# 5. Remove images
docker rmi ai-costminimizer-ai-costminimizer 2>/dev/null || true

# 6. Clean Docker system
docker system prune -f

# 7. Remove local files
rm -rf ssl/ .env

# 8. Start fresh
./start-web-interface.sh
```

## Getting Help

### View Logs
```bash
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f ai-costminimizer-1
```

### Debug Mode
```bash
# Enable Flask debug mode
echo "FLASK_ENV=development" >> .env

# Restart
docker-compose restart ai-costminimizer-1

# View detailed logs
docker-compose logs -f ai-costminimizer-1
```

### Report Issues
If you encounter issues not covered here:

1. **Collect Information:**
   ```bash
   # System info
   docker version
   docker-compose version
   
   # Container status
   docker ps -a
   
   # Logs
   docker-compose logs > logs.txt
   ```

2. **Create GitHub Issue:**
   - Go to: https://github.com/aws-samples/sample-costminimizer/issues
   - Include: Error message, logs, system info
   - Describe: Steps to reproduce

## Prevention Tips

### Regular Maintenance
```bash
# Weekly cleanup
docker system prune -f

# Check disk space
df -h

# Update images
docker-compose pull
docker-compose up -d --build
```

### Best Practices
1. Always use `./start-web-interface.sh` for starting
2. Use `docker-compose down` before making changes
3. Keep Docker and Docker Compose updated
4. Monitor disk space (Docker can use a lot)
5. Backup report data regularly:
   ```bash
   docker run --rm -v ai-costminimizer_cow_data:/data -v $(pwd):/backup \
     alpine tar -czf /backup/cow-backup-$(date +%Y%m%d).tar.gz /data
   ```

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Network error | `docker-compose down && ./start-web-interface.sh` |
| Port in use | Edit `.env`, change ports |
| Container conflict | `docker rm -f ai-costminimizer-1 ai-costminimizer-nginx-1` |
| SSL error | Use `http://localhost:6000` instead |
| Services not starting | `docker-compose logs -f` |
| Credentials invalid | Check IAM permissions |
| Reports slow | Normal, wait 5-15 minutes |
| Chat not working | Enable Bedrock, check permissions |
| EOF error | `docker-compose down && docker-compose up -d --build` |
| Can't access | Check `docker ps`, try different port |
| Build fails | `docker system prune -a && docker-compose build --no-cache` |

---

**Still having issues?** Check the full documentation:
- [WEB_INTERFACE.md](WEB_INTERFACE.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [QUICK_START.md](QUICK_START.md)
