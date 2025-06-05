# Docker Deployment Troubleshooting Guide

## Common Docker Issues and Solutions

### Issue 1: Mosquitto Config File Mounting Error
**Error**: `Config file /mosquitto/config/mosquitto.conf is a directory` or `failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error mounting`

**Root Cause**: When mounting an entire directory (like `./config:/mosquitto/config`), the mosquitto.conf file path becomes a directory structure instead of a direct file, causing Mosquitto to fail when trying to read its configuration.

**Solutions**:

#### Solution A: Mount Specific File (Recommended - FIXED)
```yaml
# In docker-compose.yaml - CORRECT approach
volumes:
  - ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
```

#### Solution B: Use Docker Configs (Advanced)
```yaml
# In docker-compose.yaml
services:
  mosquitto:
    configs:
      - source: mosquitto_conf
        target: /mosquitto/config/mosquitto.conf
configs:
  mosquitto_conf:
    file: ./config/mosquitto.conf
```

#### Solution C: Use Default Configuration (Simplest)
```yaml
# In docker-compose.yaml
services:
  mosquitto:
    command: mosquitto -c /mosquitto-no-auth.conf  # Use built-in config
    # Remove custom config volume mounting
```

**❌ AVOID**: Mounting entire directory causes the error
```yaml
# This CAUSES the error - DON'T USE
volumes:
  - ./config:/mosquitto/config  # Makes mosquitto.conf a directory path
```

### Issue 2: Volume Mounting in Coolify
**Error**: Various volume mounting failures in Coolify environment

**Solution**: Use named volumes instead of bind mounts
```yaml
# Instead of:
volumes:
  - ./data:/app/data

# Use:
volumes:
  - traffic_data:/app/data

volumes:
  traffic_data:
    driver: local
```

### Issue 3: Health Check Failures
**Error**: Health checks timing out or failing

**Solutions**:

#### Fix 1: Install curl in Dockerfile
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

#### Fix 2: Use Python-based health check
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:5000/health')"]
```

#### Fix 3: Simplify health check
```yaml
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5000/health"]
```

## Available Docker Compose Configurations

### 1. docker-compose.yaml (Standard)
- **Use Case**: Development and testing
- **Features**: Full configuration with custom mosquitto.conf
- **Risk**: May have mounting issues in some environments

### 2. docker-compose.simple.yaml (Recommended for Coolify)
- **Use Case**: Production deployment in Coolify
- **Features**: Simplified configuration, no external file mounting
- **Benefits**: Avoids common mounting issues

### 3. docker-compose.coolify.yaml (Advanced)
- **Use Case**: Advanced Coolify deployment
- **Features**: Optimized for Coolify with configs and health checks
- **Benefits**: Better resource management and monitoring

## Quick Fix Commands

### Clean Docker State
```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Clean Docker system
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

### Debug Container Issues
```bash
# Check container logs
docker logs smart-traffic-ai-system
docker logs traffic-mosquitto
docker logs traffic-redis

# Enter container for debugging
docker exec -it smart-traffic-ai-system /bin/bash

# Check container processes
docker ps -a

# Check volume mounts
docker inspect smart-traffic-ai-system | grep -A 10 "Mounts"
```

### Test Services Individually
```bash
# Test main application
curl http://localhost:5000/health

# Test Redis
docker exec traffic-redis redis-cli ping

# Test Mosquitto
mosquitto_pub -h localhost -t test -m "hello"
```

## Environment-Specific Solutions

### For Coolify Deployment
1. **Use docker-compose.simple.yaml**
   ```bash
   cp docker-compose.simple.yaml docker-compose.yaml
   ```

2. **Remove custom config mounting**
   - Let mosquitto use default configuration
   - Avoid file-specific volume mounts

3. **Use environment variables for configuration**
   ```yaml
   environment:
     - MQTT_BROKER_HOST=mosquitto
     - MQTT_BROKER_PORT=1883
   ```

### For Local Development
1. **Use docker-compose.yaml with modifications**
2. **Ensure directories exist**
   ```bash
   mkdir -p data logs models config
   ```

3. **Set proper permissions**
   ```bash
   chmod 755 data logs models
   ```

### For Production (Non-Coolify)
1. **Use docker-compose.coolify.yaml**
2. **Configure external load balancer**
3. **Set up monitoring and logging**

## Performance Optimizations

### Resource Limits
```yaml
services:
  smart-traffic-ai:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Redis Optimization
```yaml
services:
  redis:
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Mosquitto Optimization
```yaml
services:
  mosquitto:
    environment:
      - MOSQUITTO_MAX_CONNECTIONS=1000
      - MOSQUITTO_MAX_KEEPALIVE=60
```

## Security Considerations

### 1. Network Isolation
```yaml
networks:
  traffic_network:
    driver: bridge
    internal: true  # Isolate from external networks
```

### 2. Non-root User
```dockerfile
# In Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### 3. Environment Variables
```yaml
# Use secrets instead of plain environment variables
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

## Monitoring and Logging

### Centralized Logging
```yaml
services:
  smart-traffic-ai:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Check Monitoring
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## Backup and Recovery

### Volume Backup
```bash
# Backup volumes
docker run --rm -v traffic_data:/data -v $(pwd):/backup alpine tar czf /backup/traffic_data.tar.gz -C /data .

# Restore volumes
docker run --rm -v traffic_data:/data -v $(pwd):/backup alpine tar xzf /backup/traffic_data.tar.gz -C /data
```

### Database Backup
```bash
# If using SQLite
docker exec smart-traffic-ai-system cp /app/data/traffic_system.db /app/data/backup_$(date +%Y%m%d).db
```

## Common Error Messages and Solutions

| Error | Solution |
|-------|----------|
| `bind: address already in use` | Change port mapping or stop conflicting service |
| `no such file or directory` | Ensure file exists before mounting |
| `permission denied` | Check file permissions and user context |
| `network not found` | Run `docker network create` or use `docker-compose up` |
| `volume not found` | Remove `-v` flag or create volume manually |

## Testing Checklist

- [ ] All containers start successfully
- [ ] Health checks pass
- [ ] Web interface accessible on port 5000
- [ ] Redis connection working
- [ ] MQTT broker accessible
- [ ] Database file created
- [ ] Logs being written
- [ ] No permission errors
- [ ] All volumes mounted correctly
- [ ] Network connectivity between services

## Emergency Recovery

If all else fails:
```bash
# Nuclear option - reset everything
docker-compose down -v
docker system prune -a --volumes
docker-compose up --build --force-recreate
```

For Coolify specifically:
1. Use `docker-compose.simple.yaml`
2. Remove all external file mounts
3. Use environment variables for configuration
4. Test locally first with `docker-compose -f docker-compose.simple.yaml up`
