"""
🗄️ Database Setup and Initialization Script
Script thiết lập và khởi tạo cơ sở dữ liệu cho hệ thống Smart Traffic AI
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Class để thiết lập cơ sở dữ liệu"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite in data directory
            self.data_dir = Path("data")
            self.data_dir.mkdir(exist_ok=True)
            self.database_url = f"sqlite:///{self.data_dir}/traffic_data.db"
        else:
            self.database_url = database_url
        
        self.engine = None
        self.session_factory = None
        
        logger.info(f"🗄️ Database setup initialized with URL: {self.database_url}")
    
    def create_engine_and_session(self):
        """Tạo engine và session factory"""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                connect_args={'check_same_thread': False} if 'sqlite' in self.database_url else {}
            )
            
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("✅ Database engine and session factory created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database engine: {e}")
            return False
    
    def load_schema(self) -> str:
        """Load database schema from SQL file"""
        schema_path = Path("config/database_schema.sql")
        
        if not schema_path.exists():
            logger.error(f"❌ Schema file not found: {schema_path}")
            return None
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            logger.info("✅ Database schema loaded")
            return schema_sql
            
        except Exception as e:
            logger.error(f"❌ Failed to load schema: {e}")
            return None
    
    def execute_schema(self, schema_sql: str) -> bool:
        """Execute database schema SQL"""
        if not self.engine:
            logger.error("❌ Database engine not initialized")
            return False
        
        try:
            # Split schema into individual statements
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            with self.engine.connect() as connection:
                for statement in statements:
                    if statement:
                        connection.execute(text(statement))
                connection.commit()
            
            logger.info("✅ Database schema executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to execute schema: {e}")
            return False
    
    def verify_database(self) -> bool:
        """Verify database tables were created correctly"""
        try:
            with self.engine.connect() as connection:
                # Check if main tables exist
                tables_to_check = [
                    'intersections', 'traffic_lights', 'vehicle_detections',
                    'traffic_flow', 'sensor_data', 'performance_metrics'
                ]
                
                for table in tables_to_check:
                    result = connection.execute(text(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                    ))
                    if not result.fetchone():
                        logger.error(f"❌ Table {table} not found")
                        return False
                
                # Check sample data
                result = connection.execute(text("SELECT COUNT(*) FROM intersections"))
                count = result.fetchone()[0]
                
                if count == 0:
                    logger.warning("⚠️ No sample data found in intersections table")
                else:
                    logger.info(f"✅ Found {count} sample intersections")
                
                connection.commit()
            
            logger.info("✅ Database verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")
            return False
    
    def create_data_directories(self):
        """Create necessary data directories"""
        directories = [
            "data",
            "data/logs",
            "data/models",
            "data/backups",
            "data/exports",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")
    
    def create_default_config(self):
        """Create default configuration files"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Default configuration for simulation mode
        default_config = {
            "mode": "simulation",
            "database": {
                "database_url": self.database_url,
                "redis_url": "redis://localhost:6379",
                "backup_interval_hours": 6,
                "data_retention_days": 365
            },
            "camera": {
                "camera_id": -1,  # Simulation mode
                "resolution": [1920, 1080],
                "fps": 30,
                "detection_zones": [
                    [0, 0, 960, 540],      # North
                    [960, 0, 1920, 540],   # East  
                    [960, 540, 1920, 1080], # South
                    [0, 540, 960, 1080]    # West
                ]
            },
            "ai_model": {
                "model_type": "YOLOv8",
                "model_path": "models/yolov8n.pt",
                "confidence_threshold": 0.7,
                "nms_threshold": 0.45,
                "device": "auto"
            },
            "traffic_light": {
                "min_green_time": 15,
                "max_green_time": 120,
                "yellow_time": 3,
                "adaptive_timing": True
            },
            "sensors": {
                "mqtt_broker_host": "localhost",
                "mqtt_broker_port": 1883,
                "collection_interval": 2.0,
                "ultrasonic_sensors": [
                    {"trigger_pin": 18, "echo_pin": 24}
                ],
                "radar_sensors": [
                    {"serial_port": "/dev/ttyUSB0"}
                ],
                "pressure_sensors": [
                    {"analog_pin": 0}
                ]
            },
            "web_interface": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            },
            "logging": {
                "log_level": "INFO",
                "log_file": "logs/smart_traffic.log"
            }
        }
        
        config_file = config_dir / "default_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"✅ Created default configuration: {config_file}")
        
        # Create environment-specific configs
        for env in ['development', 'production']:
            env_config = default_config.copy()
            if env == 'production':
                env_config['mode'] = 'production'
                env_config['web_interface']['debug'] = False
                env_config['logging']['log_level'] = 'INFO'
                env_config['camera']['camera_id'] = 0  # Real camera
            
            env_file = config_dir / f"{env}_config.yaml"
            with open(env_file, 'w', encoding='utf-8') as f:
                yaml.dump(env_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"✅ Created {env} configuration: {env_file}")
    
    def setup_complete_system(self) -> bool:
        """Complete system setup"""
        logger.info("🚀 Starting complete system setup...")
        
        # Step 1: Create directories
        self.create_data_directories()
        
        # Step 2: Create configuration files
        self.create_default_config()
        
        # Step 3: Setup database
        if not self.create_engine_and_session():
            return False
        
        # Step 4: Load and execute schema
        schema_sql = self.load_schema()
        if not schema_sql:
            return False
        
        if not self.execute_schema(schema_sql):
            return False
        
        # Step 5: Verify database
        if not self.verify_database():
            return False
        
        logger.info("🎉 System setup completed successfully!")
        return True

def main():
    """Main setup function"""
    print("🚦 Smart Traffic AI System - Database Setup")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Setup Smart Traffic AI System Database")
    parser.add_argument("--database-url", help="Database URL (default: SQLite)")
    parser.add_argument("--mode", choices=['simulation', 'development', 'production'], 
                       default='simulation', help="Setup mode")
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = DatabaseSetup(args.database_url)
    
    # Run complete setup
    success = setup.setup_complete_system()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run the system: python run.py --simulation")
        print("2. Open web interface: http://localhost:8000")
        print("3. Check logs: tail -f logs/smart_traffic.log")
        print("\n🗄️ Database location:", setup.database_url)
    else:
        print("\n❌ Setup failed! Check logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
