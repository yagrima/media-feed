"""
Email notification service with template support
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional and notification emails"""

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.APP_NAME

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        template_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection"""
        try:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            smtp.starttls()

            if self.smtp_password:  # Only authenticate if password is set
                smtp.login(self.smtp_user, self.smtp_password)

            return smtp
        except Exception as e:
            logger.error(f"SMTP connection failed: {str(e)}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None
    ) -> bool:
        """
        Send an email with HTML and optional plain text fallback

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email content
            text_body: Plain text fallback (optional)
            to_name: Recipient name for display (optional)

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = formataddr((to_name or '', to_email))

            # Attach plain text version if provided
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            # Attach HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Send email
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_sequel_notification(
        self,
        to_email: str,
        user_name: str,
        sequel_title: str,
        original_title: str,
        platform: Optional[str] = None,
        release_date: Optional[str] = None,
        poster_url: Optional[str] = None,
        unsubscribe_token: Optional[str] = None
    ) -> bool:
        """
        Send notification about a detected sequel

        Args:
            to_email: User's email address
            user_name: User's display name
            sequel_title: Title of the new sequel
            original_title: Title of the media user watched
            platform: Platform where sequel is available
            release_date: Release date of sequel
            poster_url: URL to sequel poster image
            unsubscribe_token: Token for unsubscribe link

        Returns:
            bool: True if sent successfully
        """
        try:
            template_data = {
                'user_name': user_name,
                'sequel_title': sequel_title,
                'original_title': original_title,
                'platform': platform,
                'release_date': release_date,
                'poster_url': poster_url,
                'app_name': settings.APP_NAME,
                'unsubscribe_url': self._generate_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
            }

            # Render templates
            html_body = self._render_template('sequel_notification.html', template_data)
            text_body = self._render_template('sequel_notification.txt', template_data)

            subject = f"New sequel available: {sequel_title}"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                to_name=user_name
            )

        except Exception as e:
            logger.error(f"Failed to send sequel notification: {str(e)}")
            return False

    def send_daily_digest(
        self,
        to_email: str,
        user_name: str,
        sequels: List[Dict[str, Any]],
        unsubscribe_token: Optional[str] = None
    ) -> bool:
        """
        Send daily digest of all new sequels

        Args:
            to_email: User's email address
            user_name: User's display name
            sequels: List of sequel dictionaries with metadata
            unsubscribe_token: Token for unsubscribe link

        Returns:
            bool: True if sent successfully
        """
        if not sequels:
            logger.info(f"No sequels to send for {to_email}, skipping digest")
            return True

        try:
            template_data = {
                'user_name': user_name,
                'sequels': sequels,
                'sequel_count': len(sequels),
                'app_name': settings.APP_NAME,
                'unsubscribe_url': self._generate_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
            }

            html_body = self._render_template('daily_digest.html', template_data)
            text_body = self._render_template('daily_digest.txt', template_data)

            subject = f"{len(sequels)} new sequel{'s' if len(sequels) != 1 else ''} found"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                to_name=user_name
            )

        except Exception as e:
            logger.error(f"Failed to send daily digest: {str(e)}")
            return False

    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification link

        Args:
            to_email: User's email address
            user_name: User's display name
            verification_token: Email verification token

        Returns:
            bool: True if sent successfully
        """
        try:
            verification_url = f"{settings.ALLOWED_ORIGINS.split(',')[0]}/verify-email?token={verification_token}"

            template_data = {
                'user_name': user_name,
                'verification_url': verification_url,
                'app_name': settings.APP_NAME
            }

            html_body = self._render_template('email_verification.html', template_data)
            text_body = self._render_template('email_verification.txt', template_data)

            subject = f"Verify your {settings.APP_NAME} account"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                to_name=user_name
            )

        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email with secure token

        Args:
            to_email: User's email address
            reset_token: Password reset token

        Returns:
            bool: True if sent successfully
        """
        try:
            # Generate reset URL (using frontend URL)
            reset_url = f"{settings.ALLOWED_ORIGINS.split(',')[0]}/reset-password?token={reset_token}"
            
            # Prepare email data
            template_data = {
                'reset_url': reset_url,
                'app_name': settings.APP_NAME,
                'support_email': settings.FROM_EMAIL
            }

            # Render templates (using email_verification templates as base)
            html_body = self._render_template('password_reset.html', template_data)
            text_body = self._render_template('password_reset.txt', template_data)
            
            subject = f"Reset your {settings.APP_NAME} password"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template

        Args:
            template_name: Name of template file
            data: Template context data

        Returns:
            str: Rendered template
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Template rendering failed for {template_name}: {str(e)}")
            # Return basic fallback
            if template_name.endswith('.txt'):
                return f"New notification from {settings.APP_NAME}. Please check the app for details."
            else:
                return f"<p>New notification from {settings.APP_NAME}. Please check the app for details.</p>"

    def _generate_unsubscribe_url(self, token: str) -> str:
        """Generate unsubscribe URL from token"""
        base_url = settings.ALLOWED_ORIGINS.split(',')[0]
        return f"{base_url}/api/notifications/unsubscribe?token={token}"


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
