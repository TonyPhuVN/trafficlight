#!/usr/bin/env python3
"""
Smart Traffic AI System - Setup Script
Handles installation and environment setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🚦 Smart Traffic AI System - Setup")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print("✅ Python version is compatible")

def install_dependencies(minimal=True):
    """Install Python dependencies"""
    requirements_file = "requirements-minimal.txt" if minimal else "requirements.txt"
    
    if not Path(requirements_file).exists():
        print(f"❌ {requirements_file} not found")
        return False
    
    print(f"📦 Installing dependencies from {requirements_file}...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--no-cache-dir", "-r", requirements_file
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data/traffic_data", 
        "models/trained_models",
        "config/environments"
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    print("✅ Directories created")

def create_env_file():
    """Create .env file with default settings"""
    env_content = """# Smart Traffic AI System - Environment Variables

# System Configuration
SYSTEM_MODE=development
PYTHONPATH=.

# Database
DATABASE_PATH=data/traffic_system.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION=30days
LOG_MAX_SIZE=50MB
LOG_ENABLE_JSON=true
LOG_ENABLE_PERFORMANCE=true
LOG_ENABLE_CONSOLE=true
LOG_ENABLE_FILE=true
LOG_COMPRESSION=zip

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=5000

# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Redis Configuration
REDIS_URL=redis://localhost:6379
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("🔧 Creating .env file...")
        env_file.write_text(env_content)
        print("✅ .env file created")
    else:
        print("ℹ️ .env file already exists")

def test_imports():
    """Test if critical imports work"""
    print("🧪 Testing critical imports...")
    
    critical_imports = [
        ("sqlite3", "Built-in SQLite"),
        ("json", "Built-in JSON"),
        ("os", "Built-in OS"),
        ("sys", "Built-in sys"),
        ("pathlib", "Built-in pathlib"),
    ]
    
    optional_imports = [
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"),
        ("yaml", "PyYAML"),
    ]
    
    # Test critical imports
    for module, name in critical_imports:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - CRITICAL")
            return False
    
    # Test optional imports
    for module, name in optional_imports:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️ {name} - Optional (install with: pip install {module})")
    
    return True

def run_basic_test():
    """Run a basic system test"""
    print("🔍 Running basic system test...")
    
    try:
        # Test logging system
        sys.path.insert(0, '.')
        from src.utils.logger import initialize_logging, get_logger
        
        # Initialize logging
        logging_config = {
            "level": "INFO",
            "log_dir": "logs",
            "enable_console": True,
            "enable_file": False,  # Don't create files during test
            "enable_json": False,
            "enable_performance": False
        }
        
        logging_system = initialize_logging(logging_config)
        logger = get_logger("setup_test")
        logger.info("Setup test successful")
        
        print("✅ Basic system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic system test failed: {e}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Ask user about installation type
    print("\nChoose installation type:")
    print("1. Minimal (core functionality only)")
    print("2. Full (all features)")
    
    choice = input("Enter choice (1 or 2) [default: 1]: ").strip()
    minimal = choice != "2"
    
    # Install dependencies
    if not install_dependencies(minimal=minimal):
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n❌ Setup failed during import tests")
        sys.exit(1)
    
    # Run basic test
    if not run_basic_test():
        print("\n⚠️ Basic system test failed, but setup completed")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review the .env file and adjust settings")
    print("2. Run: python demo.py")
    print("3. Or run: python run.py")
    print("\nFor Docker deployment:")
    print("docker-compose -f docker-compose.yaml up --build")

if __name__ == "__main__":
    main()
