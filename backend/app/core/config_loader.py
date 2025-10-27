"""
Configuration loader for sensitive values
Loads configuration from config/secrets.json file and separate key files
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Loads configuration from JSON file with environment fallbacks and file references"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            secrets_base_dir = Path(
                os.getenv(
                    "MEFEED_SECRETS_DIR",
                    project_root.parent / "Media Feed Secrets" / "secrets"
                )
            ).resolve(strict=False)
            config_path = Path(secrets_base_dir).parent / "config" / "secrets.json"
        else:
            config_abs_path = Path(config_path).resolve(strict=False)
            secrets_base_dir = (
                config_abs_path.parent.parent
                if config_abs_path.parent.name == "config"
                else config_abs_path.parent
            )
            config_path = config_abs_path

        self.config_path = Path(config_path)
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.secrets_base_dir = secrets_base_dir
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Warning: Config file not found at {self.config_path}")
                self._config = {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = {}
    
    def _resolve_file_path(self, file_path: str) -> Path:
        """Resolve file paths relative to config file location"""
        if not file_path:
            return None
        candidate = Path(file_path)

        if candidate.is_absolute():
            return candidate

        if file_path.startswith('../') or file_path.startswith('./'):
            return (self.config_path.parent / file_path).resolve(strict=False)

        return (self.secrets_base_dir / file_path).resolve(strict=False)
    
    def _read_file_content(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Read content from a file referenced in configuration"""
        resolved_path = self._resolve_file_path(file_path)
        if resolved_path and resolved_path.exists():
            try:
                with open(resolved_path, 'r', encoding=encoding) as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading file {resolved_path}: {e}")
        return None
    
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
        """Get JWT configuration with file paths resolved"""
        private_key_file = self.get('jwt.private_key_file')
        public_key_file = self.get('jwt.public_key_file')
        
        return {
            'private_key_path': str(self._resolve_file_path(private_key_file)) if private_key_file else None,
            'public_key_path': str(self._resolve_file_path(public_key_file)) if public_key_file else None
        }
    
    def get_jwt_private_key(self) -> Optional[str]:
        """Get JWT private key content directly"""
        private_key_file = self.get('jwt.private_key_file')
        return self._read_file_content(private_key_file)
    
    def get_jwt_public_key(self) -> Optional[str]:
        """Get JWT public key content directly"""
        public_key_file = self.get('jwt.public_key_file')
        return self._read_file_content(public_key_file)
    
    def get_encryption_key(self) -> Optional[str]:
        """Get encryption key content directly"""
        encryption_key_file = self.get('security.encryption_key_file')
        return self._read_file_content(encryption_key_file)
    
    def get_smtp_config(self) -> Dict[str, str]:
        """Get SMTP configuration"""
        return {
            'user': self.get('smtp.user'),
            'password': self.get('smtp.password'),
            'host': self.get('smtp.host'),
            'port': self.get('smtp.port')
        }
    
    def get_secret_key(self) -> str:
        """Get the application secret key"""
        return self.get('security.secret_key', 'dev_secret_key_change_in_production')


# Global config instance
config = ConfigLoader()
