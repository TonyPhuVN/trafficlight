-- Smart Traffic AI System Database Schema
-- Lược đồ cơ sở dữ liệu cho hệ thống AI điều khiển giao thông

-- Intersections table - Thông tin giao lộ
CREATE TABLE IF NOT EXISTS intersections (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    type VARCHAR(20) DEFAULT 'standard', -- standard, highway, pedestrian
    status VARCHAR(20) DEFAULT 'active', -- active, maintenance, disabled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Traffic lights table - Thông tin đèn giao thông
CREATE TABLE IF NOT EXISTS traffic_lights (
    id VARCHAR(50) PRIMARY KEY,
    intersection_id VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL, -- north, south, east, west
    current_state VARCHAR(10) DEFAULT 'red', -- red, yellow, green
    last_change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hardware_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'operational',
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Vehicle detections table - Dữ liệu phát hiện xe
CREATE TABLE IF NOT EXISTS vehicle_detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vehicle_type VARCHAR(20) NOT NULL, -- car, truck, bus, motorcycle, bicycle, emergency
    direction VARCHAR(20) NOT NULL,
    confidence REAL NOT NULL,
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    speed REAL DEFAULT 0,
    is_emergency_vehicle BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Traffic flow analytics - Phân tích luồng giao thông
CREATE TABLE IF NOT EXISTS traffic_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vehicle_count INTEGER DEFAULT 0,
    average_speed REAL DEFAULT 0,
    density_level VARCHAR(20) DEFAULT 'low', -- low, medium, high, congested
    waiting_time_avg REAL DEFAULT 0,
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Light timing history - Lịch sử thời gian đèn
CREATE TABLE IF NOT EXISTS light_timing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    state VARCHAR(10) NOT NULL, -- red, yellow, green
    duration INTEGER NOT NULL, -- seconds
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(50) DEFAULT 'scheduled', -- scheduled, emergency, adaptive, manual
    vehicle_count_before INTEGER DEFAULT 0,
    vehicle_count_after INTEGER DEFAULT 0,
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Sensor data table - Dữ liệu cảm biến
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(30) NOT NULL, -- ultrasonic, radar, pressure, environmental
    value REAL NOT NULL,
    unit VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(50),
    metadata TEXT, -- JSON data for additional information
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Weather conditions - Điều kiện thời tiết
CREATE TABLE IF NOT EXISTS weather_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity REAL,
    light_level REAL,
    rain_detected BOOLEAN DEFAULT FALSE,
    visibility VARCHAR(20) DEFAULT 'good', -- good, poor, very_poor
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- System performance metrics - Chỉ số hiệu suất hệ thống
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_processing_time REAL, -- milliseconds
    detection_accuracy REAL,
    system_uptime INTEGER, -- seconds
    camera_status VARCHAR(20) DEFAULT 'online',
    sensor_status VARCHAR(20) DEFAULT 'online',
    light_controller_status VARCHAR(20) DEFAULT 'online',
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Emergency events - Sự kiện khẩn cấp
CREATE TABLE IF NOT EXISTS emergency_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(30) NOT NULL, -- emergency_vehicle, accident, maintenance
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER, -- seconds
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- System alerts - Cảnh báo hệ thống
CREATE TABLE IF NOT EXISTS system_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(30) NOT NULL, -- hardware_failure, network_issue, performance_degradation
    severity VARCHAR(10) NOT NULL, -- low, medium, high, critical
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Traffic optimization results - Kết quả tối ưu giao thông
CREATE TABLE IF NOT EXISTS optimization_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm VARCHAR(30) NOT NULL,
    total_wait_time_before REAL, -- seconds
    total_wait_time_after REAL, -- seconds
    improvement_percentage REAL,
    vehicles_processed INTEGER,
    optimization_duration REAL, -- milliseconds
    FOREIGN KEY (intersection_id) REFERENCES intersections(id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vehicle_detections_timestamp ON vehicle_detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_vehicle_detections_intersection ON vehicle_detections(intersection_id);
CREATE INDEX IF NOT EXISTS idx_traffic_flow_timestamp ON traffic_flow(timestamp);
CREATE INDEX IF NOT EXISTS idx_traffic_flow_intersection ON traffic_flow(intersection_id);
CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensor_data_intersection ON sensor_data(intersection_id);
CREATE INDEX IF NOT EXISTS idx_light_timing_timestamp ON light_timing_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp);

-- Views for common queries
CREATE VIEW IF NOT EXISTS current_traffic_status AS
SELECT 
    i.id as intersection_id,
    i.name as intersection_name,
    tl.direction,
    tl.current_state,
    tl.last_change_time,
    COALESCE(tf.vehicle_count, 0) as current_vehicle_count,
    COALESCE(tf.density_level, 'unknown') as density_level,
    COALESCE(tf.average_speed, 0) as average_speed
FROM intersections i
LEFT JOIN traffic_lights tl ON i.id = tl.intersection_id
LEFT JOIN traffic_flow tf ON i.id = tf.intersection_id 
    AND tf.timestamp = (
        SELECT MAX(timestamp) 
        FROM traffic_flow 
        WHERE intersection_id = i.id AND direction = tl.direction
    )
ORDER BY i.id, tl.direction;

CREATE VIEW IF NOT EXISTS daily_traffic_summary AS
SELECT 
    intersection_id,
    DATE(timestamp) as date,
    direction,
    SUM(vehicle_count) as total_vehicles,
    AVG(average_speed) as avg_speed,
    MAX(vehicle_count) as peak_count,
    MIN(vehicle_count) as min_count
FROM traffic_flow
GROUP BY intersection_id, DATE(timestamp), direction
ORDER BY date DESC, intersection_id, direction;

-- Insert sample data
INSERT OR IGNORE INTO intersections (id, name, location, latitude, longitude, type) VALUES
('INT001', 'Ngã tư Láng Hạ - Thái Hà', 'Hà Nội', 21.0285, 105.8542, 'busy_intersection'),
('INT002', 'Ngã tư Hoàng Hoa Thám - Đội Cấn', 'Hà Nội', 21.0370, 105.8320, 'standard'),
('INT003', 'Ngã tư Cầu Giấy', 'Hà Nội', 21.0370, 105.7990, 'highway_intersection');

INSERT OR IGNORE INTO traffic_lights (id, intersection_id, direction, hardware_id) VALUES
('TL001_N', 'INT001', 'north', 'HW_001_N'),
('TL001_S', 'INT001', 'south', 'HW_001_S'),
('TL001_E', 'INT001', 'east', 'HW_001_E'),
('TL001_W', 'INT001', 'west', 'HW_001_W'),
('TL002_N', 'INT002', 'north', 'HW_002_N'),
('TL002_S', 'INT002', 'south', 'HW_002_S'),
('TL002_E', 'INT002', 'east', 'HW_002_E'),
('TL002_W', 'INT002', 'west', 'HW_002_W');
