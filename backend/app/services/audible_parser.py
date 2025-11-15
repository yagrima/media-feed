"""
Audible Parser - Map Audible library data to Media and UserMedia models

This parser transforms data from Audible's API format into our database schema.
Handles audiobooks with rich metadata including authors, narrators, series info,
and listening progress.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.models import Media, UserMedia
from app.schemas.import_schemas import ImportSource

logger = logging.getLogger(__name__)


class AudibleParser:
    """Parser for Audible library data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_library(
        self,
        user_id: uuid.UUID,
        library_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Process entire Audible library and import to database

        Args:
            user_id: User's UUID
            library_data: Library response from Audible API

        Returns:
            Dict with import statistics (imported, updated, skipped, errors)
        """
        items = library_data.get('items', [])

        stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        logger.info(f"Processing {len(items)} Audible books for user {user_id}")

        for item in items:
            try:
                await self.process_item(user_id, item)
                stats['imported'] += 1

                # Commit every 10 items to avoid large transactions
                if stats['imported'] % 10 == 0:
                    await self.db.commit()

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing Audible item {item.get('asin')}: {e}", exc_info=True)
                # Rollback this item's transaction
                await self.db.rollback()

        # Final commit
        await self.db.commit()

        logger.info(f"Audible import complete for user {user_id}: {stats}")

        return stats

    async def process_item(
        self,
        user_id: uuid.UUID,
        item: Dict[str, Any]
    ) -> None:
        """
        Process a single Audible library item

        Args:
            user_id: User's UUID
            item: Audible library item data

        Raises:
            Exception: If processing fails
        """
        asin = item.get('asin')
        if not asin:
            raise ValueError("Missing ASIN in Audible item")

        # Check if we already have this audiobook
        media = await self._find_or_create_media(item)

        # Check if user already has this audiobook imported
        existing_user_media = await self.db.execute(
            select(UserMedia).where(
                (UserMedia.user_id == user_id) &
                (UserMedia.media_id == media.id)
            )
        )

        if existing_user_media.scalar_one_or_none():
            # Already imported, skip
            logger.debug(f"Audiobook {asin} already imported for user {user_id}")
            return

        # Create UserMedia entry
        user_media = self._create_user_media(user_id, media.id, item)
        self.db.add(user_media)

        await self.db.flush()

    async def _find_or_create_media(self, item: Dict[str, Any]) -> Media:
        """
        Find existing audiobook or create new Media entry

        Args:
            item: Audible library item data

        Returns:
            Media instance
        """
        asin = item['asin']

        # Check if media already exists by ASIN
        result = await self.db.execute(
            select(Media).where(
                Media.platform_ids['asin'].astext == asin
            )
        )
        existing_media = result.scalar_one_or_none()

        if existing_media:
            # Update metadata if needed
            existing_media.media_metadata = self._extract_metadata(item)
            existing_media.updated_at = datetime.utcnow()
            return existing_media

        # Create new media entry
        media = Media(
            title=self._extract_title(item),
            type='audiobook',
            release_date=self._parse_release_date(item),
            platform='audible',
            platform_ids={'asin': asin},
            media_metadata=self._extract_metadata(item)
        )

        self.db.add(media)
        await self.db.flush()

        return media

    def _create_user_media(
        self,
        user_id: uuid.UUID,
        media_id: uuid.UUID,
        item: Dict[str, Any]
    ) -> UserMedia:
        """
        Create UserMedia entry for audiobook consumption tracking

        Args:
            user_id: User's UUID
            media_id: Media UUID
            item: Audible library item data

        Returns:
            UserMedia instance
        """
        # Determine status based on listening progress
        percent_complete = item.get('percent_complete', 0)
        is_finished = item.get('is_finished', False)

        if is_finished or percent_complete >= 95:
            status = 'finished'
        elif percent_complete > 0:
            status = 'in_progress'
        else:
            status = 'not_started'

        # Parse purchase date
        purchase_date = self._parse_purchase_date(item)

        return UserMedia(
            user_id=user_id,
            media_id=media_id,
            platform='audible',
            status=status,
            consumed_at=purchase_date,
            imported_from=ImportSource.AUDIBLE_API.value,
            raw_import_data={
                'asin': item.get('asin'),
                'percent_complete': percent_complete,
                'is_finished': is_finished,
                'purchase_date': item.get('purchase_date'),
                'is_downloaded': item.get('is_downloaded', False),
                'is_returnable': item.get('is_returnable', False),
            }
        )

    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract clean title from Audible item"""
        return item.get('title', 'Unknown Title').strip()

    def _extract_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract rich metadata from Audible item

        Args:
            item: Audible library item

        Returns:
            Metadata dictionary for storage in JSONB
        """
        # Extract authors
        authors = []
        for author in item.get('authors', []):
            if isinstance(author, dict):
                authors.append(author.get('name', ''))
            else:
                authors.append(str(author))

        # Extract narrators
        narrators = []
        for narrator in item.get('narrators', []):
            if isinstance(narrator, dict):
                narrators.append(narrator.get('name', ''))
            else:
                narrators.append(str(narrator))

        # Extract series info
        series_info = None
        series_data = item.get('series', [])
        if series_data and isinstance(series_data, list) and len(series_data) > 0:
            series = series_data[0]
            if isinstance(series, dict):
                series_info = {
                    'title': series.get('title', ''),
                    'sequence': series.get('sequence', '')
                }

        # Extract runtime (handle None from extension scraping)
        runtime_minutes = item.get('runtime_length_min') or 0
        hours = runtime_minutes // 60
        minutes = runtime_minutes % 60

        # Build metadata
        metadata = {
            'authors': authors,
            'narrators': narrators,
            'duration_minutes': runtime_minutes,
            'duration_display': f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
            'publisher': item.get('publisher_name', ''),
            'language': item.get('language', 'en'),
            'rating': item.get('rating', {}).get('overall_distribution', {}).get('display_stars', 0),
            'num_ratings': item.get('rating', {}).get('num_reviews', 0),
            'asin': item.get('asin'),
            'audible_url': f"https://www.audible.com/pd/{item.get('asin', '')}",
            'sample_url': item.get('sample_url'),
            'subtitle': item.get('subtitle', ''),
            'merchandising_summary': item.get('merchandising_summary', ''),
        }

        # Add series info if available
        if series_info:
            metadata['series'] = series_info

        # Add cover images
        if 'product_images' in item:
            metadata['cover_images'] = item['product_images']

        return metadata

    def _parse_release_date(self, item: Dict[str, Any]) -> Optional[date]:
        """
        Parse release date from Audible item

        Args:
            item: Audible library item

        Returns:
            Date object or None if parsing fails
        """
        release_date_str = item.get('release_date')
        if not release_date_str:
            return None

        try:
            # Audible returns dates in ISO format (YYYY-MM-DD)
            return datetime.fromisoformat(release_date_str).date()
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse release date: {release_date_str}")
            return None

    def _parse_purchase_date(self, item: Dict[str, Any]) -> Optional[date]:
        """
        Parse purchase date from Audible item

        Args:
            item: Audible library item

        Returns:
            Date object or None if parsing fails
        """
        purchase_date_str = item.get('purchase_date')
        if not purchase_date_str:
            return None

        try:
            # Audible returns dates in ISO format with timezone
            # Example: "2024-01-15T10:30:00Z"
            dt = datetime.fromisoformat(purchase_date_str.replace('Z', '+00:00'))
            return dt.date()
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse purchase date: {purchase_date_str}")
            return None
