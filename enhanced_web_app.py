"""
Enhanced Smart Traffic AI System Web Interface
Real-time traffic simulation with manual controls for vehicle count and road navigation
"""

import time
import threading
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import the traffic simulator and optimizer
from data_simulation.traffic_simulator import TrafficSimulator, WeatherSimulator
from ai_engine.traffic_light_optimizer import TrafficLightOptimizer

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_traffic_enhanced_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global simulation objects
traffic_sim = TrafficSimulator("MAIN_INTERSECTION")
weather_sim = WeatherSimulator()
traffic_optimizer = TrafficLightOptimizer()
simulation_running = False

# Manual control settings
manual_vehicle_counts = {
    'north': 0,
    'south': 0,
    'east': 0,
    'west': 0,
    'total_target': 50
}

road_navigation_settings = {
    'allow_emergency_vehicles': True,
    'traffic_light_override': False,
    'speed_limit': 50,  # km/h
    'weather_effects': True
}

# Manual weather control settings
manual_weather_settings = {
    'manual_control': False,
    'condition': 'sunny',
    'temperature': 25,
    'humidity': 60,
    'rain_intensity': 0,  # 0=no rain, 1=light, 2=moderate, 3=heavy
    'visibility': 100  # percentage
}

@app.route('/')
def index():
    """Enhanced dashboard with manual controls"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🚦 Enhanced Smart Traffic AI System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .header h1 {
            font-size: 2.8em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            background: linear-gradient(45deg, #ffd700, #ffeb3b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .controls-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .control-panel {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .control-panel h3 {
            margin: 0 0 20px 0;
            color: #ffd700;
            display: flex;
            align-items: center;
            font-size: 1.4em;
        }
        .control-panel h3::before {
            content: attr(data-icon);
            margin-right: 10px;
            font-size: 1.2em;
        }
        .vehicle-controls {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .direction-control {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .direction-control label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .direction-control input {
            width: 80px;
            padding: 8px;
            border: none;
            border-radius: 5px;
            text-align: center;
            font-size: 1.1em;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        .total-control {
            grid-column: span 2;
            background: rgba(255,215,0,0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid rgba(255,215,0,0.3);
        }
        .total-control label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 1.2em;
            color: #ffd700;
        }
        .total-control input {
            width: 100px;
            padding: 10px;
            border: none;
            border-radius: 5px;
            text-align: center;
            font-size: 1.3em;
            background: rgba(255,255,255,0.9);
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .navigation-controls {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        .nav-control {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .nav-control label {
            font-size: 1em;
            font-weight: 500;
        }
        .nav-control input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-left: 10px;
        }
        .nav-control input[type="number"] {
            width: 80px;
            padding: 5px;
            border: none;
            border-radius: 4px;
            text-align: center;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        .main-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
        }
        .btn {
            background: #4ade80;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .btn.primary {
            background: linear-gradient(45deg, #22c55e, #16a34a);
        }
        .btn.secondary {
            background: linear-gradient(45deg, #3b82f6, #2563eb);
        }
        .btn.danger {
            background: linear-gradient(45deg, #ef4444, #dc2626);
        }
        .btn.update {
            background: linear-gradient(45deg, #f59e0b, #d97706);
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 30px;
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
            color: #ffd700;
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
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            display: block;
            color: #4ade80;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
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
            position: relative;
            overflow: hidden;
        }
        .zone-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--zone-color, #4ade80);
        }
        .zone-name {
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .zone-count {
            font-size: 2em;
            color: #4ade80;
            font-weight: bold;
        }
        .zone-target {
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 5px;
        }
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-weight: bold;
            font-size: 1.1em;
        }
        .status.running {
            background: rgba(74, 222, 128, 0.2);
            border: 2px solid #4ade80;
            color: #4ade80;
        }
        .status.stopped {
            background: rgba(239, 68, 68, 0.2);
            border: 2px solid #ef4444;
            color: #ef4444;
        }
        .log {
            background: rgba(0,0,0,0.4);
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .road-map {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 15px;
        }
        .road-intersection {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            grid-template-rows: 1fr 2fr 1fr;
            gap: 5px;
            max-width: 300px;
            margin: 0 auto;
        }
        .road-section {
            background: #444;
            border-radius: 5px;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            position: relative;
        }
        .road-section.north { grid-column: 2; grid-row: 1; }
        .road-section.east { grid-column: 3; grid-row: 2; }
        .road-section.south { grid-column: 2; grid-row: 3; }
        .road-section.west { grid-column: 1; grid-row: 2; }
        .road-section.center { 
            grid-column: 2; 
            grid-row: 2; 
            background: #666;
            border: 2px solid #ffd700;
        }
        .vehicle-count-display {
            position: absolute;
            top: 2px;
            right: 2px;
            background: #4ade80;
            color: white;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: bold;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .pulsing {
            animation: pulse 2s infinite;
        }
        .gradient-text {
            background: linear-gradient(45deg, #ffd700, #ffeb3b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚦 Enhanced Smart Traffic AI System</h1>
            <p class="gradient-text">Manual Vehicle Control & Road Navigation Dashboard</p>
            <div id="current-time" style="font-size: 1.4em; margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; border: 2px solid #ffd700;">Loading...</div>
        </div>

        <div class="controls-section">
            <div class="control-panel">
                <h3 data-icon="🚗">Vehicle Count Controls</h3>
                <div class="vehicle-controls">
                    <div class="direction-control">
                        <label>🔼 North</label>
                        <input type="number" id="north-input" value="0" min="0" max="50">
                    </div>
                    <div class="direction-control">
                        <label>🔽 South</label>
                        <input type="number" id="south-input" value="0" min="0" max="50">
                    </div>
                    <div class="direction-control">
                        <label>◀️ West</label>
                        <input type="number" id="west-input" value="0" min="0" max="50">
                    </div>
                    <div class="direction-control">
                        <label>▶️ East</label>
                        <input type="number" id="east-input" value="0" min="0" max="50">
                    </div>
                    <div class="total-control">
                        <label>🎯 Total Target Vehicles</label>
                        <input type="number" id="total-target" value="50" min="10" max="200">
                    </div>
                </div>
                <button class="btn update" onclick="updateVehicleCounts()">🔄 Update Vehicle Counts</button>
            </div>

            <div class="control-panel">
                <h3 data-icon="🛣️">Road Navigation Settings</h3>
                <div class="navigation-controls">
                    <div class="nav-control">
                        <label>🚨 Emergency Vehicles</label>
                        <input type="checkbox" id="emergency-toggle" checked>
                    </div>
                    <div class="nav-control">
                        <label>🚦 Traffic Light Override</label>
                        <input type="checkbox" id="override-toggle">
                    </div>
                    <div class="nav-control">
                        <label>⚡ Speed Limit (km/h)</label>
                        <input type="number" id="speed-limit" value="50" min="20" max="80">
                    </div>
                    <div class="nav-control">
                        <label>🌧️ Weather Effects</label>
                        <input type="checkbox" id="weather-toggle" checked>
                    </div>
                </div>
                <button class="btn secondary" onclick="updateRoadSettings()">⚙️ Apply Road Settings</button>
            </div>
        </div>

        <div class="controls-section">
            <div class="control-panel" style="grid-column: span 2;">
                <h3 data-icon="🌦️">Weather Control Center</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">🎛️ Weather Mode</label>
                        <div style="display: flex; gap: 10px;">
                            <label style="display: flex; align-items: center; font-size: 0.9em;">
                                <input type="radio" name="weather-mode" value="auto" checked style="margin-right: 5px;"> Auto
                            </label>
                            <label style="display: flex; align-items: center; font-size: 0.9em;">
                                <input type="radio" name="weather-mode" value="manual" style="margin-right: 5px;"> Manual
                            </label>
                        </div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">🌤️ Weather Condition</label>
                        <select id="weather-condition" style="width: 100%; padding: 8px; border: none; border-radius: 5px; background: rgba(255,255,255,0.9); color: #333;">
                            <option value="sunny">☀️ Sunny & Clear</option>
                            <option value="partly_cloudy">⛅ Partly Cloudy</option>
                            <option value="cloudy">☁️ Cloudy</option>
                            <option value="light_rain">🌦️ Light Rain</option>
                            <option value="moderate_rain">🌧️ Moderate Rain</option>
                            <option value="heavy_rain">⛈️ Heavy Rain</option>
                            <option value="thunderstorm">⚡ Thunderstorm</option>
                            <option value="fog">🌫️ Fog</option>
                            <option value="hot_humid">🔥 Hot & Humid</option>
                            <option value="cold">❄️ Cold</option>
                        </select>
                    </div>

                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">🌡️ Temperature (°C)</label>
                        <input type="range" id="temperature-slider" min="10" max="40" value="25" style="width: 100%; margin-bottom: 5px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.8em;">
                            <span>10°C</span>
                            <span id="temp-display">25°C</span>
                            <span>40°C</span>
                        </div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">💧 Humidity (%)</label>
                        <input type="range" id="humidity-slider" min="30" max="95" value="60" style="width: 100%; margin-bottom: 5px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.8em;">
                            <span>30%</span>
                            <span id="humidity-display">60%</span>
                            <span>95%</span>
                        </div>
                    </div>

                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">🌧️ Rain Intensity</label>
                        <select id="rain-intensity" style="width: 100%; padding: 8px; border: none; border-radius: 5px; background: rgba(255,255,255,0.9); color: #333;">
                            <option value="0">No Rain</option>
                            <option value="1">Light Rain (1-5mm/h)</option>
                            <option value="2">Moderate Rain (5-20mm/h)</option>
                            <option value="3">Heavy Rain (20-50mm/h)</option>
                            <option value="4">Very Heavy Rain (>50mm/h)</option>
                        </select>
                    </div>

                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #ffd700;">👁️ Visibility (%)</label>
                        <input type="range" id="visibility-slider" min="20" max="100" value="100" style="width: 100%; margin-bottom: 5px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.8em;">
                            <span>20%</span>
                            <span id="visibility-display">100%</span>
                            <span>100%</span>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: center; gap: 15px;">
                    <button class="btn update" onclick="updateWeatherSettings()" style="background: linear-gradient(45deg, #06b6d4, #0891b2);">🌦️ Apply Weather Settings</button>
                    <button class="btn secondary" onclick="resetWeatherToAuto()" style="background: linear-gradient(45deg, #8b5cf6, #7c3aed);">🔄 Reset to Auto</button>
                </div>

                <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px; font-size: 0.9em;">
                    <div id="weather-effects-info">Weather effects will be applied to traffic speed, visibility, and emergency response times.</div>
                </div>
            </div>
        </div>

        <div class="main-controls">
            <button class="btn primary" onclick="startSimulation()">🚀 Start Simulation</button>
            <button class="btn danger" onclick="stopSimulation()">🛑 Stop Simulation</button>
            <button class="btn secondary" onclick="resetSimulation()">🔄 Reset All</button>
        </div>

        <div id="status" class="status stopped">⏹️ Simulation Stopped</div>

        <div class="dashboard">
            <div class="card">
                <h3 data-icon="📊">Live Traffic Statistics</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="total-vehicles">0</span>
                        <span class="stat-label">Total Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="target-vehicles">50</span>
                        <span class="stat-label">Target Count</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="avg-speed">0</span>
                        <span class="stat-label">Avg Speed (km/h)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="emergency-vehicles">0</span>
                        <span class="stat-label">Emergency Vehicles</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🧭">Vehicle Distribution Map</h3>
                <div class="road-map">
                    <div class="road-intersection">
                        <div class="road-section north">
                            <span>NORTH</span>
                            <div class="vehicle-count-display" id="north-display">0</div>
                        </div>
                        <div class="road-section east">
                            <span>EAST</span>
                            <div class="vehicle-count-display" id="east-display">0</div>
                        </div>
                        <div class="road-section center">🚦</div>
                        <div class="road-section south">
                            <span>SOUTH</span>
                            <div class="vehicle-count-display" id="south-display">0</div>
                        </div>
                        <div class="road-section west">
                            <span>WEST</span>
                            <div class="vehicle-count-display" id="west-display">0</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🚦">AI Traffic Light Control</h3>
                
                <!-- North-South Row -->
                <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="text-align: center; font-weight: bold; color: #ffd700; margin-bottom: 10px;">🔼🔽 NORTH - SOUTH DIRECTION</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                        <div class="stat-item">
                            <span class="stat-value" id="ns-green-time">30</span>
                            <span class="stat-label">🟢 Green (s)</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="ns-red-time">36</span>
                            <span class="stat-label" style="color: #ff6b6b;">🔴 Red (s)</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="ns-yellow-time">3</span>
                            <span class="stat-label" style="color: #ffd93d;">🟡 Yellow (s)</span>
                        </div>
                    </div>
                </div>

                <!-- East-West Row -->
                <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="text-align: center; font-weight: bold; color: #ffd700; margin-bottom: 10px;">◀️▶️ EAST - WEST DIRECTION</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                        <div class="stat-item">
                            <span class="stat-value" id="ew-green-time">30</span>
                            <span class="stat-label">🟢 Green (s)</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="ew-red-time">36</span>
                            <span class="stat-label" style="color: #ff6b6b;">🔴 Red (s)</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="ew-yellow-time">3</span>
                            <span class="stat-label" style="color: #ffd93d;">🟡 Yellow (s)</span>
                        </div>
                    </div>
                </div>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="cycle-time">66</span>
                        <span class="stat-label">⏱️ Total Cycle (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="efficiency-score">0.8</span>
                        <span class="stat-label">📈 Efficiency Score</span>
                    </div>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 5px;">
                    <div id="light-reasoning" style="font-size: 0.9em;">AI calculating optimal timing...</div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="🌦️">Weather Conditions</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="temperature">32</span>
                        <span class="stat-label">Temperature (°C)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="humidity">78</span>
                        <span class="stat-label">Humidity (%)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="weather-condition">Sunny</span>
                        <span class="stat-label">Condition</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="rain-status">No</span>
                        <span class="stat-label">Rain</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 data-icon="📋">System Activity Log</h3>
                <div id="activity-log" class="log">
                    <div>System initialized - Ready for manual control</div>
                    <div>Configure vehicle counts and road settings above</div>
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

        socket.on('settings_updated', function(data) {
            addLogEntry(data.message);
        });

        // Control functions
        function startSimulation() {
            socket.emit('start_simulation');
            addLogEntry('🚀 Starting enhanced simulation with manual controls...');
        }

        function stopSimulation() {
            socket.emit('stop_simulation');
            addLogEntry('🛑 Stopping simulation...');
        }

        function resetSimulation() {
            socket.emit('reset_simulation');
            addLogEntry('🔄 Resetting simulation to default state...');
        }

        function updateVehicleCounts() {
            const counts = {
                north: parseInt(document.getElementById('north-input').value) || 0,
                east: parseInt(document.getElementById('east-input').value) || 0,
                south: parseInt(document.getElementById('south-input').value) || 0,
                west: parseInt(document.getElementById('west-input').value) || 0,
                total_target: parseInt(document.getElementById('total-target').value) || 50
            };

            document.getElementById('target-vehicles').textContent = counts.total_target;
            
            socket.emit('update_vehicle_counts', counts);
            addLogEntry(`🚗 Vehicle counts updated: N:${counts.north}, E:${counts.east}, S:${counts.south}, W:${counts.west}, Target:${counts.total_target}`);
        }

        function updateRoadSettings() {
            const settings = {
                allow_emergency_vehicles: document.getElementById('emergency-toggle').checked,
                traffic_light_override: document.getElementById('override-toggle').checked,
                speed_limit: parseInt(document.getElementById('speed-limit').value) || 50,
                weather_effects: document.getElementById('weather-toggle').checked
            };

            socket.emit('update_road_settings', settings);
            addLogEntry(`🛣️ Road settings updated: Emergency:${settings.allow_emergency_vehicles}, Override:${settings.traffic_light_override}, Speed:${settings.speed_limit}km/h, Weather:${settings.weather_effects}`);
        }

        function updateStatus(running) {
            isRunning = running;
            const statusEl = document.getElementById('status');
            if (running) {
                statusEl.className = 'status running pulsing';
                statusEl.textContent = '▶️ Enhanced Simulation Running';
            } else {
                statusEl.className = 'status stopped';
                statusEl.textContent = '⏹️ Simulation Stopped';
            }
        }

        function updateTrafficStats(stats) {
            document.getElementById('total-vehicles').textContent = stats.total_vehicles;
            document.getElementById('avg-speed').textContent = Math.round(stats.average_speed);
            document.getElementById('emergency-vehicles').textContent = stats.emergency_vehicles;
        }

        function updateZoneCounts(counts) {
            document.getElementById('north-display').textContent = counts.North ? counts.North.total : 0;
            document.getElementById('east-display').textContent = counts.East ? counts.East.total : 0;
            document.getElementById('south-display').textContent = counts.South ? counts.South.total : 0;
            document.getElementById('west-display').textContent = counts.West ? counts.West.total : 0;
        }

        function updateWeatherData(weather) {
            document.getElementById('temperature').textContent = weather.temperature;
            document.getElementById('humidity').textContent = weather.humidity;
            document.getElementById('rain-status').textContent = weather.rain_detected ? 'Yes' : 'No';
            
            let conditionText = 'Sunny';
            if (weather.weather_condition) {
                switch(weather.weather_condition) {
                    case 'hot_humid': conditionText = 'Hot & Humid'; break;
                    case 'thunderstorm': conditionText = 'Thunderstorm'; break;
                    case 'rain': conditionText = 'Rainy'; break;
                    case 'sunny': conditionText = 'Sunny'; break;
                    default: conditionText = weather.weather_condition.charAt(0).toUpperCase() + weather.weather_condition.slice(1);
                }
            }
            document.getElementById('weather-condition').textContent = conditionText;
        }

        function updateTrafficLightPredictions(data) {
            document.getElementById('ns-green-time').textContent = data.north_south_green;
            document.getElementById('ew-green-time').textContent = data.east_west_green;
            document.getElementById('ns-red-time').textContent = data.north_south_red || (data.cycle_time - data.north_south_green - 3);
            document.getElementById('ew-red-time').textContent = data.east_west_red || (data.cycle_time - data.east_west_green - 3);
            document.getElementById('ns-yellow-time').textContent = data.north_south_yellow || 3;
            document.getElementById('ew-yellow-time').textContent = data.east_west_yellow || 3;
            document.getElementById('cycle-time').textContent = data.cycle_time;
            document.getElementById('efficiency-score').textContent = data.efficiency_score.toFixed(2);
            document.getElementById('light-reasoning').textContent = data.reasoning;
        }

        function addLogEntry(message) {
            const log = document.getElementById('activity-log');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.textContent = `[${timestamp}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
            
            // Keep only last 10 entries
            while (log.children.length > 10) {
                log.removeChild(log.firstChild);
            }
        }

        function updateClock() {
            const now = new Date();
            
            // Get Hanoi time (UTC+7)
            const hanoiTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Ho_Chi_Minh"}));
            
            const timeString = hanoiTime.toLocaleTimeString('en-GB', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            
            const dateString = hanoiTime.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            // Get timezone info
            const utcOffset = '+7';
            const timezoneName = 'ICT (Indochina Time)';
            
            document.getElementById('current-time').innerHTML = `
                <div style="font-size: 1.6em; font-weight: bold; color: #ffd700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    🕐 ${timeString}
                </div>
                <div style="font-size: 1.1em; margin-top: 5px; color: #ffffff;">
                    📅 ${dateString}
                </div>
                <div style="font-size: 0.9em; margin-top: 5px; color: #ffd700; font-weight: bold;">
                    🌏 Hanoi, Vietnam (UTC${utcOffset}) • ${timezoneName}
                </div>
            `;
        }

        // Initialize
        updateClock();
        setInterval(updateClock, 1000);
        
        addLogEntry('🌐 Connected to enhanced control server');
        socket.emit('get_status');
        
        // Weather control functions
        function updateWeatherSettings() {
            const weatherMode = document.querySelector('input[name="weather-mode"]:checked').value;
            const settings = {
                manual_control: weatherMode === 'manual',
                condition: document.getElementById('weather-condition').value,
                temperature: parseInt(document.getElementById('temperature-slider').value),
                humidity: parseInt(document.getElementById('humidity-slider').value),
                rain_intensity: parseInt(document.getElementById('rain-intensity').value),
                visibility: parseInt(document.getElementById('visibility-slider').value)
            };

            socket.emit('update_weather_settings', settings);
            
            const conditionName = document.getElementById('weather-condition').selectedOptions[0].text;
            addLogEntry(`🌦️ Weather updated: ${conditionName}, ${settings.temperature}°C, ${settings.humidity}% humidity`);
            
            updateWeatherEffectsInfo(settings);
        }

        function resetWeatherToAuto() {
            document.querySelector('input[name="weather-mode"][value="auto"]').checked = true;
            document.getElementById('weather-condition').value = 'sunny';
            document.getElementById('temperature-slider').value = 25;
            document.getElementById('humidity-slider').value = 60;
            document.getElementById('rain-intensity').value = 0;
            document.getElementById('visibility-slider').value = 100;
            
            updateSliderDisplays();
            
            socket.emit('update_weather_settings', {
                manual_control: false,
                condition: 'sunny',
                temperature: 25,
                humidity: 60,
                rain_intensity: 0,
                visibility: 100
            });
            
            addLogEntry('🔄 Weather control reset to automatic mode');
            document.getElementById('weather-effects-info').textContent = 'Weather effects will be applied automatically based on simulation.';
        }

        function updateSliderDisplays() {
            document.getElementById('temp-display').textContent = document.getElementById('temperature-slider').value + '°C';
            document.getElementById('humidity-display').textContent = document.getElementById('humidity-slider').value + '%';
            document.getElementById('visibility-display').textContent = document.getElementById('visibility-slider').value + '%';
        }

        function updateWeatherEffectsInfo(settings) {
            let effects = [];
            
            if (settings.rain_intensity > 0) {
                effects.push('Reduced visibility and speed');
                if (settings.rain_intensity >= 3) effects.push('Emergency response slower');
            }
            
            if (settings.visibility < 80) {
                effects.push('Poor visibility conditions');
            }
            
            if (settings.temperature > 35) {
                effects.push('High heat affecting vehicle performance');
            } else if (settings.temperature < 15) {
                effects.push('Cold weather affecting traffic flow');
            }
            
            if (settings.condition === 'fog') {
                effects.push('Fog reducing visibility and speeds');
            } else if (settings.condition === 'thunderstorm') {
                effects.push('Severe weather - major traffic disruption');
            }
            
            const effectsText = effects.length > 0 ? 
                `Active effects: ${effects.join(', ')}.` : 
                'No significant weather effects on traffic.';
            
            document.getElementById('weather-effects-info').textContent = effectsText;
        }

        // Auto-update slider displays
        document.getElementById('temperature-slider').addEventListener('input', updateSliderDisplays);
        document.getElementById('humidity-slider').addEventListener('input', updateSliderDisplays);
        document.getElementById('visibility-slider').addEventListener('input', updateSliderDisplays);

        // Auto-update weather effects info when condition changes
        document.getElementById('weather-condition').addEventListener('change', function() {
            if (document.querySelector('input[name="weather-mode"]:checked').value === 'manual') {
                const settings = {
                    manual_control: true,
                    condition: this.value,
                    temperature: parseInt(document.getElementById('temperature-slider').value),
                    humidity: parseInt(document.getElementById('humidity-slider').value),
                    rain_intensity: parseInt(document.getElementById('rain-intensity').value),
                    visibility: parseInt(document.getElementById('visibility-slider').value)
                };
                updateWeatherEffectsInfo(settings);
            }
        });

        // Auto-update total when individual counts change
        ['north-input', 'east-input', 'south-input', 'west-input'].forEach(id => {
            document.getElementById(id).addEventListener('input', function() {
                const total = ['north-input', 'east-input', 'south-input', 'west-input']
                    .reduce((sum, inputId) => sum + (parseInt(document.getElementById(inputId).value) || 0), 0);
                document.getElementById('total-target').value = Math.max(total, 10);
            });
        });

        // Initialize slider displays
        updateSliderDisplays();
    </script>
</body>
</html>
    '''

# Enhanced socket handlers with manual controls
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Enhanced client connected: {datetime.now()}")
    emit('activity_log', {'message': 'Connected to enhanced traffic control system'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Enhanced client disconnected: {datetime.now()}")

@socketio.on('start_simulation')
def handle_start_simulation():
    """Start the enhanced traffic simulation"""
    global simulation_running
    if not simulation_running:
        simulation_running = True
        emit('simulation_status', {'running': True}, broadcast=True)
        emit('activity_log', {'message': '✅ Enhanced simulation started with manual controls'}, broadcast=True)
        # Start enhanced simulation thread
        simulation_thread = threading.Thread(target=enhanced_simulation_loop, daemon=True)
        simulation_thread.start()

@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop the traffic simulation"""
    global simulation_running
    simulation_running = False
    emit('simulation_status', {'running': False}, broadcast=True)
    emit('activity_log', {'message': '🛑 Enhanced simulation stopped'}, broadcast=True)

