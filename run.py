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
from config.config import load_config, SystemMode
from src.ai_engine.vehicle_detector import VehicleDetector
from src.ai_engine.traffic_predictor import TrafficPredictor
from src.camera_system.camera_manager import CameraManager
from src.traffic_controller.light_controller import TrafficLightController
from src.sensors.sensor_manager import SensorManager
from src.database.database_manager import TrafficDatabase, AnalyticsEngine
from src.web_interface.app import app, socketio
from src.web_interface.health import add_health_routes
from src.utils.logger import initialize_logging, get_logger, performance_monitor

class SmartTrafficSystem:
    """Main system orchestrator"""
    
    def __init__(self, config_path: str = None):
        # Load configuration (default mode, no file parsing)
        self.config = load_config()
        
        # Setup advanced logging system
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
        
        self.logger.info("Smart Traffic AI System initialized successfully", 
                        system_mode=self.config.mode.value if hasattr(self.config, 'mode') else 'unknown')
    
    def _setup_logging(self):
        """Configure advanced logging system"""
        # Initialize the advanced logging system
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
        
        # Override with config if available
        if hasattr(self.config, 'logging'):
            if hasattr(self.config.logging, 'level'):
                logging_config["level"] = self.config.logging.level.upper()
        
        # Initialize the advanced logging system
        self.logging_system = initialize_logging(logging_config)
        
        # Get system logger
        self.logger = get_logger("system_orchestrator")
        
        # Log system startup
        self.logging_system.log_system_startup({
            "mode": self.config.mode.value if hasattr(self.config, 'mode') else 'unknown',
            "config_path": "config/config.py"
        })
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Database (initialize first)
            self.logger.info("Initializing database...", component="database")
            self.components['database'] = TrafficDatabase(self.config.database.database_url)
            self.components['analytics'] = AnalyticsEngine(self.components['database'])
            
            # AI Engines
            self.logger.info("Initializing AI engines...", component="ai_engine")
            self.components['vehicle_detector'] = VehicleDetector(self.config)
            self.components['traffic_predictor'] = TrafficPredictor(self.config)
            
            # Camera System
            self.logger.info("Initializing camera system...", component="camera_system")
            self.components['camera_manager'] = CameraManager(self.config)
            
            # Traffic Light Controller
            self.logger.info("Initializing traffic light controller...", component="traffic_controller")
            self.components['light_controller'] = TrafficLightController(self.config)
            
            # Sensor Manager (if not simulation mode)
            if self.config.mode != SystemMode.SIMULATION:
                self.logger.info("Initializing sensor manager...", component="sensor_manager")
                self.components['sensor_manager'] = SensorManager(self.config)
            else:
                self.logger.info("Sensor manager disabled in simulation mode", component="sensor_manager")
                self.components['sensor_manager'] = None
            
            self.logger.info("All components initialized successfully", 
                           components_count=len([c for c in self.components.values() if c is not None]))
            
        except Exception as e:
            self.logger.error("Failed to initialize components", error=e)
            raise
    
    def start(self):
        """Start the traffic AI system"""
        if self.running:
            self.logger.warning("System is already running")
            return
        
        self.logger.info("Starting Smart Traffic AI System...")
        self.running = True
        self.system_stats['start_time'] = datetime.now()
        
        try:
            # Start camera system
            if self.components['camera_manager']:
                self.components['camera_manager'].start_all_cameras()
                self.logger.info("Camera system started", component="camera_system")
            
            # Start sensor data collection
            if self.components['sensor_manager']:
                self.components['sensor_manager'].start_data_collection()
                self.logger.info("Sensor data collection started", component="sensor_manager")
            
            # Start traffic light controller
            self.components['light_controller'].start()
            self.logger.info("Traffic light controller started", component="traffic_controller")
            
            # Start main processing loop
            self.threads['main_loop'] = threading.Thread(
                target=self._main_processing_loop,
                daemon=True,
                name="MainProcessingLoop"
            )
            self.threads['main_loop'].start()
            self.logger.info("Main processing loop started", thread="MainProcessingLoop")
            
            # Start performance monitoring
            self.threads['performance_monitor'] = threading.Thread(
                target=self._performance_monitor_loop,
                daemon=True,
                name="PerformanceMonitor"
            )
            self.threads['performance_monitor'].start()
            self.logger.info("Performance monitoring started", thread="PerformanceMonitor")
            
            # Start web interface in a separate thread
            self.threads['web_interface'] = threading.Thread(
                target=self._start_web_interface,
                daemon=True,
                name="WebInterface"
            )
            self.threads['web_interface'].start()
            self.logger.info("Web interface started", thread="WebInterface")
            
            self.logger.info("Smart Traffic AI System started successfully", 
                           threads_count=len(self.threads))
            
        except Exception as e:
            self.logger.error("Failed to start system", error=e)
            self.stop()
            raise
    
    def stop(self):
        """Stop the traffic AI system"""
        if not self.running:
            return
        
        self.logger.info("Stopping Smart Traffic AI System...")
        self.running = False
        
        try:
            # Stop sensor data collection
            if self.components['sensor_manager']:
                self.components['sensor_manager'].stop_data_collection()
                self.logger.info("Sensor data collection stopped", component="sensor_manager")
            
            # Stop camera system
            if self.components['camera_manager']:
                self.components['camera_manager'].stop_all_cameras()
                self.logger.info("Camera system stopped", component="camera_system")
            
            # Stop traffic light controller
            self.components['light_controller'].stop()
            self.logger.info("Traffic light controller stopped", component="traffic_controller")
            
            # Wait for threads to finish
            for thread_name, thread in self.threads.items():
                if thread and thread.is_alive():
                    self.logger.info(f"Waiting for {thread_name} to finish...", thread=thread_name)
                    thread.join(timeout=5)
            
            # Record system shutdown
            if self.components['database']:
                self.components['database'].record_system_event(
                    'maintenance', 'low', 'System shutdown completed'
                )
            
            # Log system shutdown
            self.logging_system.log_system_shutdown(self.system_stats)
            self.logger.info("Smart Traffic AI System stopped successfully")
            
        except Exception as e:
            self.logger.error("Error during system shutdown", error=e)
    
    def _main_processing_loop(self):
        """Main processing loop - coordinates all AI and control operations"""
        loop_logger = get_logger("main_processing_loop")
        loop_logger.info("Main processing loop started")
        
        while self.running:
            try:
                # Process each intersection (use default intersections since not defined in config)
                default_intersections = ["main_intersection", "north_junction", "east_junction", "south_junction"]
                for intersection_id in default_intersections:
                    if not self.running:
                        break
                    
                    self._process_intersection(intersection_id)
                
                # Sleep between processing cycles
                time.sleep(2)  # Default processing interval
                
            except Exception as e:
                loop_logger.error("Error in main processing loop", error=e)
                time.sleep(5)  # Wait before retrying
        
        loop_logger.info("Main processing loop stopped")
    
    def _process_intersection(self, intersection_id: str):
        """Process AI analysis and control for a single intersection"""
        try:
            # Get current frame from camera manager
            frame = self.components['camera_manager'].get_current_frame()
            if frame is None:
                return
            
            current_counts = {}
            all_vehicle_types = []
            
            # Detect vehicles in the frame
            detections = self.components['vehicle_detector'].detect_vehicles(frame)
            counts = self.components['vehicle_detector'].count_vehicles_by_zone(detections)
            
            # Convert VehicleCount objects to dict format
            for zone_name, count_obj in counts.items():
                current_counts[zone_name] = count_obj.total
                # Collect vehicle types from the frame
                if hasattr(count_obj, 'vehicle_types'):
                    all_vehicle_types.extend(count_obj.vehicle_types)
            
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
            
            # AI-driven traffic light optimization (simulate for now)
            self._optimize_traffic_lights(intersection_id, current_counts, prediction)
            
            # Check for emergency situations
            self._check_emergency_conditions(intersection_id, current_counts, sensor_data)
            
        except Exception as e:
            self.logger.error(f"Error processing intersection {intersection_id}", error=e, intersection_id=intersection_id)
    
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
                base_green = 30  # Default green duration
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
            self.logger.error(f"Error optimizing traffic lights for {intersection_id}", 
                            error=e, intersection_id=intersection_id)
    
    def _check_emergency_conditions(self, intersection_id: str,
                                  current_counts: Dict[str, int],
                                  sensor_data: Dict[str, Any]):
        """Check for emergency conditions requiring immediate action"""
        try:
            # Check for extremely high traffic
            total_traffic = sum(current_counts.values())
            emergency_threshold = 50  # Default emergency threshold
            if total_traffic > emergency_threshold:
                # Record emergency event
                self.components['database'].record_system_event(
                    'emergency', 'high', 
                    f'Extremely high traffic detected: {total_traffic} vehicles',
                    intersection_id, 'traffic_monitoring'
                )
                
                # Could trigger emergency protocols here
                self.logger.warning(f"Emergency traffic level at {intersection_id}: {total_traffic} vehicles",
                                  intersection_id=intersection_id, total_traffic=total_traffic)
            
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
            self.logger.error(f"Error checking emergency conditions for {intersection_id}", 
                            error=e, intersection_id=intersection_id)
    
    def _performance_monitor_loop(self):
        """Monitor system performance and log statistics"""
        perf_logger = get_logger("performance_monitor")
        perf_logger.info("Performance monitor started")
        
        while self.running:
            try:
                # Update uptime
                if self.system_stats['start_time']:
                    uptime = datetime.now() - self.system_stats['start_time']
                    self.system_stats['uptime_seconds'] = int(uptime.total_seconds())
                
                # Log performance statistics every 5 minutes
                if self.system_stats['uptime_seconds'] % 300 == 0:
                    perf_logger.info("System Performance Statistics",
                                   uptime_seconds=self.system_stats['uptime_seconds'],
                                   vehicles_processed=self.system_stats['total_vehicles_processed'],
                                   predictions_made=self.system_stats['total_predictions_made'],
                                   light_changes=self.system_stats['total_light_changes'])
                
                # Record performance metrics in database
                self.components['database'].record_performance_metric(
                    'system_wide', 'vehicles_per_hour',
                    self.system_stats['total_vehicles_processed'] / max(1, self.system_stats['uptime_seconds'] / 3600),
                    'vehicles/hour'
                )
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                perf_logger.error("Error in performance monitor", error=e)
                time.sleep(60)
        
        perf_logger.info("Performance monitor stopped")
    
    def _start_web_interface(self):
        """Start the web interface"""
        web_logger = get_logger("web_interface")
        try:
            # Add health check routes
            add_health_routes(app)
            web_logger.info("Starting web interface on http://localhost:5000")
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            web_logger.error("Error starting web interface", error=e)
    
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
                    'active_intersections': 4  # Default number of intersections
                }
            else:
                status['components'][component_name] = {
                    'status': 'initialized' if component else 'failed'
                }
        
        return status

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    signal_logger = get_logger("signal_handler")
    signal_logger.info(f"Received signal {signum}, shutting down...", signal=signum)
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
        main_logger = get_logger("main")
        main_logger.error("System error in main", error=e)
    finally:
        if 'system' in locals():
            system.stop()
        print("👋 Smart Traffic AI System stopped")

if __name__ == "__main__":
    main()
