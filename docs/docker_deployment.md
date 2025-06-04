# 🐳 Docker Deployment Configuration for Smart Traffic AI System

## Overview

The Smart Traffic AI System is fully configured for Docker deployment with comprehensive logging support. This document outlines the Docker configuration and deployment options.

## 📁 Docker Files

### 1. Dockerfile
- **Base Image**: Python 3.11-slim for optimal performance
- **System Dependencies**: OpenCV, computer vision libraries, and system tools
- **Environment Variables**: Logging configuration support
- **Health Check**: Built-in health monitoring on `/health` endpoint
- **Port**: Exposes port 5000 for web interface

### 2. docker-compose.yml
- **Multi-service setup**: Main application, Redis, and MQTT broker
- **Volume Management**: Persistent storage for logs, data, and models
- **Network Configuration**: Isolated Docker network for services
- **Health Checks**: Monitoring for all services

### 3. .dockerignore
- **Optimized builds**: Excludes unnecessary files
- **Security**: Prevents sensitive files from being copied
- **Performance**: Reduces build context size

## 🔧 Environment Variables

### Logging Configuration
```bash
LOG_LEVEL=INFO                    # Log verbosity level
LOG_DIR=/app/logs                 # Log directory path
LOG_RETENTION=30days              # Log retention period
LOG_MAX_SIZE=50MB                 # Maximum log file size
LOG_ENABLE_JSON=true              # Enable JSON structured logs
LOG_ENABLE_PERFORMANCE=true       # Enable performance logging
LOG_ENABLE_CONSOLE=true           # Enable console output
LOG_ENABLE_FILE=true              # Enable file logging
LOG_COMPRESSION=zip               # Log compression format
```

### System Configuration
```bash
SYSTEM_MODE=production            # Deployment mode
DATABASE_PATH=/app/data/traffic_system.db
REDIS_URL=redis://redis:6379
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
```

## 🚀 Deployment Options

### Local Development
```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f smart-traffic-ai
```

### Production Deployment
```bash
# Production environment variables
export LOG_LEVEL=INFO
export LOG_ENABLE_CONSOLE=false
export LOG_RETENTION=90days
export LOG_MAX_SIZE=100MB

# Deploy with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Single Container Deployment
```bash
# Build image
docker build -t smart-traffic-ai .

# Run with volume mounts
docker run -d \
  --name smart-traffic-ai \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -e LOG_LEVEL=INFO \
  -e LOG_DIR=/app/logs \
  smart-traffic-ai
```

## 📊 Volume Management

### Persistent Volumes
```yaml
volumes:
  traffic_data:     # Database and application data
  traffic_logs:     # System logs (all formats)
  traffic_models:   # AI models and weights
  redis_data:       # Redis persistence
  mosquitto_data:   # MQTT broker data
  mosquitto_logs:   # MQTT broker logs
```

### Volume Locations
- **Application Logs**: `/app/logs/`
  - `smart_traffic_YYYY-MM-DD.log` - Main application log
  - `errors_YYYY-MM-DD.log` - Error-only log
  - `smart_traffic_structured_YYYY-MM-DD.json` - JSON structured log
  - `performance_YYYY-MM-DD.log` - Performance metrics

## 🔍 Health Monitoring

### Built-in Health Checks
```bash
# Main application health check
curl -f http://localhost:5000/health

# Check all services
docker-compose ps

# View service logs
docker-compose logs [service-name]
```

### Health Check Endpoints
- **Main Application**: `http://localhost:5000/health`
- **Redis**: Internal ping command
- **MQTT**: Internal connectivity test

## 📝 Log Access

### View Real-time Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f smart-traffic-ai

# Tail specific log file
docker exec smart-traffic-ai-system tail -f /app/logs/smart_traffic_$(date +%Y-%m-%d).log
```

### Extract Log Files
```bash
# Copy logs from container
docker cp smart-traffic-ai-system:/app/logs/ ./exported_logs/

# Mount logs directory (recommended)
# Already configured in docker-compose.yml
```

## 🔧 Advanced Configuration

### Custom Logging Configuration
```bash
# Disable console logging for production
export LOG_ENABLE_CONSOLE=false

# Enable only error logs
export LOG_LEVEL=ERROR

# Custom log directory
export LOG_DIR=/custom/log/path

# Extended retention for compliance
export LOG_RETENTION=365days
```

### Performance Optimization
```bash
# Optimize for production
export LOG_ENABLE_PERFORMANCE=true
export LOG_MAX_SIZE=100MB
export LOG_COMPRESSION=gzip

# Reduce logging for high-throughput scenarios
export LOG_LEVEL=WARN
export LOG_ENABLE_JSON=false
```

## 🛠 Troubleshooting

### Common Issues

1. **Permission Issues**
   ```bash
   # Fix log directory permissions
   sudo chown -R 1000:1000 ./logs/
   ```

2. **Disk Space**
   ```bash
   # Check log sizes
   docker exec smart-traffic-ai-system du -sh /app/logs/*
   
   # Clean old logs
   docker exec smart-traffic-ai-system find /app/logs -name "*.zip" -mtime +30 -delete
   ```

3. **Memory Issues**
   ```bash
   # Check container memory usage
   docker stats smart-traffic-ai-system
   
   # Adjust logging to reduce memory usage
   export LOG_ENABLE_JSON=false
   export LOG_LEVEL=WARN
   ```

### Debug Mode
```bash
# Run with debug logging
docker-compose down
export LOG_LEVEL=DEBUG
export LOG_ENABLE_CONSOLE=true
docker-compose up

# Access container shell
docker exec -it smart-traffic-ai-system /bin/bash
```

## 🔒 Security Considerations

### Production Security
- **Environment Variables**: Store sensitive config in Docker secrets
- **Network**: Use Docker networks for service isolation
- **Logs**: Ensure log files don't contain sensitive information
- **Volumes**: Set appropriate filesystem permissions

### Example Production Setup
```bash
# Use Docker secrets for sensitive data
echo "redis://prod-redis:6379" | docker secret create redis_url -

# Run with restricted permissions
docker run --user 1000:1000 --read-only smart-traffic-ai
```

## 📈 Monitoring and Alerting

### Log Monitoring
```bash
# Monitor error logs in real-time
docker exec smart-traffic-ai-system tail -f /app/logs/errors_$(date +%Y-%m-%d).log

# Check system performance
docker exec smart-traffic-ai-system tail -f /app/logs/performance_$(date +%Y-%m-%d).log
```

### Integration with Monitoring Tools
- **ELK Stack**: JSON logs are ready for Elasticsearch ingestion
- **Prometheus**: Performance metrics can be exported
- **Grafana**: Dashboards for log visualization
- **Alertmanager**: Error log alerts

This Docker configuration provides a robust, scalable foundation for deploying the Smart Traffic AI System with comprehensive logging capabilities.
