"""
Configuration management with security validation
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from typing import List
import os
from pathlib import Path
from .config_loader import config


class Settings(BaseSettings):
    """Application settings with security defaults"""

    # Application
    APP_NAME: str = "Me Feed"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Security - File paths for keys
    JWT_PRIVATE_KEY_PATH: str = config.get('jwt.private_key_path', "./secrets/jwt_private.pem")
    JWT_PUBLIC_KEY_PATH: str = config.get('jwt.public_key_path', "./secrets/jwt_public.pem")
    ENCRYPTION_KEY_PATH: str = config.get('encryption.key_path', "./secrets/encryption.key")
    SECRET_KEY: str = config.get('security.secret_key', '')

    # CORS & Security
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    LOGIN_RATE_LIMIT: str = "10/minute"
    IMPORT_RATE_LIMIT: str = "5/hour"

    # JWT Configuration
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_SESSIONS_PER_USER: int = 5

    # API Keys
    RAPIDAPI_KEY: str = config.get('api_keys.rapidapi', '')
    RAPIDAPI_HOST: str = ""
    TMDB_API_KEY: str = config.get('api_keys.tmdb', '')
    API_KEY_ROTATION_DAYS: int = 90

    # Job Scheduling
    MEDIA_UPDATE_INTERVAL: str = "weekly"
    MONITORING_SCHEDULE: str = "daily"
    NOTIFICATION_BATCH_SIZE: int = 50

    # Email
    SMTP_HOST: str = config.get('smtp.host', 'smtp.sendgrid.net')
    SMTP_PORT: int = config.get('smtp.port', 587)
    SMTP_USER: str = config.get('smtp.user', 'apikey')
    SMTP_PASSWORD: str = config.get('smtp.password', '')
    FROM_EMAIL: str = "noreply@mefeed.com"

    # Feature Flags
    ENABLE_2FA: bool = False
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENFORCE_HTTPS: bool = True
    MATCHING_STRATEGY: str = "exact"

    # CSV Upload Limits
    MAX_FILE_SIZE_MB: int = 10
    MAX_CSV_ROWS: int = 10000

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure SECRET_KEY is sufficiently long"""
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v, info):
        """Ensure production database password is not a placeholder"""
        # In Pydantic v2, we can't access other fields in field_validator
        # We'll check DEBUG via environment variable directly
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        if not debug and ('CHANGE_THIS_PASSWORD' in v or 'localhost' in v):
            raise ValueError(
                'Production database configuration required. '
                'DATABASE_URL contains placeholder or localhost.'
            )
        return v

    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v, info):
        """Ensure production Redis password is not a placeholder"""
        # In Pydantic v2, we can't access other fields in field_validator
        # We'll check DEBUG via environment variable directly
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        if not debug and ('CHANGE_THIS_PASSWORD' in v or 'localhost' in v):
            raise ValueError(
                'Production Redis configuration required. '
                'REDIS_URL contains placeholder or localhost.'
            )
        return v

    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_origins(cls, v):
        """Validate CORS origins format"""
        if not v:
            raise ValueError('ALLOWED_ORIGINS cannot be empty')
        return v

    @property
    def jwt_private_key(self) -> str:
        """Load JWT private key from file"""
        key_path = Path(self.JWT_PRIVATE_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"JWT private key not found at {key_path}")
        with open(key_path, 'r') as f:
            return f.read()

    @property
    def jwt_public_key(self) -> str:
        """Load JWT public key from file"""
        key_path = Path(self.JWT_PUBLIC_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"JWT public key not found at {key_path}")
        with open(key_path, 'r') as f:
            return f.read()

    @property
    def encryption_key(self) -> bytes:
        """Load encryption key from file"""
        key_path = Path(self.ENCRYPTION_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"Encryption key not found at {key_path}")
        with open(key_path, 'rb') as f:
            return f.read()

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse ALLOWED_HOSTS into list"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
