"""
🚦 Smart Traffic AI System - Logging System Demo
Demonstrates the comprehensive logging capabilities
"""

import time
import random
from datetime import datetime
from src.utils.logger import initialize_logging, get_logger, performance_monitor

def simulate_vehicle_detection():
    """Simulate vehicle detection with logging"""
    ai_logger = get_logger("ai_engine")
    
    # Simulate detection results
    detections = {
        "total_vehicles": random.randint(5, 25),
        "by_direction": {
            "north": random.randint(0, 8),
            "south": random.randint(0, 8),
            "east": random.randint(0, 8),
            "west": random.randint(0, 8)
        },
        "vehicle_types": ["car", "truck", "motorcycle", "bus"],
        "confidence": round(random.uniform(0.8, 0.99), 2)
    }
    
    ai_logger.vehicle_detection("intersection_demo", detections)
    return detections

@performance_monitor("demo_component")
def simulate_slow_operation():
    """Simulate a slow operation to test performance monitoring"""
    # Simulate processing time
    time.sleep(random.uniform(0.1, 0.5))
    return "Operation completed"

def simulate_traffic_control():
    """Simulate traffic light control with logging"""
    traffic_logger = get_logger("traffic_controller")
    
    # Simulate traffic light optimization
    timing_change = {
        "previous_green": 30,
        "new_green": random.randint(25, 50),
        "reason": random.choice(["high_traffic_detected", "emergency_vehicle", "optimization"])
    }
    
    traffic_logger.light_control("intersection_demo", "optimize_timing", timing_change)
    
    # Simulate emergency event occasionally
    if random.random() < 0.2:  # 20% chance
        emergency_details = {
            "vehicle_count": random.randint(40, 60),
            "threshold": 30,
            "action_taken": "emergency_protocol_activated"
        }
        traffic_logger.emergency_event("intersection_demo", "extremely_high_traffic", emergency_details)

def simulate_sensor_data():
    """Simulate sensor data collection with logging"""
    sensor_logger = get_logger("sensor_manager")
    
    # Simulate various sensor readings
    sensors = [
        {"id": "temp_001", "type": "temperature", "value": random.uniform(-5, 35)},
        {"id": "humid_001", "type": "humidity", "value": random.uniform(30, 90)},
        {"id": "flow_001", "type": "traffic_flow", "value": random.randint(0, 100)},
        {"id": "noise_001", "type": "noise_level", "value": random.randint(40, 80)}
    ]
    
    for sensor in sensors:
        sensor_logger.sensor_data(sensor["id"], sensor)

def simulate_web_requests():
    """Simulate web API requests with logging"""
    web_logger = get_logger("web_interface")
    
    # Simulate various API endpoints
    endpoints = [
        ("/api/status", "GET", 200, random.uniform(0.01, 0.1)),
        ("/api/intersections", "GET", 200, random.uniform(0.05, 0.2)),
        ("/api/predictions", "POST", 201, random.uniform(0.1, 0.3)),
        ("/dashboard", "GET", 200, random.uniform(0.02, 0.15))
    ]
    
    for endpoint, method, status, duration in endpoints:
        web_logger.api_request(endpoint, method, status, duration, 
                              user_agent="Demo Browser", ip="127.0.0.1")

def simulate_errors():
    """Simulate various error conditions"""
    error_logger = get_logger("system_errors")
    
    # Simulate different types of errors
    errors = [
        ("Camera connection failed", ConnectionError("Camera 1 timeout")),
        ("Database query slow", TimeoutError("Query timeout after 30s")),
        ("Sensor reading invalid", ValueError("Temperature reading out of range: 150°C"))
    ]
    
    for message, error in errors:
        if random.random() < 0.3:  # 30% chance of each error
            error_logger.error(message, error=error, severity="medium")

def main():
    """Main demo function"""
    print("🚦 Smart Traffic AI System - Logging Demo")
    print("=" * 50)
    
    # Initialize the logging system
    logging_config = {
        "level": "DEBUG",
        "log_dir": "logs",
        "max_file_size": "10 MB",
        "retention": "7 days",
        "compression": "zip",
        "enable_console": True,
        "enable_file": True,
        "enable_json": True,
        "enable_performance": True
    }
    
    logging_system = initialize_logging(logging_config)
    
    # Get system logger
    system_logger = get_logger("demo_system")
    
    # Log demo start
    system_logger.info("Starting logging system demonstration", 
                      demo_version="1.0", timestamp=datetime.now().isoformat())
    
    print("\n🔄 Running logging demonstrations...")
    print("📁 Check the 'logs' directory for output files")
    print("📊 Multiple log formats: plain text, JSON, and performance logs")
    print("\n" + "=" * 50)
    
    # Run simulation cycles
    for cycle in range(5):
        print(f"\n🔄 Simulation Cycle {cycle + 1}/5")
        
        # Simulate system activity
        detections = simulate_vehicle_detection()
        simulate_traffic_control()
        simulate_sensor_data()
        simulate_web_requests()
        
        # Test performance monitoring
        result = simulate_slow_operation()
        
        # Occasionally simulate errors
        if cycle > 0:  # Skip errors in first cycle
            simulate_errors()
        
        # Log cycle completion
        system_logger.info(f"Simulation cycle {cycle + 1} completed", 
                          cycle=cycle + 1, vehicles_detected=detections["total_vehicles"])
        
        # Brief pause between cycles
        time.sleep(1)
    
    # Demonstrate traffic prediction logging
    prediction_logger = get_logger("ai_engine")
    prediction_data = {
        "short_term": random.randint(15, 30),
        "medium_term": random.randint(20, 40),
        "long_term": random.randint(25, 50),
        "confidence": 0.85,
        "model_version": "v2.1"
    }
    prediction_logger.traffic_prediction("intersection_demo", prediction_data)
    
    # Final system status
    system_logger.info("Logging demonstration completed successfully", 
                      total_cycles=5, duration="5 seconds")
    
    print("\n✅ Logging demonstration completed!")
    print("\n📁 Generated log files:")
    print("   📄 logs/smart_traffic_YYYY-MM-DD.log - Main application log")
    print("   📄 logs/errors_YYYY-MM-DD.log - Error-only log") 
    print("   📄 logs/smart_traffic_structured_YYYY-MM-DD.json - Structured JSON log")
    print("   📄 logs/performance_YYYY-MM-DD.log - Performance metrics log")
    
    print("\n🔍 Log Features Demonstrated:")
    print("   ✓ Component-specific logging with context")
    print("   ✓ Structured event logging (vehicle detection, traffic control)")
    print("   ✓ Performance monitoring with automatic timing")
    print("   ✓ Error logging with exception details and stack traces")
    print("   ✓ Emergency event logging")
    print("   ✓ API request logging with metrics")
    print("   ✓ Sensor data logging")
    print("   ✓ Multiple output formats (console, file, JSON)")
    print("   ✓ Log rotation and compression")
    print("   ✓ Configurable log levels and retention")
    
    print("\n🎯 Next Steps:")
    print("   1. Review the generated log files")
    print("   2. Integrate logging into your specific components")
    print("   3. Customize log levels and formats as needed")
    print("   4. Set up log monitoring and alerting for production")

if __name__ == "__main__":
    main()
