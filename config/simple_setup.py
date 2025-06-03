"""
🗄️ Simple Database Setup Script
Script thiết lập cơ sở dữ liệu đơn giản cho hệ thống Smart Traffic AI
"""

import os
import sqlite3
import json
from pathlib import Path

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = [
        "data",
        "data/logs", 
        "data/models",
        "data/backups",
        "logs",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_database():
    """Tạo cơ sở dữ liệu SQLite"""
    db_path = "data/traffic_data.db"
    
    # Read schema file
    schema_path = "config/database_schema.sql"
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    try:
        # Create database and execute schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Split and execute statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database created successfully: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def create_config_files():
    """Tạo các file cấu hình"""
    
    # Default configuration
    default_config = {
        "mode": "simulation",
        "database": {
            "database_url": "sqlite:///data/traffic_data.db",
            "backup_interval_hours": 6
        },
        "camera": {
            "camera_id": -1,
            "resolution": [1920, 1080],
            "fps": 30,
            "detection_zones": [
                [0, 0, 960, 540],
                [960, 0, 1920, 540], 
                [960, 540, 1920, 1080],
                [0, 540, 960, 1080]
            ]
        },
        "ai_model": {
            "model_type": "YOLOv8",
            "model_path": "models/yolov8n.pt",
            "confidence_threshold": 0.7,
            "device": "cpu"
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
            "collection_interval": 2.0
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
    
    # Save as JSON (simpler than YAML)
    config_file = "config/default_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created configuration file: {config_file}")

def download_yolo_model():
    """Tải model YOLO nếu chưa có"""
    model_path = "models/yolov8n.pt"
    
    if os.path.exists(model_path):
        print(f"✅ YOLO model already exists: {model_path}")
        return True
    
    try:
        print("📥 Downloading YOLOv8 model...")
        # Try to import ultralytics and download model
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # This will download the model
        
        # Move to models directory
        import shutil
        if os.path.exists('yolov8n.pt'):
            shutil.move('yolov8n.pt', model_path)
            print(f"✅ YOLO model downloaded: {model_path}")
            return True
    except Exception as e:
        print(f"⚠️ Could not download YOLO model (will use simulation): {e}")
        
        # Create a dummy model file
        with open(model_path, 'w') as f:
            f.write("# Dummy YOLO model file for simulation mode\n")
        print(f"✅ Created dummy model file: {model_path}")
        return True

def main():
    """Main setup function"""
    print("🚦 Smart Traffic AI System - Simple Setup")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Step 2: Create database
    print("\n🗄️ Setting up database...")
    if not create_database():
        print("❌ Database setup failed")
        return 1
    
    # Step 3: Create config files
    print("\n⚙️ Creating configuration files...")
    create_config_files()
    
    # Step 4: Download YOLO model
    print("\n🤖 Setting up AI model...")
    download_yolo_model()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test traffic simulation: python src/data_simulation/traffic_simulator.py")
    print("2. Run the system: python run.py --simulation")
    print("3. Open web interface: http://localhost:8000")
    
    return 0

if __name__ == "__main__":
    exit(main())
