"""
🔧 Advanced Logging System for Smart Traffic AI System
Comprehensive logging with structured output, rotation, and monitoring
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
import json
import traceback
from functools import wraps

from loguru import logger
import psutil


class SmartTrafficLogger:
    """Advanced logging system for Smart Traffic AI System"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self._setup_logging()
        self._system_info = self._get_system_info()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration with environment variable support"""
        # Load configuration from environment variables or use defaults
        config = {
            "level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "log_dir": os.getenv("LOG_DIR", "logs"),
            "max_file_size": os.getenv("LOG_MAX_SIZE", "50 MB"),
            "retention": os.getenv("LOG_RETENTION", "30 days"),
            "compression": os.getenv("LOG_COMPRESSION", "zip"),
            "format": {
                "console": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
                "file": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra} | {message}"
            },
            "enable_console": os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true",
            "enable_file": os.getenv("LOG_ENABLE_FILE", "true").lower() == "true",
            "enable_json": os.getenv("LOG_ENABLE_JSON", "true").lower() == "true",
            "enable_performance": os.getenv("LOG_ENABLE_PERFORMANCE", "true").lower() == "true"
        }
        
        # Convert retention format (e.g., "30days" to "30 days")
        if "days" in config["retention"] and " " not in config["retention"]:
            config["retention"] = config["retention"].replace("days", " days")
            
        return config
    
    def _setup_logging(self):
        """Setup advanced logging configuration"""
        # Remove default handler
        logger.remove()
        
        # Create logs directory
        log_dir = Path(self.config["log_dir"])
        log_dir.mkdir(exist_ok=True)
        
        # Console logging (if enabled)
        if self.config["enable_console"]:
            logger.add(
                sys.stderr,
                format=self.config["format"]["console"],
                level=self.config["level"],
                colorize=True,
                diagnose=True
            )
        
        # File logging (if enabled)
        if self.config["enable_file"]:
            # Main application log
            logger.add(
                log_dir / "smart_traffic_{time:YYYY-MM-DD}.log",
                format=self.config["format"]["file"],
                level=self.config["level"],
                rotation="00:00",
                retention=self.config["retention"],
                compression=self.config["compression"],
                encoding="utf-8"
            )
            
            # Error-only log
            logger.add(
                log_dir / "errors_{time:YYYY-MM-DD}.log",
                format=self.config["format"]["file"],
                level="ERROR",
                rotation=self.config["max_file_size"],
                retention=self.config["retention"],
                compression=self.config["compression"],
                encoding="utf-8"
            )
        
        # JSON structured logging (if enabled)
        if self.config["enable_json"]:
            logger.add(
                log_dir / "smart_traffic_structured_{time:YYYY-MM-DD}.json",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {extra} | {message}",
                level=self.config["level"],
                rotation="00:00",
                retention=self.config["retention"],
                compression=self.config["compression"],
                serialize=True,
                encoding="utf-8"
            )
        
        # Performance logging (if enabled)
        if self.config["enable_performance"]:
            logger.add(
                log_dir / "performance_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | PERF | {message}",
                level="INFO",
                rotation="00:00",
                retention=self.config["retention"],
                compression=self.config["compression"],
                encoding="utf-8",
                filter=lambda record: record["extra"].get("performance", False)
            )
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for logging context"""
        return {
            "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown',
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "pid": os.getpid(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "started_at": datetime.now().isoformat()
        }
    
    def get_logger(self, name: str) -> 'ComponentLogger':
        """Get a component-specific logger"""
        return ComponentLogger(name, self._system_info)
    
    def log_system_startup(self, config: Dict[str, Any]):
        """Log system startup information"""
        logger.info(
            "Smart Traffic AI System Starting",
            extra={
                "event_type": "system_startup",
                "config": config,
                "system_info": self._system_info
            }
        )
    
    def log_system_shutdown(self, stats: Dict[str, Any]):
        """Log system shutdown information"""
        logger.info(
            "Smart Traffic AI System Shutting Down",
            extra={
                "event_type": "system_shutdown",
                "runtime_stats": stats,
                "system_info": self._system_info
            }
        )


class ComponentLogger:
    """Component-specific logger with enhanced functionality"""
    
    def __init__(self, component_name: str, system_info: Dict[str, Any]):
        self.component_name = component_name
        self.system_info = system_info
        self.logger = logger.bind(component=component_name)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with optional exception details"""
        extra = kwargs.copy()
        if error:
            extra.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, error: Exception = None, **kwargs):
        """Log critical message"""
        extra = kwargs.copy()
        if error:
            extra.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        self.logger.critical(message, extra=extra)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        extra = kwargs.copy()
        extra.update({
            "performance": True,
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "component": self.component_name
        })
        self.logger.info(f"Performance: {operation} took {duration:.3f}s", extra=extra)
    
    def vehicle_detection(self, intersection_id: str, detections: Dict[str, Any]):
        """Log vehicle detection events"""
        self.logger.info(
            f"Vehicle detection completed for {intersection_id}",
            extra={
                "event_type": "vehicle_detection",
                "intersection_id": intersection_id,
                "detections": detections,
                "component": self.component_name
            }
        )
    
    def traffic_prediction(self, intersection_id: str, prediction: Dict[str, Any]):
        """Log traffic prediction events"""
        self.logger.info(
            f"Traffic prediction generated for {intersection_id}",
            extra={
                "event_type": "traffic_prediction",
                "intersection_id": intersection_id,
                "prediction": prediction,
                "component": self.component_name
            }
        )
    
    def light_control(self, intersection_id: str, action: str, timing: Dict[str, Any]):
        """Log traffic light control actions"""
        self.logger.info(
            f"Traffic light control: {action} for {intersection_id}",
            extra={
                "event_type": "light_control",
                "intersection_id": intersection_id,
                "action": action,
                "timing": timing,
                "component": self.component_name
            }
        )
    
    def sensor_data(self, sensor_id: str, data: Dict[str, Any]):
        """Log sensor data events"""
        self.logger.debug(
            f"Sensor data received from {sensor_id}",
            extra={
                "event_type": "sensor_data",
                "sensor_id": sensor_id,
                "data": data,
                "component": self.component_name
            }
        )
    
    def emergency_event(self, intersection_id: str, event_type: str, details: Dict[str, Any]):
        """Log emergency events"""
        self.logger.critical(
            f"Emergency event: {event_type} at {intersection_id}",
            extra={
                "event_type": "emergency",
                "emergency_type": event_type,
                "intersection_id": intersection_id,
                "details": details,
                "component": self.component_name
            }
        )
    
    def api_request(self, endpoint: str, method: str, status_code: int, duration: float, **kwargs):
        """Log API requests"""
        self.logger.info(
            f"API {method} {endpoint} - {status_code} ({duration:.3f}s)",
            extra={
                "event_type": "api_request",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration": duration,
                "component": self.component_name,
                **kwargs
            }
        )


def performance_monitor(component_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get component logger
            if hasattr(args[0], 'logger') and hasattr(args[0].logger, 'performance'):
                component_logger = args[0].logger
            else:
                # Create a temporary logger
                temp_logger = ComponentLogger(component_name or func.__module__, {})
                component_logger = temp_logger
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                component_logger.performance(
                    f"{func.__name__}",
                    duration,
                    function=func.__name__,
                    module=func.__module__
                )
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                component_logger.error(
                    f"Function {func.__name__} failed after {duration:.3f}s",
                    error=e,
                    function=func.__name__,
                    module=func.__module__
                )
                raise
        return wrapper
    return decorator


def log_exception(component_logger: ComponentLogger):
    """Decorator to automatically log exceptions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                component_logger.error(
                    f"Exception in {func.__name__}",
                    error=e,
                    function=func.__name__,
                    module=func.__module__
                )
                raise
        return wrapper
    return decorator


# Create global logger instance
_global_logger = None

def get_logger(component_name: str) -> ComponentLogger:
    """Get a component logger (convenience function)"""
    global _global_logger
    if _global_logger is None:
        _global_logger = SmartTrafficLogger()
    return _global_logger.get_logger(component_name)


def initialize_logging(config: Optional[Dict[str, Any]] = None) -> SmartTrafficLogger:
    """Initialize the global logging system"""
    global _global_logger
    _global_logger = SmartTrafficLogger(config)
    return _global_logger


# Example usage and testing
if __name__ == "__main__":
    # Initialize logging
    logging_system = initialize_logging()
    
    # Get component loggers
    ai_logger = get_logger("ai_engine")
    camera_logger = get_logger("camera_system")
    traffic_logger = get_logger("traffic_controller")
    
    # Test different log types
    ai_logger.info("AI Engine initialized successfully")
    
    ai_logger.vehicle_detection("intersection_1", {
        "total_vehicles": 15,
        "by_direction": {"north": 5, "south": 3, "east": 4, "west": 3},
        "vehicle_types": ["car", "truck", "motorcycle"]
    })
    
    traffic_logger.light_control("intersection_1", "optimize_timing", {
        "previous_green": 30,
        "new_green": 45,
        "reason": "high_traffic_detected"
    })
    
    camera_logger.performance("frame_processing", 0.125)
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        ai_logger.error("Test error occurred", error=e)
    
    # Test emergency logging
    traffic_logger.emergency_event("intersection_1", "extremely_high_traffic", {
        "vehicle_count": 50,
        "threshold": 30,
        "action_taken": "emergency_protocol_activated"
    })
    
    print("✅ Logging system test completed. Check the 'logs' directory for output files.")
