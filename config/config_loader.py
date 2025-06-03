"""
🔧 Configuration Loader for Smart Traffic AI System
Simple configuration loading utility
"""

import json
import os
from config.config import SmartTrafficConfig, SystemMode

def load_config(config_file: str = None, mode: SystemMode = SystemMode.SIMULATION) -> SmartTrafficConfig:
    """Load configuration from file or create default"""
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Create config with specified mode
            mode_str = config_data.get('mode', 'simulation')
            if mode_str == 'simulation':
                mode = SystemMode.SIMULATION
            elif mode_str == 'development':
                mode = SystemMode.DEVELOPMENT
            elif mode_str == 'production':
                mode = SystemMode.PRODUCTION
            
            config = SmartTrafficConfig(mode)
            
            # Update database URL if specified
            if 'database' in config_data:
                db_config = config_data['database']
                if 'database_url' in db_config:
                    config.database.database_url = db_config['database_url']
            
            return config
            
        except Exception as e:
            print(f"Error loading config file {config_file}: {e}")
            print("Using default configuration...")
            return SmartTrafficConfig(mode)
    else:
        return SmartTrafficConfig(mode)
