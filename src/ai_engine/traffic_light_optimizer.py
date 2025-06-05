"""
🚦 AI Traffic Light Optimizer
Predicts optimal green and red light timing based on real-time vehicle counts and traffic patterns
"""

import time
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class LightTiming:
    """Traffic light timing prediction"""
    direction: str
    green_duration: int  # seconds
    red_duration: int    # seconds
    yellow_duration: int = 3  # standard yellow duration
    confidence: float = 0.8
    reasoning: str = ""
    priority: int = 1  # 1=normal, 2=high, 3=emergency
    timestamp: float = 0

@dataclass
class TrafficPhase:
    """Complete traffic light phase for intersection"""
    phase_name: str
    north_south_timing: LightTiming
    east_west_timing: LightTiming
    total_cycle_time: int
    efficiency_score: float
    timestamp: float

class TrafficLightOptimizer:
    """AI-powered traffic light timing optimizer"""
    
    def __init__(self):
        # Base timing parameters (seconds)
        self.min_green_time = 15    # Minimum green light duration
        self.max_green_time = 90    # Maximum green light duration
        self.default_green_time = 30 # Default green duration
        self.yellow_time = 3        # Standard yellow duration
        self.pedestrian_time = 10   # Time for pedestrian crossing
        
        # Traffic analysis parameters
        self.vehicle_processing_rate = 2.0  # vehicles per second per lane
        self.queue_clearance_time = 3       # extra seconds for queue clearance
        self.emergency_priority_multiplier = 2.0
        
        # Historical data for learning
        self.traffic_patterns = {
            'morning_rush': {'north_south_ratio': 0.7, 'east_west_ratio': 0.3},
            'evening_rush': {'north_south_ratio': 0.3, 'east_west_ratio': 0.7},
            'normal_day': {'north_south_ratio': 0.5, 'east_west_ratio': 0.5},
            'night': {'north_south_ratio': 0.4, 'east_west_ratio': 0.6},
            'weekend': {'north_south_ratio': 0.45, 'east_west_ratio': 0.55}
        }
        
        # Current intersection state
        self.current_phase = None
        self.last_optimization_time = 0
        self.optimization_interval = 30  # Re-optimize every 30 seconds
        
        print("🚦 Traffic Light Optimizer initialized")
    
    def predict_optimal_timing(self, vehicle_counts: Dict[str, int], 
                             emergency_vehicles: int = 0,
                             weather_condition: str = "normal") -> TrafficPhase:
        """
        Predict optimal traffic light timing based on current conditions
        
        Args:
            vehicle_counts: Dictionary with vehicle counts by direction
                          (e.g., {'North': 5, 'South': 3, 'East': 8, 'West': 2})
            emergency_vehicles: Number of emergency vehicles detected
            weather_condition: Weather condition affecting traffic
            
        Returns:
            TrafficPhase with optimized timing
        """
        current_time = time.time()
        
        # Get current traffic pattern
        pattern = self._get_current_traffic_pattern()
        
        # Calculate traffic demand for each axis
        north_south_demand = vehicle_counts.get('North', 0) + vehicle_counts.get('South', 0)
        east_west_demand = vehicle_counts.get('East', 0) + vehicle_counts.get('West', 0)
        total_demand = north_south_demand + east_west_demand
        
        # Apply weather adjustments
        weather_factor = self._get_weather_factor(weather_condition)
        
        # Calculate base timing using traffic demand
        if total_demand == 0:
            # No traffic - use minimal timing
            ns_green = self.min_green_time
            ew_green = self.min_green_time
            reasoning = "No traffic detected - using minimal timing"
        else:
            # Calculate proportional timing
            ns_ratio = north_south_demand / total_demand if total_demand > 0 else 0.5
            ew_ratio = east_west_demand / total_demand if total_demand > 0 else 0.5
            
            # Apply pattern-based adjustments
            pattern_data = self.traffic_patterns.get(pattern, self.traffic_patterns['normal_day'])
            ns_ratio = (ns_ratio + pattern_data['north_south_ratio']) / 2
            ew_ratio = (ew_ratio + pattern_data['east_west_ratio']) / 2
            
            # Calculate base cycle time based on total demand
            base_cycle_time = self._calculate_base_cycle_time(total_demand)
            
            # Distribute time proportionally
            available_green_time = base_cycle_time - (2 * self.yellow_time)
            ns_green = max(self.min_green_time, 
                          min(self.max_green_time, 
                              int(available_green_time * ns_ratio)))
            ew_green = max(self.min_green_time,
                          min(self.max_green_time, 
                              int(available_green_time * ew_ratio)))
            
            reasoning = f"Proportional timing: NS={ns_ratio:.2f}, EW={ew_ratio:.2f}, Total vehicles={total_demand}"
        
        # Apply weather factor
        ns_green = int(ns_green * weather_factor)
        ew_green = int(ew_green * weather_factor)
        
        # Emergency vehicle priority
        priority_level = 1
        if emergency_vehicles > 0:
            priority_level = 3
            # Give priority to direction with emergency vehicles
            max_emergency_green = int(self.max_green_time * self.emergency_priority_multiplier)
            if self._has_emergency_in_direction(vehicle_counts, 'north_south'):
                ns_green = min(max_emergency_green, ns_green + 20)
                ew_green = max(self.min_green_time, ew_green - 10)
            elif self._has_emergency_in_direction(vehicle_counts, 'east_west'):
                ew_green = min(max_emergency_green, ew_green + 20)
                ns_green = max(self.min_green_time, ns_green - 10)
            reasoning += f" | Emergency priority applied"
        
        # Create timing objects
        ns_timing = LightTiming(
            direction="North-South",
            green_duration=ns_green,
            red_duration=ew_green + self.yellow_time,
            yellow_duration=self.yellow_time,
            confidence=self._calculate_confidence(north_south_demand, total_demand),
            reasoning=reasoning,
            priority=priority_level,
            timestamp=current_time
        )
        
        ew_timing = LightTiming(
            direction="East-West",
            green_duration=ew_green,
            red_duration=ns_green + self.yellow_time,
            yellow_duration=self.yellow_time,
            confidence=self._calculate_confidence(east_west_demand, total_demand),
            reasoning=reasoning,
            priority=priority_level,
            timestamp=current_time
        )
        
        # Calculate total cycle time and efficiency
        total_cycle = ns_green + ew_green + (2 * self.yellow_time)
        efficiency = self._calculate_efficiency_score(vehicle_counts, ns_green, ew_green)
        
        # Create complete phase
        phase = TrafficPhase(
            phase_name=f"{pattern}_optimized",
            north_south_timing=ns_timing,
            east_west_timing=ew_timing,
            total_cycle_time=total_cycle,
            efficiency_score=efficiency,
            timestamp=current_time
        )
        
        self.current_phase = phase
        self.last_optimization_time = current_time
        
        return phase
    
    def _get_current_traffic_pattern(self) -> str:
        """Determine current traffic pattern based on time"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        if weekday >= 5:  # Weekend
            return 'weekend'
        elif 7 <= hour <= 9:  # Morning rush
            return 'morning_rush'
        elif 17 <= hour <= 19:  # Evening rush
            return 'evening_rush'
        elif 22 <= hour or hour <= 6:  # Night
            return 'night'
        else:
            return 'normal_day'
    
    def _calculate_base_cycle_time(self, total_demand: int) -> int:
        """Calculate base cycle time based on traffic demand"""
        if total_demand == 0:
            return 60  # Minimum cycle
        elif total_demand <= 5:
            return 60  # Light traffic
        elif total_demand <= 15:
            return 90  # Moderate traffic
        elif total_demand <= 25:
            return 120  # Heavy traffic
        else:
            return 150  # Very heavy traffic
    
    def _get_weather_factor(self, weather_condition: str) -> float:
        """Get timing adjustment factor based on weather"""
        weather_factors = {
            'normal': 1.0,
            'rain': 1.3,    # 30% longer for safety
            'heavy_rain': 1.5,
            'fog': 1.4,
            'snow': 1.6,
            'ice': 1.8
        }
        return weather_factors.get(weather_condition.lower(), 1.0)
    
    def _has_emergency_in_direction(self, vehicle_counts: Dict[str, int], direction: str) -> bool:
        """Check if emergency vehicles are in specific direction"""
        # Simplified - in real implementation, this would track emergency vehicle locations
        return True if direction == 'north_south' and vehicle_counts.get('North', 0) > 0 else False
    
    def _calculate_confidence(self, direction_demand: int, total_demand: int) -> float:
        """Calculate confidence level for timing prediction"""
        if total_demand == 0:
            return 0.5
        
        # Higher confidence with more data points
        base_confidence = 0.7
        demand_factor = min(1.0, direction_demand / 10)  # Max confidence at 10+ vehicles
        pattern_factor = 0.1  # Add pattern-based confidence
        
        return min(0.95, base_confidence + demand_factor * 0.2 + pattern_factor)
    
    def _calculate_efficiency_score(self, vehicle_counts: Dict[str, int], 
                                  ns_green: int, ew_green: int) -> float:
        """Calculate efficiency score for the timing plan"""
        total_vehicles = sum(vehicle_counts.values())
        if total_vehicles == 0:
            return 0.8
        
        # Calculate vehicles served per second
        ns_vehicles = vehicle_counts.get('North', 0) + vehicle_counts.get('South', 0)
        ew_vehicles = vehicle_counts.get('East', 0) + vehicle_counts.get('West', 0)
        
        ns_throughput = min(ns_vehicles, ns_green * self.vehicle_processing_rate)
        ew_throughput = min(ew_vehicles, ew_green * self.vehicle_processing_rate)
        
        total_throughput = ns_throughput + ew_throughput
        efficiency = total_throughput / total_vehicles if total_vehicles > 0 else 0
        
        return min(1.0, efficiency)
    
    def get_next_light_change_prediction(self, current_light_state: Dict[str, str]) -> Dict[str, Tuple[str, int]]:
        """
        Predict when lights will change next
        
        Args:
            current_light_state: Current state {'north_south': 'green', 'east_west': 'red'}
            
        Returns:
            Dictionary with next state and time until change
        """
        if not self.current_phase:
            return {
                'north_south': ('green', 30),
                'east_west': ('red', 30)
            }
        
        predictions = {}
        
        # North-South prediction
        if current_light_state.get('north_south') == 'green':
            next_state = 'yellow'
            time_until = self.current_phase.north_south_timing.green_duration
        elif current_light_state.get('north_south') == 'yellow':
            next_state = 'red'
            time_until = self.yellow_time
        else:  # red
            next_state = 'green'
            time_until = self.current_phase.east_west_timing.green_duration + self.yellow_time
        
        predictions['north_south'] = (next_state, time_until)
        
        # East-West prediction
        if current_light_state.get('east_west') == 'green':
            next_state = 'yellow'
            time_until = self.current_phase.east_west_timing.green_duration
        elif current_light_state.get('east_west') == 'yellow':
            next_state = 'red'
            time_until = self.yellow_time
        else:  # red
            next_state = 'green'
            time_until = self.current_phase.north_south_timing.green_duration + self.yellow_time
        
        predictions['east_west'] = (next_state, time_until)
        
        return predictions
    
    def analyze_intersection_performance(self, historical_data: List[Dict]) -> Dict:
        """Analyze intersection performance and suggest improvements"""
        if not historical_data:
            return {'status': 'insufficient_data'}
        
        # Calculate average metrics
        avg_cycle_time = sum(d.get('cycle_time', 90) for d in historical_data) / len(historical_data)
        avg_vehicles = sum(d.get('total_vehicles', 0) for d in historical_data) / len(historical_data)
        avg_wait_time = sum(d.get('avg_wait_time', 30) for d in historical_data) / len(historical_data)
        
        # Performance analysis
        performance = {
            'intersection_efficiency': min(1.0, avg_vehicles / (avg_cycle_time / 10)),
            'average_cycle_time': avg_cycle_time,
            'average_vehicles_per_cycle': avg_vehicles,
            'average_wait_time': avg_wait_time,
            'recommendations': []
        }
        
        # Generate recommendations
        if avg_cycle_time > 120:
            performance['recommendations'].append("Consider reducing cycle time during low traffic periods")
        
        if avg_wait_time > 60:
            performance['recommendations'].append("Implement adaptive timing to reduce wait times")
        
        if avg_vehicles < 5:
            performance['recommendations'].append("Use demand-responsive timing for low traffic periods")
        
        return performance
    
    def export_timing_schedule(self, num_hours: int = 24) -> Dict[str, Dict]:
        """Export a complete timing schedule for different time periods"""
        schedule = {}
        
        for hour in range(num_hours):
            # Simulate vehicle counts for each hour
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                vehicle_counts = {'North': 8, 'South': 6, 'East': 12, 'West': 10}
            elif 22 <= hour or hour <= 6:  # Night
                vehicle_counts = {'North': 1, 'South': 1, 'East': 2, 'West': 1}
            else:  # Normal day
                vehicle_counts = {'North': 4, 'South': 3, 'East': 5, 'West': 4}
            
            # Get optimal timing for this hour
            phase = self.predict_optimal_timing(vehicle_counts)
            
            schedule[f"{hour:02d}:00"] = {
                'north_south_green': phase.north_south_timing.green_duration,
                'east_west_green': phase.east_west_timing.green_duration,
                'cycle_time': phase.total_cycle_time,
                'efficiency_score': phase.efficiency_score,
                'pattern': phase.phase_name
            }
        
        return schedule

def test_traffic_light_optimizer():
    """Test the traffic light optimizer"""
    print("🚦 Testing Traffic Light Optimizer")
    print("=" * 50)
    
    optimizer = TrafficLightOptimizer()
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Light Traffic',
            'counts': {'North': 2, 'South': 1, 'East': 3, 'West': 2},
            'emergency': 0
        },
        {
            'name': 'Heavy North-South Traffic',
            'counts': {'North': 12, 'South': 8, 'East': 3, 'West': 2},
            'emergency': 0
        },
        {
            'name': 'Emergency Vehicle Present',
            'counts': {'North': 5, 'South': 4, 'East': 6, 'West': 3},
            'emergency': 1
        },
        {
            'name': 'Rush Hour Traffic',
            'counts': {'North': 15, 'South': 12, 'East': 18, 'West': 14},
            'emergency': 0
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"Vehicle counts: {scenario['counts']}")
        
        phase = optimizer.predict_optimal_timing(
            scenario['counts'], 
            scenario['emergency']
        )
        
        print(f"🚦 North-South: {phase.north_south_timing.green_duration}s green, {phase.north_south_timing.red_duration}s red")
        print(f"🚦 East-West: {phase.east_west_timing.green_duration}s green, {phase.east_west_timing.red_duration}s red")
        print(f"⏱️ Total cycle: {phase.total_cycle_time}s")
        print(f"📈 Efficiency: {phase.efficiency_score:.2f}")
        print(f"💭 Reasoning: {phase.north_south_timing.reasoning}")
        
        # Test light change predictions
        current_state = {'north_south': 'green', 'east_west': 'red'}
        predictions = optimizer.get_next_light_change_prediction(current_state)
        print(f"🔮 Next changes: NS→{predictions['north_south'][0]} in {predictions['north_south'][1]}s, EW→{predictions['east_west'][0]} in {predictions['east_west'][1]}s")

if __name__ == "__main__":
    test_traffic_light_optimizer()
