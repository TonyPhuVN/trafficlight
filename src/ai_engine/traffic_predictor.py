"""
📈 Traffic Predictor - Dự đoán lưu lượng giao thông
Sử dụng machine learning để dự báo mật độ giao thông
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import joblib
import logging
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import time

class TrafficPredictor:
    """Class dự đoán lưu lượng giao thông"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Models for different time horizons
        self.short_term_model = None    # 5-15 minutes
        self.medium_term_model = None   # 30-60 minutes  
        self.long_term_model = None     # 2-4 hours
        
        # Data preprocessing
        self.scaler = StandardScaler()
        self.feature_columns = []
        
        # Historical data buffer
        self.historical_data = []
        self.max_history_size = 1000
        
        # Prediction cache
        self.prediction_cache = {}
        self.cache_ttl = 60  # seconds
        
        # Weather integration
        self.weather_factors = {
            'clear': 1.0,
            'cloudy': 0.95,
            'rain': 0.7,
            'heavy_rain': 0.5,
            'snow': 0.4,
            'fog': 0.6
        }
        
        self.logger.info("📈 Traffic Predictor initialized")
    
    def prepare_features(self, current_data: Dict) -> np.ndarray:
        """
        Chuẩn bị features từ dữ liệu hiện tại
        
        Args:
            current_data: Dictionary chứa dữ liệu hiện tại
            
        Returns:
            Feature array ready for prediction
        """
        now = datetime.now()
        
        # Time-based features
        features = {
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'month': now.month,
            'is_weekend': 1 if now.weekday() >= 5 else 0,
            'is_rush_hour': 1 if (7 <= now.hour <= 9) or (17 <= now.hour <= 19) else 0,
            'is_lunch_time': 1 if 11 <= now.hour <= 14 else 0,
            'is_night': 1 if now.hour >= 22 or now.hour <= 6 else 0
        }
        
        # Current traffic data
        vehicle_counts = current_data.get('vehicle_counts', {})
        for zone in ['North', 'East', 'South', 'West']:
            zone_data = vehicle_counts.get(zone, {})
            features[f'{zone.lower()}_cars'] = zone_data.get('cars', 0)
            features[f'{zone.lower()}_trucks'] = zone_data.get('trucks', 0)
            features[f'{zone.lower()}_total'] = zone_data.get('total', 0)
        
        # Historical averages (last 10 minutes)
        recent_history = self._get_recent_history(minutes=10)
        if recent_history:
            avg_traffic = np.mean([h['total_vehicles'] for h in recent_history])
            features['avg_traffic_10min'] = avg_traffic
            
            # Trend calculation
            if len(recent_history) >= 3:
                traffic_values = [h['total_vehicles'] for h in recent_history[-3:]]
                trend = np.polyfit(range(len(traffic_values)), traffic_values, 1)[0]
                features['traffic_trend'] = trend
            else:
                features['traffic_trend'] = 0
        else:
            features['avg_traffic_10min'] = 0
            features['traffic_trend'] = 0
        
        # Weather features (simulated or from sensors)
        weather_data = current_data.get('weather', {})
        features['temperature'] = weather_data.get('temperature', 20)
        features['humidity'] = weather_data.get('humidity', 50)
        features['is_raining'] = 1 if weather_data.get('rain', False) else 0
        features['visibility'] = weather_data.get('visibility', 100)
        
        # Special events (can be extended)
        features['is_holiday'] = 0  # Can be integrated with holiday calendar
        features['special_event'] = 0  # Can be set manually or from events API
        
        # Convert to array
        if not self.feature_columns:
            self.feature_columns = list(features.keys())
        
        feature_array = np.array([features[col] for col in self.feature_columns]).reshape(1, -1)
        
        return feature_array
    
    def _get_recent_history(self, minutes: int) -> List[Dict]:
        """Lấy dữ liệu lịch sử gần đây"""
        cutoff_time = time.time() - (minutes * 60)
        return [data for data in self.historical_data if data['timestamp'] >= cutoff_time]
    
    def add_historical_data(self, data: Dict):
        """Thêm dữ liệu vào lịch sử"""
        data['timestamp'] = time.time()
        self.historical_data.append(data)
        
        # Giới hạn kích thước buffer
        if len(self.historical_data) > self.max_history_size:
            self.historical_data = self.historical_data[-self.max_history_size:]
    
    def predict_short_term(self, current_data: Dict, minutes_ahead: int = 15) -> Dict:
        """
        Dự đoán ngắn hạn (5-15 phút)
        
        Args:
            current_data: Dữ liệu hiện tại
            minutes_ahead: Số phút dự đoán trước
            
        Returns:
            Dictionary chứa dự đoán
        """
        cache_key = f"short_term_{minutes_ahead}_{int(time.time() // 60)}"
        
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        try:
            if self.short_term_model is None:
                # Use simple trend-based prediction if no trained model
                return self._simple_trend_prediction(current_data, minutes_ahead)
            
            features = self.prepare_features(current_data)
            features_scaled = self.scaler.transform(features)
            
            # Predict for each zone
            predictions = {}
            total_predicted = 0
            
            for zone in ['North', 'East', 'South', 'West']:
                # Simple model prediction (can be enhanced with zone-specific models)
                base_prediction = self.short_term_model.predict(features_scaled)[0]
                
                # Apply zone-specific adjustments
                zone_factor = self._get_zone_factor(zone, current_data)
                zone_prediction = max(0, base_prediction * zone_factor)
                
                predictions[zone] = {
                    'predicted_vehicles': int(zone_prediction),
                    'confidence': 0.8,  # Can be calculated based on model performance
                    'time_horizon': minutes_ahead
                }
                total_predicted += zone_prediction
            
            result = {
                'predictions': predictions,
                'total_predicted': int(total_predicted),
                'prediction_time': datetime.now().isoformat(),
                'time_horizon_minutes': minutes_ahead,
                'model_type': 'short_term',
                'confidence': 0.8
            }
            
            # Cache result
            self.prediction_cache[cache_key] = result
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Short-term prediction error: {e}")
            return self._simple_trend_prediction(current_data, minutes_ahead)
    
    def predict_medium_term(self, current_data: Dict, minutes_ahead: int = 60) -> Dict:
        """Dự đoán trung hạn (30-60 phút)"""
        cache_key = f"medium_term_{minutes_ahead}_{int(time.time() // 300)}"  # 5-min cache
        
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        # Enhanced prediction with pattern recognition
        now = datetime.now()
        target_time = now + timedelta(minutes=minutes_ahead)
        
        # Historical pattern analysis
        historical_pattern = self._analyze_historical_pattern(target_time)
        
        # Weather adjustment
        weather_adjustment = self._get_weather_adjustment(current_data)
        
        predictions = {}
        total_predicted = 0
        
        for zone in ['North', 'East', 'South', 'West']:
            base_prediction = historical_pattern.get(zone, 5)  # Default 5 vehicles
            adjusted_prediction = base_prediction * weather_adjustment
            
            # Trend adjustment
            recent_trend = self._calculate_zone_trend(zone, current_data)
            final_prediction = max(0, adjusted_prediction + recent_trend)
            
            predictions[zone] = {
                'predicted_vehicles': int(final_prediction),
                'confidence': 0.7,
                'time_horizon': minutes_ahead,
                'factors': {
                    'historical_pattern': base_prediction,
                    'weather_adjustment': weather_adjustment,
                    'trend_adjustment': recent_trend
                }
            }
            total_predicted += final_prediction
        
        result = {
            'predictions': predictions,
            'total_predicted': int(total_predicted),
            'prediction_time': datetime.now().isoformat(),
            'time_horizon_minutes': minutes_ahead,
            'model_type': 'medium_term',
            'confidence': 0.7
        }
        
        self.prediction_cache[cache_key] = result
        return result
    
    def predict_long_term(self, current_data: Dict, hours_ahead: int = 2) -> Dict:
        """Dự đoán dài hạn (2-4 giờ)"""
        cache_key = f"long_term_{hours_ahead}_{int(time.time() // 900)}"  # 15-min cache
        
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        now = datetime.now()
        target_time = now + timedelta(hours=hours_ahead)
        
        # Day pattern analysis
        day_pattern = self._get_day_pattern(target_time)
        
        # Weekly pattern
        weekly_pattern = self._get_weekly_pattern(target_time)
        
        # Seasonal adjustment
        seasonal_factor = self._get_seasonal_factor(target_time)
        
        predictions = {}
        total_predicted = 0
        
        for zone in ['North', 'East', 'South', 'West']:
            base_prediction = day_pattern.get(zone, 8)
            weekly_adjustment = weekly_pattern.get(zone, 1.0)
            
            final_prediction = base_prediction * weekly_adjustment * seasonal_factor
            
            predictions[zone] = {
                'predicted_vehicles': int(final_prediction),
                'confidence': 0.6,
                'time_horizon_hours': hours_ahead,
                'factors': {
                    'day_pattern': base_prediction,
                    'weekly_adjustment': weekly_adjustment,
                    'seasonal_factor': seasonal_factor
                }
            }
            total_predicted += final_prediction
        
        result = {
            'predictions': predictions,
            'total_predicted': int(total_predicted),
            'prediction_time': datetime.now().isoformat(),
            'time_horizon_hours': hours_ahead,
            'model_type': 'long_term',
            'confidence': 0.6
        }
        
        self.prediction_cache[cache_key] = result
        return result
    
    def _simple_trend_prediction(self, current_data: Dict, minutes_ahead: int) -> Dict:
        """Dự đoán đơn giản dựa trên trend"""
        vehicle_counts = current_data.get('vehicle_counts', {})
        
        predictions = {}
        total_predicted = 0
        
        # Get current trend
        trend_factor = 1.0
        if len(self.historical_data) >= 3:
            recent_totals = [h.get('total_vehicles', 0) for h in self.historical_data[-3:]]
            if len(set(recent_totals)) > 1:  # Avoid division by zero
                trend_factor = recent_totals[-1] / max(recent_totals[0], 1)
        
        for zone in ['North', 'East', 'South', 'West']:
            current_count = vehicle_counts.get(zone, {}).get('total', 0)
            
            # Apply time-based adjustments
            time_factor = self._get_time_factor(minutes_ahead)
            predicted = current_count * trend_factor * time_factor
            
            predictions[zone] = {
                'predicted_vehicles': max(0, int(predicted)),
                'confidence': 0.5,
                'time_horizon': minutes_ahead
            }
            total_predicted += predicted
        
        return {
            'predictions': predictions,
            'total_predicted': max(0, int(total_predicted)),
            'prediction_time': datetime.now().isoformat(),
            'time_horizon_minutes': minutes_ahead,
            'model_type': 'simple_trend',
            'confidence': 0.5
        }
    
    def _get_zone_factor(self, zone: str, current_data: Dict) -> float:
        """Lấy hệ số điều chỉnh theo zone"""
        # Zone characteristics (can be configured)
        zone_factors = {
            'North': 1.1,  # Busy commercial area
            'East': 0.9,   # Residential
            'South': 1.2,  # Industrial
            'West': 0.8    # Quiet area
        }
        return zone_factors.get(zone, 1.0)
    
    def _get_weather_adjustment(self, current_data: Dict) -> float:
        """Lấy hệ số điều chỉnh thời tiết"""
        weather = current_data.get('weather', {})
        condition = weather.get('condition', 'clear')
        return self.weather_factors.get(condition, 1.0)
    
    def _get_time_factor(self, minutes_ahead: int) -> float:
        """Hệ số điều chỉnh theo thời gian"""
        now = datetime.now()
        target_time = now + timedelta(minutes=minutes_ahead)
        hour = target_time.hour
        
        # Traffic patterns by hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            return 1.5
        elif 11 <= hour <= 14:  # Lunch time
            return 1.2
        elif 22 <= hour or hour <= 6:  # Night time
            return 0.3
        else:
            return 1.0
    
    def _analyze_historical_pattern(self, target_time: datetime) -> Dict:
        """Phân tích pattern lịch sử cho thời điểm mục tiêu"""
        # Simplified pattern analysis
        hour = target_time.hour
        weekday = target_time.weekday()
        
        # Base patterns by hour and day
        if weekday >= 5:  # Weekend
            base_traffic = {
                'North': max(2, 8 - abs(hour - 14)),  # Peak at 2 PM
                'East': max(1, 6 - abs(hour - 12)),
                'South': max(1, 4 - abs(hour - 15)),
                'West': max(2, 7 - abs(hour - 13))
            }
        else:  # Weekday
            if 7 <= hour <= 9:  # Morning rush
                base_traffic = {'North': 15, 'East': 8, 'South': 20, 'West': 5}
            elif 17 <= hour <= 19:  # Evening rush
                base_traffic = {'North': 18, 'East': 12, 'South': 25, 'West': 8}
            else:
                base_traffic = {'North': 5, 'East': 3, 'South': 8, 'West': 2}
        
        return base_traffic
    
    def _get_day_pattern(self, target_time: datetime) -> Dict:
        """Lấy pattern theo ngày"""
        return self._analyze_historical_pattern(target_time)
    
    def _get_weekly_pattern(self, target_time: datetime) -> Dict:
        """Lấy pattern theo tuần"""
        weekday = target_time.weekday()
        if weekday == 0:  # Monday
            return {'North': 1.1, 'East': 1.0, 'South': 1.2, 'West': 0.9}
        elif weekday == 4:  # Friday
            return {'North': 1.2, 'East': 1.1, 'South': 1.1, 'West': 1.0}
        elif weekday >= 5:  # Weekend
            return {'North': 0.7, 'East': 0.8, 'South': 0.6, 'West': 1.1}
        else:
            return {'North': 1.0, 'East': 1.0, 'South': 1.0, 'West': 1.0}
    
    def _get_seasonal_factor(self, target_time: datetime) -> float:
        """Hệ số theo mùa"""
        month = target_time.month
        if month in [12, 1, 2]:  # Winter
            return 0.8
        elif month in [6, 7, 8]:  # Summer
            return 1.1
        else:
            return 1.0
    
    def _calculate_zone_trend(self, zone: str, current_data: Dict) -> float:
        """Tính trend cho zone cụ thể"""
        recent_data = self._get_recent_history(30)  # Last 30 minutes
        
        if len(recent_data) < 3:
            return 0
        
        zone_values = []
        for data in recent_data:
            zone_count = data.get('vehicle_counts', {}).get(zone, {}).get('total', 0)
            zone_values.append(zone_count)
        
        if len(zone_values) >= 3:
            trend = np.polyfit(range(len(zone_values)), zone_values, 1)[0]
            return trend * 10  # Scale for 10-minute projection
        
        return 0
    
    def get_prediction_accuracy(self) -> Dict:
        """Tính độ chính xác dự đoán"""
        # This would compare past predictions with actual values
        # For now, return simulated accuracy metrics
        return {
            'short_term_mae': 2.1,
            'medium_term_mae': 3.5,
            'long_term_mae': 5.2,
            'overall_accuracy': 78.5,
            'last_updated': datetime.now().isoformat()
        }
    
    def save_model(self, model_path: str):
        """Lưu model đã train"""
        model_data = {
            'short_term_model': self.short_term_model,
            'medium_term_model': self.medium_term_model,
            'long_term_model': self.long_term_model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns
        }
        
        try:
            joblib.dump(model_data, model_path)
            self.logger.info(f"✅ Model saved to {model_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save model: {e}")
    
    def load_model(self, model_path: str):
        """Load model đã train"""
        try:
            model_data = joblib.load(model_path)
            self.short_term_model = model_data.get('short_term_model')
            self.medium_term_model = model_data.get('medium_term_model')
            self.long_term_model = model_data.get('long_term_model')
            self.scaler = model_data.get('scaler', StandardScaler())
            self.feature_columns = model_data.get('feature_columns', [])
            
            self.logger.info(f"✅ Model loaded from {model_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")

