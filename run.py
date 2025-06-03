"""
Smart Traffic AI System - Main Application Runner
Orchestrates all system components: AI engines, cameras, sensors, traffic control, and web interface
"""

import asyncio
import threading
import time
import signal
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Import all system components
from config.config_loader import load_config
from config.config import SystemMode
from src.ai_engine.vehicle_detector import VehicleDetector
from src.ai_engine.traffic_predictor import TrafficPredictor
from src.camera_system.camera_manager import CameraManager
from src.traffic_controller.light_controller import TrafficLightController
from src.sensors.sensor_manager import SensorManager
from src.database.database_manager import TrafficDatabase, AnalyticsEngine
from src.web_interface.app import app, socketio
from src.web_interface.health import add_health_routes

class SmartTrafficSystem:
    """Main system orchestrator"""
    
    def __init__(self, config_path: str = "config/config.py"):
        # Load configuration
        self.config = load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # System state
        self.running = False
        self.components = {}
        self.threads = {}
        
        # Performance monitoring
        self.system_stats = {
            'start_time': None,
            'total_vehicles_processed': 0,
            'total_predictions_made': 0,
            'total_light_changes': 0,
            'uptime_seconds': 0
        }
        
        # Initialize all components
        self._initialize_components()
        
        logging.info("Smart Traffic AI System initialized")
    
    def _setup_logging(self):
        """Configure system logging"""
        log_level = getattr(logging, self.config.logging.level.upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.logging.file_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduce verbose logging from some libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Database (initialize first)
            logging.info("Initializing database...")
            self.components['database'] = TrafficDatabase(self.config.database.db_path)
            self.components['analytics'] = AnalyticsEngine(self.components['database'])
            
            # AI Engines
            logging.info("Initializing AI engines...")
            self.components['vehicle_detector'] = VehicleDetector(self.config.ai_models)
            self.components['traffic_predictor'] = TrafficPredictor(self.config.ai_models)
            
            # Camera System
            logging.info("Initializing camera system...")
            self.components['camera_manager'] = CameraManager(self.config.cameras)
            
            # Traffic Light Controller
            logging.info("Initializing traffic light controller...")
            self.components['light_controller'] = TrafficLightController(self.config.traffic_lights)
            
            # Sensor Manager (if not simulation mode)
            if self.config.system.mode != SystemMode.SIMULATION:
                logging.info("Initializing sensor manager...")
                self.components['sensor_manager'] = SensorManager(self.config)
            else:
                logging.info("Sensor manager disabled in simulation mode")
                self.components['sensor_manager'] = None
            
            logging.info("All components initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            raise
    
    def start(self):
        """Start the traffic AI system"""
        if self.running:
            logging.warning("System is already running")
            return
        
        logging.info("Starting Smart Traffic AI System...")
        self.running = True
        self.system_stats['start_time'] = datetime.now()
        
        try:
            # Start camera system
            if self.components['camera_manager']:
                self.components['camera_manager'].start_all_cameras()
                logging.info("Camera system started")
            
            # Start sensor data collection
            if self.components['sensor_manager']:
                self.components['sensor_manager'].start_data_collection()
                logging.info("Sensor data collection started")
            
            # Start traffic light controller
            self.components['light_controller'].start()
            logging.info("Traffic light controller started")
            
            # Start main processing loop
            self.threads['main_loop'] = threading.Thread(
                target=self._main_processing_loop,
                daemon=True,
                name="MainProcessingLoop"
            )
            self.threads['main_loop'].start()
            
            # Start performance monitoring
            self.threads['performance_monitor'] = threading.Thread(
                target=self._performance_monitor_loop,
                daemon=True,
                name="PerformanceMonitor"
            )
            self.threads['performance_monitor'].start()
            
            # Start web interface in a separate thread
            self.threads['web_interface'] = threading.Thread(
                target=self._start_web_interface,
                daemon=True,
                name="WebInterface"
            )
            self.threads['web_interface'].start()
            
            logging.info("Smart Traffic AI System started successfully")
            
        except Exception as e:
            logging.error(f"Failed to start system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the traffic AI system"""
        if not self.running:
            return
        
        logging.info("Stopping Smart Traffic AI System...")
        self.running = False
        
        try:
            # Stop sensor data collection
            if self.components['sensor_manager']:
                self.components['sensor_manager'].stop_data_collection()
            
            # Stop camera system
            if self.components['camera_manager']:
                self.components['camera_manager'].stop_all_cameras()
            
            # Stop traffic light controller
            self.components['light_controller'].stop()
            
            # Wait for threads to finish
            for thread_name, thread in self.threads.items():
                if thread and thread.is_alive():
                    logging.info(f"Waiting for {thread_name} to finish...")
                    thread.join(timeout=5)
            
            # Record system shutdown
            if self.components['database']:
                self.components['database'].record_system_event(
                    'maintenance', 'low', 'System shutdown completed'
                )
            
            logging.info("Smart Traffic AI System stopped")
            
        except Exception as e:
            logging.error(f"Error during system shutdown: {e}")
    
    def _main_processing_loop(self):
        """Main processing loop - coordinates all AI and control operations"""
        logging.info("Main processing loop started")
        
        while self.running:
            try:
                # Process each intersection
                for intersection_id in self.config.traffic_lights.intersections:
                    if not self.running:
                        break
                    
                    self._process_intersection(intersection_id)
                
                # Sleep between processing cycles
                time.sleep(self.config.system.processing_interval)
                
            except Exception as e:
                logging.error(f"Error in main processing loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        logging.info("Main processing loop stopped")
    
    def _process_intersection(self, intersection_id: str):
        """Process AI analysis and control for a single intersection"""
        try:
            # Get camera frames
            cameras = self.components['camera_manager'].get_intersection_cameras(intersection_id)
            if not cameras:
                return
            
            current_counts = {}
            all_vehicle_types = []
            
            # Process each camera view
            for camera in cameras:
                frame = camera.get_latest_frame()
                if frame is None:
                    continue
                
                # Detect vehicles
                detection_result = self.components['vehicle_detector'].detect_vehicles(frame)
                
                # Count vehicles by direction
                direction_counts = self.components['vehicle_detector'].count_vehicles(
                    frame, intersection_id
                )
                
                # Merge counts
                for direction, count in direction_counts.items():
                    current_counts[direction] = current_counts.get(direction, 0) + count
                
                # Collect vehicle types
                if 'vehicles' in detection_result:
                    for vehicle in detection_result['vehicles']:
                        all_vehicle_types.append(vehicle['class'])
            
            # Record vehicle detections in database
            for direction, count in current_counts.items():
                if count > 0:
                    self.components['database'].record_vehicle_detection(
                        intersection_id, direction, count, all_vehicle_types,
                        detection_method='camera'
                    )
                    self.system_stats['total_vehicles_processed'] += count
            
            # Get sensor data if available
            sensor_data = {}
            if self.components['sensor_manager']:
                sensor_data = self.components['sensor_manager'].get_intersection_sensor_data(intersection_id)
            
            # Generate traffic predictions
            prediction = self.components['traffic_predictor'].predict_traffic_flow(
                intersection_id, current_counts
            )
            
            # Record prediction in database
            if prediction:
                for horizon, volume in prediction.items():
                    if horizon in ['short_term', 'medium_term', 'long_term']:
                        self.components['database'].record_traffic_prediction(
                            intersection_id, horizon, int(volume),
                            confidence=0.8  # Mock confidence
                        )
                self.system_stats['total_predictions_made'] += 1
            
            # AI-driven traffic light optimization
            if self.config.traffic_lights.ai_optimization_enabled:
                self._optimize_traffic_lights(intersection_id, current_counts, prediction)
            
            # Check for emergency situations
            self._check_emergency_conditions(intersection_id, current_counts, sensor_data)
            
        except Exception as e:
            logging.error(f"Error processing intersection {intersection_id}: {e}")
    
    def _optimize_traffic_lights(self, intersection_id: str, 
                               current_counts: Dict[str, int],
                               prediction: Dict[str, float]):
        """AI-driven traffic light optimization"""
        try:
            # Get current light states
            current_states = self.components['light_controller'].get_intersection_state(intersection_id)
            
            # Calculate optimal timing based on traffic
            total_traffic = sum(current_counts.values())
            
            if total_traffic == 0:
                # No traffic - use default timing
                return
            
            # Simple AI optimization algorithm
            max_direction = max(current_counts.items(), key=lambda x: x[1])
            max_direction_name, max_count = max_direction
            
            # If one direction has significantly more traffic, prioritize it
            if max_count > sum(current_counts.values()) * 0.6:
                # Calculate extended green time
                base_green = self.config.traffic_lights.default_green_duration
                traffic_factor = min(max_count / 10, 2.0)  # Max 2x extension
                extended_green = int(base_green * traffic_factor)
                
                # Apply optimization
                result = self.components['light_controller'].optimize_intersection_timing(
                    intersection_id, current_counts, prediction
                )
                
                if result:
                    self.system_stats['total_light_changes'] += 1
                    
                    # Record the control action
                    self.components['database'].record_traffic_light_state(
                        intersection_id, max_direction_name, 'green', 
                        extended_green, 'auto'
                    )
        
        except Exception as e:
            logging.error(f"Error optimizing traffic lights for {intersection_id}: {e}")
    
    def _check_emergency_conditions(self, intersection_id: str,
                                  current_counts: Dict[str, int],
                                  sensor_data: Dict[str, Any]):
        """Check for emergency conditions requiring immediate action"""
        try:
            # Check for extremely high traffic
            total_traffic = sum(current_counts.values())
            if total_traffic > self.config.traffic_lights.emergency_threshold:
                # Record emergency event
                self.components['database'].record_system_event(
                    'emergency', 'high', 
                    f'Extremely high traffic detected: {total_traffic} vehicles',
                    intersection_id, 'traffic_monitoring'
                )
                
                # Could trigger emergency protocols here
                logging.warning(f"Emergency traffic level at {intersection_id}: {total_traffic} vehicles")
            
            # Check sensor data for anomalies
            if sensor_data and 'sensors' in sensor_data:
                for sensor_id, sensor_info in sensor_data['sensors'].items():
                    if sensor_info['type'] == 'environmental':
                        # Check for extreme weather conditions
                        if 'temperature' in sensor_id and sensor_info['value'] < -10:
                            self.components['database'].record_system_event(
                                'alert', 'medium',
                                f'Extreme cold weather detected: {sensor_info["value"]}°C',
                                intersection_id, 'environmental_sensor'
                            )
        
        except Exception as e:
            logging.error(f"Error checking emergency conditions for {intersection_id}: {e}")
    
    def _performance_monitor_loop(self):
        """Monitor system performance and log statistics"""
        logging.info("Performance monitor started")
        
        while self.running:
            try:
                # Update uptime
                if self.system_stats['start_time']:
                    uptime = datetime.now() - self.system_stats['start_time']
                    self.system_stats['uptime_seconds'] = int(uptime.total_seconds())
                
                # Log performance statistics every 5 minutes
                if self.system_stats['uptime_seconds'] % 300 == 0:
                    logging.info(f"System Performance - "
                               f"Uptime: {self.system_stats['uptime_seconds']}s, "
                               f"Vehicles: {self.system_stats['total_vehicles_processed']}, "
                               f"Predictions: {self.system_stats['total_predictions_made']}, "
                               f"Light Changes: {self.system_stats['total_light_changes']}")
                
                # Record performance metrics in database
                self.components['database'].record_performance_metric(
                    'system_wide', 'vehicles_per_hour',
                    self.system_stats['total_vehicles_processed'] / max(1, self.system_stats['uptime_seconds'] / 3600),
                    'vehicles/hour'
                )
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logging.error(f"Error in performance monitor: {e}")
                time.sleep(60)
        
        logging.info("Performance monitor stopped")
    
    def _start_web_interface(self):
        """Start the web interface"""
        try:
            # Add health check routes
            add_health_routes(app)
            logging.info("Starting web interface on http://localhost:5000")
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            logging.error(f"Error starting web interface: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'running': self.running,
            'uptime_seconds': self.system_stats['uptime_seconds'],
            'start_time': self.system_stats['start_time'].isoformat() if self.system_stats['start_time'] else None,
            'performance_stats': self.system_stats.copy(),
            'components': {}
        }
        
        # Check component status
        for component_name, component in self.components.items():
            if component_name == 'camera_manager':
                status['components'][component_name] = {
                    'active_cameras': len(component.cameras) if component else 0,
                    'status': 'running' if component and component.cameras else 'stopped'
                }
            elif component_name == 'sensor_manager':
                status['components'][component_name] = {
                    'status': 'running' if component and component.running else 'stopped',
                    'mqtt_connected': component.mqtt_manager.connected if component else False
                }
            elif component_name == 'light_controller':
                status['components'][component_name] = {
                    'status': 'running' if component and component.running else 'stopped',
                    'active_intersections': len(self.config.traffic_lights.intersections)
                }
            else:
                status['components'][component_name] = {
                    'status': 'initialized' if component else 'failed'
                }
        
        return status

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logging.info(f"Received signal {signum}, shutting down...")
    if hasattr(signal_handler, 'system'):
        signal_handler.system.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    print("🚦 Smart Traffic AI System")
    print("=" * 50)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize system
        system = SmartTrafficSystem()
        signal_handler.system = system  # Store reference for signal handler
        
        # Start system
        system.start()
        
        print("\n✅ System started successfully!")
        print("📊 Web Dashboard: http://localhost:5000")
        print("🔧 Press Ctrl+C to stop\n")
        
        # Keep main thread alive
        while system.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        logging.error(f"System error: {e}")
    finally:
        if 'system' in locals():
            system.stop()
        print("👋 Smart Traffic AI System stopped")

if __name__ == "__main__":
    main()
