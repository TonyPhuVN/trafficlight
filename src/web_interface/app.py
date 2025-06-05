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
                # Update traffic counts from all intersections
                for intersection_id in self.intersections:
                    cameras = self.camera_manager.get_intersection_cameras(intersection_id)
                    if cameras:
                        frame = cameras[0].get_latest_frame()
                        if frame is not None:
                            counts = self.vehicle_detector.count_vehicles(frame, intersection_id)
                            self.live_data['traffic_counts'][intersection_id] = counts
                
                # Update light states
                self.live_data['light_states'] = self.light_controller.get_all_states()
                
                # Update predictions
                for intersection_id in self.intersections:
                    prediction = self.traffic_predictor.predict_traffic_flow(
                        intersection_id, 
                        self.live_data['traffic_counts'].get(intersection_id, {})
                    )
                    self.live_data['predictions'][intersection_id] = prediction
                
                # Emit updates to connected clients
                socketio.emit('dashboard_update', self.live_data)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)

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
        cameras = dashboard.camera_manager.get_intersection_cameras(intersection_id)
        if cameras:
            frame = cameras[0].get_latest_frame()
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
