"""
🎭 Traffic Data Simulator
Mô phỏng dữ liệu giao thông thực tế cho phát triển và kiểm thử
"""

import time
import random
import threading
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
import cv2

@dataclass
class SimulatedVehicle:
    """Phương tiện mô phỏng"""
    id: str
    vehicle_type: str  # car, truck, bus, motorcycle, bicycle, emergency
    position: Tuple[int, int]  # (x, y)
    speed: float  # km/h
    direction: str  # north, south, east, west
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    timestamp: float

class TrafficSimulator:
    """Simulator cho giao thông"""
    
    def __init__(self, intersection_id: str = "INT001"):
        self.intersection_id = intersection_id
        self.vehicles = []
        self.vehicle_counter = 0
        
        # Simulation parameters
        self.frame_width = 1920
        self.frame_height = 1080
        self.running = False
        
        # Traffic patterns based on time of day
        self.traffic_patterns = {
            'rush_hour_morning': {'density': 0.8, 'speed_factor': 0.6},
            'rush_hour_evening': {'density': 0.9, 'speed_factor': 0.5},
            'normal_day': {'density': 0.4, 'speed_factor': 1.0},
            'night': {'density': 0.1, 'speed_factor': 1.2},
            'weekend': {'density': 0.3, 'speed_factor': 1.1}
        }
        
        # Vehicle type probabilities
        self.vehicle_probabilities = {
            'car': 0.70,
            'motorcycle': 0.15,
            'truck': 0.08,
            'bus': 0.05,
            'bicycle': 0.015,
            'emergency': 0.005
        }
        
        # Speed ranges by vehicle type (km/h)
        self.speed_ranges = {
            'car': (20, 60),
            'motorcycle': (25, 70),
            'truck': (15, 45),
            'bus': (20, 50),
            'bicycle': (10, 25),
            'emergency': (40, 80)
        }
        
        # Vehicle size ranges (width, height)
        self.size_ranges = {
            'car': (120, 80),
            'motorcycle': (60, 40),
            'truck': (200, 120),
            'bus': (250, 140),
            'bicycle': (40, 30),
            'emergency': (130, 90)
        }
        
        # Detection zones (North, East, South, West)
        self.detection_zones = [
            (0, 0, 960, 540),           # North
            (960, 0, 1920, 540),        # East
            (960, 540, 1920, 1080),     # South
            (0, 540, 960, 1080)         # West
        ]
        
        # Entry/exit points for each direction
        self.entry_points = {
            'north': [(480, 50), (580, 50), (680, 50)],
            'south': [(1440, 1030), (1540, 1030), (1640, 1030)],
            'east': [(1870, 270), (1870, 370), (1870, 470)],
            'west': [(50, 810), (50, 910), (50, 1010)]
        }
        
        self.exit_points = {
            'north': [(480, 500), (580, 500), (680, 500)],
            'south': [(1440, 580), (1540, 580), (1640, 580)],
            'east': [(1000, 270), (1000, 370), (1000, 470)],
            'west': [(900, 810), (900, 910), (900, 1010)]
        }
    
    def get_current_traffic_pattern(self) -> Dict:
        """Lấy pattern giao thông hiện tại dựa trên thời gian"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        if weekday >= 5:  # Weekend
            return self.traffic_patterns['weekend']
        elif 7 <= hour <= 9:  # Morning rush
            return self.traffic_patterns['rush_hour_morning']
        elif 17 <= hour <= 19:  # Evening rush
            return self.traffic_patterns['rush_hour_evening']
        elif 22 <= hour or hour <= 6:  # Night
            return self.traffic_patterns['night']
        else:  # Normal day
            return self.traffic_patterns['normal_day']
    
    def generate_vehicle_type(self) -> str:
        """Tạo loại xe ngẫu nhiên theo xác suất"""
        rand = random.random()
        cumulative = 0
        
        for vehicle_type, probability in self.vehicle_probabilities.items():
            cumulative += probability
            if rand <= cumulative:
                return vehicle_type
        
        return 'car'  # Fallback
    
    def generate_vehicle(self, direction: str) -> SimulatedVehicle:
        """Tạo một phương tiện mới"""
        vehicle_type = self.generate_vehicle_type()
        self.vehicle_counter += 1
        vehicle_id = f"SIM_{self.intersection_id}_{self.vehicle_counter:06d}"
        
        # Get entry point
        entry_points = self.entry_points[direction]
        entry_point = random.choice(entry_points)
        
        # Generate speed
        speed_range = self.speed_ranges[vehicle_type]
        speed = random.uniform(*speed_range)
        
        # Apply traffic pattern speed factor
        pattern = self.get_current_traffic_pattern()
        speed *= pattern['speed_factor']
        
        # Add some randomness
        speed += random.gauss(0, 5)  # Normal distribution with std=5
        speed = max(5, speed)  # Minimum 5 km/h
        
        # Generate bounding box
        size_range = self.size_ranges[vehicle_type]
        width = random.randint(int(size_range[0] * 0.8), int(size_range[0] * 1.2))
        height = random.randint(int(size_range[1] * 0.8), int(size_range[1] * 1.2))
        
        x, y = entry_point
        bbox = (x - width//2, y - height//2, x + width//2, y + height//2)
        
        # Generate confidence (simulating AI detection uncertainty)
        base_confidence = 0.85
        if vehicle_type == 'bicycle':
            base_confidence = 0.75  # Harder to detect
        elif vehicle_type == 'truck':
            base_confidence = 0.95  # Easier to detect
        
        confidence = base_confidence + random.gauss(0, 0.1)
        confidence = max(0.5, min(0.99, confidence))
        
        return SimulatedVehicle(
            id=vehicle_id,
            vehicle_type=vehicle_type,
            position=entry_point,
            speed=speed,
            direction=direction,
            bbox=bbox,
            confidence=confidence,
            timestamp=time.time()
        )
    
    def update_vehicle_position(self, vehicle: SimulatedVehicle, dt: float):
        """Cập nhật vị trí phương tiện"""
        # Convert speed from km/h to pixels/second (approximate)
        pixels_per_second = vehicle.speed * 0.5  # Rough conversion
        distance = pixels_per_second * dt
        
        x, y = vehicle.position
        
        # Move based on direction
        if vehicle.direction == 'north':
            y += distance
        elif vehicle.direction == 'south':
            y -= distance
        elif vehicle.direction == 'east':
            x -= distance
        elif vehicle.direction == 'west':
            x += distance
        
        # Add some random movement (lane changes, etc.)
        x += random.gauss(0, 2)
        y += random.gauss(0, 2)
        
        # Update position and bbox
        vehicle.position = (int(x), int(y))
        
        # Update bounding box
        bbox_width = vehicle.bbox[2] - vehicle.bbox[0]
        bbox_height = vehicle.bbox[3] - vehicle.bbox[1]
        vehicle.bbox = (
            int(x - bbox_width//2),
            int(y - bbox_height//2),
            int(x + bbox_width//2),
            int(y + bbox_height//2)
        )
    
    def should_remove_vehicle(self, vehicle: SimulatedVehicle) -> bool:
        """Kiểm tra xem có nên xóa phương tiện không"""
        x, y = vehicle.position
        
        # Remove if out of frame
        if x < -100 or x > self.frame_width + 100 or y < -100 or y > self.frame_height + 100:
            return True
        
        # Remove if reached exit point
        exit_points = self.exit_points[vehicle.direction]
        for exit_x, exit_y in exit_points:
            distance = ((x - exit_x) ** 2 + (y - exit_y) ** 2) ** 0.5
            if distance < 50:  # Close to exit
                return True
        
        return False
    
    def generate_new_vehicles(self):
        """Tạo phương tiện mới dựa trên traffic pattern"""
        pattern = self.get_current_traffic_pattern()
        density = pattern['density']
        
        # Probability of new vehicle per direction per update
        base_probability = 0.1 * density
        
        for direction in ['north', 'south', 'east', 'west']:
            if random.random() < base_probability:
                new_vehicle = self.generate_vehicle(direction)
                self.vehicles.append(new_vehicle)
    
    def update_simulation(self, dt: float = 1.0):
        """Cập nhật toàn bộ simulation"""
        # Update existing vehicles
        for vehicle in self.vehicles[:]:  # Copy list to allow removal
            self.update_vehicle_position(vehicle, dt)
            
            # Remove vehicles that have exited
            if self.should_remove_vehicle(vehicle):
                self.vehicles.remove(vehicle)
        
        # Generate new vehicles
        self.generate_new_vehicles()
        
        # Limit total vehicles to prevent memory issues
        if len(self.vehicles) > 50:
            # Remove oldest vehicles
            self.vehicles = sorted(self.vehicles, key=lambda v: v.timestamp)
            self.vehicles = self.vehicles[-30:]  # Keep newest 30
    
    def get_current_detections(self) -> List[Dict]:
        """Lấy danh sách detection hiện tại"""
        detections = []
        
        for vehicle in self.vehicles:
            detection = {
                'class_id': hash(vehicle.vehicle_type) % 100,
                'class_name': vehicle.vehicle_type,
                'confidence': vehicle.confidence,
                'bbox': vehicle.bbox,
                'center': vehicle.position,
                'area': (vehicle.bbox[2] - vehicle.bbox[0]) * (vehicle.bbox[3] - vehicle.bbox[1]),
                'timestamp': time.time(),
                'speed': vehicle.speed,
                'direction': vehicle.direction,
                'vehicle_id': vehicle.id
            }
            detections.append(detection)
        
        return detections
    
    def get_vehicle_counts_by_zone(self) -> Dict[str, Dict]:
        """Đếm xe theo zone"""
        zone_names = ['North', 'East', 'South', 'West']
        counts = {name: {'cars': 0, 'trucks': 0, 'buses': 0, 'motorcycles': 0, 
                        'bicycles': 0, 'emergency_vehicles': 0, 'total': 0} 
                 for name in zone_names}
        
        for vehicle in self.vehicles:
            # Determine which zone the vehicle is in
            x, y = vehicle.position
            zone_index = -1
            
            for i, (x1, y1, x2, y2) in enumerate(self.detection_zones):
                if x1 <= x <= x2 and y1 <= y <= y2:
                    zone_index = i
                    break
            
            if zone_index >= 0:
                zone_name = zone_names[zone_index]
                vehicle_type = vehicle.vehicle_type
                
                if vehicle_type == 'car':
                    counts[zone_name]['cars'] += 1
                elif vehicle_type == 'truck':
                    counts[zone_name]['trucks'] += 1
                elif vehicle_type == 'bus':
                    counts[zone_name]['buses'] += 1
                elif vehicle_type == 'motorcycle':
                    counts[zone_name]['motorcycles'] += 1
                elif vehicle_type == 'bicycle':
                    counts[zone_name]['bicycles'] += 1
                elif vehicle_type == 'emergency':
                    counts[zone_name]['emergency_vehicles'] += 1
                
                counts[zone_name]['total'] += 1
        
        return counts
    
    def generate_simulation_frame(self) -> np.ndarray:
        """Tạo frame mô phỏng với các phương tiện"""
        # Create black frame
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        # Draw road layout (simplified)
        road_color = (64, 64, 64)  # Dark gray
        
        # Horizontal roads
        cv2.rectangle(frame, (0, 400), (self.frame_width, 700), road_color, -1)
        # Vertical roads  
        cv2.rectangle(frame, (800, 0), (1120, self.frame_height), road_color, -1)
        
        # Draw lane markings
        lane_color = (255, 255, 255)
        
        # Horizontal lane markings
        for y in [500, 600]:
            for x in range(0, self.frame_width, 40):
                cv2.rectangle(frame, (x, y-2), (x+20, y+2), lane_color, -1)
        
        # Vertical lane markings
        for x in [900, 1020]:
            for y in range(0, self.frame_height, 40):
                cv2.rectangle(frame, (x-2, y), (x+2, y+20), lane_color, -1)
        
        # Draw detection zones
        zone_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        for i, (x1, y1, x2, y2) in enumerate(self.detection_zones):
            cv2.rectangle(frame, (x1, y1), (x2, y2), zone_colors[i], 2)
        
        # Draw vehicles
        for vehicle in self.vehicles:
            self._draw_vehicle(frame, vehicle)
        
        return frame
    
    def _draw_vehicle(self, frame: np.ndarray, vehicle: SimulatedVehicle):
        """Vẽ phương tiện lên frame"""
        x1, y1, x2, y2 = vehicle.bbox
        
        # Color by vehicle type
        colors = {
            'car': (0, 255, 0),      # Green
            'truck': (255, 0, 0),    # Red
            'bus': (0, 0, 255),      # Blue
            'motorcycle': (255, 255, 0),  # Yellow
            'bicycle': (255, 0, 255),     # Magenta
            'emergency': (0, 165, 255)    # Orange
        }
        
        color = colors.get(vehicle.vehicle_type, (128, 128, 128))
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw vehicle center
        center_x, center_y = vehicle.position
        cv2.circle(frame, (center_x, center_y), 3, color, -1)
        
        # Draw label
        label = f"{vehicle.vehicle_type} {vehicle.speed:.0f}km/h"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def get_traffic_statistics(self) -> Dict:
        """Lấy thống kê giao thông"""
        total_vehicles = len(self.vehicles)
        
        # Count by type
        type_counts = {}
        total_speed = 0
        emergency_count = 0
        
        for vehicle in self.vehicles:
            vehicle_type = vehicle.vehicle_type
            type_counts[vehicle_type] = type_counts.get(vehicle_type, 0) + 1
            total_speed += vehicle.speed
            
            if vehicle_type == 'emergency':
                emergency_count += 1
        
        avg_speed = total_speed / total_vehicles if total_vehicles > 0 else 0
        
        # Traffic density
        pattern = self.get_current_traffic_pattern()
        density_level = 'low'
        if total_vehicles > 30:
            density_level = 'high'
        elif total_vehicles > 15:
            density_level = 'medium'
        
        return {
            'total_vehicles': total_vehicles,
            'by_type': type_counts,
            'average_speed': avg_speed,
            'emergency_vehicles': emergency_count,
            'density_level': density_level,
            'traffic_pattern': pattern,
            'timestamp': time.time()
        }

# Weather simulation
class WeatherSimulator:
    """Mô phỏng điều kiện thời tiết"""
    
    def __init__(self):
        self.base_temperature = 25.0  # Celsius
        self.base_humidity = 60.0     # Percentage
        self.base_light_level = 500.0 # Lux
        self.rain_probability = 0.1   # 10% chance per hour
        self.is_raining = False
        self.rain_start_time = None
    
    def update_weather(self) -> Dict:
        """Cập nhật điều kiện thời tiết"""
        now = datetime.now()
        hour = now.hour
        
        # Temperature varies by time of day
        temp_variation = 10 * np.sin(2 * np.pi * (hour - 6) / 24)
        temperature = self.base_temperature + temp_variation + random.gauss(0, 2)
        
        # Humidity varies inversely with temperature
        humidity = self.base_humidity + (30 - temperature) + random.gauss(0, 5)
        humidity = max(20, min(100, humidity))
        
        # Light level varies by time of day
        if 6 <= hour <= 18:  # Daytime
            light_factor = 0.5 + 0.5 * np.sin(np.pi * (hour - 6) / 12)
            light_level = self.base_light_level * (0.5 + light_factor) + random.gauss(0, 50)
        else:  # Nighttime
            light_level = 50 + random.gauss(0, 20)
        
        light_level = max(10, light_level)
        
        # Rain simulation
        if not self.is_raining and random.random() < self.rain_probability / 3600:  # Per second
            self.is_raining = True
            self.rain_start_time = now
        elif self.is_raining:
            # Rain lasts 30 minutes to 3 hours
            rain_duration = random.uniform(1800, 10800)  # seconds
            if (now - self.rain_start_time).total_seconds() > rain_duration:
                self.is_raining = False
                self.rain_start_time = None
        
        # Rain affects other parameters
        if self.is_raining:
            humidity += 20
            light_level *= 0.7
            temperature -= 3
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'light_level': round(light_level, 1),
            'rain_detected': self.is_raining,
            'visibility': 'poor' if self.is_raining else 'good',
            'timestamp': time.time()
        }

if __name__ == "__main__":
    # Test simulation
    simulator = TrafficSimulator("INT001")
    weather_sim = WeatherSimulator()
    
    print("🎭 Traffic Simulation Test")
    print("=" * 40)
    
    # Run simulation for 30 seconds
    start_time = time.time()
    while time.time() - start_time < 30:
        simulator.update_simulation(1.0)
        
        # Print stats every 5 seconds
        if int(time.time() - start_time) % 5 == 0:
            stats = simulator.get_traffic_statistics()
            weather = weather_sim.update_weather()
            counts = simulator.get_vehicle_counts_by_zone()
            
            print(f"\n⏰ Time: {int(time.time() - start_time)}s")
            print(f"🚗 Vehicles: {stats['total_vehicles']}")
            print(f"🌡️ Weather: {weather['temperature']}°C, {weather['humidity']}% humidity")
            
            total_by_zone = sum(zone['total'] for zone in counts.values())
            print(f"📊 Total in zones: {total_by_zone}")
        
        time.sleep(1)
    
    print("\n✅ Simulation test completed!")
