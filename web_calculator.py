"""
🚦 Traffic Light Calculator Web App
Web-based interface for calculating traffic light timing
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine.traffic_light_optimizer import TrafficLightOptimizer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic_light_calculator_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the optimizer
optimizer = TrafficLightOptimizer()

@app.route('/')
def index():
    """Main calculator page"""
    return render_template('calculator.html')

@app.route('/api/calculate', methods=['POST'])
def calculate_timing():
    """API endpoint to calculate traffic light timing"""
    try:
        data = request.get_json()
        
        # Extract input data
        vehicle_counts = {
            'North': int(data.get('north', 0)),
            'South': int(data.get('south', 0)),
            'East': int(data.get('east', 0)),
            'West': int(data.get('west', 0))
        }
        
        emergency_vehicles = 1 if data.get('emergency', False) else 0
        weather_condition = data.get('weather', 'normal')
        
        # Calculate optimal timing
        phase = optimizer.predict_optimal_timing(
            vehicle_counts,
            emergency_vehicles,
            weather_condition
        )
        
        # Prepare response
        total_vehicles = sum(vehicle_counts.values())
        ns_vehicles = vehicle_counts['North'] + vehicle_counts['South']
        ew_vehicles = vehicle_counts['East'] + vehicle_counts['West']
        
        response = {
            'success': True,
            'input': {
                'vehicle_counts': vehicle_counts,
                'total_vehicles': total_vehicles,
                'ns_vehicles': ns_vehicles,
                'ew_vehicles': ew_vehicles,
                'emergency_vehicles': emergency_vehicles,
                'weather_condition': weather_condition
            },
            'results': {
                'north_south': {
                    'green_duration': phase.north_south_timing.green_duration,
                    'yellow_duration': phase.north_south_timing.yellow_duration,
                    'red_duration': phase.north_south_timing.red_duration,
                    'confidence': round(phase.north_south_timing.confidence * 100, 1)
                },
                'east_west': {
                    'green_duration': phase.east_west_timing.green_duration,
                    'yellow_duration': phase.east_west_timing.yellow_duration,
                    'red_duration': phase.east_west_timing.red_duration,
                    'confidence': round(phase.east_west_timing.confidence * 100, 1)
                },
                'analysis': {
                    'total_cycle_time': phase.total_cycle_time,
                    'efficiency_score': round(phase.efficiency_score * 100, 1),
                    'phase_name': phase.phase_name,
                    'reasoning': phase.north_south_timing.reasoning
                }
            },
            'distributions': {
                'traffic': {
                    'ns_percentage': round((ns_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 50,
                    'ew_percentage': round((ew_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 50
                },
                'timing': {
                    'total_green': phase.north_south_timing.green_duration + phase.east_west_timing.green_duration,
                    'ns_time_percentage': 0,
                    'ew_time_percentage': 0
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate timing percentages
        total_green = response['distributions']['timing']['total_green']
        if total_green > 0:
            response['distributions']['timing']['ns_time_percentage'] = round(
                (phase.north_south_timing.green_duration / total_green * 100), 1
            )
            response['distributions']['timing']['ew_time_percentage'] = round(
                (phase.east_west_timing.green_duration / total_green * 100), 1
            )
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error calculating traffic light timing'
        }), 400

@app.route('/api/examples')
def get_examples():
    """Get example scenarios"""
    examples = [
        {
            'name': 'Morning Rush Hour',
            'description': 'Heavy northbound traffic during morning commute',
            'data': {'north': 18, 'south': 12, 'east': 6, 'west': 4, 'emergency': False, 'weather': 'normal'}
        },
        {
            'name': 'Evening Rush Hour',
            'description': 'Heavy east-west traffic during evening rush',
            'data': {'north': 5, 'south': 7, 'east': 16, 'west': 14, 'emergency': False, 'weather': 'normal'}
        },
        {
            'name': 'Night Traffic',
            'description': 'Light traffic during late night hours',
            'data': {'north': 2, 'south': 1, 'east': 3, 'west': 1, 'emergency': False, 'weather': 'normal'}
        },
        {
            'name': 'Emergency Response',
            'description': 'Normal traffic with emergency vehicle priority',
            'data': {'north': 8, 'south': 6, 'east': 7, 'west': 5, 'emergency': True, 'weather': 'normal'}
        },
        {
            'name': 'Rainy Weather',
            'description': 'Moderate traffic during rain conditions',
            'data': {'north': 10, 'south': 8, 'east': 9, 'west': 7, 'emergency': False, 'weather': 'rain'}
        },
        {
            'name': 'Balanced Traffic',
            'description': 'Equal traffic distribution in all directions',
            'data': {'north': 8, 'south': 8, 'east': 8, 'west': 8, 'emergency': False, 'weather': 'normal'}
        }
    ]
    return jsonify(examples)

@app.route('/api/save', methods=['POST'])
def save_calculation():
    """Save calculation results to file"""
    try:
        data = request.get_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"traffic_calculation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Results saved to {filename}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error saving calculation results'
        }), 400

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("🚦 Starting Traffic Light Calculator Web App")
    print("=" * 50)
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    print()
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True)
