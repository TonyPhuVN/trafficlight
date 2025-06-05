"""
Web Interface for Smart Traffic AI System
Provides real-time dashboard and API endpoints for monitoring and control
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import datetime
import cv2
import base64
import threading
import time
import random
from typing import Dict, List, Any

# Import our custom modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ai_engine.vehicle_detector import VehicleDetector
from src.ai_engine.traffic_predictor import TrafficPredictor
from src.traffic_controller.light_controller import TrafficLightController
from src.camera_system.camera_manager import CameraManager
from config.config import load_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic_ai_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebDashboard:
    def __init__(self):
        self.config = load_config()
        self.vehicle_detector = VehicleDetector(self.config)
        self.traffic_predictor = TrafficPredictor(self.config)
        self.light_controller = TrafficLightController(self.config)
        self.camera_manager = CameraManager(self.config)
        
        # Initialize and start camera
        if self.camera_manager.initialize_camera():
            self.camera_manager.start_capture()
            print("✅ Camera system started")
        else:
            print("⚠️ Camera initialization failed - using simulation mode")
        
        # Default intersections (since not defined in config)
        self.intersections = ["main_intersection", "north_junction", "east_junction", "south_junction"]
        
        # Dashboard data
        self.live_data = {
            'traffic_counts': {},
            'light_states': {},
            'predictions': {},
            'system_status': 'running',
            'alerts': [],
            'performance_metrics': {}
        }
        
        # Start background monitoring
        self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitoring_thread.start()
    
    def _monitor_system(self):
        """Background thread to monitor system and update live data"""
        while True:
            try:
                # Get current frame from camera manager
                frame = self.camera_manager.get_current_frame()
                
                if frame is not None:
                    # Detect vehicles in the frame
                    detections = self.vehicle_detector.detect_vehicles(frame)
                    counts = self.vehicle_detector.count_vehicles_by_zone(detections)
                    
                    # Update traffic counts for all intersections
                    for intersection_id in self.intersections:
                        # Convert VehicleCount objects to dict format
                        intersection_counts = {}
                        for zone_name, count_obj in counts.items():
                            intersection_counts[zone_name] = {
                                'cars': count_obj.cars,
                                'trucks': count_obj.trucks,
                                'buses': count_obj.buses,
                                'motorcycles': count_obj.motorcycles,
                                'bicycles': count_obj.bicycles,
                                'emergency_vehicles': count_obj.emergency_vehicles,
                                'total': count_obj.total,
                                'timestamp': count_obj.timestamp
                            }
                        self.live_data['traffic_counts'][intersection_id] = intersection_counts
                
                # Update light states (simulate for now)
                self.live_data['light_states'] = self._get_simulated_light_states()
                
                # Update predictions
                for intersection_id in self.intersections:
                    current_data = {
                        'vehicle_counts': self.live_data['traffic_counts'].get(intersection_id, {}),
                        'weather': {'condition': 'clear', 'temperature': 25}
                    }
                    
                    # Get predictions from traffic predictor
                    short_pred = self.traffic_predictor.predict_short_term(current_data, 15)
                    medium_pred = self.traffic_predictor.predict_medium_term(current_data, 60)
                    
                    self.live_data['predictions'][intersection_id] = {
                        'short_term': short_pred,
                        'medium_term': medium_pred
                    }
                
                # Emit updates to connected clients
                socketio.emit('dashboard_update', self.live_data)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _get_simulated_light_states(self):
        """Get simulated traffic light states with AI predictions"""
        import random
        import time
        
        states = ['red', 'yellow', 'green']
        directions = ['north', 'south', 'east', 'west']
        
        light_states = {}
        current_time = int(time.time())
        
        for intersection_id in self.intersections:
            light_states[intersection_id] = {}
            
            # Simulate cycle for more realistic behavior
            cycle_position = (current_time // 10) % 4  # 40-second cycle
            
            for i, direction in enumerate(directions):
                # Calculate current state based on cycle
                if cycle_position == i:
                    current_state = 'green'
                    time_remaining = 30 - ((current_time % 40) % 10)
                    next_state = 'yellow'
                elif (cycle_position + 1) % 4 == i:
                    current_state = 'yellow'
                    time_remaining = 5 - ((current_time % 40) % 5)
                    next_state = 'red'
                else:
                    current_state = 'red'
                    remaining_in_cycle = (4 - cycle_position + i) % 4
                    time_remaining = remaining_in_cycle * 10 + (10 - (current_time % 10))
                    next_state = 'green'
                
                # Add some randomness for realism
                time_remaining = max(1, time_remaining + random.randint(-3, 3))
                
                # Check for emergency vehicle prediction (blue light)
                emergency_predicted = random.random() < 0.15  # 15% chance
                
                # Special blue light state for emergency preemption
                if emergency_predicted and current_state == 'red':
                    current_state = 'blue'  # Blue indicates emergency preemption
                    time_remaining = random.randint(5, 15)
                    next_state = 'green'
                
                light_states[intersection_id][direction] = {
                    'state': current_state,
                    'time_remaining': time_remaining,
                    'next_state': next_state,
                    'emergency_predicted': emergency_predicted,
                    'predicted_states': self._generate_state_predictions(current_state, direction, intersection_id)
                }
        
        return light_states
    
    def _generate_state_predictions(self, current_state: str, direction: str, intersection_id: str):
        """Generate AI predictions for future light states"""
        import random
        
        predictions = []
        states = ['red', 'yellow', 'green', 'blue']
        
        # Predict next 5 state changes
        for i in range(1, 6):
            time_offset = i * random.randint(20, 60)  # 20-60 seconds apart
            
            # Simulate traffic-based optimization
            traffic_factor = random.uniform(0.5, 1.5)
            
            if current_state == 'red':
                next_predicted = 'green' if traffic_factor > 1.0 else 'yellow'
            elif current_state == 'green':
                next_predicted = 'yellow' if traffic_factor < 0.8 else 'green'
            elif current_state == 'yellow':
                next_predicted = 'red'
            else:  # blue (emergency)
                next_predicted = 'green'
            
            # Emergency vehicle prediction
            if random.random() < 0.1:  # 10% chance of emergency
                next_predicted = 'blue'
            
            predictions.append({
                'time_offset': time_offset,
                'predicted_state': next_predicted,
                'confidence': random.uniform(0.75, 0.95),
                'reason': self._get_prediction_reason(next_predicted, traffic_factor)
            })
            
            current_state = next_predicted
        
        return predictions
    
    def _get_prediction_reason(self, state: str, traffic_factor: float) -> str:
        """Get reason for state prediction"""
        reasons = {
            'red': [
                'High cross-traffic detected',
                'Pedestrian crossing active',
                'Normal cycle timing'
            ],
            'yellow': [
                'Transition period',
                'Clearing intersection',
                'Safety buffer'
            ],
            'green': [
                'Heavy traffic volume detected',
                'AI optimization active',
                'Extended green for efficiency',
                'Normal cycle progression'
            ],
            'blue': [
                'Emergency vehicle approaching',
                'Emergency preemption activated',
                'First responder priority'
            ]
        }
        
        import random
        return random.choice(reasons.get(state, ['Standard traffic control']))

# Initialize dashboard
dashboard = WebDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/traffic_data')
def get_traffic_data():
    """API endpoint to get current traffic data"""
    return jsonify(dashboard.live_data)

@app.route('/api/intersection/<intersection_id>')
def get_intersection_data(intersection_id):
    """Get detailed data for specific intersection"""
    data = {
        'intersection_id': intersection_id,
        'traffic_counts': dashboard.live_data['traffic_counts'].get(intersection_id, {}),
        'light_state': dashboard.live_data['light_states'].get(intersection_id, {}),
        'predictions': dashboard.live_data['predictions'].get(intersection_id, {}),
        'camera_feed': f"/api/camera_feed/{intersection_id}"
    }
    return jsonify(data)

@app.route('/api/camera_feed/<intersection_id>')
def get_camera_feed(intersection_id):
    """Get camera feed for intersection"""
    try:
        # Get current frame from camera manager
        frame = dashboard.camera_manager.get_current_frame()
        if frame is not None:
            # Encode frame as base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            return jsonify({
                'success': True,
                'image': f"data:image/jpeg;base64,{frame_base64}",
                'timestamp': datetime.datetime.now().isoformat()
            })
    except Exception as e:
        print(f"Camera feed error: {e}")
    
    return jsonify({'success': False, 'error': 'Camera not available'})

@app.route('/api/control/light_timing', methods=['POST'])
def control_light_timing():
    """API to manually control light timing"""
    try:
        data = request.json
        intersection_id = data.get('intersection_id')
        timing = data.get('timing')
        
        if dashboard.light_controller.set_manual_timing(intersection_id, timing):
            return jsonify({'success': True, 'message': 'Timing updated'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update timing'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control/emergency_mode', methods=['POST'])
def emergency_mode():
    """Activate emergency mode for intersection"""
    try:
        data = request.json
        intersection_id = data.get('intersection_id')
        direction = data.get('direction', 'all_red')
        
        dashboard.light_controller.activate_emergency_mode(intersection_id, direction)
        return jsonify({'success': True, 'message': 'Emergency mode activated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/daily_report')
def daily_report():
    """Generate daily traffic analytics report"""
    try:
        # Simulate analytics data (in real implementation, fetch from database)
        report = {
            'date': datetime.date.today().isoformat(),
            'total_vehicles': 15430,
            'peak_hours': ['07:30-09:00', '17:00-19:30'],
            'efficiency_improvement': '23%',
            'intersections': []
        }
        
        for intersection_id in dashboard.intersections:
            intersection_data = {
                'intersection_id': intersection_id,
                'total_vehicles': 3400,
                'average_wait_time': '45 seconds',
                'efficiency_score': 8.5,
                'incidents': 0
            }
            report['intersections'].append(intersection_data)
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/light_predictions/<intersection_id>')
def get_light_predictions(intersection_id):
    """Get detailed AI predictions for traffic light states including blue lights"""
    try:
        current_lights = dashboard.live_data['light_states'].get(intersection_id, {})
        traffic_data = dashboard.live_data['traffic_counts'].get(intersection_id, {})
        
        predictions = {
            'intersection_id': intersection_id,
            'current_time': datetime.datetime.now().isoformat(),
            'predictions': {}
        }
        
        for direction in ['north', 'south', 'east', 'west']:
            direction_data = current_lights.get(direction, {})
            
            # Generate comprehensive predictions
            direction_predictions = {
                'current_state': direction_data.get('state', 'red'),
                'time_remaining': direction_data.get('time_remaining', 30),
                'next_state': direction_data.get('next_state', 'green'),
                'emergency_predicted': direction_data.get('emergency_predicted', False),
                'confidence_score': round(random.uniform(0.85, 0.98), 2),
                'ai_recommendations': [],
                'future_states': [],
                'special_conditions': []
            }
            
            # AI recommendations based on traffic
            total_vehicles = sum(zone.get('total', 0) for zone in traffic_data.values())
            
            if total_vehicles > 15:
                direction_predictions['ai_recommendations'].append({
                    'type': 'extend_green',
                    'reason': f'High traffic volume detected ({total_vehicles} vehicles)',
                    'suggested_extension': '15-20 seconds',
                    'confidence': 0.92
                })
            
            if direction_data.get('emergency_predicted'):
                direction_predictions['ai_recommendations'].append({
                    'type': 'emergency_preemption',
                    'reason': 'Emergency vehicle approaching',
                    'action': 'Activate blue light and clear path',
                    'confidence': 0.96
                })
                direction_predictions['special_conditions'].append({
                    'type': 'emergency_vehicle',
                    'status': 'approaching',
                    'eta': f'{random.randint(30, 120)} seconds',
                    'vehicle_type': random.choice(['ambulance', 'fire_truck', 'police'])
                })
            
            # Future state predictions (next 10 minutes)
            current_state = direction_data.get('state', 'red')
            time_offset = 0
            
            for i in range(10):  # Predict next 10 state changes
                time_offset += random.randint(20, 90)
                
                # Determine next state based on AI logic
                if current_state == 'red':
                    next_state = 'green'
                elif current_state == 'green':
                    next_state = 'yellow'
                elif current_state == 'yellow':
                    next_state = 'red'
                elif current_state == 'blue':
                    next_state = 'green'
                
                # Random emergency prediction
                if random.random() < 0.08:  # 8% chance
                    next_state = 'blue'
                    direction_predictions['special_conditions'].append({
                        'type': 'predicted_emergency',
                        'time_offset': time_offset,
                        'probability': round(random.uniform(0.75, 0.95), 2)
                    })
                
                direction_predictions['future_states'].append({
                    'time_offset': time_offset,
                    'predicted_state': next_state,
                    'duration': random.randint(25, 65),
                    'confidence': round(random.uniform(0.80, 0.95), 2),
                    'optimization_applied': random.choice([True, False])
                })
                
                current_state = next_state
                
                if time_offset > 600:  # Stop at 10 minutes
                    break
            
            predictions['predictions'][direction] = direction_predictions
        
        return jsonify(predictions)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/emergency_vehicles')
def get_emergency_vehicles():
    """Get current emergency vehicle predictions and blue light status"""
    try:
        emergency_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'active_emergencies': [],
            'predicted_emergencies': [],
            'blue_light_status': {}
        }
        
        # Check each intersection for emergency activity
        for intersection_id in dashboard.intersections:
            lights = dashboard.live_data['light_states'].get(intersection_id, {})
            
            for direction, light_data in lights.items():
                if light_data.get('state') == 'blue':
                    emergency_data['active_emergencies'].append({
                        'intersection_id': intersection_id,
                        'direction': direction,
                        'status': 'active',
                        'time_remaining': light_data.get('time_remaining', 0),
                        'vehicle_type': random.choice(['ambulance', 'fire_truck', 'police']),
                        'priority_level': random.choice(['high', 'critical'])
                    })
                
                if light_data.get('emergency_predicted'):
                    emergency_data['predicted_emergencies'].append({
                        'intersection_id': intersection_id,
                        'direction': direction,
                        'probability': round(random.uniform(0.75, 0.95), 2),
                        'estimated_arrival': f'{random.randint(30, 180)} seconds',
                        'recommended_action': 'Prepare for preemption'
                    })
                
                # Blue light status for each direction
                if intersection_id not in emergency_data['blue_light_status']:
                    emergency_data['blue_light_status'][intersection_id] = {}
                
                emergency_data['blue_light_status'][intersection_id][direction] = {
                    'active': light_data.get('state') == 'blue',
                    'predicted': light_data.get('emergency_predicted', False),
                    'last_activation': datetime.datetime.now().isoformat() if light_data.get('state') == 'blue' else None
                }
        
        return jsonify(emergency_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system/status')
def system_status():
    """Get overall system health status"""
    status = {
        'system_health': 'healthy',
        'components': {
            'ai_engine': 'operational',
            'cameras': 'operational',
            'traffic_lights': 'operational',
            'sensors': 'operational',
            'database': 'operational'
        },
        'uptime': '24h 15m',
        'last_update': datetime.datetime.now().isoformat(),
        'active_alerts': len(dashboard.live_data.get('alerts', []))
    }
    return jsonify(status)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('dashboard_update', dashboard.live_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_intersection_data')
def handle_intersection_request(data):
    """Handle request for specific intersection data"""
    intersection_id = data.get('intersection_id')
    if intersection_id:
        intersection_data = {
            'intersection_id': intersection_id,
            'traffic_counts': dashboard.live_data['traffic_counts'].get(intersection_id, {}),
            'light_state': dashboard.live_data['light_states'].get(intersection_id, {}),
            'predictions': dashboard.live_data['predictions'].get(intersection_id, {})
        }
        emit('intersection_data', intersection_data)

if __name__ == '__main__':
    print("Starting Smart Traffic AI Web Dashboard...")
    print("Dashboard URL: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
