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
            'rush_hour_morning': {'density': 0.8, 'speed_factor': 0.6, 'max_vehicles': 45},
            'rush_hour_evening': {'density': 0.9, 'speed_factor': 0.5, 'max_vehicles': 50},
            'heavy_traffic': {'density': 1.2, 'speed_factor': 0.3, 'max_vehicles': 80},
            'extreme_congestion': {'density': 1.5, 'speed_factor': 0.2, 'max_vehicles': 100},
            'normal_day': {'density': 0.4, 'speed_factor': 1.0, 'max_vehicles': 25},
            'night': {'density': 0.1, 'speed_factor': 1.2, 'max_vehicles': 10},
            'weekend': {'density': 0.3, 'speed_factor': 1.1, 'max_vehicles': 20},
            'accident_scenario': {'density': 0.8, 'speed_factor': 0.1, 'max_vehicles': 60},
            'event_traffic': {'density': 1.0, 'speed_factor': 0.4, 'max_vehicles': 70}
        }
        
        # Current traffic scenario (can be changed manually)
        self.current_scenario = 'normal_day'
        self.scenario_start_time = time.time()
        
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
        """Lấy pattern giao thông hiện tại dựa trên thời gian hoặc scenario đã đặt"""
        # If manual scenario is set, use it
        if hasattr(self, 'current_scenario') and self.current_scenario in self.traffic_patterns:
            return self.traffic_patterns[self.current_scenario]
        
        # Otherwise use time-based pattern
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
    
    def set_traffic_scenario(self, scenario: str):
        """Đặt scenario giao thông cụ thể"""
        if scenario in self.traffic_patterns:
            self.current_scenario = scenario
            self.scenario_start_time = time.time()
            print(f"🚦 Traffic scenario changed to: {scenario}")
        else:
            available_scenarios = list(self.traffic_patterns.keys())
            print(f"❌ Invalid scenario. Available: {available_scenarios}")
    
    def get_available_scenarios(self) -> List[str]:
        """Lấy danh sách các scenario có sẵn"""
        return list(self.traffic_patterns.keys())
    
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
        
        # Use dynamic vehicle limit based on current traffic pattern
        pattern = self.get_current_traffic_pattern()
        max_vehicles = pattern.get('max_vehicles', 50)
        
        # Limit total vehicles based on current scenario
        if len(self.vehicles) > max_vehicles:
            # Remove oldest vehicles to maintain limit
            self.vehicles = sorted(self.vehicles, key=lambda v: v.timestamp)
            keep_count = max(int(max_vehicles * 0.8), 10)  # Keep 80% of max, minimum 10
            self.vehicles = self.vehicles[-keep_count:]
    
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
    """Mô phỏng điều kiện thời tiết Hà Nội mùa hè"""
    
    def __init__(self):
        # Hanoi summer weather parameters (June-August)
        self.base_temperature = 32.0  # Celsius - typical Hanoi summer temperature
        self.base_humidity = 78.0     # Percentage - high humidity in summer
        self.base_light_level = 800.0 # Lux - bright summer sunlight
        self.rain_probability = 0.25  # 25% chance per hour - frequent summer storms
        self.is_raining = False
        self.rain_start_time = None
        self.rain_intensity = 'light'  # light, moderate, heavy
        
        # Hanoi-specific weather patterns
        self.monsoon_season = True  # Summer is monsoon season
        self.heat_index_base = 38.0  # Feels-like temperature base
    
    def update_weather(self) -> Dict:
        """Cập nhật điều kiện thời tiết Hà Nội mùa hè"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # Hanoi summer temperature pattern (28°C night to 36°C peak afternoon)
        if 6 <= hour <= 18:  # Daytime
            # Peak heat around 2-3 PM (14-15h)
            temp_factor = 0.5 + 0.5 * np.sin(np.pi * (hour - 6) / 12)
            if 13 <= hour <= 16:  # Hottest part of day
                temp_factor += 0.3
            temperature = 28 + (8 * temp_factor) + random.gauss(0, 1.5)
        else:  # Nighttime (cooler but still warm and humid)
            temperature = 28 + random.gauss(0, 1)
        
        # Hanoi summer humidity (very high, 70-95%)
        base_humidity = self.base_humidity
        if self.is_raining:
            humidity = min(95, base_humidity + 15 + random.gauss(0, 3))
        else:
            # Higher humidity in early morning and evening
            if 5 <= hour <= 7 or 18 <= hour <= 22:
                humidity = base_humidity + random.gauss(0, 5)
            else:
                humidity = base_humidity - 5 + random.gauss(0, 5)
        
        humidity = max(65, min(95, humidity))  # Summer humidity never goes below 65%
        
        # Light level with Hanoi summer patterns
        if 6 <= hour <= 18:  # Daytime
            light_factor = 0.3 + 0.7 * np.sin(np.pi * (hour - 6) / 12)
            # Very bright summer sun
            if 10 <= hour <= 16 and not self.is_raining:
                light_level = 1200 + (300 * light_factor) + random.gauss(0, 100)
            else:
                light_level = self.base_light_level * light_factor + random.gauss(0, 80)
        else:  # Nighttime
            light_level = 30 + random.gauss(0, 15)
        
        light_level = max(15, light_level)
        
        # Hanoi summer rain patterns (afternoon thunderstorms are common)
        afternoon_storm_probability = 0.0
        if 13 <= hour <= 18:  # Afternoon storm season
            afternoon_storm_probability = 0.4  # 40% chance during peak storm hours
        elif 19 <= hour <= 22:  # Evening storms
            afternoon_storm_probability = 0.2  # 20% chance
        elif 1 <= hour <= 5:  # Early morning storms
            afternoon_storm_probability = 0.15  # 15% chance
        else:
            afternoon_storm_probability = 0.05  # 5% chance other times
        
        # Rain simulation with intensity
        if not self.is_raining:
            if random.random() < afternoon_storm_probability / 3600:  # Per second
                self.is_raining = True
                self.rain_start_time = now
                # Determine rain intensity
                intensity_rand = random.random()
                if intensity_rand < 0.4:
                    self.rain_intensity = 'light'
                elif intensity_rand < 0.8:
                    self.rain_intensity = 'moderate'
                else:
                    self.rain_intensity = 'heavy'  # Typical Hanoi thunderstorms
        elif self.is_raining:
            # Rain duration based on intensity
            if self.rain_intensity == 'light':
                rain_duration = random.uniform(900, 3600)  # 15 min to 1 hour
            elif self.rain_intensity == 'moderate':
                rain_duration = random.uniform(1800, 5400)  # 30 min to 1.5 hours
            else:  # heavy
                rain_duration = random.uniform(600, 2700)  # 10 min to 45 min (intense but shorter)
            
            if (now - self.rain_start_time).total_seconds() > rain_duration:
                self.is_raining = False
                self.rain_start_time = None
                self.rain_intensity = 'light'
        
        # Weather effects during rain
        if self.is_raining:
            if self.rain_intensity == 'heavy':
                humidity = min(95, humidity + 10)
                light_level *= 0.4  # Very dark during heavy storms
                temperature -= 5  # Significant cooling
            elif self.rain_intensity == 'moderate':
                humidity = min(92, humidity + 7)
                light_level *= 0.6
                temperature -= 3
            else:  # light
                humidity = min(88, humidity + 5)
                light_level *= 0.8
                temperature -= 1
        
        # Calculate heat index (feels-like temperature) typical for Hanoi summer
        heat_index = temperature + (humidity / 100) * 8
        if temperature > 32 and humidity > 70:
            heat_index += 2  # Extra discomfort in high heat + humidity
        
        # Air quality (often poor in summer due to heat and humidity)
        air_quality = 'moderate'
        if humidity > 85 and temperature > 32:
            air_quality = 'poor'
        elif humidity < 75 and not self.is_raining:
            air_quality = 'good'
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'heat_index': round(heat_index, 1),
            'light_level': round(light_level, 1),
            'rain_detected': self.is_raining,
            'rain_intensity': self.rain_intensity if self.is_raining else 'none',
            'air_quality': air_quality,
            'visibility': 'poor' if (self.is_raining and self.rain_intensity == 'heavy') else 'good',
            'weather_condition': 'thunderstorm' if (self.is_raining and self.rain_intensity == 'heavy') 
                               else 'rain' if self.is_raining 
                               else 'hot_humid' if (temperature > 32 and humidity > 80)
                               else 'sunny',
            'season': 'summer_monsoon',
            'location': 'Hanoi, Vietnam',
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
