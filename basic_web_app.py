"""
Basic Web Interface for Smart Traffic AI System
Simple Flask app without SocketIO dependencies
"""

import time
import json
import random
from datetime import datetime
from flask import Flask, jsonify
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the traffic simulator and optimizer
from data_simulation.traffic_simulator import TrafficSimulator, WeatherSimulator
from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

# Initialize Flask app
app = Flask(__name__)

# Global simulation objects
traffic_sim = TrafficSimulator("MAIN_INTERSECTION")
weather_sim = WeatherSimulator()
traffic_optimizer = TrafficLightOptimizer()

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
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
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
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #22c55e;
            transform: translateY(-2px);
        }
        .btn.secondary {
            background: #6366f1;
        }
        .btn.secondary:hover {
            background: #4f46e5;
        }
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: bold;
            background: rgba(74, 222, 128, 0.2);
            border: 1px solid #4ade80;
        }
        .api-links {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .api-links a {
            color: #4ade80;
            text-decoration: none;
            display: block;
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.3s ease;
        }
        .api-links a:hover {
            background: rgba(255,255,255,0.1);
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .pulsing {
            animation: pulse 2s infinite;
        }
        .auto-refresh {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 10px;
        }
    </style>
    <script>
        // Auto-refresh the page every 3 seconds to show live data
        setTimeout(function() {
            location.reload();
        }, 3000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚦 Smart Traffic AI System</h1>
            <p>Real-time Traffic Management Dashboard</p>
            <div class="auto-refresh">⟳ Auto-refreshing every 3 seconds</div>
        </div>

        <div class="controls">
            <a href="/api/traffic" class="btn">📊 View Traffic Data</a>
            <a href="/api/weather" class="btn secondary">🌡️ View Weather Data</a>
            <a href="/api/traffic-lights" class="btn">🚦 View Light Predictions</a>
        </div>

        <div class="status pulsing">▶️ Simulation Running Live</div>

        <div class="dashboard" id="dashboard">
            <!-- Dashboard content will be loaded here -->
        </div>
    </div>

    <script>
        // Load live dashboard data
        fetch('/api/dashboard')
            .then(response => response.json())
            .then(data => {
                document.getElementById('dashboard').innerHTML = data.html;
            })
            .catch(error => {
                console.error('Error loading dashboard:', error);
                document.getElementById('dashboard').innerHTML = '<div class="card"><h3>⚠️ Loading Error</h3><p>Please refresh the page</p></div>';
            });
    </script>
</body>
</html>
    '''

@app.route('/api/dashboard')
def api_dashboard():
    """Generate dashboard HTML with live data"""
    try:
        # Run simulation update
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
        
        emergency_count = stats.get('by_type', {}).get('emergency', 0)
        weather_condition = 'rain' if weather.get('rain_detected', False) else 'normal'
        
        traffic_phase = traffic_optimizer.predict_optimal_timing(
            vehicle_counts_dict, 
            emergency_count, 
            weather_condition
        )
        
        # Generate dashboard HTML
        dashboard_html = f'''
            <div class="card">
                <h3 data-icon="🚗">Traffic Statistics</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value">{stats['total_vehicles']}</span>
                        <span class="stat-label">Total Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{stats['average_speed']:.1f}</span>
                        <span class="stat-label">Avg Speed (km/h)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{emergency_count}</span>
                        <span class="stat-label">Emergency Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{stats['density_level'].title()}</span>
                        <span class="stat-label">Traffic Density</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🌡️">Weather Conditions</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value">{weather['temperature']}</span>
                        <span class="stat-label">Temperature (°C)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{weather['humidity']}</span>
                        <span class="stat-label">Humidity (%)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{weather['light_level']:.0f}</span>
                        <span class="stat-label">Light Level (Lux)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{'Yes' if weather['rain_detected'] else 'No'}</span>
                        <span class="stat-label">Rain Detected</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🧭">Vehicle Counts by Zone</h3>
                <div class="zone-grid">
                    <div class="zone-item">
                        <div class="zone-name">🔼 North</div>
                        <div class="zone-count">{zone_counts.get('North', {}).get('total', 0)}</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">▶️ East</div>
                        <div class="zone-count">{zone_counts.get('East', {}).get('total', 0)}</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">🔽 South</div>
                        <div class="zone-count">{zone_counts.get('South', {}).get('total', 0)}</div>
                    </div>
                    <div class="zone-item">
                        <div class="zone-name">◀️ West</div>
                        <div class="zone-count">{zone_counts.get('West', {}).get('total', 0)}</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🚦">Traffic Light Optimization</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value">{traffic_phase.north_south_timing.green_duration}</span>
                        <span class="stat-label">North-South Green (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{traffic_phase.east_west_timing.green_duration}</span>
                        <span class="stat-label">East-West Green (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{traffic_phase.total_cycle_time}</span>
                        <span class="stat-label">Total Cycle (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" style="color: #4ade80;">{traffic_phase.efficiency_score:.3f}</span>
                        <span class="stat-label">Efficiency Score</span>
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; font-size: 0.9em;">
                        {traffic_phase.north_south_timing.reasoning}
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🔗">API Endpoints</h3>
                <div class="api-links">
                    <a href="/api/status" target="_blank">📊 System Status</a>
                    <a href="/api/traffic" target="_blank">🚗 Traffic Data</a>
                    <a href="/api/weather" target="_blank">🌡️ Weather Data</a>
                    <a href="/api/traffic-lights" target="_blank">🚦 Traffic Light Predictions</a>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; opacity: 0.7;">
                    Last updated: {datetime.now().strftime('%H:%M:%S')}
                </div>
            </div>
        '''
        
        return jsonify({'html': dashboard_html})
        
    except Exception as e:
        error_html = f'''
            <div class="card">
                <h3 data-icon="⚠️">System Error</h3>
                <p>Error loading dashboard data: {str(e)}</p>
                <p><a href="/" class="btn">🔄 Refresh Page</a></p>
            </div>
        '''
        return jsonify({'html': error_html})

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'system': 'Smart Traffic AI System',
        'version': '1.0.0',
        'simulation': 'active'
    })

@app.route('/api/traffic')
def api_traffic():
    """API endpoint for current traffic data"""
    try:
        traffic_sim.update_simulation(1.0)
        stats = traffic_sim.get_traffic_statistics()
        zone_counts = traffic_sim.get_vehicle_counts_by_zone()
        return jsonify({
            'traffic_stats': stats,
            'zone_counts': zone_counts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def api_weather():
    """API endpoint for weather data"""
    try:
        weather = weather_sim.update_weather()
        return jsonify(weather)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/traffic-lights')
def api_traffic_lights():
    """API endpoint for traffic light predictions"""
    try:
        # Update simulation
        traffic_sim.update_simulation(1.0)
        
        # Get current data
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
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenarios')
def api_scenarios():
    """API endpoint to get available traffic scenarios"""
    try:
        scenarios = traffic_sim.get_available_scenarios()
        current_scenario = traffic_sim.current_scenario
        pattern = traffic_sim.get_current_traffic_pattern()
        
        return jsonify({
            'available_scenarios': scenarios,
            'current_scenario': current_scenario,
            'current_pattern': pattern,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenarios/<scenario>', methods=['POST'])
def api_set_scenario(scenario):
    """API endpoint to set traffic scenario"""
    try:
        traffic_sim.set_traffic_scenario(scenario)
        return jsonify({
            'success': True,
            'message': f'Scenario changed to {scenario}',
            'current_scenario': traffic_sim.current_scenario,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚦 Smart Traffic AI System - Basic Web Dashboard")
    print("=" * 55)
    print("🌐 Starting web server...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop")
    print()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        print("👋 Smart Traffic AI System stopped")
