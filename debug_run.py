#!/usr/bin/env python3
"""
Debug version to isolate the 'format' KeyError
"""

import sys
import traceback

def test_imports():
    """Test each import individually to find the problem"""
    print("🔍 Testing imports individually...")
    
    try:
        print("1. Testing config import...")
        from config.config import load_config, SystemMode
        print("   ✅ Config import successful")
        
        print("2. Testing config loading...")
        config = load_config()
        print("   ✅ Config loading successful")
        
        print("3. Testing logger import...")
        from src.utils.logger import initialize_logging, get_logger
        print("   ✅ Logger import successful")
        
        print("4. Testing logger initialization...")
        logging_config = {
            "level": "INFO",
            "log_dir": "logs",
            "enable_console": True,
            "enable_file": False,  # Disable file logging to avoid issues
            "enable_json": False,
            "enable_performance": False
        }
        logging_system = initialize_logging(logging_config)
        print("   ✅ Logger initialization successful")
        
        print("5. Testing component imports...")
        from src.ai_engine.vehicle_detector import VehicleDetector
        print("   ✅ VehicleDetector import successful")
        
        from src.camera_system.camera_manager import CameraManager
        print("   ✅ CameraManager import successful")
        
        print("6. Testing component initialization...")
        vehicle_detector = VehicleDetector(config)
        print("   ✅ VehicleDetector initialization successful")
        
        camera_manager = CameraManager(config)
        print("   ✅ CameraManager initialization successful")
        
        print("\n✅ All tests passed! The error must be elsewhere.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback:")
        traceback.print_exc()
        return False
    
    return True

def main():
    print("🔍 Debug Mode - Isolating 'format' KeyError")
    print("=" * 50)
    
    if test_imports():
        print("\n🎯 All components work individually.")
        print("The error must be in the system orchestration.")
        print("Use minimal_run.py for guaranteed working version.")
    else:
        print("\n🚨 Found the problematic component!")
        print("Use minimal_run.py for guaranteed working version.")

if __name__ == "__main__":
    main()
