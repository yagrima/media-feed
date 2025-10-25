"""
Secure token generation and validation for unsubscribe and other features.
Uses HMAC-based tokens with expiration.
"""

import hmac
import hashlib
import time
import secrets
from typing import Optional, Tuple
from datetime import datetime, timedelta

from app.core.config import settings


class TokenManager:
    """Manages secure tokens with expiration for various features."""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize token manager.

        Args:
            secret_key: Secret key for HMAC (defaults to settings.SECRET_KEY)
        """
        self.secret_key = (secret_key or settings.SECRET_KEY).encode('utf-8')

    def generate_unsubscribe_token(
        self,
        user_id: str,
        notification_id: str,
        expires_days: int = 30
    ) -> Tuple[str, datetime]:
        """
        Generate secure unsubscribe token with expiration.

        Format: {random_id}.{timestamp}.{hmac}
        - random_id: 16 bytes hex (prevents enumeration)
        - timestamp: Unix timestamp for expiration
        - hmac: HMAC-SHA256 signature

        Args:
            user_id: User ID
            notification_id: Notification ID
            expires_days: Token validity in days (default 30)

        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        # Generate random component
        random_id = secrets.token_hex(16)

        # Calculate expiration timestamp
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        timestamp = int(expires_at.timestamp())

        # Create payload
        payload = f"{random_id}.{user_id}.{notification_id}.{timestamp}"

        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Final token format
        token = f"{random_id}.{timestamp}.{signature}"

        return token, expires_at

    def validate_unsubscribe_token(
        self,
        token: str,
        user_id: str,
        notification_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate unsubscribe token.

        Args:
            token: Token to validate
            user_id: Expected user ID
            notification_id: Expected notification ID

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse token
            parts = token.split('.')
            if len(parts) != 3:
                return False, "Invalid token format"

            random_id, timestamp_str, provided_signature = parts

            # Check expiration
            timestamp = int(timestamp_str)
            if timestamp < int(time.time()):
                return False, "Token expired"

            # Recreate payload
            payload = f"{random_id}.{user_id}.{notification_id}.{timestamp}"

            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Constant-time comparison
            if not hmac.compare_digest(provided_signature, expected_signature):
                return False, "Invalid token signature"

            return True, None

        except (ValueError, AttributeError) as e:
            return False, f"Token validation error: {str(e)}"

    def generate_simple_token(self, length: int = 32) -> str:
        """
        Generate a simple secure random token.

        Args:
            length: Token length in bytes (default 32)

        Returns:
            Hex-encoded token
        """
        return secrets.token_hex(length)

    def generate_verification_token(
        self,
        user_id: str,
        purpose: str,
        expires_hours: int = 24
    ) -> Tuple[str, datetime]:
        """
        Generate verification token for email, password reset, etc.

        Args:
            user_id: User ID
            purpose: Token purpose (e.g., 'email_verify', 'password_reset')
            expires_hours: Token validity in hours

        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        # Generate random component
        random_id = secrets.token_hex(16)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        timestamp = int(expires_at.timestamp())

        # Create payload
        payload = f"{random_id}.{user_id}.{purpose}.{timestamp}"

        # Generate HMAC
        signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        token = f"{random_id}.{timestamp}.{signature}"

        return token, expires_at

    def validate_verification_token(
        self,
        token: str,
        user_id: str,
        purpose: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate verification token.

        Args:
            token: Token to validate
            user_id: Expected user ID
            purpose: Expected purpose

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False, "Invalid token format"

            random_id, timestamp_str, provided_signature = parts

            # Check expiration
            timestamp = int(timestamp_str)
            if timestamp < int(time.time()):
                return False, "Token expired"

            # Recreate payload
            payload = f"{random_id}.{user_id}.{purpose}.{timestamp}"

            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Constant-time comparison
            if not hmac.compare_digest(provided_signature, expected_signature):
                return False, "Invalid token signature"

            return True, None

        except (ValueError, AttributeError) as e:
            return False, f"Token validation error: {str(e)}"


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
