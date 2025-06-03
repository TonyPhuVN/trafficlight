"""
🚦 Smart Traffic AI System - Main Configuration
Cấu hình chính cho hệ thống AI điều khiển đèn giao thông
"""

import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class SystemMode(Enum):
    """Chế độ hoạt động của hệ thống"""
    SIMULATION = "simulation"      # Mô phỏng không cần hardware
    DEVELOPMENT = "development"    # Phát triển với hardware giả lập
    PRODUCTION = "production"      # Sản xuất với hardware thật

class VehicleType(Enum):
    """Loại phương tiện"""
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    EMERGENCY = "emergency"

@dataclass
class CameraConfig:
    """Cấu hình camera"""
    camera_id: int = 0
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    detection_zones: List[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2)
    sensitivity: float = 0.8
    auto_exposure: bool = True
    night_mode: bool = True
    
    def __post_init__(self):
        if self.detection_zones is None:
            # Zones mặc định cho 4 hướng
            w, h = self.resolution
            self.detection_zones = [
                (0, 0, w//2, h//2),         # Hướng Bắc
                (w//2, 0, w, h//2),         # Hướng Đông
                (w//2, h//2, w, h),         # Hướng Nam
                (0, h//2, w//2, h),         # Hướng Tây
            ]

@dataclass
class AIModelConfig:
    """Cấu hình mô hình AI"""
    model_type: str = "YOLOv8"
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.7
    nms_threshold: float = 0.45
    max_detections: int = 1000
    device: str = "auto"  # auto, cpu, cuda
    
    # Classes để detect
    vehicle_classes: List[str] = None
    
    def __post_init__(self):
        if self.vehicle_classes is None:
            self.vehicle_classes = [
                "car", "truck", "bus", "motorcycle", "bicycle",
                "ambulance", "fire truck", "police car"
            ]

@dataclass
class TrafficLightConfig:
    """Cấu hình đèn giao thông"""
    # Thời gian cơ bản (giây)
    min_green_time: int = 15
    max_green_time: int = 120
    yellow_time: int = 3
    red_clearance_time: int = 2
    all_red_time: int = 1
    
    # Thời gian ưu tiên
    emergency_override: bool = True
    emergency_green_time: int = 30
    pedestrian_crossing_time: int = 20
    
    # Adaptive timing
    adaptive_timing: bool = True
    rush_hour_multiplier: float = 1.5
    night_time_minimum: int = 10

@dataclass
class SensorConfig:
    """Cấu hình cảm biến"""
    # Pressure sensors
    pressure_sensors: List[str] = None
    pressure_threshold: float = 50.0  # kg
    
    # Loop detectors
    loop_detectors: List[str] = None
    
    # Weather sensors
    weather_sensor_enabled: bool = True
    rain_sensor_pin: int = 4
    temperature_sensor_pin: int = 18
    
    # IoT connectivity
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topics: Dict[str, str] = None
    
    def __post_init__(self):
        if self.pressure_sensors is None:
            self.pressure_sensors = ["north", "south", "east", "west"]
        
        if self.loop_detectors is None:
            self.loop_detectors = ["north_in", "north_out", "south_in", "south_out",
                                 "east_in", "east_out", "west_in", "west_out"]
        
        if self.mqtt_topics is None:
            self.mqtt_topics = {
                "vehicle_count": "traffic/vehicle_count",
                "light_status": "traffic/light_status",
                "sensor_data": "traffic/sensors",
                "emergency": "traffic/emergency"
            }

@dataclass
class DatabaseConfig:
    """Cấu hình database"""
    database_url: str = "sqlite:///data/traffic_data.db"
    redis_url: str = "redis://localhost:6379"
    backup_interval_hours: int = 6
    data_retention_days: int = 365
    
    # Tables
    enable_analytics: bool = True
    enable_historical: bool = True
    enable_realtime: bool = True

@dataclass
class WebInterfaceConfig:
    """Cấu hình giao diện web"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    secret_key: str = "your-secret-key-change-this"
    
    # Authentication
    enable_auth: bool = True
    admin_username: str = "admin"
    admin_password: str = "change-this-password"
    
    # Real-time updates
    websocket_enabled: bool = True
    update_interval_seconds: int = 1

@dataclass
class LoggingConfig:
    """Cấu hình logging"""
    log_level: str = "INFO"
    log_file: str = "logs/smart_traffic.log"
    log_rotation: str = "1 week"
    log_retention: str = "4 weeks"
    
    # Modules logging
    modules: Dict[str, str] = None
    
    def __post_init__(self):
        if self.modules is None:
            self.modules = {
                "ai_engine": "INFO",
                "camera_system": "INFO",
                "traffic_controller": "INFO",
                "data_processor": "DEBUG",
                "web_interface": "INFO"
            }

class SmartTrafficConfig:
    """Cấu hình tổng thể cho hệ thống"""
    
    def __init__(self, mode: SystemMode = SystemMode.SIMULATION):
        self.mode = mode
        self.camera = CameraConfig()
        self.ai_model = AIModelConfig()
        self.traffic_light = TrafficLightConfig()
        self.sensors = SensorConfig()
        self.database = DatabaseConfig()
        self.web_interface = WebInterfaceConfig()
        self.logging = LoggingConfig()
        
        # Load from environment variables
        self._load_from_env()
        
        # Apply mode-specific configurations
        self._apply_mode_config()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv("DATABASE_URL"):
            self.database.database_url = os.getenv("DATABASE_URL")
        
        if os.getenv("REDIS_URL"):
            self.database.redis_url = os.getenv("REDIS_URL")
        
        # Web interface
        if os.getenv("WEB_HOST"):
            self.web_interface.host = os.getenv("WEB_HOST")
        
        if os.getenv("WEB_PORT"):
            self.web_interface.port = int(os.getenv("WEB_PORT"))
        
        if os.getenv("SECRET_KEY"):
            self.web_interface.secret_key = os.getenv("SECRET_KEY")
        
        # AI Model
        if os.getenv("AI_DEVICE"):
            self.ai_model.device = os.getenv("AI_DEVICE")
        
        # MQTT
        if os.getenv("MQTT_BROKER"):
            self.sensors.mqtt_broker = os.getenv("MQTT_BROKER")
    
    def _apply_mode_config(self):
        """Apply mode-specific configurations"""
        if self.mode == SystemMode.SIMULATION:
            # Simulation mode - no real hardware
            self.sensors.weather_sensor_enabled = False
            self.camera.camera_id = -1  # Use simulated camera
            self.database.database_url = "sqlite:///data/simulation.db"
            
        elif self.mode == SystemMode.DEVELOPMENT:
            # Development mode - limited hardware
            self.web_interface.debug = True
            self.logging.log_level = "DEBUG"
            self.ai_model.device = "cpu"  # Force CPU for development
            
        elif self.mode == SystemMode.PRODUCTION:
            # Production mode - full features
            self.web_interface.debug = False
            self.logging.log_level = "INFO"
            self.web_interface.enable_auth = True
    
    def save_to_file(self, filepath: str):
        """Save configuration to YAML file"""
        import yaml
        
        config_dict = {
            "mode": self.mode.value,
            "camera": self.camera.__dict__,
            "ai_model": self.ai_model.__dict__,
            "traffic_light": self.traffic_light.__dict__,
            "sensors": self.sensors.__dict__,
            "database": self.database.__dict__,
            "web_interface": self.web_interface.__dict__,
            "logging": self.logging.__dict__,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """Load configuration from YAML file"""
        import yaml
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        mode = SystemMode(config_dict.get("mode", "simulation"))
        config = cls(mode)
        
        # Update configurations
        for key, value in config_dict.items():
            if hasattr(config, key) and isinstance(value, dict):
                obj = getattr(config, key)
                for attr, val in value.items():
                    if hasattr(obj, attr):
                        setattr(obj, attr, val)
        
        return config

# Default configurations for different scenarios
INTERSECTION_CONFIGS = {
    "small_intersection": {
        "camera": {"resolution": (1280, 720), "fps": 15},
        "traffic_light": {"min_green_time": 10, "max_green_time": 60},
        "ai_model": {"confidence_threshold": 0.6}
    },
    
    "busy_intersection": {
        "camera": {"resolution": (1920, 1080), "fps": 30},
        "traffic_light": {"min_green_time": 20, "max_green_time": 180},
        "ai_model": {"confidence_threshold": 0.8}
    },
    
    "highway_on_ramp": {
        "camera": {"resolution": (2560, 1440), "fps": 60},
        "traffic_light": {"min_green_time": 30, "max_green_time": 300},
        "ai_model": {"confidence_threshold": 0.9}
    }
}

# Create default config instance
default_config = SmartTrafficConfig()

if __name__ == "__main__":
    # Test configuration
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    print("🚦 Smart Traffic AI System Configuration")
    print(f"Mode: {config.mode.value}")
    print(f"Camera Resolution: {config.camera.resolution}")
    print(f"AI Model: {config.ai_model.model_type}")
    print(f"Database: {config.database.database_url}")
    
    # Save configuration
    config.save_to_file("config/default_config.yaml")
    print("✅ Configuration saved to config/default_config.yaml")
