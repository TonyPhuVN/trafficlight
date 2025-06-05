"""
🤖 AI Engine - Vehicle Detection Module
Phát hiện và đếm phương tiện giao thông sử dụng YOLO và OpenCV
"""

import cv2
import numpy as np
import torch
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import time
from ultralytics import YOLO
import logging

@dataclass
class DetectionResult:
    """Kết quả phát hiện một đối tượng"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    area: float
    timestamp: float

@dataclass
class VehicleCount:
    """Thống kê đếm xe theo hướng"""
    direction: str
    cars: int = 0
    trucks: int = 0
    buses: int = 0
    motorcycles: int = 0
    bicycles: int = 0
    emergency_vehicles: int = 0
    total: int = 0
    timestamp: float = 0
    
    def update_total(self):
        """Cập nhật tổng số xe"""
        self.total = (self.cars + self.trucks + self.buses + 
                     self.motorcycles + self.bicycles + self.emergency_vehicles)

class VehicleDetector:
    """Class phát hiện phương tiện giao thông"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load YOLO model
        self.model = None
        self.device = self._get_device()
        self.load_model()
        
        # Vehicle classes mapping
        self.vehicle_classes = {
            'car': ['car'],
            'truck': ['truck'],
            'bus': ['bus'],
            'motorcycle': ['motorcycle'],
            'bicycle': ['bicycle'],
            'emergency': ['ambulance', 'fire truck', 'police car']
        }
        
        # Detection zones for each direction
        self.detection_zones = config.camera.detection_zones
        self.zone_names = ["North", "East", "South", "West"]
        
        # Tracking variables
        self.vehicle_counts = {name: VehicleCount(name) for name in self.zone_names}
        self.last_detections = []
        self.frame_count = 0
        
        self.logger.info(f"🤖 Vehicle Detector initialized with {self.config.ai_model.model_type}")
    
    def _get_device(self) -> str:
        """Xác định device để chạy model"""
        if self.config.ai_model.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return self.config.ai_model.device
    
    def load_model(self):
        """Load YOLO model - EMERGENCY OVERRIDE: ALWAYS USE SIMULATION"""
        try:
            # EMERGENCY OVERRIDE: Always use simulation mode to prevent model loading
            self.logger.info("🎭 EMERGENCY OVERRIDE - Using simulation mode only for vehicle detection")
            self.model = None
            return
            
        except Exception as e:
            self.logger.warning(f"⚠️ Model loading override error: {e}, using simulation mode")
            self.model = None
    
    def detect_vehicles(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Phát hiện phương tiện trong frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of DetectionResult objects
        """
        if self.model is None:
            return self._simulate_detection(frame)
        
        try:
            # Run YOLO inference
            results = self.model(frame, 
                               conf=self.config.ai_model.confidence_threshold,
                               iou=self.config.ai_model.nms_threshold,
                               max_det=self.config.ai_model.max_detections)
            
            detections = []
            timestamp = time.time()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box information
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        
                        # Filter only vehicle classes
                        if self._is_vehicle(class_name):
                            center_x = int((x1 + x2) / 2)
                            center_y = int((y1 + y2) / 2)
                            area = (x2 - x1) * (y2 - y1)
                            
                            detection = DetectionResult(
                                class_id=class_id,
                                class_name=class_name,
                                confidence=confidence,
                                bbox=(int(x1), int(y1), int(x2), int(y2)),
                                center=(center_x, center_y),
                                area=area,
                                timestamp=timestamp
                            )
                            detections.append(detection)
            
            self.last_detections = detections
            return detections
            
        except Exception as e:
            self.logger.error(f"❌ Detection error: {e}")
            return []
    
    def _simulate_detection(self, frame: np.ndarray) -> List[DetectionResult]:
        """Mô phỏng phát hiện khi không có model thật"""
        import random
        
        detections = []
        timestamp = time.time()
        
        # Tạo random detections
        num_vehicles = random.randint(1, 8)
        h, w = frame.shape[:2]
        
        vehicle_types = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
        
        for i in range(num_vehicles):
            # Random position
            x1 = random.randint(0, w - 100)
            y1 = random.randint(0, h - 100)
            x2 = x1 + random.randint(50, 150)
            y2 = y1 + random.randint(30, 100)
            
            # Ensure within frame
            x2 = min(x2, w)
            y2 = min(y2, h)
            
            class_name = random.choice(vehicle_types)
            confidence = random.uniform(0.7, 0.95)
            
            detection = DetectionResult(
                class_id=i,
                class_name=class_name,
                confidence=confidence,
                bbox=(x1, y1, x2, y2),
                center=((x1 + x2) // 2, (y1 + y2) // 2),
                area=(x2 - x1) * (y2 - y1),
                timestamp=timestamp
            )
            detections.append(detection)
        
        return detections
    
    def _is_vehicle(self, class_name: str) -> bool:
        """Kiểm tra xem class có phải là phương tiện không"""
        for vehicle_type, classes in self.vehicle_classes.items():
            if class_name.lower() in [c.lower() for c in classes]:
                return True
        return False
    
    def _get_vehicle_type(self, class_name: str) -> str:
        """Lấy loại phương tiện từ class name"""
        for vehicle_type, classes in self.vehicle_classes.items():
            if class_name.lower() in [c.lower() for c in classes]:
                return vehicle_type
        return 'unknown'
    
    def count_vehicles_by_zone(self, detections: List[DetectionResult]) -> Dict[str, VehicleCount]:
        """
        Đếm xe theo zone/hướng
        
        Args:
            detections: List of detection results
            
        Returns:
            Dictionary of vehicle counts by zone
        """
        # Reset counts
        for zone_name in self.zone_names:
            count = self.vehicle_counts[zone_name]
            count.cars = 0
            count.trucks = 0
            count.buses = 0
            count.motorcycles = 0
            count.bicycles = 0
            count.emergency_vehicles = 0
            count.timestamp = time.time()
        
        # Count vehicles in each zone
        for detection in detections:
            zone_index = self._get_zone_for_detection(detection)
            if zone_index >= 0:
                zone_name = self.zone_names[zone_index]
                vehicle_type = self._get_vehicle_type(detection.class_name)
                
                count = self.vehicle_counts[zone_name]
                if vehicle_type == 'car':
                    count.cars += 1
                elif vehicle_type == 'truck':
                    count.trucks += 1
                elif vehicle_type == 'bus':
                    count.buses += 1
                elif vehicle_type == 'motorcycle':
                    count.motorcycles += 1
                elif vehicle_type == 'bicycle':
                    count.bicycles += 1
                elif vehicle_type == 'emergency':
                    count.emergency_vehicles += 1
                
                count.update_total()
        
        return self.vehicle_counts
    
    def _get_zone_for_detection(self, detection: DetectionResult) -> int:
        """Xác định zone chứa detection"""
        center_x, center_y = detection.center
        
        for i, zone in enumerate(self.detection_zones):
            x1, y1, x2, y2 = zone
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                return i
        
        return -1  # Không thuộc zone nào
    
    def analyze_traffic_density(self) -> Dict[str, str]:
        """
        Phân tích mật độ giao thông
        
        Returns:
            Dictionary with traffic density analysis
        """
        analysis = {}
        
        for zone_name, count in self.vehicle_counts.items():
            total = count.total
            
            # Phân loại mật độ
            if total == 0:
                density = "Empty"
            elif total <= 3:
                density = "Light"
            elif total <= 8:
                density = "Moderate"
            elif total <= 15:
                density = "Heavy"
            else:
                density = "Congested"
            
            analysis[zone_name] = density
        
        return analysis
    
    def get_emergency_vehicles(self) -> List[DetectionResult]:
        """Lấy danh sách xe cấp cứu"""
        emergency_vehicles = []
        for detection in self.last_detections:
            if self._get_vehicle_type(detection.class_name) == 'emergency':
                emergency_vehicles.append(detection)
        return emergency_vehicles
    
    def draw_detections(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """
        Vẽ kết quả phát hiện lên frame
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Vẽ detection zones
        for i, zone in enumerate(self.detection_zones):
            x1, y1, x2, y2 = zone
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][i]
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated_frame, self.zone_names[i], 
                       (x1 + 5, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, color, 2)
        
        # Vẽ detections
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            vehicle_type = self._get_vehicle_type(detection.class_name)
            
            # Màu theo loại xe
            colors = {
                'car': (0, 255, 0),      # Xanh lá
                'truck': (255, 0, 0),    # Đỏ
                'bus': (0, 0, 255),      # Xanh dương
                'motorcycle': (255, 255, 0),  # Vàng
                'bicycle': (255, 0, 255),     # Tím
                'emergency': (0, 165, 255)    # Cam
            }
            color = colors.get(vehicle_type, (128, 128, 128))
            
            # Vẽ bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Vẽ label
            label = f"{detection.class_name} {detection.confidence:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Vẽ thống kê
        self._draw_statistics(annotated_frame)
        
        return annotated_frame
    
    def _draw_statistics(self, frame: np.ndarray):
        """Vẽ thống kê lên frame"""
        h, w = frame.shape[:2]
        
        # Background for statistics
        cv2.rectangle(frame, (10, 10), (300, 150), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, 150), (255, 255, 255), 2)
        
        y_offset = 30
        cv2.putText(frame, "Vehicle Count by Zone:", (15, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        for i, (zone_name, count) in enumerate(self.vehicle_counts.items()):
            y_offset += 25
            text = f"{zone_name}: {count.total}"
            cv2.putText(frame, text, (15, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê tổng quan"""
        total_vehicles = sum(count.total for count in self.vehicle_counts.values())
        
        stats = {
            'total_vehicles': total_vehicles,
            'by_zone': {name: count.total for name, count in self.vehicle_counts.items()},
            'by_type': {
                'cars': sum(count.cars for count in self.vehicle_counts.values()),
                'trucks': sum(count.trucks for count in self.vehicle_counts.values()),
                'buses': sum(count.buses for count in self.vehicle_counts.values()),
                'motorcycles': sum(count.motorcycles for count in self.vehicle_counts.values()),
                'bicycles': sum(count.bicycles for count in self.vehicle_counts.values()),
                'emergency': sum(count.emergency_vehicles for count in self.vehicle_counts.values())
            },
            'timestamp': time.time(),
            'frame_count': self.frame_count
        }
        
        return stats

if __name__ == "__main__":
    # Test vehicle detector
    import sys
    sys.path.append('..')
    from config.config import SmartTrafficConfig, SystemMode
    
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    detector = VehicleDetector(config)
    
    # Create test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test detection
    detections = detector.detect_vehicles(test_frame)
    counts = detector.count_vehicles_by_zone(detections)
    
    print("🚗 Vehicle Detection Test Results:")
    for zone_name, count in counts.items():
        print(f"  {zone_name}: {count.total} vehicles")
    
    stats = detector.get_statistics()
    print(f"📊 Total vehicles detected: {stats['total_vehicles']}")
