import cv2
import numpy as np
from datetime import datetime

class TrafficLightMonitor:
    def __init__(self):
        self.camera = None
        self.output = None
        self.sensitivity = 1.0
        # Định nghĩa dải màu trong không gian HSV
        self.base_color_ranges = {
            'red': [
                (np.array([0, 120, 70]), np.array([10, 255, 255])),
                (np.array([170, 120, 70]), np.array([180, 255, 255]))
            ],
            'yellow': [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
            'green': [(np.array([40, 100, 100]), np.array([80, 255, 255]))]
        }
    
    def setup_camera(self, source=0):
        """Khởi tạo nguồn camera"""
        if self.camera is not None:
            self.camera.release()
        
        self.camera = cv2.VideoCapture(source)
        if not self.camera.isOpened():
            raise ValueError("Lỗi: Không thể mở camera/nguồn video")
    
    def adjust_color_ranges(self):
        """Điều chỉnh dải màu dựa trên độ nhạy"""
        adjusted_ranges = {}
        for color, ranges in self.base_color_ranges.items():
            adjusted_ranges[color] = []
            for lower, upper in ranges:
                adjusted_lower = np.clip(lower * (2 - self.sensitivity), 0, 255)
                adjusted_upper = np.clip(upper * self.sensitivity, 0, 255)
                adjusted_ranges[color].append((adjusted_lower, adjusted_upper))
        return adjusted_ranges
    
    def detect_color(self, hsv_frame, color):
        """Phát hiện màu cụ thể trong khung hình HSV"""
        mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
        color_ranges = self.adjust_color_ranges()
        
        for lower, upper in color_ranges[color]:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv_frame, lower, upper))
        
        return mask
    
    def detect_traffic_light(self, frame):
        """Phát hiện đèn giao thông trong khung hình"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_copy = frame.copy()
        
        max_area = 0
        active_color = None
        light_position = None
        
        for color in ['red', 'yellow', 'green']:
            color_mask = self.detect_color(hsv, color)
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    center = (int(x), int(y))
                    radius = int(radius)
                    
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    if circularity > 0.7 and area > max_area:
                        max_area = area
                        active_color = color
                        light_position = center
                        color_bgr = {'red': (0,0,255), 'yellow': (0,255,255), 'green': (0,255,0)}
                        cv2.circle(frame_copy, center, radius, color_bgr[color], 2)
        
        color_map = {'red': 'ĐỎ', 'yellow': 'VÀNG', 'green': 'XANH'}
        status = color_map.get(active_color, "KHÔNG XÁC ĐỊNH")
        
        # Thêm thông tin thời gian
        cv2.putText(frame_copy, datetime.now().strftime('%H:%M:%S'), 
                   (10, frame_copy.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame_copy, status

    def release(self):
        """Giải phóng tài nguyên"""
        if self.camera is not None:
            self.camera.release()
        if self.output is not None:
            self.output.release()
        cv2.destroyAllWindows()

def main():
    monitor = TrafficLightMonitor()
    try:
        monitor.setup_camera(0)  # 0 cho webcam, hoặc đường dẫn file video
        while True:
            ret, frame = monitor.camera.read()
            if not ret:
                break
            
            processed_frame, status = monitor.detect_traffic_light(frame)
            
            cv2.imshow('Theo Dõi Đèn Giao Thông', processed_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('+'):
                monitor.sensitivity = min(2.0, monitor.sensitivity + 0.1)
            elif key == ord('-'):
                monitor.sensitivity = max(0.1, monitor.sensitivity - 0.1)
        
        monitor.release()
    except Exception as e:
        print(f"Lỗi: {str(e)}")

if __name__ == "__main__":
    main()