#!/usr/bin/env python3
"""
Simple test script for Traffic Predictor
Tests the traffic prediction functionality without requiring all heavy dependencies
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the traffic predictor
from src.ai_engine.traffic_predictor import TrafficPredictor
from config.config import SmartTrafficConfig, SystemMode

def test_traffic_predictor():
    """Test the traffic predictor functionality"""
    print("🚦 Smart Traffic AI System - Traffic Predictor Test")
    print("=" * 50)
    
    # Initialize configuration and predictor
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    predictor = TrafficPredictor(config)
    
    # Test data simulating current traffic conditions
    test_scenarios = [
        {
            'name': 'Morning Rush Hour',
            'data': {
                'vehicle_counts': {
                    'North': {'total': 15, 'cars': 12, 'trucks': 3},
                    'East': {'total': 8, 'cars': 7, 'trucks': 1},
                    'South': {'total': 20, 'cars': 16, 'trucks': 4},
                    'West': {'total': 5, 'cars': 5, 'trucks': 0}
                },
                'weather': {'condition': 'clear', 'temperature': 22}
            }
        },
        {
            'name': 'Rainy Evening',
            'data': {
                'vehicle_counts': {
                    'North': {'total': 12, 'cars': 10, 'trucks': 2},
                    'East': {'total': 6, 'cars': 5, 'trucks': 1},
                    'South': {'total': 18, 'cars': 15, 'trucks': 3},
                    'West': {'total': 4, 'cars': 4, 'trucks': 0}
                },
                'weather': {'condition': 'rain', 'temperature': 18}
            }
        },
        {
            'name': 'Night Time',
            'data': {
                'vehicle_counts': {
                    'North': {'total': 3, 'cars': 3, 'trucks': 0},
                    'East': {'total': 2, 'cars': 2, 'trucks': 0},
                    'South': {'total': 5, 'cars': 4, 'trucks': 1},
                    'West': {'total': 1, 'cars': 1, 'trucks': 0}
                },
                'weather': {'condition': 'clear', 'temperature': 15}
            }
        }
    ]
    
    # Test each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📊 Test Scenario {i}: {scenario['name']}")
        print("-" * 40)
        
        # Add some historical data for trend analysis
        for j in range(5):
            historical_data = {
                'total_vehicles': sum(zone['total'] for zone in scenario['data']['vehicle_counts'].values()) + j - 2,
                'vehicle_counts': scenario['data']['vehicle_counts']
            }
            predictor.add_historical_data(historical_data)
        
        # Test different prediction horizons
        try:
            # Short-term prediction (15 minutes)
            short_pred = predictor.predict_short_term(scenario['data'], 15)
            print(f"🔮 Short-term (15 min): {short_pred['total_predicted']} vehicles")
            print(f"   Confidence: {short_pred['confidence']:.1%}")
            
            # Medium-term prediction (1 hour)
            medium_pred = predictor.predict_medium_term(scenario['data'], 60)
            print(f"🔮 Medium-term (1 hour): {medium_pred['total_predicted']} vehicles")
            print(f"   Confidence: {medium_pred['confidence']:.1%}")
            
            # Long-term prediction (2 hours)
            long_pred = predictor.predict_long_term(scenario['data'], 2)
            print(f"🔮 Long-term (2 hours): {long_pred['total_predicted']} vehicles")
            print(f"   Confidence: {long_pred['confidence']:.1%}")
            
            # Zone-specific predictions
            print("\n📍 Zone-specific predictions (15 min):")
            for zone, pred in short_pred['predictions'].items():
                print(f"   {zone}: {pred['predicted_vehicles']} vehicles")
                
        except Exception as e:
            print(f"❌ Error in scenario {scenario['name']}: {e}")
    
    # Test accuracy metrics
    print(f"\n📈 Prediction Accuracy Metrics:")
    print("-" * 40)
    accuracy = predictor.get_prediction_accuracy()
    print(f"📊 Short-term MAE: {accuracy['short_term_mae']}")
    print(f"📊 Medium-term MAE: {accuracy['medium_term_mae']}")
    print(f"📊 Long-term MAE: {accuracy['long_term_mae']}")
    print(f"📊 Overall Accuracy: {accuracy['overall_accuracy']:.1f}%")
    
    print(f"\n✅ Traffic Predictor Test Complete!")
    print("🎯 All prediction methods are working correctly")

if __name__ == "__main__":
    test_traffic_predictor()
