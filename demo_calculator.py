"""
🚦 Traffic Light Calculator Demo
Demonstrates traffic light timing calculations with various scenarios
"""

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine.traffic_light_optimizer import TrafficLightOptimizer

def demo_traffic_calculations():
    """Run demo calculations showing various traffic scenarios"""
    
    print("🚦 TRAFFIC LIGHT TIMING CALCULATOR DEMO")
    print("=" * 60)
    print("This demo shows how green and red light times are calculated")
    print("based on vehicle counts in each direction.\n")
    
    optimizer = TrafficLightOptimizer()
    
    # Define test scenarios
    scenarios = [
        {
            'name': '🌅 Morning Rush Hour - Heavy North-South',
            'description': 'Typical morning commute with heavy northbound traffic',
            'vehicle_counts': {'North': 18, 'South': 12, 'East': 6, 'West': 4},
            'emergency': 0,
            'weather': 'normal'
        },
        {
            'name': '🌆 Evening Rush Hour - Heavy East-West',
            'description': 'Evening rush with heavy traffic going east-west',
            'vehicle_counts': {'North': 5, 'South': 7, 'East': 16, 'West': 14},
            'emergency': 0,
            'weather': 'normal'
        },
        {
            'name': '🌙 Night Time - Light Traffic',
            'description': 'Late night with minimal traffic',
            'vehicle_counts': {'North': 2, 'South': 1, 'East': 3, 'West': 1},
            'emergency': 0,
            'weather': 'normal'
        },
        {
            'name': '🚨 Emergency Vehicle Priority',
            'description': 'Normal traffic with emergency vehicle present',
            'vehicle_counts': {'North': 8, 'South': 6, 'East': 7, 'West': 5},
            'emergency': 1,
            'weather': 'normal'
        },
        {
            'name': '🌧️ Rainy Day Traffic',
            'description': 'Moderate traffic during rain (extended timing for safety)',
            'vehicle_counts': {'North': 10, 'South': 8, 'East': 9, 'West': 7},
            'emergency': 0,
            'weather': 'rain'
        },
        {
            'name': '⚖️ Balanced Traffic',
            'description': 'Equal traffic in all directions',
            'vehicle_counts': {'North': 8, 'South': 8, 'East': 8, 'West': 8},
            'emergency': 0,
            'weather': 'normal'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*60}")
        print(f"SCENARIO {i}: {scenario['name']}")
        print(f"{'='*60}")
        print(f"📝 Description: {scenario['description']}")
        
        # Display input
        counts = scenario['vehicle_counts']
        total_vehicles = sum(counts.values())
        ns_total = counts['North'] + counts['South']
        ew_total = counts['East'] + counts['West']
        
        print("\n📊 INPUT:")
        print(f"   🔼 North: {counts['North']:2d} vehicles    🔽 South: {counts['South']:2d} vehicles")
        print(f"   ▶️ East:  {counts['East']:2d} vehicles    ◀️ West:  {counts['West']:2d} vehicles")
        print(f"   🚨 Emergency: {scenario['emergency']}          🌦️ Weather: {scenario['weather']}")
        print(f"   📈 Total: {total_vehicles} vehicles (NS: {ns_total}, EW: {ew_total})")
        
        # Calculate optimal timing
        phase = optimizer.predict_optimal_timing(
            scenario['vehicle_counts'],
            scenario['emergency'],
            scenario['weather']
        )
        
        # Display results
        print("\n🚦 CALCULATED TIMING:")
        print("   ┌─ NORTH-SOUTH ────────┬─ EAST-WEST ──────────┐")
        print(f"   │ 🟢 Green: {phase.north_south_timing.green_duration:2d} seconds │ 🟢 Green: {phase.east_west_timing.green_duration:2d} seconds │")
        print(f"   │ 🟡 Yellow: {phase.north_south_timing.yellow_duration:2d} seconds │ 🟡 Yellow: {phase.east_west_timing.yellow_duration:2d} seconds │")
        print(f"   │ 🔴 Red:   {phase.north_south_timing.red_duration:2d} seconds │ 🔴 Red:   {phase.east_west_timing.red_duration:2d} seconds │")
        print("   └──────────────────────┴──────────────────────────┘")
        
        # Show analysis
        print(f"\n📈 ANALYSIS:")
        print(f"   ⏱️ Total cycle time: {phase.total_cycle_time} seconds")
        print(f"   📊 Efficiency score: {phase.efficiency_score:.1%}")
        
        if total_vehicles > 0:
            ns_traffic_pct = (ns_total / total_vehicles) * 100
            ew_traffic_pct = (ew_total / total_vehicles) * 100
            total_green = phase.north_south_timing.green_duration + phase.east_west_timing.green_duration
            ns_time_pct = (phase.north_south_timing.green_duration / total_green) * 100
            ew_time_pct = (phase.east_west_timing.green_duration / total_green) * 100
            
            print(f"   🚗 Traffic distribution: NS {ns_traffic_pct:.1f}%, EW {ew_traffic_pct:.1f}%")
            print(f"   ⏰ Time allocation: NS {ns_time_pct:.1f}%, EW {ew_time_pct:.1f}%")
        
        print(f"   💡 Logic: {phase.north_south_timing.reasoning}")
        
        # Wait for user input between scenarios (except last one)
        if i < len(scenarios):
            input("\n⏸️ Press Enter to see next scenario...")
    
    print(f"\n{'='*60}")
    print("🎯 SUMMARY")
    print(f"{'='*60}")
    print("The Traffic Light Calculator considers:")
    print("• 📊 Vehicle counts in each direction (North, South, East, West)")
    print("• 🚨 Emergency vehicle priority")
    print("• 🌦️ Weather conditions (rain extends timing for safety)")
    print("• ⏰ Time of day patterns (rush hour vs. normal vs. night)")
    print("• ⚖️ Fair distribution based on actual traffic demand")
    print("\n🎮 KEY FEATURES:")
    print("• ✅ Minimum 15-second green lights for safety")
    print("• ✅ Maximum 90-second green lights to prevent excessive waits")  
    print("• ✅ 3-second yellow lights (standard)")
    print("• ✅ Emergency vehicles get priority timing")
    print("• ✅ Weather conditions automatically extend timing")
    print("• ✅ 95%+ efficiency scores through smart optimization")
    
    print(f"\n🚦 To use the interactive calculator, run:")
    print("   python traffic_light_calculator.py")
    print("\n🎉 Demo complete! The system is ready for your input.")

if __name__ == "__main__":
    try:
        demo_traffic_calculations()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        print("Please check the system setup and try again.")
