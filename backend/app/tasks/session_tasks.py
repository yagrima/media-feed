"""
Session Management Tasks
Handles periodic cleanup and maintenance of user sessions
"""
import logging
from datetime import datetime
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.db.models import UserSession
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    name='app.tasks.session_tasks.cleanup_expired_sessions',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def cleanup_expired_sessions(self):
    """
    Periodic task to clean up expired user sessions
    
    Runs daily at 2:00 AM UTC (configured in celery_app.py)
    Removes all sessions where expires_at < current_time
    
    Returns:
        dict: Statistics about cleaned sessions
    """
    try:
        import asyncio
        
        # Create async function for DB operations
        async def _cleanup():
            # Create async engine and session
            engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_pre_ping=True,
            )
            
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                try:
                    # Count expired sessions before deletion
                    count_query = select(UserSession).where(
                        UserSession.expires_at < datetime.utcnow()
                    )
                    result = await session.execute(count_query)
                    expired_sessions = result.scalars().all()
                    count = len(expired_sessions)
                    
                    if count == 0:
                        logger.info("No expired sessions to clean up")
                        return {
                            'status': 'success',
                            'deleted_count': 0,
                            'message': 'No expired sessions found'
                        }
                    
                    # Delete expired sessions
                    delete_query = delete(UserSession).where(
                        UserSession.expires_at < datetime.utcnow()
                    )
                    await session.execute(delete_query)
                    await session.commit()
                    
                    logger.info(
                        f"Successfully cleaned up {count} expired sessions",
                        extra={
                            'task': 'cleanup_expired_sessions',
                            'deleted_count': count
                        }
                    )
                    
                    return {
                        'status': 'success',
                        'deleted_count': count,
                        'message': f'Deleted {count} expired sessions',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                except Exception as db_error:
                    await session.rollback()
                    logger.error(
                        f"Database error during session cleanup: {str(db_error)}",
                        extra={'task': 'cleanup_expired_sessions'},
                        exc_info=True
                    )
                    raise
                    
                finally:
                    await engine.dispose()
        
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_cleanup())
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to cleanup expired sessions: {str(e)}",
            extra={'task': 'cleanup_expired_sessions'},
            exc_info=True
        )
        
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(name='app.tasks.session_tasks.get_session_stats')
def get_session_stats():
    """
    Get statistics about current sessions
    Useful for monitoring and debugging
    
    Returns:
        dict: Session statistics
    """
    import asyncio
    
    async def _get_stats():
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            try:
                # Count total sessions
                total_query = select(UserSession)
                total_result = await session.execute(total_query)
                total_count = len(total_result.scalars().all())
                
                # Count expired sessions
                expired_query = select(UserSession).where(
                    UserSession.expires_at < datetime.utcnow()
                )
                expired_result = await session.execute(expired_query)
                expired_count = len(expired_result.scalars().all())
                
                # Count active sessions
                active_count = total_count - expired_count
                
                return {
                    'total_sessions': total_count,
                    'active_sessions': active_count,
                    'expired_sessions': expired_count,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            finally:
                await engine.dispose()
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_get_stats())
