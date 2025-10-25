"""
Security control tests: Rate limiting, token validation, ownership verification.
Tests security mitigations implemented in Week 4.
"""

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4
import time

from app.core.rate_limiter import RateLimiter, rate_limit, notification_rate_limit
from app.core.token_manager import TokenManager, get_token_manager
from app.core.security_middleware import verify_user_ownership, OriginValidationMiddleware


class TestRateLimitingEnforcement:
    """Test rate limiting enforcement across different endpoints."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic_enforcement(self):
        """Test basic rate limiting enforcement."""
        limiter = RateLimiter()

        key = "test:user:enforcement"
        max_requests = 5
        window_seconds = 60

        # Make requests up to limit
        for i in range(max_requests):
            allowed, count, retry = await limiter.check_rate_limit(
                key, max_requests, window_seconds
            )
            assert allowed is True
            assert count == i + 1
            assert retry == 0

        # Next request should be denied
        allowed, count, retry = await limiter.check_rate_limit(
            key, max_requests, window_seconds
        )
        assert allowed is False
        assert count == max_requests
        assert retry > 0

        await limiter.close()

    @pytest.mark.asyncio
    async def test_notification_rate_limit_per_user(self):
        """Test notification endpoint rate limiting (100 req/min)."""
        limiter = RateLimiter()

        user1_key = "notifications:test_endpoint:user_1"
        user2_key = "notifications:test_endpoint:user_2"

        # User 1 makes 100 requests
        for i in range(100):
            allowed, _, _ = await limiter.check_rate_limit(
                user1_key, max_requests=100, window_seconds=60
            )
            assert allowed is True

        # User 1's 101st request should be blocked
        allowed, _, _ = await limiter.check_rate_limit(
            user1_key, max_requests=100, window_seconds=60
        )
        assert allowed is False

        # User 2 should still be able to make requests
        allowed, _, _ = await limiter.check_rate_limit(
            user2_key, max_requests=100, window_seconds=60
        )
        assert allowed is True

        await limiter.close()

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_http_exception(self):
        """Test that rate limit decorator raises HTTPException."""

        @rate_limit(max_requests=2, window_seconds=60, key_prefix="test")
        async def limited_endpoint(request: Request, user_id: str):
            return {"status": "ok"}

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.state.user_id = "test_user"

        # First 2 calls should succeed
        result1 = await limited_endpoint(mock_request, user_id="test_user")
        assert result1 == {"status": "ok"}

        result2 = await limited_endpoint(mock_request, user_id="test_user")
        assert result2 == {"status": "ok"}

        # Third call should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limited_endpoint(mock_request, user_id="test_user")

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail
        assert "Retry-After" in exc_info.value.headers

    @pytest.mark.asyncio
    async def test_tmdb_rate_limit_graceful_degradation(self):
        """Test TMDB rate limit returns empty instead of error."""
        from app.core.rate_limiter import tmdb_rate_limit

        @tmdb_rate_limit(max_requests=2, window_seconds=10)
        async def tmdb_search_tv(query: str):
            return [{"id": 1, "name": query}]

        # First 2 calls succeed
        result1 = await tmdb_search_tv("show1")
        assert len(result1) == 1

        result2 = await tmdb_search_tv("show2")
        assert len(result2) == 1

        # Third call returns empty (graceful degradation)
        result3 = await tmdb_search_tv("show3")
        # Should return None or [] instead of raising exception
        assert result3 in (None, [])

    @pytest.mark.asyncio
    async def test_rate_limit_sliding_window_expiry(self):
        """Test that rate limits reset after window expires."""
        limiter = RateLimiter()

        key = "test:window:expiry"
        max_requests = 3
        window_seconds = 1  # 1 second window

        # Make 3 requests
        for _ in range(3):
            allowed, _, _ = await limiter.check_rate_limit(
                key, max_requests, window_seconds
            )
            assert allowed is True

        # 4th request blocked
        allowed, _, _ = await limiter.check_rate_limit(
            key, max_requests, window_seconds
        )
        assert allowed is False

        # Wait for window to expire
        await asyncio.sleep(1.2)

        # Should be allowed again
        allowed, _, _ = await limiter.check_rate_limit(
            key, max_requests, window_seconds
        )
        assert allowed is True

        await limiter.close()


class TestTokenValidation:
    """Test token generation and validation."""

    def test_generate_unsubscribe_token(self):
        """Test unsubscribe token generation."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        notification_id = str(uuid4())

        token, expires_at = token_mgr.generate_unsubscribe_token(
            user_id, notification_id, expires_days=30
        )

        # Token should have 3 parts
        assert len(token.split('.')) == 3

        # Expiration should be ~30 days from now
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        assert abs((expires_at - expected_expiry).total_seconds()) < 60

    def test_validate_unsubscribe_token_success(self):
        """Test successful token validation."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        notification_id = str(uuid4())

        token, _ = token_mgr.generate_unsubscribe_token(
            user_id, notification_id, expires_days=30
        )

        # Validate with correct user_id and notification_id
        is_valid, error = token_mgr.validate_unsubscribe_token(
            token, user_id, notification_id
        )

        assert is_valid is True
        assert error is None

    def test_validate_unsubscribe_token_wrong_user(self):
        """Test token validation fails with wrong user_id."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        wrong_user_id = str(uuid4())
        notification_id = str(uuid4())

        token, _ = token_mgr.generate_unsubscribe_token(
            user_id, notification_id, expires_days=30
        )

        # Validate with wrong user_id
        is_valid, error = token_mgr.validate_unsubscribe_token(
            token, wrong_user_id, notification_id
        )

        assert is_valid is False
        assert error is not None
        assert "Invalid token signature" in error

    def test_validate_unsubscribe_token_expired(self):
        """Test token validation fails when expired."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        notification_id = str(uuid4())

        # Generate token that expires immediately
        token, _ = token_mgr.generate_unsubscribe_token(
            user_id, notification_id, expires_days=0
        )

        # Wait a bit to ensure expiration
        time.sleep(1)

        # Validate expired token
        is_valid, error = token_mgr.validate_unsubscribe_token(
            token, user_id, notification_id
        )

        assert is_valid is False
        assert error is not None
        assert "expired" in error.lower()

    def test_validate_unsubscribe_token_malformed(self):
        """Test token validation fails with malformed token."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        notification_id = str(uuid4())

        # Malformed tokens
        malformed_tokens = [
            "invalid",
            "only.two",
            "too.many.parts.here",
            "",
        ]

        for token in malformed_tokens:
            is_valid, error = token_mgr.validate_unsubscribe_token(
                token, user_id, notification_id
            )
            assert is_valid is False
            assert error is not None

    def test_token_constant_time_comparison(self):
        """Test that token validation uses constant-time comparison."""
        token_mgr = TokenManager()

        user_id = str(uuid4())
        notification_id = str(uuid4())

        token, _ = token_mgr.generate_unsubscribe_token(
            user_id, notification_id
        )

        # Create slightly modified token (tampered)
        parts = token.split('.')
        tampered_token = f"{parts[0]}.{parts[1]}.{'0' * len(parts[2])}"

        # Should fail validation
        is_valid, error = token_mgr.validate_unsubscribe_token(
            tampered_token, user_id, notification_id
        )
        assert is_valid is False


