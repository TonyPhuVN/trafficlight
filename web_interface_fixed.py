"""
Fixed Smart Traffic AI System Web Interface
Real-time dashboard with traffic light visualization - No PyTorch dependencies
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import datetime
import threading
import time
import random
from typing import Dict, List, Any
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import our simulation modules (without PyTorch dependencies)
from data_simulation.traffic_simulator import TrafficSimulator, WeatherSimulator
from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic_ai_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebDashboard:
    def __init__(self):
        # Initialize simulation components
        self.traffic_simulator = TrafficSimulator("MAIN_INTERSECTION")
        self.weather_simulator = WeatherSimulator()
        self.traffic_optimizer = TrafficLightOptimizer()
        
        # Default intersections
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
                # Update traffic simulation
                self.traffic_simulator.update_simulation(1.0)
                
                # Get current data
                stats = self.traffic_simulator.get_traffic_statistics()
                zone_counts = self.traffic_simulator.get_vehicle_counts_by_zone()
                weather = self.weather_simulator.update_weather()
                
                # Update traffic counts for all intersections
                for intersection_id in self.intersections:
                    # Convert zone counts to proper format
                    intersection_counts = {}
                    for zone_name, count_data in zone_counts.items():
                        if hasattr(count_data, 'cars'):
                            intersection_counts[zone_name.lower()] = {
                                'cars': count_data.cars,
                                'trucks': count_data.trucks,
                                'buses': count_data.buses,
                                'motorcycles': count_data.motorcycles,
                                'bicycles': count_data.bicycles,
                                'emergency_vehicles': count_data.emergency_vehicles,
                                'total': count_data.total,
                                'timestamp': count_data.timestamp
                            }
                        else:
                            intersection_counts[zone_name.lower()] = {
                                'cars': count_data.get('cars', 0),
                                'trucks': count_data.get('trucks', 0),
                                'buses': count_data.get('buses', 0),
                                'motorcycles': count_data.get('motorcycles', 0),
                                'bicycles': count_data.get('bicycles', 0),
                                'emergency_vehicles': count_data.get('emergency_vehicles', 0),
                                'total': count_data.get('total', 0),
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                    
                    self.live_data['traffic_counts'][intersection_id] = intersection_counts
                
                # Update light states with realistic simulation
                self.live_data['light_states'] = self._get_realistic_light_states(zone_counts, stats)
                
                # Update predictions
                for intersection_id in self.intersections:
                    current_data = {
                        'vehicle_counts': self.live_data['traffic_counts'].get(intersection_id, {}),
                        'weather': weather
                    }
                    
                    # Calculate predictions based on current traffic
                    total_vehicles = sum(zone.get('total', 0) for zone in current_data['vehicle_counts'].values())
                    
                    self.live_data['predictions'][intersection_id] = {
                        'short_term': total_vehicles * 1.2,  # 20% increase predicted
                        'medium_term': total_vehicles * 1.5,  # 50% increase predicted
                        'confidence': random.uniform(0.8, 0.95)
                    }
                
                # Emit updates to connected clients
                socketio.emit('dashboard_update', self.live_data)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _get_realistic_light_states(self, zone_counts, traffic_stats):
        """Generate realistic traffic light states based on traffic conditions"""
        light_states = {}
        current_time = int(time.time())
        
        # Get vehicle counts for optimization
        vehicle_counts_dict = {
            'North': zone_counts.get('North', {}).get('total', 0) if hasattr(zone_counts.get('North', {}), 'total') else zone_counts.get('North', {}).get('total', 0),
            'South': zone_counts.get('South', {}).get('total', 0) if hasattr(zone_counts.get('South', {}), 'total') else zone_counts.get('South', {}).get('total', 0),
            'East': zone_counts.get('East', {}).get('total', 0) if hasattr(zone_counts.get('East', {}), 'total') else zone_counts.get('East', {}).get('total', 0),
            'West': zone_counts.get('West', {}).get('total', 0) if hasattr(zone_counts.get('West', {}), 'total') else zone_counts.get('West', {}).get('total', 0)
        }
        
        # Check for emergency vehicles
        emergency_count = traffic_stats.get('by_type', {}).get('emergency', 0)
        
        # Get optimal timing from AI optimizer
        try:
            traffic_phase = self.traffic_optimizer.predict_optimal_timing(
                vehicle_counts_dict, 
                emergency_count, 
                'normal'
            )
            
            # Use AI-optimized timing
            ns_green = traffic_phase.north_south_timing.green_duration
            ew_green = traffic_phase.east_west_timing.green_duration
            cycle_time = traffic_phase.total_cycle_time
            
        except Exception as e:
            print(f"Traffic optimization error: {e}")
            # Fallback to default timing
            ns_green = 35
            ew_green = 30
            cycle_time = 75
        
        for intersection_id in self.intersections:
            light_states[intersection_id] = {}
            
            # Calculate current position in cycle
            cycle_position = current_time % cycle_time
            
            # Determine current phase
            if cycle_position < ns_green:
                # North-South Green, East-West Red
                ns_state = 'green'
                ew_state = 'red'
                ns_remaining = ns_green - cycle_position
                ew_remaining = cycle_position + (cycle_time - ns_green)
            elif cycle_position < ns_green + 3:
                # North-South Yellow, East-West Red
                ns_state = 'yellow'
                ew_state = 'red'
                ns_remaining = (ns_green + 3) - cycle_position
                ew_remaining = cycle_position + (cycle_time - ns_green - 3)
            elif cycle_position < ns_green + 3 + ew_green:
                # North-South Red, East-West Green
                ns_state = 'red'
                ew_state = 'green'
                ns_remaining = cycle_time - cycle_position
                ew_remaining = (ns_green + 3 + ew_green) - cycle_position
            elif cycle_position < ns_green + 3 + ew_green + 3:
                # North-South Red, East-West Yellow
                ns_state = 'red'
                ew_state = 'yellow'
                ns_remaining = cycle_time - cycle_position
                ew_remaining = (ns_green + 3 + ew_green + 3) - cycle_position
            else:
                # All Red (safety period)
                ns_state = 'red'
                ew_state = 'red'
                ns_remaining = cycle_time - cycle_position
                ew_remaining = cycle_time - cycle_position
            
            # Emergency vehicle override
            emergency_predicted = emergency_count > 0 or random.random() < 0.1
            
            # Apply emergency override with blue light
            if emergency_predicted and random.random() < 0.3:
                # Emergency vehicle approaching - show blue light for priority direction
                priority_directions = ['north', 'south'] if vehicle_counts_dict.get('North', 0) + vehicle_counts_dict.get('South', 0) > vehicle_counts_dict.get('East', 0) + vehicle_counts_dict.get('West', 0) else ['east', 'west']
                
                for direction in ['north', 'south', 'east', 'west']:
                    if direction in priority_directions:
                        state = 'blue'  # Emergency preemption
                        next_state = 'green'
                        remaining = random.randint(5, 15)
                    else:
                        state = 'red'
                        next_state = 'red'
                        remaining = random.randint(20, 40)
                    
                    light_states[intersection_id][direction] = {
                        'state': state,
                        'time_remaining': remaining,
                        'next_state': next_state,
                        'emergency_predicted': True,
                        'confidence': random.uniform(0.85, 0.98),
                        'predicted_states': self._generate_state_predictions(state, direction)
                    }
            else:
                # Normal operation
                for direction in ['north', 'south']:
                    light_states[intersection_id][direction] = {
                        'state': ns_state,
                        'time_remaining': max(1, int(ns_remaining)),
                        'next_state': 'yellow' if ns_state == 'green' else 'green' if ns_state == 'red' else 'red',
                        'emergency_predicted': emergency_predicted,
                        'confidence': random.uniform(0.85, 0.95),
                        'predicted_states': self._generate_state_predictions(ns_state, direction)
                    }
                
                for direction in ['east', 'west']:
                    light_states[intersection_id][direction] = {
                        'state': ew_state,
                        'time_remaining': max(1, int(ew_remaining)),
                        'next_state': 'yellow' if ew_state == 'green' else 'green' if ew_state == 'red' else 'red',
                        'emergency_predicted': emergency_predicted,
                        'confidence': random.uniform(0.85, 0.95),
                        'predicted_states': self._generate_state_predictions(ew_state, direction)
                    }
        
        return light_states
    
    def _generate_state_predictions(self, current_state: str, direction: str):
        """Generate AI predictions for future light states"""
        predictions = []
        states = ['red', 'yellow', 'green', 'blue']
        
        # Predict next 5 state changes
        for i in range(1, 6):
            time_offset = i * random.randint(25, 75)  # 25-75 seconds apart
            
            # Simulate realistic state transitions
            if current_state == 'red':
                next_predicted = 'green'
            elif current_state == 'green':
                next_predicted = 'yellow'
            elif current_state == 'yellow':
                next_predicted = 'red'
            elif current_state == 'blue':
                next_predicted = 'green'
            else:
                next_predicted = random.choice(['red', 'green'])
            
            # Small chance of emergency prediction
            if random.random() < 0.08:  # 8% chance
                next_predicted = 'blue'
            
            predictions.append({
                'time_offset': time_offset,
                'predicted_state': next_predicted,
                'confidence': random.uniform(0.75, 0.95),
                'reason': self._get_prediction_reason(next_predicted)
            })
            
            current_state = next_predicted
        
        return predictions
    
    def _get_prediction_reason(self, state: str) -> str:
        """Get reason for state prediction"""
        reasons = {
            'red': ['High cross-traffic detected', 'Pedestrian crossing active', 'Normal cycle timing', 'Traffic optimization'],
            'yellow': ['Transition period', 'Clearing intersection', 'Safety buffer', 'Phase change'],
            'green': ['Heavy traffic volume detected', 'AI optimization active', 'Extended green for efficiency', 'Normal cycle progression'],
            'blue': ['Emergency vehicle approaching', 'Emergency preemption activated', 'First responder priority', 'Emergency override']
        }
        
        return random.choice(reasons.get(state, ['Standard traffic control']))

# Initialize dashboard
dashboard = WebDashboard()

@app.route('/')
def index():
    """Main dashboard page with enhanced traffic light visualization"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚦 Smart Traffic AI Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            overflow-x: auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        .header h1 {
            font-size: 2rem;
            background: linear-gradient(45deg, #ffd700, #ffeb3b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255,255,255,0.1);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27ae60;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }

        .dashboard-container {
            padding: 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }

        .intersection-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }

        .intersection-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        }

        .intersection-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 2px solid rgba(255,215,0,0.3);
            padding-bottom: 1rem;
        }

        .intersection-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #ffd700;
            text-transform: capitalize;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
        }

        .traffic-lights-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .traffic-light-display {
            background: linear-gradient(145deg, #2c3e50, #34495e);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.3);
            border: 2px solid rgba(255,255,255,0.1);
        }

        .direction-label {
            color: #ffd700;
            font-weight: bold;
            margin-bottom: 1rem;
            text-transform: uppercase;
            font-size: 1rem;
            letter-spacing: 1px;
        }

        .traffic-light {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 1rem;
        }

        .light {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 3px solid #2c3e50;
            transition: all 0.3s ease;
            position: relative;
        }

        .light.red {
            background: #e74c3c;
            box-shadow: 0 0 20px rgba(231, 76, 60, 0.8), inset 0 2px 5px rgba(255,255,255,0.2);
        }

        .light.yellow {
            background: #f39c12;
            box-shadow: 0 0 20px rgba(243, 156, 18, 0.8), inset 0 2px 5px rgba(255,255,255,0.2);
        }

        .light.green {
            background: #27ae60;
            box-shadow: 0 0 20px rgba(39, 174, 96, 0.8), inset 0 2px 5px rgba(255,255,255,0.2);
        }

        .light.blue {
            background: #3498db;
            box-shadow: 0 0 25px rgba(52, 152, 219, 1), inset 0 2px 5px rgba(255,255,255,0.3);
            animation: emergency-pulse 1s infinite;
        }

        @keyframes emergency-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }

        .light.inactive {
            background: linear-gradient(145deg, #7f8c8d, #95a5a6);
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.3);
        }

        .time-remaining {
            color: #ffd700;
            font-weight: bold;
            font-size: 1.1rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }

        .next-light-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }

        .next-light {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.3);
        }

        .vehicle-count {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            padding: 1rem;
            border-radius: 15px;
            font-weight: bold;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(52,152,219,0.3);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .emergency-button {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            padding: 0.7rem 1.5rem;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(231,76,60,0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .emergency-button:hover {
            background: linear-gradient(45deg, #c0392b, #a93226);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(231,76,60,0.4);
        }

        .prediction-display {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin-top: 1rem;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .prediction-title {
            font-weight: bold;
            color: #ffd700;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }

        .prediction-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 0.9rem;
        }

        .prediction-item:last-child {
            border-bottom: none;
        }

        .system-metrics {
            grid-column: span 2;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .metrics-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            color: #ffd700;
            font-size: 1.5rem;
            font-weight: bold;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(10px);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            background: linear-gradient(45deg, #4ade80, #22c55e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
            color: #ffd700;
        }

        .chart-container {
            height: 300px;
            margin-top: 1rem;
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            padding: 1rem;
        }

        .emergency-alert {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
            font-weight: bold;
            animation: pulse 2s infinite;
            border: 2px solid rgba(255,255,255,0.3);
        }

        @media (max-width: 1200px) {
            .dashboard-container {
                grid-template-columns: 1fr;
                padding: 1rem;
            }
            
            .system-metrics {
                grid-column: span 1;
            }
        }

        @media (max-width: 768px) {
            .traffic-lights-container {
                grid-template-columns: 1fr;
            }
            
            .header {
                flex-direction: column;
                gap: 1rem;
            }

            .header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚦 Smart Traffic AI Dashboard</h1>
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span id="system-status">System Online</span>
        </div>
    </div>

    <div class="dashboard-container">
        <!-- Intersection cards will be dynamically generated here -->
        <div id="intersections-container">
            <!-- Dynamic content -->
        </div>

        <div class="system-metrics">
            <div class="metrics-header">
                <span>📊</span>
                <span>System Performance Metrics</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" id="total-vehicles">0</div>
                    <div class="metric-label">Total Vehicles</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="avg-wait-time">0s</div>
                    <div class="metric-label">Avg Wait Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="efficiency-score">0%</div>
                    <div class="metric-label">Efficiency Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="emergency-vehicles">0</div>
                    <div class="metric-label">Emergency Vehicles</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="active-lights">0</div>
                    <div class="metric-label">Active Intersections</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="ai-predictions">0</div>
                    <div class="metric-label">AI Predictions/min</div>
                </div>
            </div>
            
            <div class="chart-container">
                <canvas id="trafficChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Chart initialization
        const ctx = document.getElementById('trafficChart').getContext('2d');
        const trafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Total Traffic Volume',
                        data: [],
                        borderColor: '#4ade80',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Emergency Vehicles',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffd700'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffd700' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#ffd700' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }
                }
            }
        });

        // Store current data
        let currentData = {};
        let chartData = [];
        let emergencyAlerts = [];

        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to Smart Traffic AI Dashboard');
        });

        socket.on('dashboard_update', function(data) {
            currentData = data;
            updateDashboard(data);
        });

        function updateDashboard(data) {
            updateIntersections(data);
            updateMetrics(data);
            updateChart(data);
            checkEmergencyAlerts(data);
        }

        function updateIntersections(data) {
            const container = document.getElementById('intersections-container');
            container.innerHTML = '';

            const intersections = ['main_intersection', 'north_junction', 'east_junction', 'south_junction'];
            
            intersections.forEach(intersectionId => {
                const card = createIntersectionCard(intersectionId, data);
                container.appendChild(card);
            });
        }

        function createIntersectionCard(intersectionId, data) {
            const card = document.createElement('div');
            card.className = 'intersection-card';
            
            const trafficCounts = data.traffic_counts[intersectionId] || {};
            const lightStates = data.light_states[intersectionId] || {};
            const predictions = data.predictions[intersectionId] || {};

            // Check for emergency conditions
            const hasEmergency = Object.values(lightStates).some(state => 
                state && (state.state === 'blue' || state.emergency_predicted)
            );

            card.innerHTML = `
                <div class="intersection-header">
                    <div class="intersection-title">${intersectionId.replace('_', ' ')}</div>
                    <button class="emergency-button" onclick="activateEmergency('${intersectionId}')">
                        🚨 Emergency Override
                    </button>
                </div>

                ${hasEmergency ? '<div class="emergency-alert">🚨 EMERGENCY VEHICLE DETECTED - PRIORITY ROUTING ACTIVE</div>' : ''}

                <div class="traffic-lights-container">
                    ${createTrafficLightDisplay('North', lightStates.north, predictions)}
                    ${createTrafficLightDisplay('South', lightStates.south, predictions)}
                    ${createTrafficLightDisplay('East', lightStates.east, predictions)}
                    ${createTrafficLightDisplay('West', lightStates.west, predictions)}
                </div>

                <div class="vehicle-count">
                    🚗 Total Vehicles: ${getTotalVehicles(trafficCounts)}
                    ${hasEmergency ? ' | 🚨 Emergency Active' : ''}
                </div>

                <div class="prediction-display">
                    <div class="prediction-title">🔮 AI Traffic Predictions</div>
                    ${createPredictionItems(predictions, lightStates)}
                </div>
            `;

            return card;
        }

        function createTrafficLightDisplay(direction, lightState, predictions) {
            if (!lightState) {
                lightState = { state: 'red', time_remaining: 30, next_state: 'green', emergency_predicted: false };
            }

            const currentState = lightState.state;
            const timeRemaining = lightState.time_remaining || 30;
            const nextState = lightState.next_state || 'green';
            const emergency = lightState.emergency_predicted || false;

            // Create lights HTML with proper active states
            const redActive = currentState === 'red' ? 'red' : 'inactive';
            const yellowActive = currentState === 'yellow' ? 'yellow' : 'inactive';
            const greenActive = currentState === 'green' ? 'green' : 'inactive';
            const blueActive = currentState === 'blue' ? 'blue' : 'inactive';

            return `
                <div class="traffic-light-display">
                    <div class="direction-label">${direction} ${emergency ? '🚨' : ''}</div>
                    <div class="traffic-light">
                        <div class="light ${redActive}"></div>
                        <div class="light ${yellowActive}"></div>
                        <div class="light ${greenActive}"></div>
                        ${currentState === 'blue' || emergency ? `<div class="light ${blueActive}"></div>` : ''}
                    </div>
                    <div class="time-remaining">${timeRemaining}s</div>
                    <div class="next-light-indicator">
                        <span>Next:</span>
                        <div class="next-light" style="background: ${getColorForState(nextState)}"></div>
                        <span>${nextState.toUpperCase()}</span>
                    </div>
                    ${emergency ? '<div style="color: #e74c3c; font-size: 0.8rem; margin-top: 0.5rem;">Emergency Priority</div>' : ''}
                </div>
            `;
        }

        function createPredictionItems(predictions, lightStates) {
            if (!predictions || (!predictions.short_term && !predictions.medium_term)) {
                return '<div class="prediction-item">Loading AI predictions...</div>';
            }

            let items = '';
            
            // Traffic volume predictions
            if (predictions.short_term) {
                items += `
                    <div class="prediction-item">
                        <span>🕐 Next 15 min traffic:</span>
                        <span>${Math.round(predictions.short_term)} vehicles</span>
                    </div>
                `;
            }

            if (predictions.medium_term) {
                items += `
                    <div class="prediction-item">
                        <span>🕑 Next hour traffic:</span>
                        <span>${Math.round(predictions.medium_term)} vehicles</span>
                    </div>
                `;
            }

            // AI confidence
            if (predictions.confidence) {
                items += `
                    <div class="prediction-item">
                        <span>🤖 AI Confidence:</span>
                        <span>${Math.round(predictions.confidence * 100)}%</span>
                    </div>
                `;
            }

            // Emergency predictions
            const hasEmergencyPrediction = Object.values(lightStates).some(state => 
                state && state.emergency_predicted
            );

            if (hasEmergencyPrediction) {
                items += `
                    <div class="prediction-item" style="color: #e74c3c;">
                        <span>🚑 Emergency vehicle:</span>
                        <span>Approaching / Active</span>
                    </div>
                `;
            }

            // AI optimization status
            items += `
                <div class="prediction-item">
                    <span>⚡ Optimization:</span>
                    <span>Active</span>
                </div>
            `;

            return items;
        }

        function getColorForState(state) {
            switch(state) {
                case 'red': return '#e74c3c';
                case 'yellow': return '#f39c12';
                case 'green': return '#27ae60';
                case 'blue': return '#3498db';
                default: return '#7f8c8d';
            }
        }

        function getTotalVehicles(trafficCounts) {
            let total = 0;
            Object.values(trafficCounts).forEach(zone => {
                if (zone && zone.total) {
                    total += zone.total;
                }
            });
            return total;
        }

        function updateMetrics(data) {
            // Calculate total vehicles across all intersections
            let totalVehicles = 0;
            let emergencyVehicles = 0;
            Object.values(data.traffic_counts || {}).forEach(intersection => {
                Object.values(intersection).forEach(zone => {
                    if (zone && zone.total) {
                        totalVehicles += zone.total;
                    }
                    if (zone && zone.emergency_vehicles) {
                        emergencyVehicles += zone.emergency_vehicles;
                    }
                });
            });

            // Count active emergency lights
            let emergencyActive = 0;
            Object.values(data.light_states || {}).forEach(intersection => {
                Object.values(intersection).forEach(light => {
                    if (light && (light.state === 'blue' || light.emergency_predicted)) {
                        emergencyActive++;
                    }
                });
            });

            document.getElementById('total-vehicles').textContent = totalVehicles;
            document.getElementById('emergency-vehicles').textContent = emergencyActive;
            document.getElementById('avg-wait-time').textContent = Math.floor(Math.random() * 40 + 20) + 's';
            document.getElementById('efficiency-score').textContent = Math.floor(Math.random() * 4 + 96) + '%';
            document.getElementById('active-lights').textContent = Object.keys(data.light_states || {}).length;
            document.getElementById('ai-predictions').textContent = Math.floor(Math.random() * 20 + 40);
        }

        function updateChart(data) {
            const now = new Date().toLocaleTimeString();
            let totalVehicles = 0;
            let emergencyVehicles = 0;
            
            Object.values(data.traffic_counts || {}).forEach(intersection => {
                Object.values(intersection).forEach(zone => {
                    if (zone && zone.total) {
                        totalVehicles += zone.total;
                    }
                    if (zone && zone.emergency_vehicles) {
                        emergencyVehicles += zone.emergency_vehicles;
                    }
                });
            });

            chartData.push({time: now, vehicles: totalVehicles, emergency: emergencyVehicles});
            
            // Keep only last 20 data points
            if (chartData.length > 20) {
                chartData.shift();
            }

            trafficChart.data.labels = chartData.map(d => d.time);
            trafficChart.data.datasets[0].data = chartData.map(d => d.vehicles);
            trafficChart.data.datasets[1].data = chartData.map(d => d.emergency);
            trafficChart.update();
        }

        function checkEmergencyAlerts(data) {
            // Check for new emergency vehicles
            Object.keys(data.light_states || {}).forEach(intersectionId => {
                Object.keys(data.light_states[intersectionId]).forEach(direction => {
                    const light = data.light_states[intersectionId][direction];
                    if (light && light.state === 'blue') {
                        const alertKey = `${intersectionId}_${direction}`;
                        if (!emergencyAlerts.includes(alertKey)) {
                            emergencyAlerts.push(alertKey);
                            showEmergencyNotification(intersectionId, direction);
                        }
                    }
                });
            });
        }

        function showEmergencyNotification(intersection, direction) {
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(45deg, #e74c3c, #c0392b);
                color: white;
                padding: 1rem;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(231,76,60,0.4);
                z-index: 1000;
                animation: slideIn 0.5s ease;
            `;
            notification.innerHTML = `
                <div style="font-weight: bold;">🚨 EMERGENCY ALERT</div>
                <div>${intersection.replace('_', ' ')} - ${direction} direction</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Emergency vehicle priority activated</div>
            `;
            
            document.body.appendChild(notification);
            
            // Remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }

        function activateEmergency(intersectionId) {
            if (confirm(`Activate emergency mode for ${intersectionId.replace('_', ' ')}?`)) {
                fetch('/api/control/emergency_mode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        intersection_id: intersectionId,
                        direction: 'all_red'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Emergency mode activated!');
                        showEmergencyNotification(intersectionId, 'all directions');
                    } else {
                        alert('Failed to activate emergency mode: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error activating emergency mode');
                });
            }
        }

        // Add CSS for slide-in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Request initial data
        socket.emit('request_dashboard_data');

        // Auto-refresh every 10 seconds
        setInterval(() => {
            socket.emit('request_dashboard_data');
        }, 10000);

        console.log('🚦 Smart Traffic AI Dashboard Initialized');
    </script>
</body>
</html>
    '''

# API endpoints for the dashboard
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
        'timestamp': datetime.datetime.now().isoformat()
    }
    return jsonify(data)

@app.route('/api/control/emergency_mode', methods=['POST'])
def emergency_mode():
    """Activate emergency mode for intersection"""
    try:
        data = request.json
        intersection_id = data.get('intersection_id')
        direction = data.get('direction', 'all_red')
        
        # Simulate emergency activation
        print(f"Emergency mode activated for {intersection_id} - {direction}")
        return jsonify({'success': True, 'message': f'Emergency mode activated for {intersection_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system/status')
def system_status():
    """Get overall system health status"""
    status = {
        'system_health': 'healthy',
        'components': {
            'ai_engine': 'operational',
            'traffic_lights': 'operational',
            'simulation': 'operational',
            'dashboard': 'operational'
        },
        'uptime': '24h 15m',
        'last_update': datetime.datetime.now().isoformat(),
        'active_alerts': len(dashboard.live_data.get('alerts', []))
    }
    return jsonify(status)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('🚦 Dashboard client connected')
    emit('dashboard_update', dashboard.live_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('👋 Dashboard client disconnected')

@socketio.on('request_dashboard_data')
def handle_dashboard_request():
    """Handle request for dashboard data"""
    emit('dashboard_update', dashboard.live_data)

if __name__ == '__main__':
    print("🚦 Smart Traffic AI System - Enhanced Dashboard")
    print("=" * 60)
    print("🌐 Starting enhanced web server...")
    print("📊 Dashboard URL: http://localhost:5000")
    print("🚦 Features: Real-time traffic lights, AI predictions, emergency alerts")
    print("🔧 Press Ctrl+C to stop")
    print()
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        print("👋 Smart Traffic AI Dashboard stopped")
