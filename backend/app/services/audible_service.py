"""
Audible Service - Handle Audible API authentication and library fetching

This service manages secure connection to Audible accounts using the unofficial
audible Python library. It handles:
- Authentication with user credentials
- Token encryption/decryption with user-specific keys
- Library data fetching
- Device registration/deregistration
"""
import audible
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.security import security_service
from app.db.models import User

logger = logging.getLogger(__name__)


class AudibleAuthError(Exception):
    """Base exception for Audible authentication errors"""
    pass


class AudibleCaptchaRequiredError(AudibleAuthError):
    """Raised when Audible requires CAPTCHA verification"""
    pass


class AudibleTwoFactorRequiredError(AudibleAuthError):
    """Raised when 2FA is required"""
    pass


class AudibleService:
    """Service for Audible API operations"""

    # Audible marketplace codes
    MARKETPLACES = {
        'us': 'United States',
        'uk': 'United Kingdom',
        'de': 'Germany',
        'fr': 'France',
        'ca': 'Canada',
        'au': 'Australia',
        'in': 'India',
        'it': 'Italy',
        'jp': 'Japan',
        'es': 'Spain',
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(
        self,
        user_id: uuid.UUID,
        email: str,
        password: str,
        marketplace: str = 'us'
    ) -> Dict[str, Any]:
        """
        Authenticate with Audible and store encrypted token

        This method:
        1. Authenticates with Audible using provided credentials
        2. Registers a virtual device (visible in user's Amazon device list)
        3. Encrypts and stores the auth token using user-specific key
        4. NEVER stores the password (only in memory during authentication)

        Args:
            user_id: User's UUID
            email: Audible/Amazon email
            password: Audible/Amazon password (2FA code can be appended)
            marketplace: Audible marketplace code (us, uk, de, etc.)

        Returns:
            Dict with success status and device info

        Raises:
            AudibleAuthError: If authentication fails
            AudibleCaptchaRequiredError: If CAPTCHA is required
            AudibleTwoFactorRequiredError: If 2FA is required
        """
        try:
            logger.info(f"Authenticating Audible for user {user_id}, marketplace: {marketplace}")

            # Authenticate with Audible (password only in memory here)
            # Note: with_username=False means use email (standard Amazon login)
            auth = audible.Authenticator.from_login(
                username=email,
                password=password,  # Password discarded after this line
                locale=marketplace,
                with_username=False
            )

            # Password is now out of scope and will be garbage collected
            # Only the auth token remains

            # Get auth data as dictionary
            auth_dict = auth.to_dict()

            # Get device info
            device_name = auth_dict.get('device_name', 'Me Feed - Web')

            # Encrypt token with user-specific key
            auth_json = json.dumps(auth_dict)
            encrypted_token = security_service.encrypt_user_specific_data(
                auth_json,
                str(user_id)
            )

            logger.info(f"Audible authentication successful for user {user_id}, device: {device_name}")

            return {
                'success': True,
                'encrypted_token': encrypted_token,
                'device_name': device_name,
                'marketplace': marketplace,
                'authenticated_at': datetime.utcnow()
            }

        except audible.exceptions.BadRequest as e:
            error_msg = str(e)
            logger.warning(f"Audible bad request for user {user_id}: {error_msg}")

            if 'captcha' in error_msg.lower():
                raise AudibleCaptchaRequiredError(
                    "CAPTCHA verification required. Please try again later or use manual import."
                )
            elif '2fa' in error_msg.lower() or 'two-factor' in error_msg.lower():
                raise AudibleTwoFactorRequiredError(
                    "Two-factor authentication detected. Please append your 2FA code to your password."
                )
            else:
                raise AudibleAuthError(f"Authentication failed: {error_msg}")

        except audible.exceptions.Unauthorized:
            logger.warning(f"Audible unauthorized for user {user_id}")
            raise AudibleAuthError("Invalid email or password")

        except Exception as e:
            logger.error(f"Unexpected error during Audible auth for user {user_id}: {e}", exc_info=True)
            raise AudibleAuthError(f"Authentication error: {str(e)}")

    def decrypt_auth_token(self, encrypted_token: str, user_id: uuid.UUID) -> audible.Authenticator:
        """
        Decrypt stored auth token and create Authenticator

        Args:
            encrypted_token: Encrypted token from database
            user_id: User's UUID

        Returns:
            audible.Authenticator instance

        Raises:
            AudibleAuthError: If decryption fails
        """
        try:
            # Decrypt with user-specific key
            decrypted_json = security_service.decrypt_user_specific_data(
                encrypted_token,
                str(user_id)
            )

            # Parse JSON
            auth_dict = json.loads(decrypted_json)

            # Create authenticator from dict
            auth = audible.Authenticator.from_dict(auth_dict)

            return auth

        except Exception as e:
            logger.error(f"Failed to decrypt Audible token for user {user_id}: {e}")
            raise AudibleAuthError("Failed to decrypt authentication token")

    async def fetch_library(
        self,
        encrypted_token: str,
        user_id: uuid.UUID,
        num_results: int = 1000
    ) -> Dict[str, Any]:
        """
        Fetch user's Audible library

        Args:
            encrypted_token: Encrypted auth token
            user_id: User's UUID
            num_results: Maximum number of results to fetch (default: 1000)

        Returns:
            Dict containing library items and metadata

        Raises:
            AudibleAuthError: If token is invalid or API call fails
        """
        try:
            # Decrypt and create authenticator
            auth = self.decrypt_auth_token(encrypted_token, user_id)

            logger.info(f"Fetching Audible library for user {user_id}")

            # Create client and fetch library
            with audible.Client(auth=auth) as client:
                library_response = client.get(
                    "1.0/library",
                    num_results=num_results,
                    response_groups=(
                        "product_desc,product_attrs,media,series,rating,"
                        "contributors,product_details,product_extended_attrs,"
                        "customer_rights,relationships"
                    ),
                    sort_by="-PurchaseDate"
                )

            logger.info(f"Fetched {len(library_response.get('items', []))} books for user {user_id}")

            return library_response

        except audible.exceptions.Unauthorized:
            logger.warning(f"Audible token expired for user {user_id}")
            raise AudibleAuthError("Authentication token expired. Please reconnect your Audible account.")

        except Exception as e:
            logger.error(f"Error fetching Audible library for user {user_id}: {e}", exc_info=True)
            raise AudibleAuthError(f"Failed to fetch library: {str(e)}")

    async def deregister_device(
        self,
        encrypted_token: str,
        user_id: uuid.UUID
    ) -> bool:
        """
        Deregister the virtual device from user's Amazon account

        This removes the device from the user's Amazon device list.
        Should be called when user disconnects Audible integration.

        Args:
            encrypted_token: Encrypted auth token
            user_id: User's UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Decrypt and create authenticator
            auth = self.decrypt_auth_token(encrypted_token, user_id)

            logger.info(f"Deregistering Audible device for user {user_id}")

            # Deregister device
            auth.deregister_device()

            logger.info(f"Successfully deregistered Audible device for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Error deregistering Audible device for user {user_id}: {e}", exc_info=True)
            return False

    @classmethod
    def validate_marketplace(cls, marketplace: str) -> bool:
        """
        Validate marketplace code

        Args:
            marketplace: Marketplace code to validate

        Returns:
            True if valid, False otherwise
        """
        return marketplace.lower() in cls.MARKETPLACES

    @classmethod
    def get_marketplace_name(cls, marketplace: str) -> Optional[str]:
        """
        Get marketplace display name

        Args:
            marketplace: Marketplace code

        Returns:
            Display name or None if invalid
        """
        return cls.MARKETPLACES.get(marketplace.lower())

    async def test_connection(
        self,
        encrypted_token: str,
        user_id: uuid.UUID
    ) -> bool:
        """
        Test if stored auth token is still valid

        Args:
            encrypted_token: Encrypted auth token
            user_id: User's UUID

        Returns:
            True if connection works, False otherwise
        """
        try:
            # Try to fetch a minimal amount of data
            library = await self.fetch_library(encrypted_token, user_id, num_results=1)
            return 'items' in library

        except AudibleAuthError:
            return False
        except Exception as e:
            logger.error(f"Error testing Audible connection for user {user_id}: {e}")
            return False
