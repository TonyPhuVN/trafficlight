"""
🚦 Smart Traffic Controller - Điều khiển đèn giao thông thông minh
Tự động điều chỉnh thời gian đèn dựa trên AI và dữ liệu thời gian thực
"""

import time
import threading
import logging
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

class LightState(Enum):
    """Trạng thái đèn giao thông"""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    FLASHING_YELLOW = "flashing_yellow"
    FLASHING_RED = "flashing_red"
    OFF = "off"

class Direction(Enum):
    """Hướng giao thông"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

class Priority(Enum):
    """Mức độ ưu tiên"""
    NORMAL = 0
    HIGH = 1
    EMERGENCY = 2
    PEDESTRIAN = 3

@dataclass
class LightCycle:
    """Chu kỳ đèn giao thông"""
    direction: Direction
    green_time: int
    yellow_time: int
    red_time: int
    priority: Priority = Priority.NORMAL
    
class TrafficLightController:
    """Controller chính cho hệ thống đèn giao thông"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_states = {
            Direction.NORTH: LightState.RED,
            Direction.SOUTH: LightState.RED,
            Direction.EAST: LightState.RED,
            Direction.WEST: LightState.RED
        }
        
        # Timing information
        self.cycle_start_time = {}
        self.current_cycle = None
        self.cycle_queue = []
        
        # AI Integration
        self.ai_enabled = True
        self.optimization_enabled = True
        self.emergency_mode = False
        
        # Statistics
        self.cycle_history = []
        self.total_cycles = 0
        self.emergency_overrides = 0
        
        # Threading
        self.controller_thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # Callbacks for hardware integration
        self.hardware_callbacks = {}
        
        # Initialize default cycle
        self._initialize_default_cycle()
        
        self.logger.info("🚦 Traffic Light Controller initialized")
    
    def _initialize_default_cycle(self):
        """Khởi tạo chu kỳ mặc định"""
        self.default_cycles = [
            LightCycle(Direction.NORTH, 30, 3, 0),  # North-South first
            LightCycle(Direction.SOUTH, 30, 3, 0),
            LightCycle(Direction.EAST, 25, 3, 0),   # East-West second
            LightCycle(Direction.WEST, 25, 3, 0),
        ]
        
        # Group opposite directions
        self.direction_groups = [
            [Direction.NORTH, Direction.SOUTH],
            [Direction.EAST, Direction.WEST]
        ]
    
    def start_controller(self):
        """Bắt đầu controller"""
        if self.running:
            self.logger.warning("⚠️ Controller already running")
            return
        
        self.running = True
        self.controller_thread = threading.Thread(target=self._controller_loop, daemon=True)
        self.controller_thread.start()
        
        self.logger.info("🚀 Traffic Light Controller started")
    
    def stop_controller(self):
        """Dừng controller"""
        self.running = False
        if self.controller_thread:
            self.controller_thread.join(timeout=5)
        
        # Set all lights to flashing red for safety
        self._set_emergency_mode()
        
        self.logger.info("🛑 Traffic Light Controller stopped")
    
    def _controller_loop(self):
        """Main control loop"""
        while self.running:
            try:
                # Check for emergency override
                if self.emergency_mode:
                    self._handle_emergency_mode()
                    time.sleep(1)
                    continue
                
                # Get current traffic data and predictions
                current_data = self._get_current_traffic_data()
                predictions = self._get_traffic_predictions(current_data)
                
                # Calculate optimal timing
                if self.ai_enabled and self.optimization_enabled:
                    optimal_cycle = self._calculate_optimal_cycle(current_data, predictions)
                else:
                    optimal_cycle = self._get_default_cycle()
                
                # Execute cycle
                self._execute_light_cycle(optimal_cycle)
                
                # Update statistics
                self._update_statistics(optimal_cycle)
                
            except Exception as e:
                self.logger.error(f"❌ Controller loop error: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _get_current_traffic_data(self) -> Dict:
        """Lấy dữ liệu giao thông hiện tại"""
        # This would integrate with vehicle detector
        # For now, return simulated data
        import random
        
        return {
            'vehicle_counts': {
                'North': {'total': random.randint(0, 15), 'emergency': 0},
                'South': {'total': random.randint(0, 12), 'emergency': 0},
                'East': {'total': random.randint(0, 10), 'emergency': 0},
                'West': {'total': random.randint(0, 8), 'emergency': 0}
            },
            'waiting_times': {
                'North': random.randint(0, 120),
                'South': random.randint(0, 100),
                'East': random.randint(0, 80),
                'West': random.randint(0, 60)
            },
            'timestamp': time.time()
        }
    
    def _get_traffic_predictions(self, current_data: Dict) -> Dict:
        """Lấy dự đoán giao thông"""
        # This would integrate with traffic predictor
        # For now, return simulated predictions
        return {
            'short_term': {
                'North': current_data['vehicle_counts']['North']['total'] + 2,
                'South': current_data['vehicle_counts']['South']['total'] + 1,
                'East': current_data['vehicle_counts']['East']['total'] + 3,
                'West': current_data['vehicle_counts']['West']['total'] + 1
            }
        }
    
    def _calculate_optimal_cycle(self, current_data: Dict, predictions: Dict) -> List[LightCycle]:
        """
        Tính toán chu kỳ tối ưu dựa trên AI
        
        Args:
            current_data: Dữ liệu giao thông hiện tại
            predictions: Dự đoán giao thông
            
        Returns:
            List of optimized light cycles
        """
        vehicle_counts = current_data['vehicle_counts']
        waiting_times = current_data['waiting_times']
        
        # Calculate priority scores for each direction
        priority_scores = {}
        for direction in Direction:
            dir_name = direction.value.capitalize()
            
            # Factors affecting priority
            vehicle_count = vehicle_counts.get(dir_name, {}).get('total', 0)
            waiting_time = waiting_times.get(dir_name, 0)
            emergency_vehicles = vehicle_counts.get(dir_name, {}).get('emergency', 0)
            predicted_increase = predictions['short_term'].get(dir_name, 0)
            
            # Calculate weighted score
            score = (
                vehicle_count * 2.0 +           # Current vehicles
                waiting_time * 0.01 +           # Waiting time penalty
                emergency_vehicles * 100.0 +    # Emergency priority
                predicted_increase * 1.5        # Future demand
            )
            
            priority_scores[direction] = score
        
        # Create optimized cycles
        optimized_cycles = []
        
        # Group directions and calculate timing
        for group in self.direction_groups:
            group_score = sum(priority_scores[d] for d in group)
            
            # Calculate green time based on demand
            base_green = self.config.traffic_light.min_green_time
            max_green = self.config.traffic_light.max_green_time
            
            # Scale green time based on relative priority
            total_score = sum(priority_scores.values())
            if total_score > 0:
                relative_priority = group_score / total_score
                green_time = int(base_green + (max_green - base_green) * relative_priority * 2)
                green_time = max(base_green, min(green_time, max_green))
            else:
                green_time = base_green
            
            # Apply time-of-day adjustments
            green_time = self._apply_time_adjustments(green_time)
            
            # Add cycles for each direction in group
            for direction in group:
                cycle = LightCycle(
                    direction=direction,
                    green_time=green_time,
                    yellow_time=self.config.traffic_light.yellow_time,
                    red_time=0  # Calculated automatically
                )
                optimized_cycles.append(cycle)
        
        return optimized_cycles
    
    def _apply_time_adjustments(self, base_time: int) -> int:
        """Áp dụng điều chỉnh theo thời gian"""
        now = datetime.now()
        hour = now.hour
        
        # Rush hour adjustment
        if (7 <= hour <= 9) or (17 <= hour <= 19):
            multiplier = self.config.traffic_light.rush_hour_multiplier
            return int(base_time * multiplier)
        
        # Night time adjustment
        elif hour >= 22 or hour <= 6:
            return max(self.config.traffic_light.night_time_minimum, base_time // 2)
        
        return base_time
    
    def _get_default_cycle(self) -> List[LightCycle]:
        """Lấy chu kỳ mặc định"""
        return self.default_cycles.copy()
    
    def _execute_light_cycle(self, cycles: List[LightCycle]):
        """Thực thi chu kỳ đèn"""
        for cycle in cycles:
            if not self.running or self.emergency_mode:
                break
            
            self._execute_single_cycle(cycle)
    
    def _execute_single_cycle(self, cycle: LightCycle):
        """Thực thi một chu kỳ đơn lẻ"""
        direction = cycle.direction
        
        # Determine which directions to control together
        if direction in [Direction.NORTH, Direction.SOUTH]:
            active_directions = [Direction.NORTH, Direction.SOUTH]
            inactive_directions = [Direction.EAST, Direction.WEST]
        else:
            active_directions = [Direction.EAST, Direction.WEST]
            inactive_directions = [Direction.NORTH, Direction.SOUTH]
        
        try:
            # All red phase for safety
            self._set_all_lights(LightState.RED)
            self._wait_with_check(self.config.traffic_light.all_red_time)
            
            # Green phase for active directions
            for dir in active_directions:
                self._set_light_state(dir, LightState.GREEN)
            for dir in inactive_directions:
                self._set_light_state(dir, LightState.RED)
            
            self.logger.info(f"🟢 Green phase: {[d.value for d in active_directions]} for {cycle.green_time}s")
            self._wait_with_check(cycle.green_time)
            
            # Yellow phase for active directions
            for dir in active_directions:
                self._set_light_state(dir, LightState.YELLOW)
            
            self.logger.info(f"🟡 Yellow phase: {[d.value for d in active_directions]} for {cycle.yellow_time}s")
            self._wait_with_check(cycle.yellow_time)
            
            # Red clearance
            for dir in active_directions:
                self._set_light_state(dir, LightState.RED)
            
            self._wait_with_check(self.config.traffic_light.red_clearance_time)
            
        except Exception as e:
            self.logger.error(f"❌ Cycle execution error: {e}")
            self._set_emergency_mode()
    
    def _set_light_state(self, direction: Direction, state: LightState):
        """Đặt trạng thái đèn cho một hướng"""
        with self.lock:
            self.current_states[direction] = state
            
        # Call hardware callback if available
        callback = self.hardware_callbacks.get('set_light')
        if callback:
            try:
                callback(direction.value, state.value)
            except Exception as e:
                self.logger.error(f"❌ Hardware callback error: {e}")
        
        # Log state change
        self.logger.debug(f"💡 {direction.value}: {state.value}")
    
    def _set_all_lights(self, state: LightState):
        """Đặt tất cả đèn về một trạng thái"""
        for direction in Direction:
            self._set_light_state(direction, state)
    
    def _wait_with_check(self, seconds: int):
        """Chờ với kiểm tra emergency và running state"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            if not self.running or self.emergency_mode:
                break
            time.sleep(0.1)
    
    def _handle_emergency_mode(self):
        """Xử lý chế độ khẩn cấp"""
        # Set all lights to flashing red
        for direction in Direction:
            self._set_light_state(direction, LightState.FLASHING_RED)
        
        self.logger.warning("🚨 Emergency mode active - all lights flashing red")
        time.sleep(2)
    
    def _set_emergency_mode(self):
        """Kích hoạt chế độ khẩn cấp"""
        self.emergency_mode = True
        self.emergency_overrides += 1
        self._set_all_lights(LightState.FLASHING_RED)
        self.logger.warning("🚨 Emergency mode activated")
    
    def _update_statistics(self, cycles: List[LightCycle]):
        """Cập nhật thống kê"""
        self.total_cycles += 1
        
        cycle_info = {
            'cycle_number': self.total_cycles,
            'timestamp': datetime.now().isoformat(),
            'cycles': [
                {
                    'direction': cycle.direction.value,
                    'green_time': cycle.green_time,
                    'yellow_time': cycle.yellow_time
                }
                for cycle in cycles
            ]
        }
        
        self.cycle_history.append(cycle_info)
        
        # Keep only recent history
        if len(self.cycle_history) > 1000:
            self.cycle_history = self.cycle_history[-1000:]
    
    # Public API methods
    
    def override_emergency(self, direction: Direction, duration: int = 30):
        """
        Override khẩn cấp cho một hướng
        
        Args:
            direction: Hướng cần ưu tiên
            duration: Thời gian ưu tiên (giây)
        """
        self.logger.warning(f"🚨 Emergency override: {direction.value} for {duration}s")
        
        # Set all other directions to red
        for dir in Direction:
            if dir != direction:
                self._set_light_state(dir, LightState.RED)
        
        # Set emergency direction to green
        self._set_light_state(direction, LightState.GREEN)
        
        # Wait for emergency duration
        time.sleep(duration)
        
        # Return to normal operation
        self.emergency_mode = False
        self.emergency_overrides += 1
    
    def set_manual_timing(self, direction: Direction, green_time: int):
        """Đặt thời gian thủ công cho một hướng"""
        for cycle in self.default_cycles:
            if cycle.direction == direction:
                cycle.green_time = max(
                    self.config.traffic_light.min_green_time,
                    min(green_time, self.config.traffic_light.max_green_time)
                )
                break
        
        self.logger.info(f"⚙️ Manual timing set: {direction.value} = {green_time}s")
    
    def get_current_states(self) -> Dict[str, str]:
        """Lấy trạng thái hiện tại của tất cả đèn"""
        with self.lock:
            return {dir.value: state.value for dir, state in self.current_states.items()}
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê hoạt động"""
        return {
            'total_cycles': self.total_cycles,
            'emergency_overrides': self.emergency_overrides,
            'current_states': self.get_current_states(),
            'ai_enabled': self.ai_enabled,
            'optimization_enabled': self.optimization_enabled,
            'emergency_mode': self.emergency_mode,
            'uptime_seconds': time.time() - getattr(self, 'start_time', time.time()),
            'recent_cycles': self.cycle_history[-10:] if self.cycle_history else []
        }
    
    def enable_ai_optimization(self, enabled: bool = True):
        """Bật/tắt tối ưu hóa AI"""
        self.ai_enabled = enabled
        self.optimization_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"🤖 AI optimization {status}")
    
    def register_hardware_callback(self, callback_type: str, callback: Callable):
        """Đăng ký callback cho hardware"""
        self.hardware_callbacks[callback_type] = callback
        self.logger.info(f"🔧 Hardware callback registered: {callback_type}")
    
    def simulate_emergency_vehicle(self, direction: Direction):
        """Mô phỏng xe cấp cứu"""
        self.logger.warning(f"🚑 Emergency vehicle detected: {direction.value}")
        
        if self.config.traffic_light.emergency_override:
            threading.Thread(
                target=self.override_emergency,
                args=(direction, self.config.traffic_light.emergency_green_time),
                daemon=True
            ).start()

if __name__ == "__main__":
    # Test traffic light controller
    import sys
    sys.path.append('..')
    from config.config import SmartTrafficConfig, SystemMode
    
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    controller = TrafficLightController(config)
    
    print("🚦 Traffic Light Controller Test")
    print(f"Initial states: {controller.get_current_states()}")
    
    # Test emergency override
    print("\n🚨 Testing emergency override...")
    controller.simulate_emergency_vehicle(Direction.NORTH)
    
    # Test statistics
    stats = controller.get_statistics()
    print(f"\n📊 Statistics: {stats['total_cycles']} cycles completed")
    
    # Start controller for a few seconds
    print("\n🚀 Starting controller...")
    controller.start_controller()
    time.sleep(10)
    controller.stop_controller()
    
    print("✅ Test completed")