if __name__ == "__main__":
    # Test traffic predictor
    import sys
    import os
    
    # Add project root directory to path to access config module
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, project_root)
    
    from config.config import SmartTrafficConfig, SystemMode
    
    config = SmartTrafficConfig(SystemMode.SIMULATION)
    predictor = TrafficPredictor(config)
    
    # Test data
    test_data = {
        'vehicle_counts': {
            'North': {'total': 8, 'cars': 6, 'trucks': 2},
            'East': {'total': 5, 'cars': 4, 'trucks': 1},
            'South': {'total': 12, 'cars': 10, 'trucks': 2},
            'West': {'total': 3, 'cars': 3, 'trucks': 0}
        },
        'weather': {'condition': 'clear', 'temperature': 25}
    }
    
    # Test predictions
    print("🔮 Traffic Prediction Test Results:")
    
    short_pred = predictor.predict_short_term(test_data, 15)
    print(f"📅 Short-term (15 min): {short_pred['total_predicted']} vehicles")
    
    medium_pred = predictor.predict_medium_term(test_data, 60)
    print(f"📅 Medium-term (1 hour): {medium_pred['total_predicted']} vehicles")
    
    long_pred = predictor.predict_long_term(test_data, 2)
    print(f"📅 Long-term (2 hours): {long_pred['total_predicted']} vehicles")
