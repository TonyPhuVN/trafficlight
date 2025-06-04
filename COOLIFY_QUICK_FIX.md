# Coolify Deployment Quick Fix

## The Problem
You're getting this error:
```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error mounting "/data/coolify/applications/xxx/config/mosquitto.conf" to rootfs at "/mosquitto/config/mosquitto.conf": create mountpoint for /mosquitto/config/mosquitto.conf mount: cannot create subdirectories
```

## The Solution (2 minutes)

### Option 1: Use Simple Configuration (Recommended)
Replace your current `docker-compose.yaml` with the simple version:

```bash
# In your Coolify deployment, use this docker-compose.yaml content:
cp docker-compose.simple.yaml docker-compose.yaml
```

Or manually update your `docker-compose.yaml` to:

```yaml
version: '3.8'

services:
  smart-traffic-ai:
    build: .
    container_name: smart-traffic-ai-system
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - SYSTEM_MODE=production
      - DATABASE_PATH=/app/data/traffic_system.db
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379
      - MQTT_BROKER_HOST=mosquitto
      - MQTT_BROKER_PORT=1883
    volumes:
      - traffic_data:/app/data
      - traffic_logs:/app/logs
    depends_on:
      - redis
      - mosquitto
    networks:
      - traffic_network

  redis:
    image: redis:7-alpine
    container_name: traffic-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - traffic_network

  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: traffic-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_logs:/mosquitto/log
    networks:
      - traffic_network
    command: mosquitto -c /mosquitto-no-auth.conf

volumes:
  traffic_data:
  traffic_logs:
  redis_data:
  mosquitto_data:
  mosquitto_logs:

networks:
  traffic_network:
    driver: bridge
```

### Option 2: Quick Fix Current Configuration
In your existing `docker-compose.yaml`, change this line:

**From:**
```yaml
- ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf
```

**To:**
```yaml
- ./config:/mosquitto/config
```

## What This Fixes
- ✅ Removes file-specific mounting that causes the error
- ✅ Uses default mosquitto configuration to avoid mounting issues
- ✅ Maintains all other functionality
- ✅ Works reliably in Coolify environment

## Test Before Deployment
```bash
# Test locally first
docker-compose -f docker-compose.simple.yaml up --build

# If successful, deploy to Coolify
```

## Why This Happens
Coolify's Docker environment has strict requirements for file mounting. The error occurs because:
1. Docker tries to mount a single file (`mosquitto.conf`)
2. The target directory structure doesn't exist in the container
3. Docker can't create the necessary subdirectories

## Alternative Configurations Available
- `docker-compose.simple.yaml` - No external file mounts (Coolify-safe)
- `docker-compose.coolify.yaml` - Advanced Coolify configuration
- `docker-compose.yaml` - Standard configuration (may need fixes)

## Support
If this doesn't work, check `DOCKER_TROUBLESHOOTING.md` for more detailed solutions.
