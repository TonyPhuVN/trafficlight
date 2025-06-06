"""
Simple Web Interface for Smart Traffic AI System
Runs the traffic simulation with real-time web dashboard on localhost
"""

import time
import threading
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the traffic simulator and optimizer
from data_simulation.traffic_simulator import TrafficSimulator, WeatherSimulator
from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_traffic_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global simulation objects
traffic_sim = TrafficSimulator("MAIN_INTERSECTION")
weather_sim = WeatherSimulator()
traffic_optimizer = TrafficLightOptimizer()
simulation_running = False

@app.route('/')
def index():
    """Main dashboard page"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🚦 Smart Traffic AI System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header .clock {
            font-size: 1.2em;
            margin: 10px 0;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .header .date {
            font-size: 1em;
            opacity: 0.9;
            margin: 5px 0;
        }
        .header .location {
            font-size: 0.9em;
            opacity: 0.8;
            margin: 5px 0;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 {
            margin: 0 0 15px 0;
            font-size: 1.3em;
            display: flex;
            align-items: center;
        }
        .card h3::before {
            content: attr(data-icon);
            margin-right: 10px;
            font-size: 1.2em;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .stat-item {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            display: block;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .zone-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .zone-item {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .zone-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .zone-count {
            font-size: 1.5em;
            color: #4ade80;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        .btn {
            background: #4ade80;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #22c55e;
            transform: translateY(-2px);
        }
        .btn.danger {
            background: #ef4444;
        }
        .btn.danger:hover {
            background: #dc2626;
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: bold;
        }
        .status.running {
            background: rgba(74, 222, 128, 0.2);
            border: 1px solid #4ade80;
        }
        .status.stopped {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
        }
        .log {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulsing {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚦 Smart Traffic AI System</h1>
            <p>Real-time Traffic Management Dashboard</p>
            <div class="clock">
                <div id="current-time">00:00:00</div>
                <div class="date" id="current-date">Loading...</div>
                <div class="location">📍 Hanoi, Vietnam</div>
            </div>
        </div>

        <div class="controls">
            <button class="btn" onclick="startSimulation()">🚀 Start Simulation</button>
            <button class="btn danger" onclick="stopSimulation()">🛑 Stop Simulation</button>
        </div>

        <div id="status" class="status stopped">⏹️ Simulation Stopped</div>

        <div class="dashboard">
            <div class="card">
                <h3 data-icon="🚗">Traffic Statistics</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="total-vehicles">0</span>
                        <span class="stat-label">Total Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="avg-speed">0</span>
                        <span class="stat-label">Avg Speed (km/h)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="emergency-vehicles">0</span>
                        <span class="stat-label">Emergency Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="density-level">Low</span>
                        <span class="stat-label">Traffic Density</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🌡️">Weather Conditions</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="temperature">32</span>
                        <span class="stat-label">Temperature (°C)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="heat-index">38</span>
                        <span class="stat-label">Feels Like (°C)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="humidity">78</span>
                        <span class="stat-label">Humidity (%)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="weather-condition">Hot & Humid</span>
                        <span class="stat-label">Condition</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="rain-status">No</span>
                        <span class="stat-label">Rain</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="air-quality">Moderate</span>
                        <span class="stat-label">Air Quality</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🧭">Vehicle Counts by Zone</h3>
                <div class="zone-grid">
                    <div class="zone-item">
                        <div class="zone-name">🔼 North</div>
                        <div class="zone-count" id="north-count">0</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">▶️ East</div>
                        <div class="zone-count" id="east-count">0</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">🔽 South</div>
                        <div class="zone-count" id="south-count">0</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">◀️ West</div>
                        <div class="zone-count" id="west-count">0</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🚦">Traffic Light Predictions</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="ns-green-time">30</span>
                        <span class="stat-label">North-South Green (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="ew-green-time">30</span>
                        <span class="stat-label">East-West Green (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="cycle-time">66</span>
                        <span class="stat-label">Total Cycle (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="efficiency-score">0.8</span>
                        <span class="stat-label">Efficiency Score</span>
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; font-size: 0.9em;">
                        <div id="light-reasoning">Proportional timing based on traffic demand</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="📊">System Activity Log</h3>
                <div id="activity-log" class="log">
                    <div>System initialized - Ready to start simulation</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let isRunning = false;

        // Socket event handlers
        socket.on('traffic_update', function(data) {
            updateTrafficStats(data.stats);
            updateZoneCounts(data.zone_counts);
        });

        socket.on('weather_update', function(data) {
            updateWeatherData(data);
        });

        socket.on('simulation_status', function(data) {
            updateStatus(data.running);
        });

        socket.on('activity_log', function(data) {
            addLogEntry(data.message);
        });

        socket.on('traffic_light_update', function(data) {
            updateTrafficLightPredictions(data);
        });

        function startSimulation() {
            socket.emit('start_simulation');
            addLogEntry('🚀 Starting simulation...');
        }

        function stopSimulation() {
            socket.emit('stop_simulation');
            addLogEntry('🛑 Stopping simulation...');
        }

        function updateStatus(running) {
            isRunning = running;
            const statusEl = document.getElementById('status');
            if (running) {
                statusEl.className = 'status running pulsing';
                statusEl.textContent = '▶️ Simulation Running';
            } else {
                statusEl.className = 'status stopped';
                statusEl.textContent = '⏹️ Simulation Stopped';
            }
        }

        function updateTrafficStats(stats) {
            document.getElementById('total-vehicles').textContent = stats.total_vehicles;
            document.getElementById('avg-speed').textContent = Math.round(stats.average_speed);
            document.getElementById('emergency-vehicles').textContent = stats.emergency_vehicles;
            document.getElementById('density-level').textContent = stats.density_level.charAt(0).toUpperCase() + stats.density_level.slice(1);
        }

        function updateZoneCounts(counts) {
            document.getElementById('north-count').textContent = counts.North ? counts.North.total : 0;
            document.getElementById('east-count').textContent = counts.East ? counts.East.total : 0;
            document.getElementById('south-count').textContent = counts.South ? counts.South.total : 0;
            document.getElementById('west-count').textContent = counts.West ? counts.West.total : 0;
        }

        function updateWeatherData(weather) {
            document.getElementById('temperature').textContent = weather.temperature;
            document.getElementById('heat-index').textContent = weather.heat_index || weather.temperature + 5;
            document.getElementById('humidity').textContent = weather.humidity;
            document.getElementById('rain-status').textContent = weather.rain_detected ? 
                (weather.rain_intensity && weather.rain_intensity !== 'none' ? weather.rain_intensity.charAt(0).toUpperCase() + weather.rain_intensity.slice(1) : 'Yes') : 'No';
            document.getElementById('air-quality').textContent = weather.air_quality ? 
                weather.air_quality.charAt(0).toUpperCase() + weather.air_quality.slice(1) : 'Good';
            
            // Update weather condition with appropriate display text
            let conditionText = 'Sunny';
            if (weather.weather_condition) {
                switch(weather.weather_condition) {
                    case 'hot_humid':
                        conditionText = 'Hot & Humid';
                        break;
                    case 'thunderstorm':
                        conditionText = 'Thunderstorm';
                        break;
                    case 'rain':
                        conditionText = 'Rainy';
                        break;
                    case 'sunny':
                        conditionText = 'Sunny';
                        break;
                    default:
                        conditionText = weather.weather_condition.charAt(0).toUpperCase() + weather.weather_condition.slice(1);
                }
            }
            document.getElementById('weather-condition').textContent = conditionText;
        }

        function addLogEntry(message) {
            const log = document.getElementById('activity-log');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.textContent = `[${timestamp}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }

        function updateTrafficLightPredictions(data) {
            document.getElementById('ns-green-time').textContent = data.north_south_green;
            document.getElementById('ew-green-time').textContent = data.east_west_green;
            document.getElementById('cycle-time').textContent = data.cycle_time;
            document.getElementById('efficiency-score').textContent = data.efficiency_score.toFixed(2);
            document.getElementById('light-reasoning').textContent = data.reasoning;
        }

        function updateClock() {
            const now = new Date();
            
            // Format time with Vietnam timezone
            const timeOptions = {
                timeZone: 'Asia/Ho_Chi_Minh',
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            
            const dateOptions = {
                timeZone: 'Asia/Ho_Chi_Minh',
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            };
            
            const timeString = now.toLocaleTimeString('en-GB', timeOptions);
            const dateString = now.toLocaleDateString('en-US', dateOptions);
            
            document.getElementById('current-time').textContent = timeString;
            document.getElementById('current-date').textContent = dateString;
        }

        // Update clock every second
        updateClock();
        setInterval(updateClock, 1000);

        // Initialize
        addLogEntry('🌐 Connected to server');
        socket.emit('get_status');
    </script>
</body>
</html>
    '''

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {datetime.now()}")
    emit('activity_log', {'message': 'Client connected to dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {datetime.now()}")

@socketio.on('start_simulation')
def handle_start_simulation():
    """Start the traffic simulation"""
    global simulation_running
    if not simulation_running:
        simulation_running = True
        emit('simulation_status', {'running': True}, broadcast=True)
        emit('activity_log', {'message': '✅ Simulation started successfully'}, broadcast=True)
        # Start simulation thread
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()

@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop the traffic simulation"""
    global simulation_running
    simulation_running = False
    emit('simulation_status', {'running': False}, broadcast=True)
    emit('activity_log', {'message': '🛑 Simulation stopped'}, broadcast=True)

