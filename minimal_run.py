#!/usr/bin/env python3
"""
🚦 Smart Traffic AI System - Minimal Emergency Mode
This is the WORKING version that demonstrates the complete system functionality
without complex dependencies or configuration issues.
"""

import time
import random
import threading
from datetime import datetime
from typing import Dict, List

class MinimalTrafficSystem:
    """Minimal implementation of Smart Traffic AI System"""
    
    def __init__(self):
        print("🚦 Smart Traffic AI System (Minimal Emergency Mode)")
        print("=" * 50)
        print("🎭 EMERGENCY MODE - All systems simulated")
        
        self.running = False
        self.vehicle_counts = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        self.traffic_lights = {'ns': 'green', 'ew': 'red'}
        self.emergency_vehicles = 0
        self.total_vehicles_processed = 0
        
        # Initialize all components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components in simulation mode"""
        print("📹 Camera Manager: Simulated")
        print("🤖 AI Engine: Simulated")
        print("🚦 Traffic Controller: Simulated")
        print("📡 Sensor Manager: Simulated")
        print("💾 Database: Simulated")
        print()
        print("✅ All systems initialized in simulation mode")
    
    def start(self):
        """Start the traffic system simulation"""
        self.running = True
        print("🚀 Starting simulation...")
        
        # Start simulation threads
        camera_thread = threading.Thread(target=self._simulate_camera, daemon=True)
        ai_thread = threading.Thread(target=self._simulate_ai_processing, daemon=True)
        light_thread = threading.Thread(target=self._simulate_traffic_lights, daemon=True)
        
        camera_thread.start()
        ai_thread.start()
        light_thread.start()
        
        # Main simulation loop
        self._run_simulation()
    
    def _simulate_camera(self):
        """Simulate camera feed and vehicle detection"""
        while self.running:
            # Simulate vehicles detected in each direction
            for direction in self.vehicle_counts:
                # Random vehicle detection (0-5 vehicles per cycle)
                new_vehicles = random.randint(0, 5)
                self.vehicle_counts[direction] += new_vehicles
                self.total_vehicles_processed += new_vehicles
            
            # Occasionally add emergency vehicles
            if random.random() < 0.05:  # 5% chance
                self.emergency_vehicles += 1
                print(f"🚨 Emergency vehicle detected! Total: {self.emergency_vehicles}")
            
            time.sleep(2)
    
    def _simulate_ai_processing(self):
        """Simulate AI traffic analysis and predictions"""
        while self.running:
            total_vehicles = sum(self.vehicle_counts.values())
            
            if total_vehicles > 0:
                # Simulate vehicle classification
                car_ratio = 0.7
                truck_ratio = 0.2
                motorcycle_ratio = 0.1
                
                cars = int(total_vehicles * car_ratio)
                trucks = int(total_vehicles * truck_ratio)
                motorcycles = total_vehicles - cars - trucks
                
                # Simulate traffic prediction
                congestion_level = self._calculate_congestion_level(total_vehicles)
                optimal_timing = self._calculate_optimal_timing(total_vehicles)
                
                print(f"🤖 AI Analysis: {cars} cars, {trucks} trucks, {motorcycles} motorcycles")
                print(f"📊 Congestion: {congestion_level}, Optimal timing: {optimal_timing}s")
            
            time.sleep(5)
    
    def _simulate_traffic_lights(self):
        """Simulate intelligent traffic light control"""
        light_cycle = 0
        
        while self.running:
            # Calculate traffic density
            ns_traffic = self.vehicle_counts['north'] + self.vehicle_counts['south']
            ew_traffic = self.vehicle_counts['east'] + self.vehicle_counts['west']
            
            # Intelligent timing based on traffic
            if ns_traffic > ew_traffic:
                ns_time = 45
                ew_time = 30
            elif ew_traffic > ns_traffic:
                ns_time = 30
                ew_time = 45
            else:
                ns_time = ew_time = 35
            
            # Emergency vehicle priority
            if self.emergency_vehicles > 0:
                print("🚨 Emergency priority activated!")
                ns_time = ew_time = 20  # Shorter cycles for emergency
            
            # North-South green
            self.traffic_lights = {'ns': 'green', 'ew': 'red'}
            print(f"🚦 NS: GREEN ({ns_time}s), EW: RED")
            
            # Process vehicles
            self._process_vehicles('ns', ns_time)
            time.sleep(ns_time)
            
            # Yellow transition
            self.traffic_lights = {'ns': 'yellow', 'ew': 'red'}
            print("🟡 NS: YELLOW (3s)")
            time.sleep(3)
            
            # East-West green
            self.traffic_lights = {'ns': 'red', 'ew': 'green'}
            print(f"🚦 NS: RED, EW: GREEN ({ew_time}s)")
            
            # Process vehicles
            self._process_vehicles('ew', ew_time)
            time.sleep(ew_time)
            
            # Yellow transition
            self.traffic_lights = {'ns': 'red', 'ew': 'yellow'}
            print("🟡 EW: YELLOW (3s)")
            time.sleep(3)
            
            light_cycle += 1
            print(f"✅ Cycle {light_cycle} completed")
            print("-" * 30)
    
    def _process_vehicles(self, direction_group: str, green_time: int):
        """Simulate vehicles passing through intersection"""
        if direction_group == 'ns':
            directions = ['north', 'south']
        else:
            directions = ['east', 'west']
        
        # Calculate processing rate (vehicles per second)
        base_rate = 2.0  # vehicles per second
        if self.emergency_vehicles > 0:
            base_rate = 3.0  # Faster processing for emergencies
        
        total_processed = int(green_time * base_rate)
        
        for direction in directions:
            if self.vehicle_counts[direction] > 0:
                processed = min(self.vehicle_counts[direction], total_processed // 2)
                self.vehicle_counts[direction] -= processed
                print(f"   ✅ {direction.upper()}: {processed} vehicles processed")
        
        # Process emergency vehicles
        if self.emergency_vehicles > 0:
            emergency_processed = min(self.emergency_vehicles, 2)
            self.emergency_vehicles -= emergency_processed
            print(f"   🚨 Emergency vehicles processed: {emergency_processed}")
    
    def _calculate_congestion_level(self, total_vehicles: int) -> str:
        """Calculate traffic congestion level"""
        if total_vehicles < 5:
            return "Light"
        elif total_vehicles < 15:
            return "Moderate"
        elif total_vehicles < 30:
            return "Heavy"
        else:
            return "Severe"
    
    def _calculate_optimal_timing(self, total_vehicles: int) -> int:
        """Calculate optimal light timing"""
        base_time = 30
        if total_vehicles > 20:
            return base_time + 20
        elif total_vehicles > 10:
            return base_time + 10
        else:
            return base_time
    
    def _run_simulation(self):
        """Main simulation loop with periodic status updates"""
        try:
            step = 0
            while self.running:
                step += 1
                total_waiting = sum(self.vehicle_counts.values())
                
                print(f"\n📊 Simulation step {step}:")
                print(f"   🚗 Vehicles waiting: N:{self.vehicle_counts['north']}, "
                      f"E:{self.vehicle_counts['east']}, S:{self.vehicle_counts['south']}, "
                      f"W:{self.vehicle_counts['west']} (Total: {total_waiting})")
                print(f"   🚨 Emergency vehicles in queue: {self.emergency_vehicles}")
                print(f"   📈 Total vehicles processed: {self.total_vehicles_processed}")
                print(f"   🚦 Current lights: NS={self.traffic_lights['ns']}, EW={self.traffic_lights['ew']}")
                
                # Performance metrics
                if step % 5 == 0:
                    efficiency = max(0, 100 - (total_waiting * 2))
                    print(f"   📊 System efficiency: {efficiency}%")
                    
                    if total_waiting > 25:
                        print("   ⚠️ High congestion detected - optimizing timing")
                    elif total_waiting < 5:
                        print("   ✅ Traffic flow optimal")
                
                time.sleep(10)  # Status update every 10 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the traffic system"""
        self.running = False
        print("\n🔚 Smart Traffic AI System stopped")
        print(f"📊 Final Statistics:")
        print(f"   • Total vehicles processed: {self.total_vehicles_processed}")
        print(f"   • Emergency vehicles handled: {self.emergency_vehicles}")
        print("Thank you for using Smart Traffic AI System!")

def main():
    """Main entry point"""
    try:
        system = MinimalTrafficSystem()
        system.start()
    except Exception as e:
        print(f"\n❌ System error: {e}")
        print("This minimal version should work without issues.")
        print("If you see this error, please report it as a bug.")

if __name__ == "__main__":
    main()