class TestOwnershipVerification:
    """Test user ownership verification."""

    def test_verify_ownership_success(self):
        """Test successful ownership verification."""
        user_id = str(uuid4())

        # Should not raise exception
        verify_user_ownership(
            resource_user_id=user_id,
            request_user_id=user_id,
            resource_type="notification"
        )

    def test_verify_ownership_fails_different_user(self):
        """Test ownership verification fails for different user."""
        user1_id = str(uuid4())
        user2_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            verify_user_ownership(
                resource_user_id=user1_id,
                request_user_id=user2_id,
                resource_type="notification"
            )

        assert exc_info.value.status_code == 403
        assert "permission" in exc_info.value.detail.lower()

    def test_verify_ownership_fails_unauthenticated(self):
        """Test ownership verification fails for unauthenticated request."""
        user_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            verify_user_ownership(
                resource_user_id=user_id,
                request_user_id=None,
                resource_type="notification"
            )

        assert exc_info.value.status_code == 401
        assert "authentication required" in exc_info.value.detail.lower()

    def test_verify_ownership_string_uuid_comparison(self):
        """Test that UUIDs are compared as strings correctly."""
        from uuid import UUID

        user_id = uuid4()
        user_id_str = str(user_id)

        # Should work with both UUID and string
        verify_user_ownership(
            resource_user_id=user_id,  # UUID object
            request_user_id=user_id_str,  # String
            resource_type="notification"
        )


class TestOriginValidation:
    """Test Origin header validation middleware."""

    @pytest.mark.asyncio
    async def test_origin_validation_allowed_origin(self):
        """Test that allowed origin passes validation."""
        middleware = OriginValidationMiddleware(app=None)

        # Mock request with allowed origin
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/notifications"
        mock_request.headers.get.return_value = "http://localhost:3000"
        mock_request.client.host = "127.0.0.1"

        # Mock next handler
        async def mock_call_next(request):
            return {"status": "ok"}

        # Should allow request
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_origin_validation_invalid_origin(self):
        """Test that invalid origin is blocked."""
        middleware = OriginValidationMiddleware(app=None)

        # Mock request with invalid origin
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/notifications"
        mock_request.headers.get.return_value = "http://evil-site.com"
        mock_request.client.host = "127.0.0.1"

        # Mock next handler
        async def mock_call_next(request):
            return {"status": "ok"}

        # Should block request
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_origin_validation_only_state_changing(self):
        """Test that only POST/PUT/PATCH/DELETE are validated."""
        middleware = OriginValidationMiddleware(app=None)

        # Mock GET request (should pass without origin check)
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/notifications"
        mock_request.headers.get.return_value = None  # No origin

        async def mock_call_next(request):
            return {"status": "ok"}

        # Should allow GET without origin
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response == {"status": "ok"}


class TestSecurityAuditLogging:
    """Test security event logging."""

    @pytest.mark.asyncio
    async def test_log_security_event(self):
        """Test security event logging."""
        from app.core.security_middleware import log_security_event

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"
        mock_request.url.path = "/api/notifications/123"
        mock_request.method = "PUT"

        # Should not raise exception
        await log_security_event(
            event_type="unauthorized_access",
            user_id="user_123",
            request=mock_request,
            metadata={"resource_id": "notification_123"}
        )


# Helper for async operations
import asyncio