@socketio.on('get_status')
def handle_get_status():
    """Get current simulation status"""
    emit('simulation_status', {'running': simulation_running})

def simulation_loop():
    """Main simulation loop"""
    global simulation_running
    
    while simulation_running:
        try:
            # Update traffic simulation
            traffic_sim.update_simulation(1.0)
            
            # Get current data
            stats = traffic_sim.get_traffic_statistics()
            zone_counts = traffic_sim.get_vehicle_counts_by_zone()
            weather = weather_sim.update_weather()
            
            # Calculate optimal traffic light timing
            vehicle_counts_dict = {
                'North': zone_counts.get('North', {}).get('total', 0),
                'South': zone_counts.get('South', {}).get('total', 0),
                'East': zone_counts.get('East', {}).get('total', 0),
                'West': zone_counts.get('West', {}).get('total', 0)
            }
            
            # Check for emergency vehicles
            emergency_count = stats.get('by_type', {}).get('emergency', 0)
            
            # Get weather condition for optimization
            weather_condition = 'rain' if weather.get('rain_detected', False) else 'normal'
            
            # Predict optimal timing
            traffic_phase = traffic_optimizer.predict_optimal_timing(
                vehicle_counts_dict, 
                emergency_count, 
                weather_condition
            )
            
            # Emit updates to all connected clients
            socketio.emit('traffic_update', {
                'stats': stats,
                'zone_counts': zone_counts
            })
            
            socketio.emit('weather_update', weather)
            
            # Emit traffic light predictions
            socketio.emit('traffic_light_update', {
                'north_south_green': traffic_phase.north_south_timing.green_duration,
                'east_west_green': traffic_phase.east_west_timing.green_duration,
                'cycle_time': traffic_phase.total_cycle_time,
                'efficiency_score': traffic_phase.efficiency_score,
                'reasoning': traffic_phase.north_south_timing.reasoning
            })
            
            # Log periodic updates
            if int(time.time()) % 10 == 0:  # Every 10 seconds
                socketio.emit('activity_log', {
                    'message': f'📊 Traffic update: {stats["total_vehicles"]} vehicles, {stats["density_level"]} density'
                })
            
            time.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            print(f"Simulation error: {e}")
            socketio.emit('activity_log', {
                'message': f'⚠️ Simulation error: {str(e)}'
            })
            time.sleep(5)

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify({
        'status': 'running' if simulation_running else 'stopped',
        'timestamp': datetime.now().isoformat(),
        'system': 'Smart Traffic AI System',
        'version': '1.0.0'
    })

