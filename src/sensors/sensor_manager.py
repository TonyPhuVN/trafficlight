"""
📡 Sensor Manager - IoT Sensors and Data Collection
Manages various sensors for environmental and traffic monitoring
"""

import time
import threading
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

class SensorManager:
    """Manager for all IoT sensors in the traffic system"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Sensor data storage
        self.sensor_data = {}
        self.data_lock = threading.Lock()
        
        # Collection thread
        self.collection_thread = None
        
        # Compatibility attributes for run.py interface
        self.mqtt_manager = type('MockMQTT', (), {'connected': False})()  # Mock MQTT manager
        
        # Simulated sensors (for testing/simulation mode)
        self.simulated_sensors = {
            'temp_001': {'type': 'environmental', 'unit': '°C', 'range': (15, 35)},
            'humidity_001': {'type': 'environmental', 'unit': '%', 'range': (30, 80)},
            'pressure_001': {'type': 'environmental', 'unit': 'hPa', 'range': (980, 1020)},
            'ultrasonic_001': {'type': 'distance', 'unit': 'cm', 'range': (10, 200)},
            'motion_001': {'type': 'motion', 'unit': 'boolean', 'range': (0, 1)},
            'air_quality_001': {'type': 'environmental', 'unit': 'AQI', 'range': (20, 150)}
        }
        
        self.logger.info("📡 Sensor Manager initialized")
    
    def start_data_collection(self):
        """Start sensor data collection"""
        if self.running:
            self.logger.warning("⚠️ Data collection already running")
            return
        
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        self.logger.info("🚀 Sensor data collection started")
    
    def stop_data_collection(self):
        """Stop sensor data collection"""
        self.running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        self.logger.info("🛑 Sensor data collection stopped")
    
    def _collection_loop(self):
        """Main sensor data collection loop"""
        while self.running:
            try:
                # Collect data from all sensors
                self._collect_sensor_readings()
                
                # Sleep between collections
                time.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Sensor collection error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _collect_sensor_readings(self):
        """Collect readings from all sensors"""
        timestamp = time.time()
        
        with self.data_lock:
            for sensor_id, sensor_config in self.simulated_sensors.items():
                try:
                    # Generate simulated sensor reading
                    value = self._generate_sensor_value(sensor_config)
                    
                    # Store sensor reading
                    self.sensor_data[sensor_id] = {
                        'sensor_id': sensor_id,
                        'type': sensor_config['type'],
                        'value': value,
                        'unit': sensor_config['unit'],
                        'timestamp': timestamp,
                        'status': 'active'
                    }
                    
                except Exception as e:
                    self.logger.error(f"❌ Error reading sensor {sensor_id}: {e}")
                    # Mark sensor as error
                    self.sensor_data[sensor_id] = {
                        'sensor_id': sensor_id,
                        'type': sensor_config['type'],
                        'value': None,
                        'unit': sensor_config['unit'],
                        'timestamp': timestamp,
                        'status': 'error',
                        'error': str(e)
                    }
    
    def _generate_sensor_value(self, sensor_config: Dict) -> Any:
        """Generate simulated sensor value"""
        sensor_type = sensor_config['type']
        value_range = sensor_config['range']
        
        if sensor_type == 'environmental':
            # Environmental sensors with some variation
            base_value = random.uniform(value_range[0], value_range[1])
            # Add some noise
            noise = random.uniform(-2, 2)
            return round(base_value + noise, 1)
        
        elif sensor_type == 'distance':
            # Distance sensors (ultrasonic)
            return round(random.uniform(value_range[0], value_range[1]), 1)
        
        elif sensor_type == 'motion':
            # Motion sensors (boolean)
            return random.choice([True, False])
        
        else:
            # Default random value in range
            return round(random.uniform(value_range[0], value_range[1]), 1)
    
    def get_sensor_reading(self, sensor_id: str) -> Optional[Dict]:
        """Get latest reading from a specific sensor"""
        with self.data_lock:
            return self.sensor_data.get(sensor_id)
    
    def get_all_sensor_readings(self) -> Dict[str, Dict]:
        """Get latest readings from all sensors"""
        with self.data_lock:
            return self.sensor_data.copy()
    
    def get_intersection_sensor_data(self, intersection_id: str) -> Dict:
        """Get sensor data for a specific intersection"""
        # In a real implementation, this would filter sensors by location
        # For simulation, return all sensor data
        
        with self.data_lock:
            return {
                'intersection_id': intersection_id,
                'sensors': self.sensor_data.copy(),
                'timestamp': time.time()
            }
    
    def get_environmental_conditions(self) -> Dict:
        """Get current environmental conditions"""
        conditions = {
            'temperature': None,
            'humidity': None,
            'pressure': None,
            'air_quality': None,
            'visibility': 100,  # Default good visibility
            'weather_condition': 'clear'
        }
        
        with self.data_lock:
            for sensor_id, reading in self.sensor_data.items():
                if reading['status'] != 'active':
                    continue
                
                if 'temp' in sensor_id:
                    conditions['temperature'] = reading['value']
                elif 'humidity' in sensor_id:
                    conditions['humidity'] = reading['value']
                elif 'pressure' in sensor_id:
                    conditions['pressure'] = reading['value']
                elif 'air_quality' in sensor_id:
                    conditions['air_quality'] = reading['value']
        
        # Determine weather condition based on sensors
        if conditions['humidity'] and conditions['humidity'] > 70:
            if conditions['temperature'] and conditions['temperature'] < 10:
                conditions['weather_condition'] = 'fog'
            else:
                conditions['weather_condition'] = 'rain'
        elif conditions['humidity'] and conditions['humidity'] > 50:
            conditions['weather_condition'] = 'cloudy'
        else:
            conditions['weather_condition'] = 'clear'
        
        return conditions
    
    def get_sensor_statistics(self) -> Dict:
        """Get sensor system statistics"""
        with self.data_lock:
            total_sensors = len(self.simulated_sensors)
            active_sensors = sum(1 for reading in self.sensor_data.values() 
                               if reading.get('status') == 'active')
            error_sensors = sum(1 for reading in self.sensor_data.values() 
                              if reading.get('status') == 'error')
        
        return {
            'total_sensors': total_sensors,
            'active_sensors': active_sensors,
            'error_sensors': error_sensors,
            'uptime_percentage': (active_sensors / total_sensors * 100) if total_sensors > 0 else 0,
            'last_collection': max((reading.get('timestamp', 0) for reading in self.sensor_data.values()), default=0)
        }
    
    def calibrate_sensor(self, sensor_id: str) -> bool:
        """Calibrate a specific sensor"""
        if sensor_id not in self.simulated_sensors:
            self.logger.error(f"❌ Sensor {sensor_id} not found")
            return False
        
        try:
            # Simulate calibration process
            self.logger.info(f"📐 Calibrating sensor {sensor_id}...")
            time.sleep(2)  # Simulate calibration time
            
            # Update sensor status
            with self.data_lock:
                if sensor_id in self.sensor_data:
                    self.sensor_data[sensor_id]['status'] = 'calibrated'
            
            self.logger.info(f"✅ Sensor {sensor_id} calibrated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Calibration failed for {sensor_id}: {e}")
            return False
    
    def add_sensor(self, sensor_id: str, sensor_type: str, unit: str, value_range: tuple):
        """Add a new sensor to the system"""
        self.simulated_sensors[sensor_id] = {
            'type': sensor_type,
            'unit': unit,
            'range': value_range
        }
        
        self.logger.info(f"➕ Added sensor {sensor_id} ({sensor_type})")
    
    def remove_sensor(self, sensor_id: str):
        """Remove a sensor from the system"""
        if sensor_id in self.simulated_sensors:
            del self.simulated_sensors[sensor_id]
            
            with self.data_lock:
                if sensor_id in self.sensor_data:
                    del self.sensor_data[sensor_id]
            
            self.logger.info(f"➖ Removed sensor {sensor_id}")
        else:
            self.logger.warning(f"⚠️ Sensor {sensor_id} not found for removal")
    
    def get_sensor_health(self) -> Dict[str, str]:
        """Get health status of all sensors"""
        health_status = {}
        
        with self.data_lock:
            for sensor_id in self.simulated_sensors:
                if sensor_id in self.sensor_data:
                    reading = self.sensor_data[sensor_id]
                    status = reading.get('status', 'unknown')
                    
                    # Check if reading is recent (within last 30 seconds)
                    if time.time() - reading.get('timestamp', 0) > 30:
                        status = 'stale'
                    
                    health_status[sensor_id] = status
                else:
                    health_status[sensor_id] = 'not_initialized'
        
        return health_status

if __name__ == "__main__":
    # Test sensor manager
    import sys
    import os
    
    # Add project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, project_root)
    
    from config.config import SmartTrafficConfig, SystemMode
    
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    sensor_manager = SensorManager(config)
    
    print("📡 Sensor Manager Test")
    
    # Start data collection
    sensor_manager.start_data_collection()
    print("🚀 Data collection started")
    
    # Test for a few seconds
    for i in range(5):
        time.sleep(2)
        readings = sensor_manager.get_all_sensor_readings()
        stats = sensor_manager.get_sensor_statistics()
        conditions = sensor_manager.get_environmental_conditions()
        
        print(f"\n--- Reading {i+1} ---")
        print(f"Active sensors: {stats['active_sensors']}/{stats['total_sensors']}")
        print(f"Temperature: {conditions.get('temperature')}°C")
        print(f"Humidity: {conditions.get('humidity')}%")
        print(f"Weather: {conditions.get('weather_condition')}")
    
    # Test intersection data
    intersection_data = sensor_manager.get_intersection_sensor_data("test_intersection")
    print(f"\nIntersection data: {len(intersection_data['sensors'])} sensors")
    
    sensor_manager.stop_data_collection()
    print("\n🛑 Test completed")
