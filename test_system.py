"""
Smart Traffic AI System - Test Runner
Quick test to verify all components work together
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_system_components():
    """Test all system components individually"""
    print("🧪 Testing Smart Traffic AI System Components...")
    print("=" * 60)
    
    # Test 1: Configuration
    print("\n📋 Testing Configuration...")
    try:
        from config.config import load_config, SystemMode
        config = load_config()
        print(f"   ✅ Configuration loaded successfully")
        print(f"   📍 System mode: {config.system.mode}")
        print(f"   🔧 Processing interval: {config.system.processing_interval}s")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    # Test 2: Database
    print("\n🗄️ Testing Database...")
    try:
        from src.database.database_manager import TrafficDatabase, AnalyticsEngine
        db = TrafficDatabase("data/test_traffic.db")
        analytics = AnalyticsEngine(db)
        
        # Test data insertion
        db.record_vehicle_detection("test_intersection", "north", 3, ["car", "truck", "car"])
        db.record_system_event("test", "low", "System test event")
        
        print("   ✅ Database operations successful")
    except Exception as e:
        print(f"   ❌ Database failed: {e}")
        return False
    
    # Test 3: AI Engines
    print("\n🤖 Testing AI Engines...")
    try:
        from src.ai_engine.vehicle_detector import VehicleDetector
        from src.ai_engine.traffic_predictor import TrafficPredictor
        
        detector = VehicleDetector(config.ai_models)
        predictor = TrafficPredictor(config.ai_models)
        
        # Test with mock data
        test_counts = {"north": 5, "south": 3, "east": 2, "west": 4}
        prediction = predictor.predict_traffic_flow("test_intersection", test_counts)
        
        print("   ✅ AI engines initialized successfully")
        print(f"   📊 Sample prediction: {prediction}")
    except Exception as e:
        print(f"   ❌ AI engines failed: {e}")
        return False
    
    # Test 4: Camera System
    print("\n📷 Testing Camera System...")
    try:
        from src.camera_system.camera_manager import CameraManager
        
        camera_manager = CameraManager(config.cameras)
        print("   ✅ Camera system initialized (simulation mode)")
        print(f"   📹 Available cameras: {len(camera_manager.cameras)}")
    except Exception as e:
        print(f"   ❌ Camera system failed: {e}")
        return False
    
    # Test 5: Traffic Controller
    print("\n🚦 Testing Traffic Light Controller...")
    try:
        from src.traffic_controller.light_controller import TrafficLightController
        
        controller = TrafficLightController(config.traffic_lights)
        
        # Test getting states
        states = controller.get_all_states()
        print("   ✅ Traffic controller initialized")
        print(f"   💡 Active intersections: {len(states)}")
    except Exception as e:
        print(f"   ❌ Traffic controller failed: {e}")
        return False
    
    # Test 6: Sensor Manager (simulation mode)
    print("\n📡 Testing Sensor Manager...")
    try:
        from src.sensors.sensor_manager import SensorManager
        
        sensor_manager = SensorManager(config)
        print("   ✅ Sensor manager initialized (simulation mode)")
    except Exception as e:
        print(f"   ❌ Sensor manager failed: {e}")
        return False
    
    # Test 7: Web Interface Components
    print("\n🌐 Testing Web Interface...")
    try:
        from src.web_interface.app import app
        
        with app.test_client() as client:
            response = client.get('/api/system/status')
            print("   ✅ Web interface components loaded")
            print(f"   🔗 API response status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Web interface failed: {e}")
        return False
    
    print("\n🎉 All component tests passed!")
    return True

def test_integration():
    """Test component integration"""
    print("\n🔗 Testing Component Integration...")
    print("-" * 40)
    
    try:
        # Load configuration
        from config.config import load_config
        config = load_config()
        
        # Initialize core components
        from src.database.database_manager import TrafficDatabase
        from src.ai_engine.vehicle_detector import VehicleDetector
        from src.ai_engine.traffic_predictor import TrafficPredictor
        from src.traffic_controller.light_controller import TrafficLightController
        
        db = TrafficDatabase("data/integration_test.db")
        detector = VehicleDetector(config.ai_models)
        predictor = TrafficPredictor(config.ai_models)
        controller = TrafficLightController(config.traffic_lights)
        
        print("   ✅ Core components initialized")
        
        # Simulate traffic processing workflow
        intersection_id = "test_intersection_001"
        
        # 1. Simulate vehicle detection
        mock_counts = {"north": 8, "south": 5, "east": 3, "west": 6}
        
        # 2. Record detections in database
        for direction, count in mock_counts.items():
            db.record_vehicle_detection(intersection_id, direction, count, ["car"] * count)
        
        print("   ✅ Vehicle detections recorded")
        
        # 3. Generate predictions
        prediction = predictor.predict_traffic_flow(intersection_id, mock_counts)
        
        # 4. Record predictions
        for horizon, volume in prediction.items():
            if horizon in ['short_term', 'medium_term', 'long_term']:
                db.record_traffic_prediction(intersection_id, horizon, int(volume))
        
        print("   ✅ Traffic predictions generated and recorded")
        
        # 5. Optimize traffic lights
        optimization_result = controller.optimize_intersection_timing(
            intersection_id, mock_counts, prediction
        )
        
        print(f"   ✅ Traffic light optimization: {optimization_result}")
        
        # 6. Retrieve analytics
        patterns = db.get_traffic_patterns(intersection_id)
        alerts = db.get_system_alerts(hours=1)
        
        print(f"   📊 Traffic patterns retrieved: {len(patterns.get('hourly_patterns', []))} data points")
        print(f"   🚨 System alerts: {len(alerts)}")
        
        print("   🎯 Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_quick_demo():
    """Run a quick 30-second demo of the system"""
    print("\n🚀 Running Quick Demo (30 seconds)...")
    print("-" * 50)
    
    try:
        # Load system
        from run import SmartTrafficSystem
        
        print("   🔧 Initializing system...")
        system = SmartTrafficSystem()
        
        print("   ▶️ Starting system...")
        system.start()
        
        # Run for 30 seconds
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                status = system.get_system_status()
                print(f"   ⏱️ {i+1}s - Vehicles processed: {status['performance_stats']['total_vehicles_processed']}")
        
        print("   ⏹️ Stopping system...")
        system.stop()
        
        final_status = system.get_system_status()
        print(f"\n   📈 Demo Results:")
        print(f"     • Uptime: {final_status['uptime_seconds']} seconds")
        print(f"     • Vehicles processed: {final_status['performance_stats']['total_vehicles_processed']}")
        print(f"     • Predictions made: {final_status['performance_stats']['total_predictions_made']}")
        print(f"     • Light changes: {final_status['performance_stats']['total_light_changes']}")
        
        print("   🎊 Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("🚦 Smart Traffic AI System - Test Runner")
    print("🕒 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    # Setup basic logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    all_passed = True
    
    # Run component tests
    if not test_system_components():
        all_passed = False
    
    # Run integration tests
    if not test_integration():
        all_passed = False
    
    # Run quick demo (optional, comment out if not needed)
    demo_choice = input("\n🤔 Run 30-second demo? (y/N): ").lower().strip()
    if demo_choice in ['y', 'yes']:
        if not run_quick_demo():
            all_passed = False
    
    # Final results
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is ready to run.")
        print("\n📋 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Start system: python run.py")
        print("   3. Open dashboard: http://localhost:5000")
    else:
        print("❌ SOME TESTS FAILED! Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Check dependencies are installed")
        print("   2. Verify Python version (3.8+)")
        print("   3. Check file permissions")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