@socketio.on('reset_simulation')
def handle_reset_simulation():
    """Reset simulation to default state"""
    global manual_vehicle_counts, road_navigation_settings, simulation_running
    
    # Stop simulation first
    simulation_running = False
    
    # Reset manual controls
    manual_vehicle_counts = {
        'north': 0,
        'south': 0,
        'east': 0,
        'west': 0,
        'total_target': 50
    }
    
    road_navigation_settings = {
        'allow_emergency_vehicles': True,
        'traffic_light_override': False,
        'speed_limit': 50,
        'weather_effects': True
    }
    
    # Clear vehicles
    traffic_sim.vehicles = []
    traffic_sim.vehicle_counter = 0
    
    emit('simulation_status', {'running': False}, broadcast=True)
    emit('activity_log', {'message': '🔄 Simulation reset to default state'}, broadcast=True)

@socketio.on('update_vehicle_counts')
def handle_update_vehicle_counts(data):
    """Update manual vehicle count settings"""
    global manual_vehicle_counts
    
    manual_vehicle_counts.update(data)
    
    # Apply vehicle count changes to simulator
    apply_manual_vehicle_counts()
    
    emit('settings_updated', {
        'message': f'Vehicle counts updated: Total target {data.get("total_target", 50)}'
    }, broadcast=True)

