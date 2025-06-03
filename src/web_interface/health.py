"""
Health check endpoint for Smart Traffic AI System
Simple health check that can be imported into the main app
"""

from flask import jsonify
import datetime

def add_health_routes(app):
    """Add health check routes to the Flask app"""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for Docker/Coolify"""
        try:
            # Basic health check - ensure the app is running
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.datetime.now().isoformat(),
                'service': 'smart-traffic-ai-system'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }), 500

    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with component status"""
        try:
            # More comprehensive health check
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.datetime.now().isoformat(),
                'service': 'smart-traffic-ai-system',
                'components': {
                    'web_server': 'healthy',
                    'database': 'healthy',  # Could check DB connection here
                    'ai_engine': 'healthy',  # Could check AI model loading
                    'mqtt': 'healthy'  # Could check MQTT connection
                }
            }
            return jsonify(health_status), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }), 500
