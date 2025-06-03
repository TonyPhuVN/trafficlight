"""
Database Management System for Smart Traffic AI
Handles data storage, analytics, and reporting for traffic monitoring system
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import threading
from contextlib import contextmanager

class TrafficDatabase:
    """Main database manager for traffic system data"""
    
    def __init__(self, db_path: str = "data/traffic_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
        # Initialize database tables
        self._initialize_database()
        
        logging.info(f"Traffic database initialized at {self.db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Vehicle detection records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intersection_id TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    vehicle_count INTEGER NOT NULL,
                    vehicle_types TEXT,  -- JSON array of detected vehicle types
                    detection_method TEXT,  -- 'camera', 'sensor', 'radar'
                    timestamp DATETIME NOT NULL,
                    confidence_score REAL,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Traffic light states
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_light_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intersection_id TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    state TEXT NOT NULL,  -- 'red', 'yellow', 'green'
                    duration INTEGER,  -- Duration in seconds
                    control_mode TEXT,  -- 'auto', 'manual', 'emergency'
                    timestamp DATETIME NOT NULL,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Sensor readings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    intersection_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    location TEXT,
                    timestamp DATETIME NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # System events and alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,  -- 'alert', 'error', 'maintenance', 'emergency'
                    severity TEXT NOT NULL,    -- 'low', 'medium', 'high', 'critical'
                    intersection_id TEXT,
                    component TEXT,            -- 'camera', 'sensor', 'ai_engine', 'traffic_light'
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Traffic predictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intersection_id TEXT NOT NULL,
                    prediction_horizon TEXT,  -- 'short_term', 'medium_term', 'long_term'
                    predicted_volume INTEGER,
                    predicted_peak_time DATETIME,
                    confidence_score REAL,
                    model_version TEXT,
                    timestamp DATETIME NOT NULL,
                    actual_volume INTEGER,     -- Filled later for accuracy tracking
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intersection_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,  -- 'wait_time', 'throughput', 'efficiency'
                    value REAL NOT NULL,
                    unit TEXT,
                    calculation_period INTEGER,  -- Period in minutes
                    timestamp DATETIME NOT NULL,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Daily summaries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    intersection_id TEXT NOT NULL,
                    total_vehicles INTEGER,
                    peak_hour_start TIME,
                    peak_hour_end TIME,
                    average_wait_time REAL,
                    efficiency_score REAL,
                    incidents_count INTEGER,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_detections_timestamp ON vehicle_detections(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_detections_intersection ON vehicle_detections(intersection_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_intersection ON sensor_readings(intersection_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_summaries_date ON daily_summaries(date)")
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic closing"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()
    
    def record_vehicle_detection(self, intersection_id: str, direction: str, 
                               vehicle_count: int, vehicle_types: List[str] = None,
                               detection_method: str = 'camera', confidence: float = 1.0,
                               metadata: Dict[str, Any] = None):
        """Record vehicle detection data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicle_detections 
                (intersection_id, direction, vehicle_count, vehicle_types, detection_method, 
                 timestamp, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intersection_id, direction, vehicle_count,
                json.dumps(vehicle_types) if vehicle_types else None,
                detection_method, datetime.now(), confidence,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def record_traffic_light_state(self, intersection_id: str, direction: str,
                                 state: str, duration: int = None,
                                 control_mode: str = 'auto', metadata: Dict[str, Any] = None):
        """Record traffic light state change"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO traffic_light_states 
                (intersection_id, direction, state, duration, control_mode, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                intersection_id, direction, state, duration, control_mode,
                datetime.now(), json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def record_sensor_reading(self, sensor_id: str, sensor_type: str,
                            intersection_id: str, value: float, unit: str = None,
                            location: str = None, confidence: float = 1.0,
                            metadata: Dict[str, Any] = None):
        """Record sensor reading"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_readings 
                (sensor_id, sensor_type, intersection_id, value, unit, location, 
                 timestamp, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sensor_id, sensor_type, intersection_id, value, unit, location,
                datetime.now(), confidence, json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def record_system_event(self, event_type: str, severity: str, message: str,
                          intersection_id: str = None, component: str = None,
                          metadata: Dict[str, Any] = None):
        """Record system event or alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_events 
                (event_type, severity, intersection_id, component, message, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type, severity, intersection_id, component, message,
                datetime.now(), json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def record_traffic_prediction(self, intersection_id: str, horizon: str,
                                predicted_volume: int, predicted_peak_time: datetime = None,
                                confidence: float = 1.0, model_version: str = "v1.0",
                                metadata: Dict[str, Any] = None):
        """Record traffic prediction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO traffic_predictions 
                (intersection_id, prediction_horizon, predicted_volume, predicted_peak_time,
                 confidence_score, model_version, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intersection_id, horizon, predicted_volume, predicted_peak_time,
                confidence, model_version, datetime.now(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def record_performance_metric(self, intersection_id: str, metric_type: str,
                                value: float, unit: str = None, period: int = 60,
                                metadata: Dict[str, Any] = None):
        """Record performance metric"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics 
                (intersection_id, metric_type, value, unit, calculation_period, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                intersection_id, metric_type, value, unit, period,
                datetime.now(), json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def get_recent_vehicle_counts(self, intersection_id: str = None, 
                                hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent vehicle detection counts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT intersection_id, direction, vehicle_count, timestamp, 
                       detection_method, confidence_score
                FROM vehicle_detections 
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(hours)
            
            params = []
            if intersection_id:
                query += " AND intersection_id = ?"
                params.append(intersection_id)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_traffic_patterns(self, intersection_id: str, days: int = 7) -> Dict[str, Any]:
        """Analyze traffic patterns for an intersection"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get hourly traffic counts
            cursor.execute("""
                SELECT 
                    strftime('%H', timestamp) as hour,
                    SUM(vehicle_count) as total_vehicles,
                    COUNT(*) as detection_count
                FROM vehicle_detections 
                WHERE intersection_id = ? 
                AND timestamp >= datetime('now', '-{} days')
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """.format(days), (intersection_id,))
            
            hourly_data = [dict(row) for row in cursor.fetchall()]
            
            # Get daily totals
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(vehicle_count) as total_vehicles
                FROM vehicle_detections 
                WHERE intersection_id = ? 
                AND timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """.format(days), (intersection_id,))
            
            daily_data = [dict(row) for row in cursor.fetchall()]
            
            # Calculate statistics
            total_vehicles = sum(day['total_vehicles'] for day in daily_data)
            avg_daily_vehicles = total_vehicles / len(daily_data) if daily_data else 0
            
            # Find peak hours
            peak_hour = max(hourly_data, key=lambda x: x['total_vehicles']) if hourly_data else None
            
            return {
                'intersection_id': intersection_id,
                'analysis_period_days': days,
                'total_vehicles': total_vehicles,
                'average_daily_vehicles': avg_daily_vehicles,
                'peak_hour': peak_hour,
                'hourly_patterns': hourly_data,
                'daily_totals': daily_data
            }
    
    def get_system_alerts(self, hours: int = 24, severity: str = None) -> List[Dict[str, Any]]:
        """Get recent system alerts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM system_events 
                WHERE timestamp >= datetime('now', '-{} hours')
                AND event_type IN ('alert', 'error', 'emergency')
            """.format(hours)
            
            params = []
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_performance_metrics(self, intersection_id: str = None, 
                              hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    intersection_id,
                    metric_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as sample_count,
                    unit
                FROM performance_metrics 
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(hours)
            
            params = []
            if intersection_id:
                query += " AND intersection_id = ?"
                params.append(intersection_id)
            
            query += " GROUP BY intersection_id, metric_type"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = {}
            for row in rows:
                row_dict = dict(row)
                intersection = row_dict['intersection_id']
                metric_type = row_dict['metric_type']
                
                if intersection not in metrics:
                    metrics[intersection] = {}
                
                metrics[intersection][metric_type] = {
                    'average': row_dict['avg_value'],
                    'minimum': row_dict['min_value'],
                    'maximum': row_dict['max_value'],
                    'sample_count': row_dict['sample_count'],
                    'unit': row_dict['unit']
                }
            
            return metrics
    
    def generate_daily_summary(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily summary report"""
        if date is None:
            date = datetime.now().date()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get traffic data for the day
            cursor.execute("""
                SELECT 
                    intersection_id,
                    SUM(vehicle_count) as total_vehicles,
                    COUNT(*) as detection_count
                FROM vehicle_detections 
                WHERE DATE(timestamp) = ?
                GROUP BY intersection_id
            """, (date,))
            
            traffic_data = [dict(row) for row in cursor.fetchall()]
            
            # Get alerts for the day
            cursor.execute("""
                SELECT 
                    intersection_id,
                    severity,
                    COUNT(*) as alert_count
                FROM system_events 
                WHERE DATE(timestamp) = ? AND event_type IN ('alert', 'error', 'emergency')
                GROUP BY intersection_id, severity
            """, (date,))
            
            alert_data = [dict(row) for row in cursor.fetchall()]
            
            # Calculate totals
            total_vehicles = sum(item['total_vehicles'] for item in traffic_data)
            total_alerts = sum(item['alert_count'] for item in alert_data)
            
            return {
                'date': date.isoformat(),
                'total_vehicles_city_wide': total_vehicles,
                'total_alerts': total_alerts,
                'intersection_data': traffic_data,
                'alert_breakdown': alert_data,
                'active_intersections': len(traffic_data)
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to manage database size"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            tables_to_clean = [
                'vehicle_detections',
                'traffic_light_states', 
                'sensor_readings',
                'traffic_predictions',
                'performance_metrics'
            ]
            
            cleaned_records = 0
            for table in tables_to_clean:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff_date,))
                cleaned_records += cursor.rowcount
            
            # Keep system events longer (6 months)
            event_cutoff = datetime.now() - timedelta(days=180)
            cursor.execute("DELETE FROM system_events WHERE timestamp < ? AND resolved = TRUE", 
                         (event_cutoff,))
            cleaned_records += cursor.rowcount
            
            conn.commit()
            
            logging.info(f"Cleaned up {cleaned_records} old records from database")
    
    def export_data(self, start_date: datetime, end_date: datetime, 
                   output_format: str = 'csv') -> str:
        """Export data for external analysis"""
        with self.get_connection() as conn:
            
            # Export vehicle detections
            vehicle_df = pd.read_sql_query("""
                SELECT * FROM vehicle_detections 
                WHERE timestamp BETWEEN ? AND ?
            """, conn, params=(start_date, end_date))
            
            # Export sensor readings
            sensor_df = pd.read_sql_query("""
                SELECT * FROM sensor_readings 
                WHERE timestamp BETWEEN ? AND ?
            """, conn, params=(start_date, end_date))
            
            # Export performance metrics
            metrics_df = pd.read_sql_query("""
                SELECT * FROM performance_metrics 
                WHERE timestamp BETWEEN ? AND ?
            """, conn, params=(start_date, end_date))
            
            # Save to files
            export_dir = Path("data/exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format == 'csv':
                vehicle_file = export_dir / f"vehicle_detections_{timestamp}.csv"
                sensor_file = export_dir / f"sensor_readings_{timestamp}.csv"
                metrics_file = export_dir / f"performance_metrics_{timestamp}.csv"
                
                vehicle_df.to_csv(vehicle_file, index=False)
                sensor_df.to_csv(sensor_file, index=False)
                metrics_df.to_csv(metrics_file, index=False)
                
                return str(export_dir)
            
            elif output_format == 'json':
                export_data = {
                    'vehicle_detections': vehicle_df.to_dict('records'),
                    'sensor_readings': sensor_df.to_dict('records'),
                    'performance_metrics': metrics_df.to_dict('records'),
                    'export_timestamp': timestamp,
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
                
                json_file = export_dir / f"traffic_data_{timestamp}.json"
                with open(json_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                return str(json_file)

class AnalyticsEngine:
    """Advanced analytics engine for traffic data"""
    
    def __init__(self, database: TrafficDatabase):
        self.db = database
    
    def calculate_intersection_efficiency(self, intersection_id: str, 
                                        hours: int = 24) -> Dict[str, Any]:
        """Calculate efficiency metrics for an intersection"""
        # Get traffic patterns
        patterns = self.db.get_traffic_patterns(intersection_id, days=1)
        
        # Get performance metrics
        metrics = self.db.get_performance_metrics(intersection_id, hours)
        
        # Calculate efficiency score (simplified algorithm)
        total_vehicles = patterns.get('total_vehicles', 0)
        peak_hour_data = patterns.get('peak_hour', {})
        peak_volume = peak_hour_data.get('total_vehicles', 0) if peak_hour_data else 0
        
        # Efficiency based on traffic distribution and wait times
        efficiency_score = 0.0
        if total_vehicles > 0:
            peak_ratio = peak_volume / total_vehicles if total_vehicles > 0 else 0
            # Lower peak ratio indicates better traffic distribution
            distribution_score = max(0, 1 - peak_ratio * 2)
            
            # Wait time factor (if available)
            wait_time_score = 1.0  # Default if no wait time data
            if intersection_id in metrics and 'wait_time' in metrics[intersection_id]:
                avg_wait = metrics[intersection_id]['wait_time']['average']
                wait_time_score = max(0, 1 - avg_wait / 120)  # Normalize to 2 minutes max
            
            efficiency_score = (distribution_score * 0.6 + wait_time_score * 0.4) * 100
        
        return {
            'intersection_id': intersection_id,
            'efficiency_score': round(efficiency_score, 2),
            'total_vehicles_24h': total_vehicles,
            'peak_hour_volume': peak_volume,
            'traffic_distribution_score': round(distribution_score * 100, 2),
            'average_wait_time': metrics.get(intersection_id, {}).get('wait_time', {}).get('average', 0),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def predict_maintenance_needs(self) -> List[Dict[str, Any]]:
        """Predict maintenance needs based on system performance"""
        maintenance_predictions = []
        
        # Analyze recent alerts and performance degradation
        recent_alerts = self.db.get_system_alerts(hours=168)  # Last week
        
        # Group alerts by component and intersection
        component_issues = {}
        for alert in recent_alerts:
            key = f"{alert['intersection_id']}_{alert['component']}"
            if key not in component_issues:
                component_issues[key] = []
            component_issues[key].append(alert)
        
        # Predict maintenance needs based on alert frequency
        for key, alerts in component_issues.items():
            intersection_id, component = key.split('_', 1)
            
            high_severity_count = sum(1 for a in alerts if a['severity'] in ['high', 'critical'])
            total_alerts = len(alerts)
            
            if high_severity_count >= 3 or total_alerts >= 10:
                priority = 'high' if high_severity_count >= 5 else 'medium'
                
                maintenance_predictions.append({
                    'intersection_id': intersection_id,
                    'component': component,
                    'priority': priority,
                    'predicted_failure_date': (datetime.now() + timedelta(days=7)).isoformat(),
                    'alert_count': total_alerts,
                    'high_severity_alerts': high_severity_count,
                    'recommendation': f"Schedule maintenance for {component} at {intersection_id}"
                })
        
        return maintenance_predictions

if __name__ == "__main__":
    # Test database functionality
    db = TrafficDatabase("data/test_traffic.db")
    analytics = AnalyticsEngine(db)
    
    # Test data insertion
    db.record_vehicle_detection("intersection_001", "north", 5, ["car", "truck", "car", "car", "motorcycle"])
    db.record_sensor_reading("sensor_001", "ultrasonic", "intersection_001", 25.5, "cm")
    db.record_system_event("alert", "medium", "High traffic volume detected", "intersection_001")
    
    # Test data retrieval
    patterns = db.get_traffic_patterns("intersection_001")
    print("Traffic patterns:", json.dumps(patterns, indent=2, default=str))
    
    efficiency = analytics.calculate_intersection_efficiency("intersection_001")
    print("Efficiency analysis:", json.dumps(efficiency, indent=2, default=str))