@socketio.on('update_road_settings')
def handle_update_road_settings(data):
    """Update road navigation settings"""
    global road_navigation_settings
    
    road_navigation_settings.update(data)
    
    # Apply settings to simulator
    apply_road_navigation_settings()
    
    emit('settings_updated', {
        'message': f'Road settings updated: Speed limit {data.get("speed_limit", 50)} km/h'
    }, broadcast=True)

@socketio.on('update_weather_settings')
def handle_update_weather_settings(data):
    """Update manual weather settings"""
    global manual_weather_settings
    
    manual_weather_settings.update(data)
    
    # Apply weather settings to simulator
    apply_manual_weather_settings()
    
    condition_name = data.get('condition', 'sunny').replace('_', ' ').title()
    emit('settings_updated', {
        'message': f'Weather updated: {condition_name}, {data.get("temperature", 25)}°C'
    }, broadcast=True)

@socketio.on('get_status')
def handle_get_status():
    """Get current simulation status"""
    emit('simulation_status', {'running': simulation_running})

def apply_manual_vehicle_counts():
    """Apply manual vehicle count settings to the simulator"""
    global manual_vehicle_counts, traffic_sim
    
    target_total = manual_vehicle_counts.get('total_target', 50)
    
    # Update traffic simulator's maximum vehicle settings
    current_pattern = traffic_sim.get_current_traffic_pattern()
    current_pattern['max_vehicles'] = target_total
    
    # Force vehicle generation to meet targets if simulation is running
    if simulation_running:
        current_total = len(traffic_sim.vehicles)
        
        # If we're significantly below target, generate vehicles more aggressively
        if current_total < target_total * 0.8:
            # Generate additional vehicles for each direction based on manual settings
            for direction in ['north', 'south', 'east', 'west']:
                target_for_direction = manual_vehicle_counts.get(direction, 0)
                
                # Count current vehicles in this direction
                current_in_direction = sum(1 for v in traffic_sim.vehicles if v.direction == direction)
                
                # Generate additional vehicles if needed
                needed = max(0, target_for_direction - current_in_direction)
                for _ in range(min(needed, 5)):  # Generate up to 5 at a time to avoid flooding
                    if len(traffic_sim.vehicles) < target_total:
                        new_vehicle = traffic_sim.generate_vehicle(direction)
                        traffic_sim.vehicles.append(new_vehicle)

