"""
Structured logging configuration with sensitive data filtering
"""
import logging
import sys
from pythonjsonlogger import jsonlogger


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""

    SENSITIVE_KEYS = [
        'password', 'token', 'secret', 'api_key', 'apikey',
        'authorization', 'auth', 'jwt', 'session_id',
        'ssn', 'credit_card', 'cvv'
    ]

    def filter(self, record):
        """Redact sensitive data from log record"""
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)

        # Redact message
        if hasattr(record, 'msg'):
            for key in self.SENSITIVE_KEYS:
                if key in str(record.msg).lower():
                    record.msg = str(record.msg).replace(key, f"{key}=***REDACTED***")

        return True

    def _redact_dict(self, data: dict) -> dict:
        """Recursively redact sensitive keys from dictionary"""
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            else:
                redacted[key] = value
        return redacted


def setup_logging():
    """Configure structured JSON logging"""

    # Create JSON formatter with simpler config
    json_formatter = jsonlogger.JsonFormatter(
        '%(levelname)s %(name)s %(message)s',
        timestamp=True
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.addFilter(SensitiveDataFilter())

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    return root_logger


# Global logger instance
logger = setup_logging()
