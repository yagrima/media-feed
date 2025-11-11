"""
Core security module: JWT, encryption, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets

from app.core.config import settings


# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class SecurityService:
    """Centralized security service for authentication and encryption"""

    def __init__(self):
        """Initialize security service with keys from settings"""
        self._private_key = None
        self._public_key = None
        self._fernet = None

    @property
    def private_key(self) -> str:
        """Lazy load private key"""
        if self._private_key is None:
            self._private_key = settings.jwt_private_key
        return self._private_key

    @property
    def public_key(self) -> str:
        """Lazy load public key"""
        if self._public_key is None:
            self._public_key = settings.jwt_public_key
        return self._public_key

    @property
    def fernet(self) -> Fernet:
        """Lazy load Fernet cipher"""
        if self._fernet is None:
            self._fernet = Fernet(settings.encryption_key)
        return self._fernet

    def create_access_token(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Create JWT access token with RS256 signature

        Args:
            user_id: User's unique identifier
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT token
        """
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16)
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.private_key, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create JWT refresh token with longer expiration

        Args:
            user_id: User's unique identifier

        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        }

        return jwt.encode(payload, self.private_key, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Verify token type
            if payload.get("type") != token_type:
                return None

            return payload

        except JWTError:
            return None

    def hash_password(self, password: str) -> str:
        """
        Hash password using Argon2

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet

        Args:
            data: Plain text data to encrypt

        Returns:
            Encrypted data as string
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted data string

        Returns:
            Decrypted plain text
        """
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def generate_token(self, nbytes: int = 32) -> str:
        """
        Generate secure random token

        Args:
            nbytes: Number of random bytes

        Returns:
            URL-safe random token
        """
        return secrets.token_urlsafe(nbytes)

    def hash_token(self, token: str) -> str:
        """
        Create hash of token for storage

        Args:
            token: Token to hash

        Returns:
            Hashed token
        """
        return pwd_context.hash(token)

    def verify_token_hash(self, token: str, token_hash: str) -> bool:
        """
        Verify token against stored hash

        Args:
            token: Plain token
            token_hash: Stored hash

        Returns:
            True if token matches hash
        """
        return pwd_context.verify(token, token_hash)

    def encrypt_user_specific_data(self, data: str, user_id: str) -> str:
        """
        Encrypt data with user-specific cipher (more secure for third-party credentials)
        
        Uses PBKDF2 to derive a user-specific cipher from base material and user ID.
        Each user's data is encrypted with a unique cipher for isolation.

        Args:
            data: Plain text data to encrypt
            user_id: User's UUID as string

        Returns:
            Encrypted data as base64 string
        """
        import hashlib
        import base64
        
        # Derive user-specific cipher using PBKDF2
        base_material = settings.encryption_key.decode() if isinstance(settings.encryption_key, bytes) else settings.encryption_key
        user_salt = user_id.encode()
        
        # Generate 32-byte cipher using PBKDF2 with 100,000 iterations
        computed_value = hashlib.pbkdf2_hmac('sha256', base_material.encode(), user_salt, 100000, dklen=32)
        computed_b64 = base64.urlsafe_b64encode(computed_value)
        
        # Create Fernet cipher with computed value
        user_fernet = Fernet(computed_b64)
        
        # Encrypt and return
        encrypted = user_fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_user_specific_data(self, encrypted_data: str, user_id: str) -> str:
        """
        Decrypt data encrypted with user-specific cipher

        Args:
            encrypted_data: Encrypted data as base64 string
            user_id: User's UUID as string

        Returns:
            Decrypted plain text

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        import hashlib
        import base64
        
        # Derive same user-specific cipher
        base_material = settings.encryption_key.decode() if isinstance(settings.encryption_key, bytes) else settings.encryption_key
        user_salt = user_id.encode()
        
        computed_value = hashlib.pbkdf2_hmac('sha256', base_material.encode(), user_salt, 100000, dklen=32)
        computed_b64 = base64.urlsafe_b64encode(computed_value)
        
        # Create Fernet cipher with computed value
        user_fernet = Fernet(computed_b64)
        
        # Decrypt and return
        decrypted = user_fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()


# Global security service instance
security_service = SecurityService()
