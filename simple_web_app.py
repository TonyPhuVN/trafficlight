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

# Manual vehicle count override
manual_mode = False
manual_vehicle_counts = {
    'North': 0,
    'East': 0,
    'South': 0,
    'West': 0
}

# Auto mode maximum limits
auto_mode_limits = {
    'North': 15,
    'East': 15,
    'South': 15,
    'West': 15
}

# Automated test scenarios - Nhiều trường hợp thực tế
test_mode = False
test_scenarios = [
    # Các trường hợp bình thường hàng ngày
    {
        'name': 'Sáng sớm (6:00-7:00)',
        'description': 'Giao thông nhẹ, chủ yếu xe đi làm sớm và xe tập thể dục',
        'counts': {'North': 8, 'East': 6, 'South': 10, 'West': 5},
        'duration': 10
    },
    {
        'name': 'Giờ cao điểm sáng (7:00-9:00)',
        'description': 'Giao thông đông từ khu dân cư vào trung tâm thành phố',
        'counts': {'North': 25, 'East': 12, 'South': 30, 'West': 15},
        'duration': 15
    },
    {
        'name': 'Giữa buổi sáng (9:00-11:00)',
        'description': 'Giao thông vừa phải, chủ yếu xe công việc và mua sắm',
        'counts': {'North': 12, 'East': 15, 'South': 10, 'West': 18},
        'duration': 12
    },
    {
        'name': 'Trưa (11:00-13:00)',
        'description': 'Giao thông tăng nhẹ do giờ ăn trưa và nghỉ trưa',
        'counts': {'North': 18, 'East': 20, 'South': 16, 'West': 22},
        'duration': 12
    },
    {
        'name': 'Chiều (13:00-16:00)',
        'description': 'Giao thông ổn định, hoạt động thương mại bình thường',
        'counts': {'North': 14, 'East': 16, 'South': 12, 'West': 19},
        'duration': 10
    },
    {
        'name': 'Giờ cao điểm chiều (16:00-18:00)',
        'description': 'Giao thông đông từ trung tâm về khu dân cư',
        'counts': {'North': 15, 'East': 28, 'South': 12, 'West': 35},
        'duration': 15
    },
    {
        'name': 'Tối (18:00-20:00)',
        'description': 'Giao thông giảm dần, một số hoạt động giải trí',
        'counts': {'North': 10, 'East': 14, 'South': 8, 'West': 16},
        'duration': 10
    },
    {
        'name': 'Cuối tuần sáng',
        'description': 'Giao thông nhẹ, chủ yếu đi chợ và dạo phố',
        'counts': {'North': 12, 'East': 18, 'South': 15, 'West': 20},
        'duration': 12
    },
    {
        'name': 'Cuối tuần chiều',
        'description': 'Giao thông tăng do hoạt động mua sắm và giải trí',
        'counts': {'North': 20, 'East': 25, 'South': 18, 'West': 28},
        'duration': 12
    },
    {
        'name': 'Giờ tan trường',
        'description': 'Giao thông đông quanh khu vực trường học',
        'counts': {'North': 22, 'East': 18, 'South': 28, 'West': 15},
        'duration': 10
    },
    {
        'name': 'Ngày mưa',
        'description': 'Giao thông chậm và tắc nghẽn do thời tiết xấu',
        'counts': {'North': 30, 'East': 25, 'South': 35, 'West': 28},
        'duration': 15
    },
    {
        'name': 'Đêm khuya (22:00-6:00)',
        'description': 'Giao thông rất nhẹ, chủ yếu xe tải và taxi',
        'counts': {'North': 3, 'East': 5, 'South': 2, 'West': 4},
        'duration': 8
    },
    {
        'name': 'Sự kiện đặc biệt',
        'description': 'Giao thông đông do có sự kiện lớn trong khu vực',
        'counts': {'North': 35, 'East': 30, 'South': 40, 'West': 32},
        'duration': 12
    },
    {
        'name': 'Thi công đường',
        'description': 'Giao thông bị ảnh hưởng do thi công, phân luồng không đều',
        'counts': {'North': 40, 'East': 8, 'South': 45, 'West': 10},
        'duration': 12
    },
    {
        'name': 'Tình huống khẩn cấp',
        'description': 'Giao thông cao với nhiều xe cứu thương và cứu hỏa',
        'counts': {'North': 45, 'East': 40, 'South': 50, 'West': 38},
        'duration': 10
    }
]
current_test_index = 0
test_start_time = 0

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
        .manual-inputs {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 15px 0;
        }
        .input-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .input-group label {
            font-weight: bold;
            min-width: 80px;
        }
        .input-group input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 1em;
        }
        .input-hint {
            font-size: 0.8em;
            opacity: 0.7;
            min-width: 80px;
            text-align: right;
        }
        .input-group input:focus {
            outline: none;
            border-color: #4ade80;
            box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.2);
        }
        .btn.active {
            background: #f59e0b;
        }
        .btn.active:hover {
            background: #d97706;
        }
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .preset-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            padding: 12px;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            font-size: 0.9em;
        }
        .preset-btn:hover {
            background: rgba(74, 222, 128, 0.2);
            border-color: #4ade80;
            transform: translateY(-2px);
        }
        .preset-btn small {
            display: block;
            margin-top: 5px;
            opacity: 0.8;
            font-size: 0.8em;
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
            <button class="btn" onclick="toggleManualMode()" id="manual-toggle">🎛️ Manual Mode</button>
            <button class="btn" onclick="toggleTestMode()" id="test-toggle">🧪 Test Mode</button>
        </div>

        <div id="status" class="status stopped">⏹️ Simulation Stopped</div>

        <!-- Test Mode Status Panel -->
        <div id="test-status" class="card" style="display: none; margin: 20px 0; text-align: center;">
            <h3 data-icon="🧪">Automated Test Mode</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0;">
                <div class="stat-item">
                    <span class="stat-value" id="current-test">-</span>
                    <span class="stat-label">Current Scenario</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="test-progress">0/15</span>
                    <span class="stat-label">Progress</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="time-remaining">--</span>
                    <span class="stat-label">Time Remaining</span>
                </div>
            </div>
            <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin: 10px 0;">
                <div id="test-description" style="font-style: italic;">Ready to start automated testing...</div>
            </div>
            <div style="margin-top: 10px;">
                <button class="btn" onclick="nextTest()">⏭️ Next Scenario</button>
                <button class="btn" onclick="resetTests()">🔄 Reset Tests</button>
            </div>
        </div>

        <!-- Vehicle Control Panel -->
        <div id="control-panel" class="card" style="display: none; margin: 20px 0;">
            <h3 data-icon="🎛️" id="control-title">Manual Vehicle Control</h3>
            <p id="control-description" style="margin-bottom: 15px; opacity: 0.9;">Set specific vehicle counts for each direction:</p>
            <div class="manual-inputs">
                <div class="input-group">
                    <label>🔼 North:</label>
                    <input type="number" id="north-input" min="0" max="100" value="0" onchange="updateVehicleCount('North', this.value)">
                    <span class="input-hint" id="north-hint">Fixed count</span>
                </div>
                <div class="input-group">
                    <label>▶️ East:</label>
                    <input type="number" id="east-input" min="0" max="100" value="0" onchange="updateVehicleCount('East', this.value)">
                    <span class="input-hint" id="east-hint">Fixed count</span>
                </div>
                <div class="input-group">
                    <label>🔽 South:</label>
                    <input type="number" id="south-input" min="0" max="100" value="0" onchange="updateVehicleCount('South', this.value)">
                    <span class="input-hint" id="south-hint">Fixed count</span>
                </div>
                <div class="input-group">
                    <label>◀️ West:</label>
                    <input type="number" id="west-input" min="0" max="100" value="0" onchange="updateVehicleCount('West', this.value)">
                    <span class="input-hint" id="west-hint">Fixed count</span>
                </div>
            </div>
            <div style="margin-top: 15px; text-align: center;">
                <button class="btn" onclick="applyVehicleCounts()">✅ Apply Changes</button>
                <button class="btn" onclick="resetVehicleCounts()">🔄 Reset All</button>
                <button class="btn" onclick="showPresetScenarios()" id="preset-btn">📋 Preset Scenarios</button>
            </div>
        </div>

        <!-- Preset Scenarios Panel -->
        <div id="preset-panel" class="card" style="display: none; margin: 20px 0;">
            <h3 data-icon="📋">Traffic Scenario Presets</h3>
            <p style="margin-bottom: 15px; opacity: 0.9;">Choose a typical traffic scenario:</p>
            <div class="preset-grid">
                <button class="preset-btn" onclick="applyPreset('morning_light')">🌅 Early Morning<br><small>N:8, E:6, S:10, W:5</small></button>
                <button class="preset-btn" onclick="applyPreset('morning_rush')">🚗 Morning Rush<br><small>N:25, E:12, S:30, W:15</small></button>
                <button class="preset-btn" onclick="applyPreset('lunch_time')">🍽️ Lunch Time<br><small>N:18, E:20, S:16, W:22</small></button>
                <button class="preset-btn" onclick="applyPreset('evening_rush')">🌆 Evening Rush<br><small>N:15, E:28, S:12, W:35</small></button>
                <button class="preset-btn" onclick="applyPreset('weekend')">🛍️ Weekend<br><small>N:20, E:25, S:18, W:28</small></button>
                <button class="preset-btn" onclick="applyPreset('night')">🌙 Late Night<br><small>N:3, E:5, S:2, W:4</small></button>
                <button class="preset-btn" onclick="applyPreset('rain')">🌧️ Rainy Day<br><small>N:30, E:25, S:35, W:28</small></button>
                <button class="preset-btn" onclick="applyPreset('emergency')">🚨 Emergency<br><small>N:45, E:40, S:50, W:38</small></button>
            </div>
            <div style="margin-top: 15px; text-align: center;">
                <button class="btn" onclick="hidePresetScenarios()">❌ Close</button>
            </div>
        </div>

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
        let manualMode = false;
        let testMode = false;
        let testTimer = null;

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

        socket.on('auto_limits_data', function(data) {
            // Update input fields with auto limits
            document.getElementById('north-input').value = data.North || 15;
            document.getElementById('east-input').value = data.East || 15;
            document.getElementById('south-input').value = data.South || 15;
            document.getElementById('west-input').value = data.West || 15;
        });

        socket.on('test_status_update', function(data) {
            document.getElementById('current-test').textContent = data.current_test;
            document.getElementById('test-progress').textContent = `${data.test_index + 1}/${data.total_tests}`;
            document.getElementById('time-remaining').textContent = `${data.time_remaining}s`;
            document.getElementById('test-description').textContent = data.description;
        });

        socket.on('test_scenario_changed', function(data) {
            addLogEntry(`🧪 Test: ${data.name} - ${data.description}`);
        });

        function startSimulation() {
            socket.emit('start_simulation');
            addLogEntry('🚀 Starting simulation...');
        }

        function stopSimulation() {
            socket.emit('stop_simulation');
            addLogEntry('🛑 Stopping simulation...');
        }

        function toggleManualMode() {
            manualMode = !manualMode;
            const panel = document.getElementById('control-panel');
            const button = document.getElementById('manual-toggle');
            const title = document.getElementById('control-title');
            const description = document.getElementById('control-description');

            if (manualMode) {
                // Manual Mode - Fixed vehicle counts
                panel.style.display = 'block';
                button.textContent = '🤖 Auto Mode';
                button.classList.add('active');
                title.textContent = '🎛️ Manual Vehicle Control';
                description.textContent = 'Set specific vehicle counts for each direction:';

                // Update input hints
                updateInputHints('Fixed count');

                socket.emit('set_manual_mode', {enabled: true});
                addLogEntry('🎛️ Manual mode enabled - Set exact vehicle counts');
            } else {
                // Auto Mode - Maximum vehicle limits
                title.textContent = '🤖 Auto Mode Limits';
                description.textContent = 'Set maximum vehicle limits for each direction:';
                button.textContent = '🎛️ Manual Mode';
                button.classList.remove('active');

                // Update input hints
                updateInputHints('Max limit');

                // Load current auto limits
                loadAutoLimits();

                socket.emit('set_manual_mode', {enabled: false});
                addLogEntry('🤖 Auto mode enabled - Set maximum vehicle limits');
            }
        }

        function updateInputHints(hintText) {
            document.getElementById('north-hint').textContent = hintText;
            document.getElementById('east-hint').textContent = hintText;
            document.getElementById('south-hint').textContent = hintText;
            document.getElementById('west-hint').textContent = hintText;
        }

        function loadAutoLimits() {
            // Request current auto limits from server
            socket.emit('get_auto_limits');
        }

        function updateVehicleCount(direction, value) {
            const count = parseInt(value) || 0;
            const mode = manualMode ? 'fixed count' : 'max limit';
            addLogEntry(`📝 ${direction} ${mode}: ${count} vehicles`);
        }

        function applyVehicleCounts() {
            const counts = {
                North: parseInt(document.getElementById('north-input').value) || 0,
                East: parseInt(document.getElementById('east-input').value) || 0,
                South: parseInt(document.getElementById('south-input').value) || 0,
                West: parseInt(document.getElementById('west-input').value) || 0
            };

            if (manualMode) {
                socket.emit('update_manual_counts', counts);
                const total = counts.North + counts.East + counts.South + counts.West;
                addLogEntry(`✅ Applied manual counts - Total: ${total} vehicles`);
            } else {
                socket.emit('update_auto_limits', counts);
                const total = counts.North + counts.East + counts.South + counts.West;
                addLogEntry(`✅ Applied auto limits - Max total: ${total} vehicles`);
            }
        }

        function resetVehicleCounts() {
            const defaultValue = manualMode ? 0 : 15;
            document.getElementById('north-input').value = defaultValue;
            document.getElementById('east-input').value = defaultValue;
            document.getElementById('south-input').value = defaultValue;
            document.getElementById('west-input').value = defaultValue;
            applyVehicleCounts();
            const mode = manualMode ? 'manual counts' : 'auto limits';
            addLogEntry(`🔄 Reset all ${mode} to ${defaultValue}`);
        }

        function toggleTestMode() {
            testMode = !testMode;
            const testPanel = document.getElementById('test-status');
            const controlPanel = document.getElementById('control-panel');
            const testButton = document.getElementById('test-toggle');
            const manualButton = document.getElementById('manual-toggle');

            if (testMode) {
                // Enable test mode
                testPanel.style.display = 'block';
                controlPanel.style.display = 'none';
                testButton.textContent = '🎛️ Disable Test Mode';
                testButton.classList.add('active');
                manualButton.disabled = true;
                manualButton.style.opacity = '0.5';

                socket.emit('set_test_mode', {enabled: true});
                addLogEntry('🧪 Test mode enabled - Running automated scenarios');

                // Start test countdown
                startTestCountdown();
            } else {
                // Disable test mode
                testPanel.style.display = 'none';
                testButton.textContent = '🧪 Test Mode';
                testButton.classList.remove('active');
                manualButton.disabled = false;
                manualButton.style.opacity = '1';

                socket.emit('set_test_mode', {enabled: false});
                addLogEntry('🎛️ Test mode disabled - Manual control restored');

                // Clear test timer
                if (testTimer) {
                    clearInterval(testTimer);
                    testTimer = null;
                }
            }
        }

        function startTestCountdown() {
            if (testTimer) clearInterval(testTimer);

            testTimer = setInterval(() => {
                socket.emit('get_test_status');
            }, 1000); // Update every second
        }

        function nextTest() {
            socket.emit('next_test');
            addLogEntry('⏭️ Skipping to next test scenario');
        }

        function resetTests() {
            socket.emit('reset_tests');
            addLogEntry('🔄 Resetting test scenarios to beginning');
        }

        function showPresetScenarios() {
            const presetPanel = document.getElementById('preset-panel');
            const presetBtn = document.getElementById('preset-btn');

            if (presetPanel.style.display === 'none' || presetPanel.style.display === '') {
                presetPanel.style.display = 'block';
                presetBtn.textContent = '❌ Close Presets';
                presetBtn.classList.add('active');
            } else {
                hidePresetScenarios();
            }
        }

        function hidePresetScenarios() {
            const presetPanel = document.getElementById('preset-panel');
            const presetBtn = document.getElementById('preset-btn');

            presetPanel.style.display = 'none';
            presetBtn.textContent = '📋 Preset Scenarios';
            presetBtn.classList.remove('active');
        }

        function applyPreset(presetType) {
            const presets = {
                'morning_light': {North: 8, East: 6, South: 10, West: 5, name: 'Early Morning'},
                'morning_rush': {North: 25, East: 12, South: 30, West: 15, name: 'Morning Rush'},
                'lunch_time': {North: 18, East: 20, South: 16, West: 22, name: 'Lunch Time'},
                'evening_rush': {North: 15, East: 28, South: 12, West: 35, name: 'Evening Rush'},
                'weekend': {North: 20, East: 25, South: 18, West: 28, name: 'Weekend'},
                'night': {North: 3, East: 5, South: 2, West: 4, name: 'Late Night'},
                'rain': {North: 30, East: 25, South: 35, West: 28, name: 'Rainy Day'},
                'emergency': {North: 45, East: 40, South: 50, West: 38, name: 'Emergency'}
            };

            const preset = presets[presetType];
            if (preset) {
                document.getElementById('north-input').value = preset.North;
                document.getElementById('east-input').value = preset.East;
                document.getElementById('south-input').value = preset.South;
                document.getElementById('west-input').value = preset.West;

                applyVehicleCounts();
                hidePresetScenarios();
                addLogEntry(`📋 Applied preset: ${preset.name}`);
            }
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

@socketio.on('set_manual_mode')
def handle_set_manual_mode(data):
    """Enable or disable manual mode"""
    global manual_mode
    manual_mode = data.get('enabled', False)
    mode_text = "Manual" if manual_mode else "Automatic"
    emit('activity_log', {'message': f'🔧 Mode changed to: {mode_text}'}, broadcast=True)

@socketio.on('update_manual_counts')
def handle_update_manual_counts(data):
    """Update manual vehicle counts"""
    global manual_vehicle_counts
    manual_vehicle_counts.update(data)
    total = sum(manual_vehicle_counts.values())
    emit('activity_log', {'message': f'📊 Manual counts updated - Total: {total} vehicles'}, broadcast=True)

@socketio.on('update_auto_limits')
def handle_update_auto_limits(data):
    """Update auto mode maximum limits"""
    global auto_mode_limits
    auto_mode_limits.update(data)
    total = sum(auto_mode_limits.values())
    emit('activity_log', {'message': f'🤖 Auto limits updated - Max total: {total} vehicles'}, broadcast=True)

@socketio.on('get_auto_limits')
def handle_get_auto_limits():
    """Send current auto limits to client"""
    emit('auto_limits_data', auto_mode_limits)

@socketio.on('set_test_mode')
def handle_set_test_mode(data):
    """Enable or disable test mode"""
    global test_mode, test_start_time, current_test_index
    test_mode = data.get('enabled', False)
    if test_mode:
        test_start_time = time.time()
        current_test_index = 0
        emit('activity_log', {'message': '🧪 Automated test mode started'}, broadcast=True)
    else:
        emit('activity_log', {'message': '🎛️ Test mode stopped'}, broadcast=True)

@socketio.on('get_test_status')
def handle_get_test_status():
    """Send current test status"""
    if test_mode and test_scenarios:
        current_scenario = test_scenarios[current_test_index]
        elapsed = time.time() - test_start_time
        remaining = max(0, current_scenario['duration'] - int(elapsed))

        emit('test_status_update', {
            'current_test': current_scenario['name'],
            'description': current_scenario['description'],
            'test_index': current_test_index,
            'total_tests': len(test_scenarios),
            'time_remaining': remaining
        })

@socketio.on('next_test')
def handle_next_test():
    """Skip to next test scenario"""
    global current_test_index, test_start_time
    if test_mode:
        current_test_index = (current_test_index + 1) % len(test_scenarios)
        test_start_time = time.time()
        emit('activity_log', {'message': f'⏭️ Switched to: {test_scenarios[current_test_index]["name"]}'}, broadcast=True)

@socketio.on('reset_tests')
def handle_reset_tests():
    """Reset test scenarios to beginning"""
    global current_test_index, test_start_time
    if test_mode:
        current_test_index = 0
        test_start_time = time.time()
        emit('activity_log', {'message': '🔄 Test scenarios reset to beginning'}, broadcast=True)

def simulation_loop():
    """Main simulation loop"""
    global simulation_running, manual_mode, manual_vehicle_counts, auto_mode_limits
    global test_mode, test_scenarios, current_test_index, test_start_time

    while simulation_running:
        try:
            # Handle test mode scenario switching
            if test_mode and test_scenarios:
                current_scenario = test_scenarios[current_test_index]
                elapsed = time.time() - test_start_time

                # Check if it's time to switch to next scenario
                if elapsed >= current_scenario['duration']:
                    current_test_index = (current_test_index + 1) % len(test_scenarios)
                    test_start_time = time.time()
                    new_scenario = test_scenarios[current_test_index]

                    socketio.emit('test_scenario_changed', {
                        'name': new_scenario['name'],
                        'description': new_scenario['description']
                    })
                    socketio.emit('activity_log', {
                        'message': f'🧪 Auto-switched to: {new_scenario["name"]}'
                    })

                # Use current test scenario counts
                zone_counts = {}
                total_test = 0
                for direction, count in current_scenario['counts'].items():
                    zone_counts[direction] = {
                        'cars': max(0, count - 3),
                        'trucks': min(3, count // 3),
                        'buses': min(2, count // 4),
                        'motorcycles': min(4, count // 2),
                        'bicycles': min(2, count // 5),
                        'emergency_vehicles': 2 if count > 20 else 1 if count > 10 else 0,
                        'total': count
                    }
                    total_test += count

                # Create test stats
                stats = {
                    'total_vehicles': total_test,
                    'by_type': {
                        'cars': sum(zc.get('cars', 0) for zc in zone_counts.values()),
                        'trucks': sum(zc.get('trucks', 0) for zc in zone_counts.values()),
                        'buses': sum(zc.get('buses', 0) for zc in zone_counts.values()),
                        'motorcycles': sum(zc.get('motorcycles', 0) for zc in zone_counts.values()),
                        'emergency': sum(zc.get('emergency_vehicles', 0) for zc in zone_counts.values())
                    },
                    'average_speed': max(15, 45 - (total_test * 0.3)),  # Speed decreases with more vehicles
                    'emergency_vehicles': sum(zc.get('emergency_vehicles', 0) for zc in zone_counts.values()),
                    'density_level': 'low' if total_test < 30 else 'medium' if total_test < 60 else 'high' if total_test < 100 else 'extreme',
                    'timestamp': time.time()
                }

            elif manual_mode:
                # Manual Mode - Use exact counts
                zone_counts = {}
                total_manual = 0
                for direction, count in manual_vehicle_counts.items():
                    zone_counts[direction] = {
                        'cars': max(0, count - 2),
                        'trucks': min(2, count // 3),
                        'buses': min(1, count // 5),
                        'motorcycles': min(3, count // 2),
                        'bicycles': min(2, count // 4),
                        'emergency_vehicles': 1 if count > 10 else 0,
                        'total': count
                    }
                    total_manual += count

                # Create manual stats
                stats = {
                    'total_vehicles': total_manual,
                    'by_type': {
                        'cars': sum(zc.get('cars', 0) for zc in zone_counts.values()),
                        'trucks': sum(zc.get('trucks', 0) for zc in zone_counts.values()),
                        'buses': sum(zc.get('buses', 0) for zc in zone_counts.values()),
                        'motorcycles': sum(zc.get('motorcycles', 0) for zc in zone_counts.values()),
                        'emergency': sum(zc.get('emergency_vehicles', 0) for zc in zone_counts.values())
                    },
                    'average_speed': 35 + (total_manual * -0.2),  # Speed decreases with more vehicles
                    'emergency_vehicles': sum(zc.get('emergency_vehicles', 0) for zc in zone_counts.values()),
                    'density_level': 'low' if total_manual < 20 else 'medium' if total_manual < 40 else 'high',
                    'timestamp': time.time()
                }
            else:
                # Auto Mode - Use simulation with limits
                traffic_sim.update_simulation(1.0)
                stats = traffic_sim.get_traffic_statistics()
                zone_counts = traffic_sim.get_vehicle_counts_by_zone()

                # Apply auto mode limits
                for direction, limit in auto_mode_limits.items():
                    if direction in zone_counts:
                        current_total = zone_counts[direction].get('total', 0)
                        if current_total > limit:
                            # Scale down all vehicle types proportionally
                            scale_factor = limit / current_total if current_total > 0 else 1
                            for vehicle_type in zone_counts[direction]:
                                if vehicle_type != 'total':
                                    zone_counts[direction][vehicle_type] = int(zone_counts[direction][vehicle_type] * scale_factor)
                            zone_counts[direction]['total'] = limit

                # Recalculate stats with limited counts
                total_limited = sum(zc.get('total', 0) for zc in zone_counts.values())
                stats['total_vehicles'] = total_limited
                stats['density_level'] = 'low' if total_limited < 20 else 'medium' if total_limited < 40 else 'high'

            # Get weather data
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
                if test_mode:
                    current_scenario = test_scenarios[current_test_index]
                    elapsed = int(time.time() - test_start_time)
                    remaining = max(0, current_scenario['duration'] - elapsed)
                    mode_indicator = f"🧪 Test: {current_scenario['name']} ({remaining}s)"
                else:
                    mode_indicator = "🎛️ Manual" if manual_mode else "🤖 Auto"

                socketio.emit('activity_log', {
                    'message': f'📊 {mode_indicator} - {stats["total_vehicles"]} vehicles, {stats["density_level"]} density'
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
