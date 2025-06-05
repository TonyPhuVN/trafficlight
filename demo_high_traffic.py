#!/usr/bin/env python3
"""
🚦 High Traffic Demo Script
Demonstrates traffic scenarios with more than 20 vehicles
"""

import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_simulation.traffic_simulator import TrafficSimulator, WeatherSimulator
from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

def demo_traffic_scenario(simulator, weather_sim, optimizer, scenario_name, duration=30):
    """Demo a specific traffic scenario"""
    print(f"\n🚦 === {scenario_name.upper().replace('_', ' ')} SCENARIO ===")
    print("=" * 60)
    
    # Set the scenario
    simulator.set_traffic_scenario(scenario_name)
    pattern = simulator.get_current_traffic_pattern()
    
    print(f"📊 Scenario Settings:")
    print(f"   • Density Factor: {pattern['density']}")
    print(f"   • Speed Factor: {pattern['speed_factor']}")
    print(f"   • Max Vehicles: {pattern['max_vehicles']}")
    print()
    
    start_time = time.time()
    max_vehicles_seen = 0
    
    while time.time() - start_time < duration:
        # Update simulation
        simulator.update_simulation(1.0)
        
        # Get current stats
        stats = simulator.get_traffic_statistics()
        zone_counts = simulator.get_vehicle_counts_by_zone()
        weather = weather_sim.update_weather()
        
        current_vehicles = stats['total_vehicles']
        max_vehicles_seen = max(max_vehicles_seen, current_vehicles)
        
        # Show stats every 5 seconds
        elapsed = int(time.time() - start_time)
        if elapsed % 5 == 0 and elapsed > 0:
            # Calculate optimal traffic light timing
            vehicle_counts_dict = {
                'North': zone_counts.get('North', {}).get('total', 0),
                'South': zone_counts.get('South', {}).get('total', 0),
                'East': zone_counts.get('East', {}).get('total', 0),
                'West': zone_counts.get('West', {}).get('total', 0)
            }
            
            emergency_count = stats.get('by_type', {}).get('emergency', 0)
            weather_condition = 'rain' if weather.get('rain_detected', False) else 'normal'
            
            traffic_phase = optimizer.predict_optimal_timing(
                vehicle_counts_dict, 
                emergency_count, 
                weather_condition
            )
            
            print(f"⏰ Time: {elapsed}s | 🚗 Vehicles: {current_vehicles} | "
                  f"💨 Avg Speed: {stats['average_speed']:.1f} km/h | "
                  f"🚨 Emergency: {emergency_count}")
            
            print(f"   🧭 Zone Distribution: N:{vehicle_counts_dict['North']} "
                  f"E:{vehicle_counts_dict['East']} S:{vehicle_counts_dict['South']} "
                  f"W:{vehicle_counts_dict['West']}")
            
            print(f"   🚦 Light Timing: NS={traffic_phase.north_south_timing.green_duration}s, "
                  f"EW={traffic_phase.east_west_timing.green_duration}s | "
                  f"Efficiency: {traffic_phase.efficiency_score:.3f}")
            print()
        
        time.sleep(1)
    
    print(f"✅ Scenario complete! Maximum vehicles seen: {max_vehicles_seen}")
    return max_vehicles_seen

def main():
    """Main demo function"""
    print("🚦 Smart Traffic AI System - High Traffic Scenario Demo")
    print("=" * 70)
    print("This demo will test various traffic scenarios with different vehicle counts")
    print()
    
    # Initialize components
    simulator = TrafficSimulator("DEMO_INTERSECTION")
    weather_sim = WeatherSimulator()
    optimizer = TrafficLightOptimizer()
    
    # List of scenarios to demo
    scenarios_to_test = [
        ('normal_day', 20),
        ('rush_hour_morning', 25),
        ('rush_hour_evening', 25),
        ('heavy_traffic', 30),
        ('extreme_congestion', 35),
        ('accident_scenario', 25),
        ('event_traffic', 30)
    ]
    
    results = {}
    
    for scenario, duration in scenarios_to_test:
        max_vehicles = demo_traffic_scenario(simulator, weather_sim, optimizer, scenario, duration)
        results[scenario] = max_vehicles
        
        # Brief pause between scenarios
        print("⏸️  Pausing for 3 seconds before next scenario...")
        time.sleep(3)
    
    # Summary
    print("\n🎯 === DEMO SUMMARY ===")
    print("=" * 50)
    print("Maximum vehicles achieved in each scenario:")
    print()
    
    for scenario, max_vehicles in results.items():
        pattern = simulator.traffic_patterns[scenario]
        status = "✅ SUCCESS" if max_vehicles >= 20 else "⚠️  LOW"
        print(f"  {scenario.replace('_', ' ').title():<20}: {max_vehicles:>3} vehicles ({status})")
        print(f"    Target: {pattern['max_vehicles']} | Density: {pattern['density']} | Speed: {pattern['speed_factor']}")
        print()
    
    high_traffic_scenarios = [s for s, v in results.items() if v >= 20]
    print(f"🏆 Scenarios with 20+ vehicles: {len(high_traffic_scenarios)}")
    print(f"📈 Highest vehicle count: {max(results.values())} vehicles")
    
    if max(results.values()) >= 20:
        print("\n🎉 SUCCESS: The system successfully demonstrated scenarios with 20+ vehicles!")
    else:
        print("\n⚠️  NOTE: Increase simulation parameters to achieve higher vehicle counts")
    
    print("\n💡 To see live data in the web interface:")
    print("   1. Run: python basic_web_app.py")
    print("   2. Open: http://localhost:5000")
    print("   3. Use API endpoints to switch scenarios:")
    print("      POST /api/scenarios/heavy_traffic")
    print("      POST /api/scenarios/extreme_congestion")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
    finally:
        print("\n👋 Demo completed")
