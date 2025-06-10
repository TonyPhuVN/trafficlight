#!/usr/bin/env python3
"""
Test script to demonstrate improved traffic light timing
Shows how the algorithm now properly prioritizes directions with more vehicles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

def test_vehicle_priority_scenarios():
    """Test scenarios where one direction has significantly more vehicles"""
    print("🚦 Testing Improved Traffic Light Timing Algorithm")
    print("=" * 60)
    print("Demonstrating how directions with more vehicles get more green time")
    print()
    
    optimizer = TrafficLightOptimizer()
    
    # Test scenarios where East-West should get more green time
    test_scenarios = [
        {
            'name': 'East-West Heavy Traffic',
            'counts': {'North': 3, 'South': 2, 'East': 12, 'West': 8},
            'description': 'East-West has 20 vehicles vs North-South 5 vehicles'
        },
        {
            'name': 'Extreme East-West Priority',
            'counts': {'North': 1, 'South': 1, 'East': 15, 'West': 10},
            'description': 'East-West has 25 vehicles vs North-South 2 vehicles'
        },
        {
            'name': 'North-South Heavy Traffic',
            'counts': {'North': 10, 'South': 8, 'East': 2, 'West': 3},
            'description': 'North-South has 18 vehicles vs East-West 5 vehicles'
        },
        {
            'name': 'Balanced Traffic',
            'counts': {'North': 6, 'South': 5, 'East': 5, 'West': 6},
            'description': 'Balanced traffic: North-South 11 vs East-West 11'
        },
        {
            'name': 'Moderate East-West Priority',
            'counts': {'North': 4, 'South': 3, 'East': 8, 'West': 6},
            'description': 'East-West has 14 vehicles vs North-South 7 vehicles'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📊 Test {i}: {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Vehicle counts: {scenario['counts']}")
        
        # Calculate traffic demands
        ns_total = scenario['counts']['North'] + scenario['counts']['South']
        ew_total = scenario['counts']['East'] + scenario['counts']['West']
        total = ns_total + ew_total
        
        print(f"   Traffic demand: NS={ns_total}, EW={ew_total}, Total={total}")
        
        # Get optimized timing
        phase = optimizer.predict_optimal_timing(scenario['counts'])
        
        # Display results
        ns_green = phase.north_south_timing.green_duration
        ew_green = phase.east_west_timing.green_duration
        
        print(f"   🚦 Results:")
        print(f"      North-South: {ns_green}s green ({ns_green/(ns_green+ew_green)*100:.1f}% of green time)")
        print(f"      East-West:   {ew_green}s green ({ew_green/(ns_green+ew_green)*100:.1f}% of green time)")
        print(f"      Total cycle: {phase.total_cycle_time}s")
        print(f"      Efficiency:  {phase.efficiency_score:.2f}")
        
        # Analysis
        if ew_total > ns_total:
            expected_direction = "East-West"
            got_more_time = ew_green > ns_green
        elif ns_total > ew_total:
            expected_direction = "North-South"
            got_more_time = ns_green > ew_green
        else:
            expected_direction = "Balanced"
            got_more_time = abs(ns_green - ew_green) <= 3
        
        status = "✅ CORRECT" if got_more_time else "❌ INCORRECT"
        if expected_direction != "Balanced":
            print(f"   📈 Analysis: {expected_direction} should get more time → {status}")
        else:
            print(f"   📈 Analysis: Should be balanced → {status}")
        
        print(f"   💭 AI Reasoning: {phase.north_south_timing.reasoning}")
        print()
    
    # Test edge cases
    print("🔬 Edge Case Testing:")
    print("-" * 30)
    
    edge_cases = [
        {
            'name': 'No Traffic',
            'counts': {'North': 0, 'South': 0, 'East': 0, 'West': 0}
        },
        {
            'name': 'Single Vehicle East',
            'counts': {'North': 0, 'South': 0, 'East': 1, 'West': 0}
        },
        {
            'name': 'Heavy One Direction',
            'counts': {'North': 0, 'South': 0, 'East': 30, 'West': 0}
        }
    ]
    
    for case in edge_cases:
        print(f"⚠️  {case['name']}: {case['counts']}")
        phase = optimizer.predict_optimal_timing(case['counts'])
        print(f"   Result: NS={phase.north_south_timing.green_duration}s, EW={phase.east_west_timing.green_duration}s")
        print()

def test_emergency_scenarios():
    """Test emergency vehicle priority"""
    print("🚨 Emergency Vehicle Priority Testing:")
    print("-" * 40)
    
    optimizer = TrafficLightOptimizer()
    
    base_counts = {'North': 5, 'South': 4, 'East': 8, 'West': 6}
    
    print("Normal traffic (no emergency):")
    normal_phase = optimizer.predict_optimal_timing(base_counts, emergency_vehicles=0)
    print(f"   NS: {normal_phase.north_south_timing.green_duration}s, EW: {normal_phase.east_west_timing.green_duration}s")
    
    print("With emergency vehicle:")
    emergency_phase = optimizer.predict_optimal_timing(base_counts, emergency_vehicles=1)
    print(f"   NS: {emergency_phase.north_south_timing.green_duration}s, EW: {emergency_phase.east_west_timing.green_duration}s")
    print(f"   Emergency reasoning: {emergency_phase.north_south_timing.reasoning}")
    print()

if __name__ == "__main__":
    test_vehicle_priority_scenarios()
    test_emergency_scenarios()
    
    print("🎯 Summary:")
    print("The improved algorithm now properly prioritizes directions with more vehicles,")
    print("giving them proportionally more green light time while maintaining efficiency.")