def apply_road_navigation_settings():
    """Apply road navigation settings to the simulator"""
    global road_navigation_settings, traffic_sim
    
    # Update vehicle probabilities based on emergency vehicle setting
    if road_navigation_settings.get('allow_emergency_vehicles', True):
        traffic_sim.vehicle_probabilities['emergency'] = 0.005  # 0.5% chance
    else:
        traffic_sim.vehicle_probabilities['emergency'] = 0.0  # No emergency vehicles
    
    # Update speed ranges based on speed limit
    speed_limit = road_navigation_settings.get('speed_limit', 50)
    for vehicle_type in traffic_sim.speed_ranges:
        current_min, current_max = traffic_sim.speed_ranges[vehicle_type]
        # Adjust max speed based on speed limit, keeping proportions
        adjustment_factor = speed_limit / 50  # 50 is default speed limit
        traffic_sim.speed_ranges[vehicle_type] = (
            current_min * adjustment_factor,
            min(current_max * adjustment_factor, speed_limit)
        )

def apply_manual_weather_settings():
    """Apply manual weather settings to affect traffic behavior"""
    global manual_weather_settings, traffic_sim
    
    if not manual_weather_settings.get('manual_control', False):
        return  # Use automatic weather
    
    # Get weather settings
    condition = manual_weather_settings.get('condition', 'sunny')
    temperature = manual_weather_settings.get('temperature', 25)
    rain_intensity = manual_weather_settings.get('rain_intensity', 0)
    visibility = manual_weather_settings.get('visibility', 100)
    
    # Apply speed adjustments based on weather conditions
    weather_speed_factor = 1.0
    
    # Rain effects on speed
    if rain_intensity > 0:
        rain_factors = {1: 0.9, 2: 0.8, 3: 0.65, 4: 0.5}
        weather_speed_factor *= rain_factors.get(rain_intensity, 0.5)
    
    # Visibility effects
    if visibility < 100:
        visibility_factor = max(0.5, visibility / 100)
        weather_speed_factor *= visibility_factor
    
    # Temperature effects
    if temperature > 35:  # Very hot
        weather_speed_factor *= 0.95
    elif temperature < 10:  # Very cold
        weather_speed_factor *= 0.9
    
    # Condition-specific effects
    condition_factors = {
        'fog': 0.6,
        'thunderstorm': 0.5,
        'heavy_rain': 0.65,
        'moderate_rain': 0.8,
        'light_rain': 0.9,
        'cloudy': 0.98,
        'partly_cloudy': 0.99,
        'sunny': 1.0,
        'hot_humid': 0.95,
        'cold': 0.9
    }
    weather_speed_factor *= condition_factors.get(condition, 1.0)
    
    # Apply speed adjustments to all vehicle types
    base_speed_limit = road_navigation_settings.get('speed_limit', 50)
    for vehicle_type in traffic_sim.speed_ranges:
        base_min, base_max = traffic_sim.speed_ranges[vehicle_type]
        adjusted_max = min(base_max * weather_speed_factor, base_speed_limit * weather_speed_factor)
        adjusted_min = min(base_min * weather_speed_factor, adjusted_max * 0.8)
        traffic_sim.speed_ranges[vehicle_type] = (adjusted_min, adjusted_max)

