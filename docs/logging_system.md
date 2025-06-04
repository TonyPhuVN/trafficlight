# 🔧 Smart Traffic AI System - Advanced Logging Documentation

## Overview

The Smart Traffic AI System includes a comprehensive, production-ready logging system built on top of [Loguru](https://loguru.readthedocs.io/), providing structured logging, performance monitoring, and multiple output formats for effective system monitoring and debugging.

## Features

### 🎯 Core Capabilities

- **Multiple Log Formats**: Console, file, JSON structured logs, and performance logs
- **Component-Specific Logging**: Each system component has its own logger with context
- **Structured Event Logging**: Special methods for traffic events (detection, prediction, control)
- **Performance Monitoring**: Automatic timing with decorators and manual performance logging
- **Error Handling**: Enhanced error logging with exception details and stack traces
- **Log Rotation**: Automatic log rotation by size and time with compression
- **Configurable Output**: Enable/disable different log outputs and customize formats

### 📊 Log Types

1. **Application Logs**: Main system events and operations
2. **Error Logs**: Error-only logs for quick troubleshooting
3. **Structured JSON Logs**: Machine-readable logs for analysis
4. **Performance Logs**: Timing and performance metrics

## Quick Start

### Basic Usage

```python
from src.utils.logger import get_logger

# Get a component-specific logger
logger = get_logger("my_component")

# Basic logging
logger.info("System initialized")
logger.error("Connection failed", error=some_exception)
```

### Structured Event Logging

```python
# Vehicle detection logging
logger.vehicle_detection("intersection_1", {
    "total_vehicles": 15,
    "by_direction": {"north": 5, "south": 3, "east": 4, "west": 3},
    "vehicle_types": ["car", "truck", "motorcycle"]
})

# Traffic light control logging
logger.light_control("intersection_1", "optimize_timing", {
    "previous_green": 30,
    "new_green": 45,
    "reason": "high_traffic_detected"
})

# Emergency event logging
logger.emergency_event("intersection_1", "extremely_high_traffic", {
    "vehicle_count": 50,
    "threshold": 30,
    "action_taken": "emergency_protocol_activated"
})
```

### Performance Monitoring

```python
from src.utils.logger import performance_monitor

# Automatic performance monitoring with decorator
@performance_monitor("my_component")
def process_camera_frame(frame):
    # Processing logic here
    return result

# Manual performance logging
start_time = time.time()
# ... do work ...
duration = time.time() - start_time
logger.performance("image_processing", duration)
```

## Configuration

### Default Configuration

```python
logging_config = {
    "level": "INFO",
    "log_dir": "logs",
    "max_file_size": "50 MB",
    "retention": "30 days",
    "compression": "zip",
    "enable_console": True,
    "enable_file": True,
    "enable_json": True,
    "enable_performance": True
}
```

### Custom Configuration

```python
from src.utils.logger import initialize_logging

# Custom configuration
custom_config = {
    "level": "DEBUG",
    "log_dir": "custom_logs",
    "max_file_size": "100 MB",
    "retention": "60 days",
    "enable_console": False,  # Disable console output
    "enable_json": False      # Disable JSON logs
}

logging_system = initialize_logging(custom_config)
```

## Log Formats

### Console Output (Colored)
```
2025-06-04 19:30:15 | INFO     | ai_engine:detect_vehicles:45 | Vehicle detection completed for intersection_1
2025-06-04 19:30:15 | ERROR    | camera_system:connect:23 | Camera connection failed | ConnectionError: timeout
```

### File Output (Detailed)
```
2025-06-04 19:30:15.123 | INFO     | ai_engine:detect_vehicles:45 | {"component": "ai_engine", "intersection_id": "intersection_1"} | Vehicle detection completed for intersection_1
```

### JSON Structured Output
```json
{
    "text": "Vehicle detection completed for intersection_1",
    "record": {
        "elapsed": {"repr": "0:00:01.234567", "seconds": 1.234567},
        "exception": null,
        "extra": {
            "component": "ai_engine",
            "event_type": "vehicle_detection",
            "intersection_id": "intersection_1",
            "detections": {"total_vehicles": 15, "by_direction": {...}}
        },
        "file": {"name": "vehicle_detector.py", "path": "/path/to/file.py"},
        "function": "detect_vehicles",
        "level": {"icon": "ℹ️", "name": "INFO", "no": 20},
        "line": 45,
        "message": "Vehicle detection completed for intersection_1",
        "module": "vehicle_detector",
        "name": "ai_engine",
        "process": {"id": 12345, "name": "MainProcess"},
        "thread": {"id": 140123456789, "name": "MainThread"},
        "time": {"repr": "2025-06-04 19:30:15.123456+07:00", "timestamp": 1733327415.123456}
    }
}
```

### Performance Log Output
```
2025-06-04 19:30:15.123 | PERF | Performance: image_processing took 0.125s
2025-06-04 19:30:15.234 | PERF | Performance: vehicle_detection took 0.089s
2025-06-04 19:30:15.345 | PERF | Performance: traffic_optimization took 0.056s
```

## Component Logger Methods

### Standard Logging Methods

```python
logger.info(message, **kwargs)       # Informational messages
logger.debug(message, **kwargs)      # Debug information
logger.warning(message, **kwargs)    # Warning messages
logger.error(message, error=None, **kwargs)    # Error messages with optional exception
logger.critical(message, error=None, **kwargs) # Critical system issues
```

### Specialized Event Methods

```python
# Vehicle detection events
logger.vehicle_detection(intersection_id, detections_dict)

# Traffic prediction events
logger.traffic_prediction(intersection_id, prediction_dict)

# Traffic light control actions
logger.light_control(intersection_id, action, timing_dict)

# Sensor data collection
logger.sensor_data(sensor_id, data_dict)

# Emergency events
logger.emergency_event(intersection_id, event_type, details_dict)

# API request logging
logger.api_request(endpoint, method, status_code, duration, **kwargs)

# Performance metrics
logger.performance(operation, duration, **kwargs)
```

## File Structure

The logging system creates the following file structure:

```
logs/
├── smart_traffic_2025-06-04.log              # Main application log
├── smart_traffic_2025-06-04.log.zip          # Compressed older logs
├── errors_2025-06-04.log                     # Error-only log
├── smart_traffic_structured_2025-06-04.json  # Structured JSON log
└── performance_2025-06-04.log                # Performance metrics log
```

## Integration Examples

### In System Components

```python
# In AI Engine component
class VehicleDetector:
    def __init__(self):
        self.logger = get_logger("ai_engine")
    
    def detect_vehicles(self, frame):
        start_time = time.time()
        
        try:
            # Detection logic here
            results = self.process_frame(frame)
            
            # Log successful detection
            self.logger.vehicle_detection("intersection_1", results)
            
            # Log performance
            duration = time.time() - start_time
            self.logger.performance("vehicle_detection", duration)
            
            return results
            
        except Exception as e:
            self.logger.error("Vehicle detection failed", error=e)
            raise
```

### In Web Interface

```python
# In FastAPI application
from fastapi import FastAPI, Request
import time

app = FastAPI()
web_logger = get_logger("web_interface")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    web_logger.api_request(
        str(request.url.path),
        request.method,
        response.status_code,
        duration,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host
    )
    
    return response
```

### Error Handling with Decorators

```python
from src.utils.logger import log_exception

class CameraManager:
    def __init__(self):
        self.logger = get_logger("camera_system")
    
    @log_exception(logger)
    def connect_camera(self, camera_id):
        # Camera connection logic
        # Any exceptions will be automatically logged
        pass
```

## Production Deployment

### Log Monitoring

For production environments, consider:

1. **Log Aggregation**: Use tools like ELK Stack (Elasticsearch, Logstash, Kibana) or Fluentd
2. **Alerting**: Set up alerts for ERROR and CRITICAL level logs
3. **Metrics**: Extract metrics from performance logs for monitoring dashboards
4. **Storage**: Configure appropriate log retention and archival policies

### Configuration for Production

```python
production_config = {
    "level": "INFO",                # Reduce verbosity
    "log_dir": "/var/log/smart_traffic",
    "max_file_size": "100 MB",     # Larger files for production
    "retention": "90 days",        # Longer retention
    "compression": "gzip",         # Better compression
    "enable_console": False,       # Disable console in production
    "enable_file": True,
    "enable_json": True,           # Enable for log analysis
    "enable_performance": True
}
```

### Log Analysis Queries

Example queries for structured JSON logs:

```bash
# Find all error events
jq 'select(.record.level.name == "ERROR")' smart_traffic_structured_*.json

# Find vehicle detection events
jq 'select(.record.extra.event_type == "vehicle_detection")' smart_traffic_structured_*.json

# Find performance issues (>1 second)
jq 'select(.record.extra.performance == true and .record.extra.duration_ms > 1000)' smart_traffic_structured_*.json

# Emergency events
jq 'select(.record.extra.event_type == "emergency")' smart_traffic_structured_*.json
```

## Demo and Testing

Run the logging demo to see all features in action:

```bash
python demo_logging.py
```

This will:
- Initialize the logging system
- Simulate various traffic system events
- Generate sample logs in all formats
- Demonstrate performance monitoring
- Show error handling capabilities

## Best Practices

1. **Use Appropriate Log Levels**: 
   - DEBUG: Detailed debugging information
   - INFO: General system operations
   - WARNING: Unexpected but handled situations
   - ERROR: Error conditions that need attention
   - CRITICAL: Serious errors that may abort the program

2. **Include Context**: Always provide relevant context with log messages

3. **Structured Data**: Use the specialized event methods for consistent structured logging

4. **Performance Monitoring**: Use performance logging for critical operations

5. **Error Handling**: Always log exceptions with the `error` parameter for full stack traces

6. **Component Naming**: Use consistent, descriptive names for component loggers

7. **Production Configuration**: Adjust log levels and outputs for production environments

This comprehensive logging system provides the foundation for effective monitoring, debugging, and maintenance of the Smart Traffic AI System.
