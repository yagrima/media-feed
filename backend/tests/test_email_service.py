"""
Unit tests for EmailService.
Tests email sending, template rendering, and SMTP connection handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart

from app.services.email_service import EmailService, get_email_service


class TestEmailServiceInitialization:
    """Test EmailService initialization."""

    @patch('app.services.email_service.settings')
    def test_initialization_with_config(self, mock_settings):
        """Test service initializes with correct configuration."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        service = EmailService()

        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 587
        assert service.smtp_user == "test@example.com"
        assert service.smtp_password == "password123"
        assert service.from_email == "noreply@example.com"
        assert service.from_name == "Me Feed"

    def test_jinja_environment_created(self):
        """Test Jinja2 environment is properly initialized."""
        service = EmailService()

        assert service.jinja_env is not None
        assert service.jinja_env.autoescape is not None


class TestSMTPConnection:
    """Test SMTP connection handling."""

    @patch('smtplib.SMTP')
    @patch('app.services.email_service.settings')
    def test_create_smtp_connection_success(self, mock_settings, mock_smtp_class):
        """Test successful SMTP connection."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        # Setup mock SMTP instance
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        smtp_conn = service._create_smtp_connection()

        # Verify SMTP initialized correctly
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=10)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("test@example.com", "password123")

    @patch('smtplib.SMTP')
    @patch('app.services.email_service.settings')
    def test_create_smtp_connection_no_password(self, mock_settings, mock_smtp_class):
        """Test SMTP connection without password (no auth)."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = None
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        smtp_conn = service._create_smtp_connection()

        # Verify login not called without password
        mock_smtp_instance.login.assert_not_called()

    @patch('smtplib.SMTP')
    @patch('app.services.email_service.settings')
    def test_create_smtp_connection_failure(self, mock_settings, mock_smtp_class):
        """Test SMTP connection failure handling."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        # Make SMTP raise exception
        mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")

        service = EmailService()

        with pytest.raises(smtplib.SMTPException):
            service._create_smtp_connection()


class TestSendEmail:
    """Test basic email sending."""

    @patch.object(EmailService, '_create_smtp_connection')
    @patch('app.services.email_service.settings')
    def test_send_email_success(self, mock_settings, mock_create_smtp):
        """Test successful email sending."""
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"

        # Mock SMTP connection
        mock_smtp = MagicMock()
        mock_create_smtp.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_create_smtp.return_value.__exit__ = Mock(return_value=False)

        service = EmailService()
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<p>Test HTML</p>",
            text_body="Test Text",
            to_name="Recipient Name"
        )

        assert success is True
        mock_smtp.send_message.assert_called_once()

    @patch.object(EmailService, '_create_smtp_connection')
    @patch('app.services.email_service.settings')
    def test_send_email_without_text_body(self, mock_settings, mock_create_smtp):
        """Test email sending without text fallback."""
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"

        mock_smtp = MagicMock()
        mock_create_smtp.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_create_smtp.return_value.__exit__ = Mock(return_value=False)

        service = EmailService()
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<p>Test HTML</p>"
        )

        assert success is True

    @patch.object(EmailService, '_create_smtp_connection')
    @patch('app.services.email_service.settings')
    def test_send_email_failure(self, mock_settings, mock_create_smtp):
        """Test email sending failure handling."""
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"

        # Make SMTP raise exception
        mock_create_smtp.side_effect = Exception("SMTP error")

        service = EmailService()
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<p>Test HTML</p>"
        )

        assert success is False


class TestTemplateRendering:
    """Test email template rendering."""

    @patch('app.services.email_service.settings')
    def test_render_template_success(self, mock_settings):
        """Test successful template rendering."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        service = EmailService()

        # Mock template
        mock_template = MagicMock()
        mock_template.render.return_value = "<p>Rendered HTML</p>"
        service.jinja_env.get_template = Mock(return_value=mock_template)

        result = service._render_template(
            'test_template.html',
            {'var': 'value'}
        )

        assert result == "<p>Rendered HTML</p>"
        mock_template.render.assert_called_once_with(var='value')

    @patch('app.services.email_service.settings')
    def test_render_template_failure_fallback_html(self, mock_settings):
        """Test template rendering failure with HTML fallback."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        service = EmailService()
        service.jinja_env.get_template = Mock(side_effect=Exception("Template not found"))

        result = service._render_template('missing.html', {})

        assert "<p>" in result
        assert "Me Feed" in result

    @patch('app.services.email_service.settings')
    def test_render_template_failure_fallback_text(self, mock_settings):
        """Test template rendering failure with text fallback."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        service = EmailService()
        service.jinja_env.get_template = Mock(side_effect=Exception("Template not found"))

        result = service._render_template('missing.txt', {})

        assert "Me Feed" in result
        assert "<p>" not in result  # Should be plain text