def get_manual_weather_data():
    """Generate weather data from manual settings"""
    global manual_weather_settings
    
    if not manual_weather_settings.get('manual_control', False):
        return None
    
    condition = manual_weather_settings.get('condition', 'sunny')
    temperature = manual_weather_settings.get('temperature', 25)
    humidity = manual_weather_settings.get('humidity', 60)
    rain_intensity = manual_weather_settings.get('rain_intensity', 0)
    
    # Determine rain status based on condition and intensity
    rain_detected = rain_intensity > 0 or 'rain' in condition or condition == 'thunderstorm'
    
    # Map condition to weather_condition format
    weather_condition_map = {
        'sunny': 'sunny',
        'partly_cloudy': 'sunny',
        'cloudy': 'sunny',
        'light_rain': 'rain',
        'moderate_rain': 'rain',
        'heavy_rain': 'rain',
        'thunderstorm': 'thunderstorm',
        'fog': 'rain',  # Treat fog as poor visibility condition
        'hot_humid': 'hot_humid',
        'cold': 'sunny'  # Cold but clear
    }
    
    return {
        'temperature': temperature,
        'humidity': humidity,
        'rain_detected': rain_detected,
        'weather_condition': weather_condition_map.get(condition, 'sunny'),
        'manual_control': True,
        'condition_name': condition
    }

