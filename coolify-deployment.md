# Smart Traffic AI System - Coolify Deployment Guide

## Overview
This guide explains how to deploy the Smart Traffic AI System on Coolify, a self-hosted platform-as-a-service (PaaS) solution.

## Prerequisites
- Coolify instance running and accessible
- Git repository with the Smart Traffic AI System code
- Domain name (optional, for custom domains)

## Deployment Steps

### 1. Project Setup in Coolify

1. **Login to your Coolify dashboard**
2. **Create a new project**:
   - Click "New Project"
   - Name: `smart-traffic-ai-system`
   - Description: `AI-powered traffic management system`

### 2. Application Configuration

1. **Add new application**:
   - Type: `Docker Compose`
   - Name: `smart-traffic-ai`
   - Repository: `[Your Git Repository URL]`
   - Branch: `main` (or your default branch)

2. **Build Configuration**:
   - Build Pack: `Docker`
   - Dockerfile Path: `./Dockerfile`
   - Docker Compose File: `./docker-compose.yml`

### 3. Environment Variables

Configure the following environment variables in Coolify:

```bash
# System Configuration
SYSTEM_MODE=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# Database Configuration
DATABASE_PATH=/app/data/traffic_system.db

# Redis Configuration
REDIS_URL=redis://redis:6379

# MQTT Configuration
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883

# Security (generate secure values)
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Optional: External Services
# WEATHER_API_KEY=your-weather-api-key
# EMERGENCY_WEBHOOK_URL=https://your-emergency-system.com/webhook
```

### 4. Port Configuration

- **Main Application**: Port `5000` (HTTP)
- **Redis**: Port `6379` (Internal)
- **MQTT**: Port `1883` (Internal), Port `9001` (WebSocket, Internal)

### 5. Volume Mounts

Coolify will automatically handle Docker volumes defined in docker-compose.yml:
- `traffic_data`: Persistent storage for database and traffic data
- `traffic_logs`: Application logs
- `traffic_models`: AI models and training data
- `redis_data`: Redis persistent storage
- `mosquitto_data`: MQTT broker data
- `mosquitto_logs`: MQTT broker logs

### 6. Domain Configuration

1. **Add domain** in Coolify:
   - Domain: `traffic.yourdomain.com`
   - Enable HTTPS: Yes (Let's Encrypt)
   - Port: `5000`

### 7. Health Checks

The application includes health checks:
- **Endpoint**: `http://localhost:5000/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### 8. Deploy

1. **Commit all changes** to your Git repository
2. **Push to the configured branch**
3. **Trigger deployment** in Coolify dashboard
4. **Monitor deployment logs** for any issues

## Post-Deployment Configuration

### 1. Verify Services

Access your deployed application and check:
- ✅ Main dashboard loads at `https://traffic.yourdomain.com`
- ✅ Health check responds at `https://traffic.yourdomain.com/health`
- ✅ Database is initialized
- ✅ Redis is connected
- ✅ MQTT broker is running

### 2. Initialize System Data

If needed, you can run initialization commands:

```bash
# Through Coolify terminal or container exec
docker exec -it smart-traffic-ai-system python config/setup.py
```

### 3. Upload AI Models (Optional)

If you have trained models, upload them to the persistent volume:
```bash
# Copy models to the container
docker cp your-model.pt smart-traffic-ai-system:/app/models/trained_models/
```

## Monitoring and Maintenance

### 1. Logs

View logs through Coolify dashboard or:
```bash
# Application logs
docker logs smart-traffic-ai-system

# Redis logs
docker logs traffic-redis

# MQTT logs
docker logs traffic-mosquitto
```

### 2. Database Backup

Create regular backups of the SQLite database:
```bash
# Backup database
docker exec smart-traffic-ai-system cp /app/data/traffic_system.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db
```

### 3. Updates

To update the application:
1. Push new code to your Git repository
2. Trigger redeploy in Coolify dashboard
3. Monitor deployment logs

### 4. Scaling

For high-traffic scenarios:
- Increase container resources in Coolify
- Consider horizontal scaling with multiple instances
- Use external Redis/PostgreSQL for better performance

## Troubleshooting

### Common Issues

1. **Container fails to start**:
   - Check environment variables
   - Verify all required files are in repository
   - Check Dockerfile syntax

2. **Database errors**:
   - Ensure persistent volume is mounted
   - Check database permissions
   - Verify SQLite installation

3. **AI model loading fails**:
   - Check model file permissions
   - Verify PyTorch/CUDA compatibility
   - Check available memory/CPU

4. **MQTT connection issues**:
   - Verify mosquitto service is running
   - Check network connectivity between containers
   - Validate MQTT configuration

### Performance Optimization

1. **Resource Allocation**:
   - CPU: Minimum 2 cores, recommended 4+ cores
   - Memory: Minimum 4GB, recommended 8GB+
   - Storage: SSD recommended for database performance

2. **Caching**:
   - Redis caching is configured for AI model results
   - Consider CDN for static assets

3. **Database Optimization**:
   - For production, consider PostgreSQL instead of SQLite
   - Regular database maintenance and cleanup

## Security Considerations

1. **Environment Variables**:
   - Use strong, unique secrets
   - Don't commit secrets to Git
   - Rotate keys regularly

2. **Network Security**:
   - Use HTTPS for all external communications
   - Consider VPN for MQTT if exposed externally
   - Implement proper firewall rules

3. **Data Protection**:
   - Regular backups
   - Encrypt sensitive data
   - Comply with local privacy regulations

## Support

For deployment issues:
1. Check Coolify documentation
2. Review application logs
3. Consult Smart Traffic AI System documentation
4. Check GitHub issues/discussions

## Useful Commands

```bash
# Check container status
docker ps

# View live logs
docker logs -f smart-traffic-ai-system

# Access container shell
docker exec -it smart-traffic-ai-system bash

# Check system resources
docker stats

# Restart services
docker-compose restart smart-traffic-ai
```

This guide should help you successfully deploy the Smart Traffic AI System on Coolify with full functionality and monitoring capabilities.
