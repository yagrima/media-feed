"""
Configuration management with security validation
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os
from pathlib import Path
from .config_loader import config


# For Railway/Production: Use environment-specified paths or /tmp/secrets
# For local dev: Use relative path to Media Feed Secrets
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("JWT_PRIVATE_KEY_PATH"):
    # Production environment (Railway)
    DEFAULT_SECRETS_DIR = Path("/tmp/secrets")
    DEFAULT_ENV_FILE = Path("/tmp/.env")
else:
    # Local development
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
    DEFAULT_SECRETS_DIR = Path(
        os.getenv(
            "MEFEED_SECRETS_DIR",
            PROJECT_ROOT.parent / "Media Feed Secrets" / "secrets"
        )
    ).resolve(strict=False)
    DEFAULT_ENV_FILE = Path(
        os.getenv("MEFEED_ENV_FILE", DEFAULT_SECRETS_DIR / ".env")
    ).resolve(strict=False)


class Settings(BaseSettings):
    """Application settings with security defaults"""

    # Application
    APP_NAME: str = "Me Feed"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = ''
    REDIS_URL: str = ''
    
    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def build_database_url(cls, v):
        """Build DATABASE_URL from components if not provided"""
        if v:
            # Ensure asyncpg driver is used
            if v.startswith('postgresql://'):
                v = v.replace('postgresql://', 'postgresql+asyncpg://', 1)
            return v
        
        # Build from individual components
        import urllib.parse
        db_config = config.get_database_config()
        if all(db_config.values()):
            encoded_password = urllib.parse.quote_plus(db_config['password'])
            return f"postgresql+asyncpg://{db_config['user']}:{encoded_password}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        return v
    
    @field_validator('REDIS_URL', mode='before')
    @classmethod
    def build_redis_url(cls, v):
        """Build REDIS_URL from components if not provided or contains placeholder"""
        if v and 'CHANGE_THIS_PASSWORD' not in v:
            return v
            
        # Build from individual components
        redis_config = config.get_redis_config()
        if redis_config['password']:
            return f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        else:
            return f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"

    # Security - File paths for keys
    SECRETS_BASE_DIR: str = str(DEFAULT_SECRETS_DIR)

    JWT_PRIVATE_KEY_PATH: str = config.get('jwt.private_key_file', str(DEFAULT_SECRETS_DIR / "secrets" / "jwt_private.pem"))
    JWT_PUBLIC_KEY_PATH: str = config.get('jwt.public_key_file', str(DEFAULT_SECRETS_DIR / "secrets" / "jwt_public.pem"))
    ENCRYPTION_KEY_PATH: str = config.get('security.encryption_key_file', str(DEFAULT_SECRETS_DIR / "secrets" / "encryption.key"))
    SECRET_KEY: str = config.get('security.secret_key', '')

    # CORS & Security
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
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
    MAX_SESSIONS_PER_USER: int = 3  # Reduced from 5 for better security

    # API Keys
    RAPIDAPI_KEY: str = config.get('api_keys.rapidapi', '')
    RAPIDAPI_HOST: str = ""
    TMDB_API_KEY: str = ""  # Read from environment variable or config file
    API_KEY_ROTATION_DAYS: int = 90
    
    # Error Tracking
    SENTRY_DSN: str = config.get('monitoring.sentry_dsn', '')
    ENVIRONMENT: str = "production"
    
    @field_validator('TMDB_API_KEY', mode='before')
    @classmethod
    def load_tmdb_key(cls, v):
        """Load TMDB API key from environment or config"""
        # Environment variable takes precedence
        if v:
            return v
        # Fallback to config file
        return config.get('api_keys.tmdb', '')

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
    def validate_database_url(cls, v):
        """Ensure production database password is not a placeholder"""
        # Skip validation in development if localhost
        if 'localhost' in v:
            return v
        if 'CHANGE_THIS_PASSWORD' in v:
            raise ValueError(
                'Production database configuration required. '
                'DATABASE_URL contains placeholder.'
            )
        return v

    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v):
        """Ensure production Redis password is not a placeholder"""
        # Skip validation in development if localhost
        if 'localhost' in v:
            return v
        if 'CHANGE_THIS_PASSWORD' in v:
            raise ValueError(
                'Production Redis configuration required. '
                'REDIS_URL contains placeholder.'
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
        # Only use env_file in local development, not in Railway
        env_file = str(DEFAULT_ENV_FILE) if not os.getenv("RAILWAY_ENVIRONMENT") else None
        case_sensitive = True


# Global settings instance
settings = Settings()
