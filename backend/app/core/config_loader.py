"""
Configuration loader for sensitive values
Loads configuration from config/secrets.json file
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Loads configuration from JSON file with environment fallbacks"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/secrets.json relative to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            config_path = project_root / "config" / "secrets.json"
        
        self.config_path = Path(config_path)
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
            else:
                print(f"Warning: Config file not found at {self.config_path}")
                self._config = {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('database.password')
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                # Fall back to environment variables
                env_key = '_'.join(keys).upper()
                env_value = os.getenv(env_key)
                if env_value is not None:
                    return env_value
                return default
        
        # Also check environment variable as final fallback
        env_key = '_'.join(keys).upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
            
        return value
    
    def get_api_key(self, service: str) -> str:
        """Get API key for specific service"""
        return self.get(f'api_keys.{service}')
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            'user': self.get('database.user'),
            'password': self.get('database.password'),
            'host': self.get('database.host'),
            'port': self.get('database.port'),
            'name': self.get('database.name')
        }
    
    def get_redis_config(self) -> Dict[str, str]:
        """Get Redis configuration"""
        return {
            'password': self.get('redis.password'),
            'host': self.get('redis.host'),
            'port': self.get('redis.port'),
            'db': self.get('redis.db')
        }
    
    def get_jwt_config(self) -> Dict[str, str]:
        """Get JWT configuration"""
        return {
            'private_key_path': self.get('jwt.private_key_path'),
            'public_key_path': self.get('jwt.public_key_path')
        }
    
    def get_smtp_config(self) -> Dict[str, str]:
        """Get SMTP configuration"""
        return {
            'user': self.get('smtp.user'),
            'password': self.get('smtp.password'),
            'host': self.get('smtp.host'),
            'port': self.get('smtp.port')
        }


# Global config instance
config = ConfigLoader()
