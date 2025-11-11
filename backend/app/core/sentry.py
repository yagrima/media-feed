import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging

logger = logging.getLogger(__name__)

def init_sentry(dsn: str, environment: str = "production", version: str = "1.1.0"):
    """
    Initialize Sentry error tracking
    
    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (production, development, etc.)
        version: Application version for release tracking
    """
    if not dsn:
        logger.warning("SENTRY_DSN not configured - error tracking disabled")
        return
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=environment,
            release=f"me-feed-backend@{version}",
            send_default_pii=False,
        )
        logger.info(f"Sentry initialized successfully for environment: {environment}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
