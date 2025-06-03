"""
IoT Sensor Manager for Smart Traffic AI System
Handles integration with various sensors: ultrasonic, radar, pressure sensors, and MQTT communication
"""

import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import paho.mqtt.client as mqtt
import serial
import requests

# Mock sensor libraries for simulation
try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI_AVAILABLE = True
except ImportError:
    RASPBERRY_PI_AVAILABLE = False
    print("RPi.GPIO not available - running in simulation mode")

@dataclass
class SensorReading:
    """Data structure for sensor readings"""
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    location: str
    intersection_id: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

class SensorSimulator:
    """Simulates sensor readings for development/testing"""
    
    def __init__(self):
        self.base_values = {
            'ultrasonic': 50.0,  # cm
            'radar': 0.0,        # vehicles/min
            'pressure': 0.0,     # kg/cm²
            'magnetic': 0.0,     # magnetic field strength
            'temperature': 25.0,  # °C
            'humidity': 60.0,     # %
            'light': 500.0       # lux
        }
    
    def read_sensor(self, sensor_type: str, sensor_id: str) -> float:
        """Simulate sensor reading with realistic variations"""
        base = self.base_values.get(sensor_type, 0.0)
        
        if sensor_type == 'ultrasonic':
            # Distance sensor - varies with vehicle presence
            import random
            if random.random() < 0.3:  # 30% chance of vehicle
                return random.uniform(10, 30)  # Vehicle detected
            return random.uniform(50, 200)  # No vehicle
            
        elif sensor_type == 'radar':
            # Speed sensor - occasional vehicles
            import random
            if random.random() < 0.2:  # 20% chance of vehicle
                return random.uniform(20, 80)  # km/h
            return 0.0
            
        elif sensor_type == 'pressure':
            # Road pressure sensor
            import random
            if random.random() < 0.25:  # 25% chance of vehicle
                return random.uniform(500, 2000)  # kg
            return random.uniform(0, 50)  # Background pressure
            
        else:
            # Environmental sensors with small variations
            import random
            variation = random.uniform(-0.1, 0.1)
            return base * (1 + variation)

class UltrasonicSensor:
    """Ultrasonic distance sensor for vehicle detection"""
    
    def __init__(self, trigger_pin: int, echo_pin: int, sensor_id: str):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.sensor_id = sensor_id
        self.simulator = SensorSimulator()
        
        if RASPBERRY_PI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
    
    def measure_distance(self) -> float:
        """Measure distance in centimeters"""
        if not RASPBERRY_PI_AVAILABLE:
            return self.simulator.read_sensor('ultrasonic', self.sensor_id)
        
        # Send trigger pulse
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)
        
        # Measure echo duration
        start_time = time.time()
        stop_time = time.time()
        
        while GPIO.input(self.echo_pin) == 0:
            start_time = time.time()
        
        while GPIO.input(self.echo_pin) == 1:
            stop_time = time.time()
        
        # Calculate distance
        duration = stop_time - start_time
        distance = (duration * 34300) / 2  # Sound speed = 343 m/s
        
        return distance
    
    def is_vehicle_detected(self, threshold: float = 100.0) -> bool:
        """Check if vehicle is detected based on distance threshold"""
        distance = self.measure_distance()
        return distance < threshold

class RadarSensor:
    """Radar sensor for speed and vehicle detection"""
    
    def __init__(self, sensor_id: str, serial_port: str = "/dev/ttyUSB0"):
        self.sensor_id = sensor_id
        self.serial_port = serial_port
        self.simulator = SensorSimulator()
        self.serial_connection = None
        
        if not RASPBERRY_PI_AVAILABLE:
            print(f"Radar sensor {sensor_id} running in simulation mode")
        else:
            try:
                self.serial_connection = serial.Serial(serial_port, 9600, timeout=1)
            except Exception as e:
                print(f"Failed to connect to radar sensor: {e}")
                self.serial_connection = None
    
    def read_speed(self) -> float:
        """Read vehicle speed in km/h"""
        if not self.serial_connection:
            return self.simulator.read_sensor('radar', self.sensor_id)
        
        try:
            # Send command to radar sensor
            self.serial_connection.write(b'READ_SPEED\n')
            response = self.serial_connection.readline().decode('utf-8').strip()
            
            if response.startswith('SPEED:'):
                speed = float(response.split(':')[1])
                return speed
        except Exception as e:
            print(f"Error reading radar sensor: {e}")
        
        return 0.0
    
    def get_vehicle_count(self, duration: int = 60) -> int:
        """Count vehicles passing in given duration (seconds)"""
        count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            speed = self.read_speed()
            if speed > 5:  # Vehicle detected if speed > 5 km/h
                count += 1
                time.sleep(2)  # Avoid double counting
            time.sleep(0.5)
        
        return count

