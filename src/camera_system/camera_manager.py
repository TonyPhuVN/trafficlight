"""
📹 Camera System - Quản lý camera và xử lý video
Tích hợp với AI để phân tích giao thông thời gian thực
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass
from queue import Queue, Empty
import os

@dataclass
class CameraStatus:
    """Trạng thái camera"""
    camera_id: int
    is_connected: bool
    fps: float
    resolution: Tuple[int, int]
    last_frame_time: float
    error_count: int
    total_frames: int

class CameraManager:
    """Quản lý camera và video feed"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Camera object
        self.camera = None
        self.camera_status = CameraStatus(
            camera_id=config.camera.camera_id,
            is_connected=False,
            fps=0.0,
            resolution=(0, 0),
            last_frame_time=0.0,
            error_count=0,
            total_frames=0
        )
        
        # Frame processing
        self.frame_queue = Queue(maxsize=30)  # Buffer for frames
        self.processed_frame_queue = Queue(maxsize=10)
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Threading
        self.capture_thread = None
        self.processing_thread = None
        self.running = False
        
        # Callbacks
        self.frame_callbacks = []
        self.detection_callbacks = []
        
        # Recording
        self.is_recording = False
        self.video_writer = None
        self.recording_path = None
        
        # Performance monitoring
        self.performance_stats = {
            'avg_fps': 0.0,
            'dropped_frames': 0,
            'processing_time': 0.0,
            'queue_size': 0
        }
        
        self.logger.info(f"📹 Camera Manager initialized for camera {config.camera.camera_id}")
    
    def initialize_camera(self) -> bool:
        """
        Khởi tạo camera
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle simulation mode
            if self.config.camera.camera_id == -1:
                self.logger.info("🎭 Simulation mode - using simulated camera")
                self.camera = SimulatedCamera(self.config)
                self.camera_status.is_connected = True
                return True
            
            # Initialize real camera
            self.camera = cv2.VideoCapture(self.config.camera.camera_id)
            
            if not self.camera.isOpened():
                self.logger.error(f"❌ Failed to open camera {self.config.camera.camera_id}")
                return False
            
            # Configure camera settings
            self._configure_camera()
            
            # Test capture
            ret, frame = self.camera.read()
            if not ret or frame is None:
                self.logger.error("❌ Failed to capture test frame")
                return False
            
            # Update status
            self.camera_status.is_connected = True
            self.camera_status.resolution = (frame.shape[1], frame.shape[0])
            
            self.logger.info(f"✅ Camera initialized: {self.camera_status.resolution}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Camera initialization error: {e}")
            return False
    
    def _configure_camera(self):
        """Cấu hình camera settings"""
        if self.camera is None:
            return
        
        try:
            # Set resolution
            width, height = self.config.camera.resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Set FPS
            self.camera.set(cv2.CAP_PROP_FPS, self.config.camera.fps)
            
            # Auto exposure
            if self.config.camera.auto_exposure:
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
            
            # Buffer size
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.logger.info("⚙️ Camera configured")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Camera configuration warning: {e}")
    
    def start_capture(self):
        """Bắt đầu capture video"""
        if self.running:
            self.logger.warning("⚠️ Capture already running")
            return
        
        if not self.camera_status.is_connected:
            if not self.initialize_camera():
                self.logger.error("❌ Cannot start capture - camera not initialized")
                return
        
        self.running = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        self.logger.info("🚀 Camera capture started")
    
    def stop_capture(self):
        """Dừng capture video"""
        self.running = False
        
        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Release camera
        if self.camera:
            self.camera.release()
        
        self.camera_status.is_connected = False
        self.logger.info("🛑 Camera capture stopped")
    
    def _capture_loop(self):
        """Main capture loop"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.running:
            try:
                # Capture frame
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    self.camera_status.error_count += 1
                    if self.camera_status.error_count > 10:
                        self.logger.error("❌ Too many capture errors - stopping")
                        break
                    time.sleep(0.1)
                    continue
                
                # Reset error count on successful capture
                self.camera_status.error_count = 0
                self.camera_status.total_frames += 1
                self.camera_status.last_frame_time = time.time()
                
                # Update current frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Add to processing queue
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    # Queue full - drop oldest frame
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                        self.performance_stats['dropped_frames'] += 1
                    except Empty:
                        pass
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter >= 30:  # Update every 30 frames
                    elapsed = time.time() - fps_start_time
                    self.camera_status.fps = fps_counter / elapsed
                    self.performance_stats['avg_fps'] = self.camera_status.fps
                    fps_counter = 0
                    fps_start_time = time.time()
                
                # Recording
                if self.is_recording and self.video_writer:
                    self.video_writer.write(frame)
                
                # Control frame rate
                time.sleep(1.0 / self.config.camera.fps)
                
            except Exception as e:
                self.logger.error(f"❌ Capture loop error: {e}")
                time.sleep(1)
    
    def _processing_loop(self):
        """Frame processing loop"""
        while self.running:
            try:
                # Get frame from queue
                try:
                    frame = self.frame_queue.get(timeout=1)
                except Empty:
                    continue
                
                start_time = time.time()
                
                # Process frame
                processed_frame = self._process_frame(frame)
                
                # Add to processed queue
                try:
                    self.processed_frame_queue.put_nowait(processed_frame)
                except:
                    # Queue full - drop oldest
                    try:
                        self.processed_frame_queue.get_nowait()
                        self.processed_frame_queue.put_nowait(processed_frame)
                    except Empty:
                        pass
                
                # Update performance stats
                processing_time = time.time() - start_time
                self.performance_stats['processing_time'] = processing_time
                self.performance_stats['queue_size'] = self.frame_queue.qsize()
                
                # Call frame callbacks
                for callback in self.frame_callbacks:
                    try:
                        callback(processed_frame)
                    except Exception as e:
                        self.logger.error(f"❌ Frame callback error: {e}")
                
            except Exception as e:
                self.logger.error(f"❌ Processing loop error: {e}")
                time.sleep(1)
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Xử lý frame cơ bản
        
        Args:
            frame: Input frame
            
        Returns:
            Processed frame
        """
        processed = frame.copy()
        
        # Draw detection zones
        for i, zone in enumerate(self.config.camera.detection_zones):
            x1, y1, x2, y2 = zone
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][i % 4]
            cv2.rectangle(processed, (x1, y1), (x2, y2), color, 2)
            
            # Zone label
            zone_names = ["North", "East", "South", "West"]
            label = zone_names[i % 4]
            cv2.putText(processed, label, (x1 + 5, y1 + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(processed, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add camera info
        info_text = f"Camera {self.camera_status.camera_id} | FPS: {self.camera_status.fps:.1f}"
        cv2.putText(processed, info_text, (10, processed.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return processed
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Lấy frame hiện tại"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_processed_frame(self) -> Optional[np.ndarray]:
        """Lấy frame đã xử lý"""
        try:
            return self.processed_frame_queue.get_nowait()
        except Empty:
            return None
    
    def start_recording(self, output_path: str, codec: str = 'XVID') -> bool:
        """
        Bắt đầu recording video
        
        Args:
            output_path: Đường dẫn file output
            codec: Video codec
            
        Returns:
            True if successful
        """
        if self.is_recording:
            self.logger.warning("⚠️ Already recording")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*codec)
            self.video_writer = cv2.VideoWriter(
                output_path,
                fourcc,
                self.config.camera.fps,
                self.camera_status.resolution
            )
            
            if not self.video_writer.isOpened():
                self.logger.error("❌ Failed to initialize video writer")
                return False
            
            self.is_recording = True
            self.recording_path = output_path
            
            self.logger.info(f"📹 Recording started: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Recording start error: {e}")
            return False
    
    def stop_recording(self):
        """Dừng recording"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.logger.info(f"⏹️ Recording stopped: {self.recording_path}")
        self.recording_path = None
    
    def add_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Thêm callback cho frame processing"""
        self.frame_callbacks.append(callback)
        self.logger.info(f"📝 Frame callback added (total: {len(self.frame_callbacks)})")
    
    def remove_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Xóa frame callback"""
        if callback in self.frame_callbacks:
            self.frame_callbacks.remove(callback)
            self.logger.info(f"🗑️ Frame callback removed")
    
    def get_camera_status(self) -> Dict:
        """Lấy trạng thái camera"""
        return {
            'camera_id': self.camera_status.camera_id,
            'is_connected': self.camera_status.is_connected,
            'fps': round(self.camera_status.fps, 2),
            'resolution': self.camera_status.resolution,
            'error_count': self.camera_status.error_count,
            'total_frames': self.camera_status.total_frames,
            'is_recording': self.is_recording,
            'recording_path': self.recording_path,
            'performance': self.performance_stats.copy()
        }
    
    def calibrate_camera(self) -> bool:
        """Hiệu chỉnh camera"""
        if not self.camera_status.is_connected:
            self.logger.error("❌ Camera not connected for calibration")
            return False
        
        try:
            # Capture calibration frames
            calibration_frames = []
            self.logger.info("📐 Starting camera calibration...")
            
            for i in range(10):
                frame = self.get_current_frame()
                if frame is not None:
                    calibration_frames.append(frame)
                time.sleep(0.5)
            
            if len(calibration_frames) < 5:
                self.logger.error("❌ Not enough frames for calibration")
                return False
            
            # Simple calibration - check brightness and contrast
            avg_brightness = np.mean([np.mean(frame) for frame in calibration_frames])
            self.logger.info(f"📊 Average brightness: {avg_brightness:.1f}")
            
            # Adjust camera settings if needed
            if avg_brightness < 50:
                self.logger.warning("⚠️ Low brightness detected")
            elif avg_brightness > 200:
                self.logger.warning("⚠️ High brightness detected")
            
            self.logger.info("✅ Camera calibration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Calibration error: {e}")
            return False