class TestSequelNotification:
    """Test sequel notification email."""

    @patch.object(EmailService, 'send_email')
    @patch.object(EmailService, '_render_template')
    @patch('app.services.email_service.settings')
    def test_send_sequel_notification_success(
        self,
        mock_settings,
        mock_render,
        mock_send
    ):
        """Test sending sequel notification."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.ALLOWED_ORIGINS = "https://app.example.com"

        mock_render.return_value = "<html>Test</html>"
        mock_send.return_value = True

        service = EmailService()
        success = service.send_sequel_notification(
            to_email="user@example.com",
            user_name="Test User",
            sequel_title="Stranger Things: Season 5",
            original_title="Stranger Things: Season 4",
            platform="netflix",
            release_date="2024-07-15",
            poster_url="https://image.tmdb.org/poster.jpg",
            unsubscribe_token="test_token_123"
        )

        assert success is True
        mock_send.assert_called_once()

        # Verify template rendering was called with correct data
        assert mock_render.call_count == 2  # HTML and text templates
        html_call = mock_render.call_args_list[0]
        assert html_call[0][0] == 'sequel_notification.html'
        assert html_call[0][1]['sequel_title'] == "Stranger Things: Season 5"
        assert html_call[0][1]['original_title'] == "Stranger Things: Season 4"

    @patch.object(EmailService, '_render_template')
    @patch('app.services.email_service.settings')
    def test_send_sequel_notification_failure(self, mock_settings, mock_render):
        """Test sequel notification sending failure."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        mock_render.side_effect = Exception("Template error")

        service = EmailService()
        success = service.send_sequel_notification(
            to_email="user@example.com",
            user_name="Test User",
            sequel_title="Test",
            original_title="Test"
        )

        assert success is False


class TestDailyDigest:
    """Test daily digest email."""

    @patch.object(EmailService, 'send_email')
    @patch.object(EmailService, '_render_template')
    @patch('app.services.email_service.settings')
    def test_send_daily_digest_success(
        self,
        mock_settings,
        mock_render,
        mock_send
    ):
        """Test sending daily digest."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.ALLOWED_ORIGINS = "https://app.example.com"

        mock_render.return_value = "<html>Digest</html>"
        mock_send.return_value = True

        sequels = [
            {
                'sequel_title': 'Show: Season 2',
                'original_title': 'Show: Season 1',
                'platform': 'netflix'
            },
            {
                'sequel_title': 'Movie 2',
                'original_title': 'Movie 1',
                'platform': 'prime'
            }
        ]

        service = EmailService()
        success = service.send_daily_digest(
            to_email="user@example.com",
            user_name="Test User",
            sequels=sequels,
            unsubscribe_token="test_token"
        )

        assert success is True

        # Verify template data
        html_call = mock_render.call_args_list[0]
        assert html_call[0][1]['sequel_count'] == 2
        assert len(html_call[0][1]['sequels']) == 2

    @patch('app.services.email_service.settings')
    def test_send_daily_digest_empty_sequels(self, mock_settings):
        """Test daily digest with no sequels (should skip)."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"

        service = EmailService()
        success = service.send_daily_digest(
            to_email="user@example.com",
            user_name="Test User",
            sequels=[],
            unsubscribe_token="test_token"
        )

        # Should return True but not send email
        assert success is True


class TestVerificationEmail:
    """Test email verification email."""

    @patch.object(EmailService, 'send_email')
    @patch.object(EmailService, '_render_template')
    @patch('app.services.email_service.settings')
    def test_send_verification_email_success(
        self,
        mock_settings,
        mock_render,
        mock_send
    ):
        """Test sending verification email."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.ALLOWED_ORIGINS = "https://app.example.com"

        mock_render.return_value = "<html>Verify</html>"
        mock_send.return_value = True

        service = EmailService()
        success = service.send_verification_email(
            to_email="user@example.com",
            user_name="Test User",
            verification_token="verify_token_123"
        )

        assert success is True

        # Verify verification URL constructed correctly
        html_call = mock_render.call_args_list[0]
        assert 'verification_url' in html_call[0][1]
        assert 'verify_token_123' in html_call[0][1]['verification_url']


class TestUnsubscribeURL:
    """Test unsubscribe URL generation."""

    @patch('app.services.email_service.settings')
    def test_generate_unsubscribe_url(self, mock_settings):
        """Test unsubscribe URL generation."""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.FROM_EMAIL = "noreply@example.com"
        mock_settings.APP_NAME = "Me Feed"
        mock_settings.ALLOWED_ORIGINS = "https://app.example.com,https://other.com"

        service = EmailService()
        url = service._generate_unsubscribe_url("test_token_123")

        assert url == "https://app.example.com/api/notifications/unsubscribe?token=test_token_123"


class TestEmailServiceSingleton:
    """Test singleton pattern for EmailService."""

    def test_get_email_service_singleton(self):
        """Test that get_email_service returns same instance."""
        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2
