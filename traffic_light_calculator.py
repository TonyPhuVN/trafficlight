"""
🚦 Traffic Light Timing Calculator
Simple tool to calculate green and red light times based on your input
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine.traffic_light_optimizer import TrafficLightOptimizer

class TrafficLightCalculator:
    """User-friendly traffic light timing calculator"""
    
    def __init__(self):
        self.optimizer = TrafficLightOptimizer()
        print("🚦 Traffic Light Timing Calculator")
        print("=" * 50)
        print("Calculate optimal green and red light times based on vehicle counts")
        print()
    
    def get_user_input(self):
        """Get vehicle counts from user input"""
        print("📊 Enter vehicle counts for each direction:")
        print("(Enter 0 if no vehicles in that direction)")
        print()
        
        try:
            north = int(input("🔼 North direction (vehicles): ") or "0")
            south = int(input("🔽 South direction (vehicles): ") or "0")
            east = int(input("▶️ East direction (vehicles): ") or "0")
            west = int(input("◀️ West direction (vehicles): ") or "0")
            
            print()
            emergency = input("🚨 Any emergency vehicles? (y/n): ").lower().startswith('y')
            emergency_count = 1 if emergency else 0
            
            weather = input("🌦️ Weather condition (normal/rain/fog/snow): ").lower()
            if weather not in ['normal', 'rain', 'fog', 'snow', 'heavy_rain', 'ice']:
                weather = 'normal'
            
            return {
                'North': north,
                'South': south,
                'East': east,
                'West': west
            }, emergency_count, weather
            
        except ValueError:
            print("❌ Invalid input. Please enter numbers only.")
            return None, 0, 'normal'
    
    def display_results(self, phase, vehicle_counts, emergency_count, weather):
        """Display calculation results in a user-friendly format"""
        print("\n" + "=" * 60)
        print("🚦 TRAFFIC LIGHT TIMING CALCULATION RESULTS")
        print("=" * 60)
        
        # Input summary
        print("📊 INPUT SUMMARY:")
        print(f"   🔼 North: {vehicle_counts['North']} vehicles")
        print(f"   🔽 South: {vehicle_counts['South']} vehicles")
        print(f"   ▶️ East: {vehicle_counts['East']} vehicles")
        print(f"   ◀️ West: {vehicle_counts['West']} vehicles")
        print(f"   🚨 Emergency vehicles: {emergency_count}")
        print(f"   🌦️ Weather: {weather}")
        
        total_vehicles = sum(vehicle_counts.values())
        ns_vehicles = vehicle_counts['North'] + vehicle_counts['South']
        ew_vehicles = vehicle_counts['East'] + vehicle_counts['West']
        
        print(f"   📈 Total vehicles: {total_vehicles}")
        print(f"   📊 North-South total: {ns_vehicles}")
        print(f"   📊 East-West total: {ew_vehicles}")
        
        print()
        print("🚦 RECOMMENDED TIMING:")
        print(f"   ┌─ North-South Direction ─┐")
        print(f"   │ 🟢 Green Light: {phase.north_south_timing.green_duration:2d} seconds │")
        print(f"   │ 🟡 Yellow Light: {phase.north_south_timing.yellow_duration:2d} seconds │")
        print(f"   │ 🔴 Red Light:   {phase.north_south_timing.red_duration:2d} seconds │")
        print(f"   └─────────────────────────┘")
        
        print(f"   ┌─ East-West Direction ────┐")
        print(f"   │ 🟢 Green Light: {phase.east_west_timing.green_duration:2d} seconds │")
        print(f"   │ 🟡 Yellow Light: {phase.east_west_timing.yellow_duration:2d} seconds │")
        print(f"   │ 🔴 Red Light:   {phase.east_west_timing.red_duration:2d} seconds │")
        print(f"   └─────────────────────────┘")
        
        print()
        print("⏱️ CYCLE INFORMATION:")
        print(f"   🔄 Total cycle time: {phase.total_cycle_time} seconds")
        print(f"   📈 Efficiency score: {phase.efficiency_score:.1%}")
        print(f"   🎯 Confidence level: {phase.north_south_timing.confidence:.1%}")
        
        print()
        print("💡 CALCULATION REASONING:")
        print(f"   {phase.north_south_timing.reasoning}")
        
        # Traffic distribution analysis
        if total_vehicles > 0:
            ns_percentage = (ns_vehicles / total_vehicles) * 100
            ew_percentage = (ew_vehicles / total_vehicles) * 100
            print()
            print("📈 TRAFFIC DISTRIBUTION:")
            print(f"   North-South: {ns_percentage:.1f}% of traffic")
            print(f"   East-West:   {ew_percentage:.1f}% of traffic")
            
            # Timing distribution
            total_green = phase.north_south_timing.green_duration + phase.east_west_timing.green_duration
            ns_time_percentage = (phase.north_south_timing.green_duration / total_green) * 100
            ew_time_percentage = (phase.east_west_timing.green_duration / total_green) * 100
            print()
            print("⏱️ TIME ALLOCATION:")
            print(f"   North-South gets: {ns_time_percentage:.1f}% of green time")
            print(f"   East-West gets:   {ew_time_percentage:.1f}% of green time")
    
    def save_results(self, phase, vehicle_counts, emergency_count, weather):
        """Save results to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"traffic_calculation_{timestamp}.json"
        
        result_data = {
            'timestamp': datetime.now().isoformat(),
            'input': {
                'vehicle_counts': vehicle_counts,
                'emergency_vehicles': emergency_count,
                'weather_condition': weather
            },
            'results': {
                'north_south': {
                    'green_duration': phase.north_south_timing.green_duration,
                    'yellow_duration': phase.north_south_timing.yellow_duration,
                    'red_duration': phase.north_south_timing.red_duration,
                    'confidence': phase.north_south_timing.confidence
                },
                'east_west': {
                    'green_duration': phase.east_west_timing.green_duration,
                    'yellow_duration': phase.east_west_timing.yellow_duration,
                    'red_duration': phase.east_west_timing.red_duration,
                    'confidence': phase.east_west_timing.confidence
                },
                'cycle_info': {
                    'total_cycle_time': phase.total_cycle_time,
                    'efficiency_score': phase.efficiency_score,
                    'phase_name': phase.phase_name
                },
                'reasoning': phase.north_south_timing.reasoning
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(result_data, f, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save results: {e}")
    
    def run_interactive_calculator(self):
        """Run the interactive calculator"""
        while True:
            print("\n" + "─" * 60)
            print("🚦 Traffic Light Timing Calculator")
            print("─" * 60)
            
            # Get user input
            vehicle_counts, emergency_count, weather = self.get_user_input()
            
            if vehicle_counts is None:
                continue
            
            # Calculate timing
            print("\n🔄 Calculating optimal timing...")
            phase = self.optimizer.predict_optimal_timing(
                vehicle_counts, 
                emergency_count, 
                weather
            )
            
            # Display results
            self.display_results(phase, vehicle_counts, emergency_count, weather)
            
            # Ask if user wants to save results
            save = input("\n💾 Save results to file? (y/n): ").lower().startswith('y')
            if save:
                self.save_results(phase, vehicle_counts, emergency_count, weather)
            
            # Ask if user wants to continue
            print("\n" + "─" * 60)
            continue_calc = input("🔄 Calculate another scenario? (y/n): ").lower().startswith('y')
            if not continue_calc:
                break
        
        print("\n🚦 Thank you for using the Traffic Light Calculator!")
        print("Have a safe day! 🚗💨")

def run_quick_calculation():
    """Run a quick calculation with example data"""
    print("🚀 Quick Example Calculation")
    print("=" * 40)
    
    calculator = TrafficLightCalculator()
    
    # Example scenarios
    examples = [
        {
            'name': 'Morning Rush Hour',
            'counts': {'North': 15, 'South': 12, 'East': 8, 'West': 6},
            'emergency': 0,
            'weather': 'normal'
        },
        {
            'name': 'Light Evening Traffic',
            'counts': {'North': 3, 'South': 2, 'East': 5, 'West': 4},
            'emergency': 0,
            'weather': 'normal'
        },
        {
            'name': 'Emergency Response',
            'counts': {'North': 7, 'South': 5, 'East': 8, 'West': 6},
            'emergency': 1,
            'weather': 'normal'
        }
    ]
    
    for example in examples:
        print(f"\n🎯 Example: {example['name']}")
        
        phase = calculator.optimizer.predict_optimal_timing(
            example['counts'],
            example['emergency'],
            example['weather']
        )
        
        calculator.display_results(phase, example['counts'], example['emergency'], example['weather'])
        input("\nPress Enter to continue to next example...")

def main():
    """Main function"""
    print("🚦 Welcome to Traffic Light Timing Calculator!")
    print("=" * 50)
    print("Choose an option:")
    print("1. Interactive Calculator (enter your own data)")
    print("2. Quick Example Calculations")
    print("3. Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            calculator = TrafficLightCalculator()
            calculator.run_interactive_calculator()
        elif choice == '2':
            run_quick_calculation()
        elif choice == '3':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice. Please run the program again.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Calculator interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your input and try again.")

if __name__ == "__main__":
    main()