class SimulatedCamera:
    """Camera mô phỏng cho testing"""
    
    def __init__(self, config):
        self.config = config
        self.frame_count = 0
        
    def read(self):
        """Tạo frame mô phỏng"""
        import random
        
        width, height = self.config.camera.resolution
        
        # Create base frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add some random "traffic" rectangles
        for _ in range(random.randint(2, 8)):
            x1 = random.randint(0, width - 100)
            y1 = random.randint(0, height - 50)
            x2 = x1 + random.randint(50, 100)
            y2 = y1 + random.randint(30, 50)
            
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        
        # Add frame counter
        cv2.putText(frame, f"Simulated Frame {self.frame_count}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.frame_count += 1
        return True, frame
    
    def release(self):
        """Release simulated camera"""
        pass
    
    def isOpened(self):
        """Always return True for simulation"""
        return True
    
    def set(self, prop, value):
        """Mock camera property setting"""
        pass

if __name__ == "__main__":
    # Test camera manager
    import sys
    sys.path.append('..')
    from config.config import SmartTrafficConfig, SystemMode
    
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    camera_manager = CameraManager(config)
    
    print("📹 Camera Manager Test")
    
    # Initialize and start
    if camera_manager.initialize_camera():
        print("✅ Camera initialized")
        
        camera_manager.start_capture()
        print("🚀 Capture started")
        
        # Test for a few seconds
        for i in range(10):
            status = camera_manager.get_camera_status()
            print(f"Status {i+1}: FPS={status['fps']}, Frames={status['total_frames']}")
            time.sleep(1)
        
        camera_manager.stop_capture()
        print("🛑 Capture stopped")
    else:
        print("❌ Camera initialization failed")