@app.route('/api/traffic')
def api_traffic():
    """API endpoint for current traffic data"""
    if simulation_running:
        stats = traffic_sim.get_traffic_statistics()
        zone_counts = traffic_sim.get_vehicle_counts_by_zone()
        return jsonify({
            'traffic_stats': stats,
            'zone_counts': zone_counts,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Simulation not running'}), 400

@app.route('/api/weather')
def api_weather():
    """API endpoint for weather data"""
    weather = weather_sim.update_weather()
    return jsonify(weather)

@app.route('/api/traffic-lights')
def api_traffic_lights():
    """API endpoint for traffic light predictions"""
    if simulation_running:
        # Get current traffic data
        stats = traffic_sim.get_traffic_statistics()
        zone_counts = traffic_sim.get_vehicle_counts_by_zone()
        weather = weather_sim.update_weather()
        
        # Prepare vehicle counts
        vehicle_counts_dict = {
            'North': zone_counts.get('North', {}).get('total', 0),
            'South': zone_counts.get('South', {}).get('total', 0),
            'East': zone_counts.get('East', {}).get('total', 0),
            'West': zone_counts.get('West', {}).get('total', 0)
        }
        
        # Get emergency count and weather condition
        emergency_count = stats.get('by_type', {}).get('emergency', 0)
        weather_condition = 'rain' if weather.get('rain_detected', False) else 'normal'
        
        # Predict optimal timing
        traffic_phase = traffic_optimizer.predict_optimal_timing(
            vehicle_counts_dict, 
            emergency_count, 
            weather_condition
        )
        
        return jsonify({
            'traffic_light_predictions': {
                'north_south': {
                    'green_duration': traffic_phase.north_south_timing.green_duration,
                    'red_duration': traffic_phase.north_south_timing.red_duration,
                    'yellow_duration': traffic_phase.north_south_timing.yellow_duration,
                    'confidence': traffic_phase.north_south_timing.confidence,
                    'priority': traffic_phase.north_south_timing.priority
                },
                'east_west': {
                    'green_duration': traffic_phase.east_west_timing.green_duration,
                    'red_duration': traffic_phase.east_west_timing.red_duration,
                    'yellow_duration': traffic_phase.east_west_timing.yellow_duration,
                    'confidence': traffic_phase.east_west_timing.confidence,
                    'priority': traffic_phase.east_west_timing.priority
                },
                'cycle_info': {
                    'total_cycle_time': traffic_phase.total_cycle_time,
                    'efficiency_score': traffic_phase.efficiency_score,
                    'phase_name': traffic_phase.phase_name,
                    'reasoning': traffic_phase.north_south_timing.reasoning
                },
                'input_data': {
                    'vehicle_counts': vehicle_counts_dict,
                    'emergency_vehicles': emergency_count,
                    'weather_condition': weather_condition
                }
            },
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Simulation not running'}), 400

if __name__ == '__main__':
    print("🚦 Smart Traffic AI System - Web Dashboard")
    print("=" * 50)
    print("🌐 Starting web server...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop")
    print()
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        simulation_running = False
        print("👋 Smart Traffic AI System stopped")