def enhanced_simulation_loop():
    """Enhanced simulation loop with manual controls"""
    global simulation_running
    
    while simulation_running:
        try:
            # Apply manual settings continuously
            apply_manual_vehicle_counts()
            apply_road_navigation_settings()
            
            # Update traffic simulation
            traffic_sim.update_simulation(1.0)
            
            # Get current data
            stats = traffic_sim.get_traffic_statistics()
            zone_counts = traffic_sim.get_vehicle_counts_by_zone()
            
            # Apply weather effects if enabled
            if road_navigation_settings.get('weather_effects', True):
                # Check if manual weather control is enabled
                manual_weather = get_manual_weather_data()
                if manual_weather:
                    # Use manual weather settings
                    weather = manual_weather
                    # Apply manual weather effects to traffic
                    apply_manual_weather_settings()
                else:
                    # Use automatic weather simulation
                    weather = weather_sim.update_weather()
            else:
                # Use default good weather
                weather = {
                    'temperature': 25,
                    'humidity': 60,
                    'rain_detected': False,
                    'weather_condition': 'sunny'
                }
            
            # Calculate optimal traffic light timing
            vehicle_counts_dict = {
                'North': zone_counts.get('North', {}).get('total', 0),
                'South': zone_counts.get('South', {}).get('total', 0),
                'East': zone_counts.get('East', {}).get('total', 0),
                'West': zone_counts.get('West', {}).get('total', 0)
            }
            
            # Check for emergency vehicles
            emergency_count = stats.get('by_type', {}).get('emergency', 0)
            
            # Override traffic light timing if enabled
            if road_navigation_settings.get('traffic_light_override', False):
                # Use manual override - equal timing
                traffic_phase_data = {
                    'north_south_green': 30,
                    'east_west_green': 30,
                    'north_south_red': 33,
                    'east_west_red': 33,
                    'north_south_yellow': 3,
                    'east_west_yellow': 3,
                    'cycle_time': 66,
                    'efficiency_score': 0.75,
                    'reasoning': 'Manual override - Equal timing for all directions'
                }
            else:
                # Use AI optimization
                weather_condition = 'rain' if weather.get('rain_detected', False) else 'normal'
                traffic_phase = traffic_optimizer.predict_optimal_timing(
                    vehicle_counts_dict, 
                    emergency_count, 
                    weather_condition
                )
                
                traffic_phase_data = {
                    'north_south_green': traffic_phase.north_south_timing.green_duration,
                    'east_west_green': traffic_phase.east_west_timing.green_duration,
                    'north_south_red': traffic_phase.north_south_timing.red_duration,
                    'east_west_red': traffic_phase.east_west_timing.red_duration,
                    'north_south_yellow': traffic_phase.north_south_timing.yellow_duration,
                    'east_west_yellow': traffic_phase.east_west_timing.yellow_duration,
                    'cycle_time': traffic_phase.total_cycle_time,
                    'efficiency_score': traffic_phase.efficiency_score,
                    'reasoning': traffic_phase.north_south_timing.reasoning
                }
            
            # Emit updates to all connected clients
            socketio.emit('traffic_update', {
                'stats': stats,
                'zone_counts': zone_counts
            })
            
            socketio.emit('weather_update', weather)
            socketio.emit('traffic_light_update', traffic_phase_data)
            
            # Log periodic updates with manual control info
            if int(time.time()) % 15 == 0:  # Every 15 seconds
                total_target = manual_vehicle_counts.get('total_target', 50)
                current_total = stats["total_vehicles"]
                socketio.emit('activity_log', {
                    'message': f'📊 Manual control: {current_total}/{total_target} vehicles, Speed limit: {road_navigation_settings.get("speed_limit", 50)}km/h'
                })
            
            time.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            print(f"Enhanced simulation error: {e}")
            socketio.emit('activity_log', {
                'message': f'⚠️ Enhanced simulation error: {str(e)}'
            })
            time.sleep(5)

# API endpoints remain the same but with enhanced data
@app.route('/api/status')
def api_status():
    """Enhanced API endpoint for system status"""
    return jsonify({
        'status': 'running' if simulation_running else 'stopped',
        'timestamp': datetime.now().isoformat(),
        'system': 'Enhanced Smart Traffic AI System',
        'version': '2.0.0',
        'manual_controls': {
            'vehicle_counts': manual_vehicle_counts,
            'road_settings': road_navigation_settings
        }
    })

@app.route('/api/manual-controls')
def api_manual_controls():
    """API endpoint for manual control settings"""
    return jsonify({
        'vehicle_counts': manual_vehicle_counts,
        'road_navigation': road_navigation_settings,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚦 Enhanced Smart Traffic AI System - Manual Control Dashboard")
    print("=" * 60)
    print("🌐 Starting enhanced web server...")
    print("📊 Dashboard: http://localhost:5000")
    print("🎮 Manual Controls: Vehicle counts & road navigation")
    print("🔧 Press Ctrl+C to stop")
    print()
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down enhanced system...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        simulation_running = False
        print("👋 Enhanced Smart Traffic AI System stopped")