class PressureSensor:
    """Road pressure sensor for vehicle weight detection"""
    
    def __init__(self, sensor_id: str, analog_pin: int = 0):
        self.sensor_id = sensor_id
        self.analog_pin = analog_pin
        self.simulator = SensorSimulator()
        self.baseline_pressure = 0.0
        self.calibrated = False
    
    def calibrate(self, samples: int = 100):
        """Calibrate sensor baseline when no vehicles present"""
        total = 0.0
        for _ in range(samples):
            total += self.read_raw_pressure()
            time.sleep(0.1)
        
        self.baseline_pressure = total / samples
        self.calibrated = True
        print(f"Pressure sensor {self.sensor_id} calibrated. Baseline: {self.baseline_pressure:.2f}")
    
    def read_raw_pressure(self) -> float:
        """Read raw pressure value"""
        if not RASPBERRY_PI_AVAILABLE:
            return self.simulator.read_sensor('pressure', self.sensor_id)
        
        # Implementation for actual ADC reading would go here
        # This is a placeholder for actual hardware integration
        return 0.0
    
    def get_vehicle_weight(self) -> float:
        """Estimate vehicle weight based on pressure difference"""
        if not self.calibrated:
            self.calibrate()
        
        current_pressure = self.read_raw_pressure()
        pressure_diff = current_pressure - self.baseline_pressure
        
        # Convert pressure difference to estimated weight (simplified)
        if pressure_diff > 10:  # Threshold for vehicle detection
            estimated_weight = pressure_diff * 0.5  # Conversion factor
            return max(0, estimated_weight)
        
        return 0.0

class EnvironmentalSensor:
    """Environmental sensors for weather conditions"""
    
    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self.simulator = SensorSimulator()
    
    def read_temperature(self) -> float:
        """Read temperature in Celsius"""
        return self.simulator.read_sensor('temperature', self.sensor_id)
    
    def read_humidity(self) -> float:
        """Read humidity percentage"""
        return self.simulator.read_sensor('humidity', self.sensor_id)
    
    def read_light_level(self) -> float:
        """Read light level in lux"""
        return self.simulator.read_sensor('light', self.sensor_id)
    
    def get_weather_data(self) -> Dict[str, float]:
        """Get complete weather data"""
        return {
            'temperature': self.read_temperature(),
            'humidity': self.read_humidity(),
            'light_level': self.read_light_level()
        }

