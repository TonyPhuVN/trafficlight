#!/usr/bin/env python3
"""
Traffic Light Prediction Demo
Demonstrates the Smart Traffic AI system's ability to predict and display
red, green, yellow, and blue traffic lights with AI recommendations.
"""

import requests
import json
import time
import threading
from datetime import datetime

class TrafficLightDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.running = False
        
    def start_demo(self):
        """Start the traffic light prediction demo"""
        print("🚦 Smart Traffic AI - Light Prediction Demo")
        print("=" * 60)
        print(f"📡 Connecting to: {self.base_url}")
        print("🔄 Real-time traffic light predictions with AI")
        print()
        
        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/api/system/status", timeout=5)
            if response.status_code == 200:
                print("✅ Server is online")
            else:
                print("❌ Server not responding")
                return
        except requests.exceptions.RequestException:
            print("❌ Cannot connect to server. Please start the web interface first:")
            print("   python src/web_interface/app.py")
            return
        
        self.running = True
        
        # Start real-time monitoring
        monitor_thread = threading.Thread(target=self._monitor_lights, daemon=True)
        monitor_thread.start()
        
        # Interactive demo
        self._interactive_demo()
    
    def _monitor_lights(self):
        """Monitor traffic lights in real-time"""
        while self.running:
            try:
                # Get current traffic data
                response = requests.get(f"{self.base_url}/api/traffic_data")
                if response.status_code == 200:
                    data = response.json()
                    self._display_light_summary(data)
                
                time.sleep(3)  # Update every 3 seconds
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(5)
    
    def _display_light_summary(self, data):
        """Display summary of all traffic lights"""
        print("\033[2J\033[H")  # Clear screen
        print("🚦 REAL-TIME TRAFFIC LIGHT STATUS")
        print("=" * 60)
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        light_states = data.get('light_states', {})
        
        for intersection_id, directions in light_states.items():
            print(f"📍 {intersection_id.upper().replace('_', ' ')}")
            print("-" * 40)
            
            for direction, light_data in directions.items():
                state = light_data.get('state', 'unknown')
                time_remaining = light_data.get('time_remaining', 0)
                emergency = light_data.get('emergency_predicted', False)
                
                # Color coding
                if state == 'red':
                    color = "🔴"
                elif state == 'yellow':
                    color = "🟡"
                elif state == 'green':
                    color = "🟢"
                elif state == 'blue':
                    color = "🔵"
                else:
                    color = "⚪"
                
                emergency_indicator = " 🚨" if emergency else ""
                
                print(f"  {direction.capitalize():>6}: {color} {state.upper()} ({time_remaining}s){emergency_indicator}")
            
            print()
        
        # Show emergency status
        emergency_response = requests.get(f"{self.base_url}/api/emergency_vehicles")
        if emergency_response.status_code == 200:
            emergency_data = emergency_response.json()
            active_emergencies = emergency_data.get('active_emergencies', [])
            predicted_emergencies = emergency_data.get('predicted_emergencies', [])
            
            if active_emergencies or predicted_emergencies:
                print("🚨 EMERGENCY VEHICLE STATUS")
                print("-" * 30)
                
                for emergency in active_emergencies:
                    print(f"🚑 ACTIVE: {emergency['intersection_id']} ({emergency['direction']}) - {emergency['vehicle_type']}")
                
                for emergency in predicted_emergencies:
                    prob = int(emergency['probability'] * 100)
                    print(f"⚠️  PREDICTED: {emergency['intersection_id']} ({emergency['direction']}) - {prob}% chance")
                
                print()
    
    def _interactive_demo(self):
        """Interactive demo commands"""
        print("\n🎮 INTERACTIVE COMMANDS:")
        print("1️⃣  - Show detailed predictions for Main Intersection")
        print("2️⃣  - Show emergency vehicle predictions")
        print("3️⃣  - Trigger emergency mode test")
        print("4️⃣  - Show all API endpoints")
        print("❌ - Exit demo")
        print()
        
        while self.running:
            try:
                choice = input("Enter command: ").strip()
                
                if choice == '1':
                    self._show_detailed_predictions()
                elif choice == '2':
                    self._show_emergency_predictions()
                elif choice == '3':
                    self._test_emergency_mode()
                elif choice == '4':
                    self._show_api_endpoints()
                elif choice.lower() in ['x', 'exit', 'quit']:
                    break
                else:
                    print("❌ Invalid command")
                    
            except KeyboardInterrupt:
                break
        
        self.running = False
        print("\n👋 Demo stopped")
    
    def _show_detailed_predictions(self):
        """Show detailed AI predictions for main intersection"""
        print("\n🔮 DETAILED AI PREDICTIONS - MAIN INTERSECTION")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/light_predictions/main_intersection")
            if response.status_code == 200:
                data = response.json()
                
                for direction, pred in data['predictions'].items():
                    print(f"\n📍 {direction.upper()} DIRECTION")
                    print("-" * 30)
                    print(f"Current State: {pred['current_state'].upper()}")
                    print(f"Time Remaining: {pred['time_remaining']} seconds")
                    print(f"Next State: {pred['next_state'].upper()}")
                    print(f"Emergency Predicted: {'YES 🚨' if pred['emergency_predicted'] else 'NO'}")
                    print(f"AI Confidence: {pred['confidence_score']*100:.1f}%")
                    
                    # Show AI recommendations
                    if pred['ai_recommendations']:
                        print("\n🤖 AI RECOMMENDATIONS:")
                        for rec in pred['ai_recommendations']:
                            print(f"  • {rec['type'].replace('_', ' ').title()}: {rec['reason']}")
                            if 'action' in rec:
                                print(f"    Action: {rec['action']}")
                    
                    # Show future predictions
                    print("\n⏭️  FUTURE PREDICTIONS:")
                    for future in pred['future_states'][:3]:  # Show first 3
                        offset = future['time_offset']
                        state = future['predicted_state']
                        confidence = future['confidence'] * 100
                        print(f"  • In {offset}s: {state.upper()} ({confidence:.0f}% confidence)")
                    
                    # Show special conditions
                    if pred['special_conditions']:
                        print("\n⚠️  SPECIAL CONDITIONS:")
                        for condition in pred['special_conditions']:
                            if condition['type'] == 'emergency_vehicle':
                                print(f"  • {condition['vehicle_type'].title()} approaching - ETA: {condition['eta']}")
            else:
                print("❌ Failed to get predictions")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _show_emergency_predictions(self):
        """Show emergency vehicle predictions and blue light status"""
        print("\n🚨 EMERGENCY VEHICLE PREDICTIONS")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/api/emergency_vehicles")
            if response.status_code == 200:
                data = response.json()
                
                print(f"⏰ Timestamp: {data['timestamp']}")
                print()
                
                # Active emergencies
                active = data.get('active_emergencies', [])
                if active:
                    print("🚑 ACTIVE EMERGENCY VEHICLES:")
                    for emergency in active:
                        print(f"  • {emergency['intersection_id']} ({emergency['direction']})")
                        print(f"    Vehicle: {emergency['vehicle_type'].title()}")
                        print(f"    Priority: {emergency['priority_level'].upper()}")
                        print(f"    Time Remaining: {emergency['time_remaining']}s")
                        print()
                else:
                    print("✅ No active emergency vehicles")
                
                # Predicted emergencies
                predicted = data.get('predicted_emergencies', [])
                if predicted:
                    print("🔮 PREDICTED EMERGENCY VEHICLES:")
                    for pred in predicted:
                        prob = int(pred['probability'] * 100)
                        print(f"  • {pred['intersection_id']} ({pred['direction']})")
                        print(f"    Probability: {prob}%")
                        print(f"    Estimated Arrival: {pred['estimated_arrival']}")
                        print(f"    Recommended Action: {pred['recommended_action']}")
                        print()
                else:
                    print("✅ No emergency vehicles predicted")
                
                # Blue light status
                blue_lights = data.get('blue_light_status', {})
                print("🔵 BLUE LIGHT STATUS:")
                for intersection, directions in blue_lights.items():
                    for direction, status in directions.items():
                        if status['active'] or status['predicted']:
                            active_str = "ACTIVE" if status['active'] else "PREDICTED"
                            print(f"  • {intersection} ({direction}): {active_str}")
                
            else:
                print("❌ Failed to get emergency data")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _test_emergency_mode(self):
        """Test emergency mode activation"""
        print("\n🚨 EMERGENCY MODE TEST")
        print("=" * 30)
        
        intersections = ["main_intersection", "north_junction", "east_junction", "south_junction"]
        
        print("Available intersections:")
        for i, intersection in enumerate(intersections, 1):
            print(f"  {i}. {intersection}")
        
        try:
            choice = input("\nSelect intersection (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                intersection = intersections[int(choice) - 1]
                
                print(f"\n🚨 Activating emergency mode for {intersection}...")
                
                response = requests.post(f"{self.base_url}/api/control/emergency_mode", 
                                       json={
                                           'intersection_id': intersection,
                                           'direction': 'all_red'
                                       })
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print("✅ Emergency mode activated successfully!")
                    else:
                        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                else:
                    print("❌ Request failed")
            else:
                print("❌ Invalid choice")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _show_api_endpoints(self):
        """Show all available API endpoints"""
        print("\n📡 AVAILABLE API ENDPOINTS")
        print("=" * 50)
        
        endpoints = [
            ("GET", "/api/traffic_data", "Get all traffic data"),
            ("GET", "/api/intersection/<id>", "Get specific intersection data"),
            ("GET", "/api/light_predictions/<id>", "Get AI light predictions"),
            ("GET", "/api/emergency_vehicles", "Get emergency vehicle status"),
            ("GET", "/api/camera_feed/<id>", "Get camera feed"),
            ("GET", "/api/system/status", "Get system health status"),
            ("GET", "/api/analytics/daily_report", "Get daily analytics"),
            ("POST", "/api/control/emergency_mode", "Activate emergency mode"),
            ("POST", "/api/control/light_timing", "Manual light timing control"),
        ]
        
        for method, endpoint, description in endpoints:
            print(f"{method:>4} {endpoint:<30} - {description}")
        
        print(f"\nBase URL: {self.base_url}")
        print("\nExample usage:")
        print(f"curl {self.base_url}/api/light_predictions/main_intersection")
        
        input("\nPress Enter to continue...")

def main():
    """Main demo function"""
    print("🚦 Smart Traffic AI - Traffic Light Prediction Demo")
    print()
    
    # Check for custom server URL
    import sys
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    demo = TrafficLightDemo(base_url)
    demo.start_demo()

if __name__ == "__main__":
    main()