class MQTTSensorManager:
    """MQTT manager for sensor data communication"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.connected = False
        self.sensor_data_callbacks = []
        
        # MQTT event handlers
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker")
            # Subscribe to sensor topics
            client.subscribe("traffic/sensors/+/+")
            client.subscribe("traffic/intersection/+/sensors/+")
        else:
            print(f"Failed to connect to MQTT broker. Code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        self.connected = False
        print("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split('/')
            payload = json.loads(msg.payload.decode())
            
            # Parse sensor data from MQTT message
            sensor_reading = SensorReading(
                sensor_id=payload.get('sensor_id'),
                sensor_type=payload.get('sensor_type'),
                value=payload.get('value'),
                unit=payload.get('unit'),
                timestamp=datetime.fromisoformat(payload.get('timestamp')),
                location=payload.get('location'),
                intersection_id=payload.get('intersection_id'),
                confidence=payload.get('confidence', 1.0),
                metadata=payload.get('metadata', {})
            )
            
            # Notify callbacks
            for callback in self.sensor_data_callbacks:
                callback(sensor_reading)
                
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_sensor_data(self, reading: SensorReading):
        """Publish sensor reading to MQTT"""
        if not self.connected:
            return False
        
        topic = f"traffic/intersection/{reading.intersection_id}/sensors/{reading.sensor_type}"
        payload = json.dumps(asdict(reading), default=str)
        
        result = self.client.publish(topic, payload)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def add_sensor_data_callback(self, callback):
        """Add callback for sensor data reception"""
        self.sensor_data_callbacks.append(callback)

class SensorManager:
    """Main sensor management system"""
    
    def __init__(self, config):
        self.config = config
        self.sensors = {}
        self.mqtt_manager = MQTTSensorManager(
            config.sensors.mqtt_broker_host,
            config.sensors.mqtt_broker_port
        )
        self.running = False
        self.data_collection_thread = None
        self.sensor_readings = []
        
        # Initialize sensors based on configuration
        self._initialize_sensors()
        
        # Setup MQTT callbacks
        self.mqtt_manager.add_sensor_data_callback(self._handle_sensor_data)
    
    def _initialize_sensors(self):
        """Initialize all configured sensors"""
        for intersection_id in self.config.traffic_lights.intersections:
            intersection_sensors = {}
            
            # Initialize ultrasonic sensors
            for i, ultrasonic_config in enumerate(self.config.sensors.ultrasonic_sensors):
                sensor_id = f"{intersection_id}_ultrasonic_{i}"
                sensor = UltrasonicSensor(
                    trigger_pin=ultrasonic_config.get('trigger_pin', 18),
                    echo_pin=ultrasonic_config.get('echo_pin', 24),
                    sensor_id=sensor_id
                )
                intersection_sensors[sensor_id] = sensor
            
            # Initialize radar sensors
            for i, radar_config in enumerate(self.config.sensors.radar_sensors):
                sensor_id = f"{intersection_id}_radar_{i}"
                sensor = RadarSensor(
                    sensor_id=sensor_id,
                    serial_port=radar_config.get('serial_port', '/dev/ttyUSB0')
                )
                intersection_sensors[sensor_id] = sensor
            
            # Initialize pressure sensors
            for i, pressure_config in enumerate(self.config.sensors.pressure_sensors):
                sensor_id = f"{intersection_id}_pressure_{i}"
                sensor = PressureSensor(
                    sensor_id=sensor_id,
                    analog_pin=pressure_config.get('analog_pin', 0)
                )
                intersection_sensors[sensor_id] = sensor
            
            # Initialize environmental sensor
            env_sensor_id = f"{intersection_id}_environment"
            intersection_sensors[env_sensor_id] = EnvironmentalSensor(env_sensor_id)
            
            self.sensors[intersection_id] = intersection_sensors
    
    def _handle_sensor_data(self, reading: SensorReading):
        """Handle incoming sensor data"""
        self.sensor_readings.append(reading)
        
        # Keep only recent readings (last 1000)
        if len(self.sensor_readings) > 1000:
            self.sensor_readings = self.sensor_readings[-1000:]
        
        # Log sensor data
        logging.info(f"Sensor data: {reading.sensor_id} = {reading.value} {reading.unit}")
    
    def start_data_collection(self):
        """Start continuous sensor data collection"""
        if self.running:
            return
        
        self.running = True
        self.mqtt_manager.connect()
        
        self.data_collection_thread = threading.Thread(
            target=self._data_collection_loop,
            daemon=True
        )
        self.data_collection_thread.start()
        
        print("Sensor data collection started")
    
    def stop_data_collection(self):
        """Stop sensor data collection"""
        self.running = False
        
        if self.data_collection_thread:
            self.data_collection_thread.join(timeout=5)
        
        self.mqtt_manager.disconnect()
        print("Sensor data collection stopped")
    
    def _data_collection_loop(self):
        """Main data collection loop"""
        while self.running:
            try:
                for intersection_id, intersection_sensors in self.sensors.items():
                    for sensor_id, sensor in intersection_sensors.items():
                        reading = self._read_sensor(sensor, sensor_id, intersection_id)
                        if reading:
                            self.mqtt_manager.publish_sensor_data(reading)
                            self._handle_sensor_data(reading)
                
                time.sleep(self.config.sensors.collection_interval)
                
            except Exception as e:
                logging.error(f"Error in data collection loop: {e}")
                time.sleep(5)
    
    def _read_sensor(self, sensor, sensor_id: str, intersection_id: str) -> Optional[SensorReading]:
        """Read data from a specific sensor"""
        try:
            if isinstance(sensor, UltrasonicSensor):
                distance = sensor.measure_distance()
                return SensorReading(
                    sensor_id=sensor_id,
                    sensor_type='ultrasonic',
                    value=distance,
                    unit='cm',
                    timestamp=datetime.now(),
                    location='road_surface',
                    intersection_id=intersection_id,
                    metadata={'vehicle_detected': distance < 100}
                )
            
            elif isinstance(sensor, RadarSensor):
                speed = sensor.read_speed()
                return SensorReading(
                    sensor_id=sensor_id,
                    sensor_type='radar',
                    value=speed,
                    unit='km/h',
                    timestamp=datetime.now(),
                    location='roadside',
                    intersection_id=intersection_id,
                    metadata={'vehicle_detected': speed > 5}
                )
            
            elif isinstance(sensor, PressureSensor):
                weight = sensor.get_vehicle_weight()
                return SensorReading(
                    sensor_id=sensor_id,
                    sensor_type='pressure',
                    value=weight,
                    unit='kg',
                    timestamp=datetime.now(),
                    location='road_embedded',
                    intersection_id=intersection_id,
                    metadata={'vehicle_detected': weight > 500}
                )
            
            elif isinstance(sensor, EnvironmentalSensor):
                weather_data = sensor.get_weather_data()
                # Return multiple readings for environmental sensor
                readings = []
                for param, value in weather_data.items():
                    unit_map = {'temperature': '°C', 'humidity': '%', 'light_level': 'lux'}
                    readings.append(SensorReading(
                        sensor_id=f"{sensor_id}_{param}",
                        sensor_type='environmental',
                        value=value,
                        unit=unit_map.get(param, ''),
                        timestamp=datetime.now(),
                        location='roadside_pole',
                        intersection_id=intersection_id,
                        metadata={'parameter': param}
                    ))
                return readings[0]  # Return first reading for simplicity
                
        except Exception as e:
            logging.error(f"Error reading sensor {sensor_id}: {e}")
        
        return None
    
    def get_intersection_sensor_data(self, intersection_id: str) -> Dict[str, Any]:
        """Get latest sensor data for specific intersection"""
        intersection_data = {
            'intersection_id': intersection_id,
            'sensors': {},
            'summary': {
                'vehicles_detected': 0,
                'average_speed': 0.0,
                'weather_conditions': {},
                'last_update': datetime.now().isoformat()
            }
        }
        
        # Filter readings for this intersection
        intersection_readings = [
            r for r in self.sensor_readings 
            if r.intersection_id == intersection_id and 
            (datetime.now() - r.timestamp).seconds < 300  # Last 5 minutes
        ]
        
        # Process sensor data
        vehicles_detected = 0
        speeds = []
        
        for reading in intersection_readings:
            intersection_data['sensors'][reading.sensor_id] = {
                'type': reading.sensor_type,
                'value': reading.value,
                'unit': reading.unit,
                'timestamp': reading.timestamp.isoformat(),
                'metadata': reading.metadata
            }
            
            # Aggregate data for summary
            if reading.metadata and reading.metadata.get('vehicle_detected'):
                vehicles_detected += 1
            
            if reading.sensor_type == 'radar' and reading.value > 0:
                speeds.append(reading.value)
            
            if reading.sensor_type == 'environmental':
                param = reading.metadata.get('parameter', 'unknown')
                intersection_data['summary']['weather_conditions'][param] = reading.value
        
        intersection_data['summary']['vehicles_detected'] = vehicles_detected
        intersection_data['summary']['average_speed'] = sum(speeds) / len(speeds) if speeds else 0.0
        
        return intersection_data
    
    def get_all_sensor_data(self) -> Dict[str, Any]:
        """Get sensor data for all intersections"""
        all_data = {}
        for intersection_id in self.sensors.keys():
            all_data[intersection_id] = self.get_intersection_sensor_data(intersection_id)
        return all_data

if __name__ == "__main__":
    # Test sensor manager
    from config.config import load_config
    
    config = load_config()
    sensor_manager = SensorManager(config)
    
    try:
        sensor_manager.start_data_collection()
        
        # Run for 30 seconds
        time.sleep(30)
        
        # Print sensor data
        data = sensor_manager.get_all_sensor_data()
        print(json.dumps(data, indent=2, default=str))
        
    finally:
        sensor_manager.stop_data_collection()
