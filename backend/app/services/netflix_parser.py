"""
Netflix CSV Parser - Parse Netflix viewing history CSV
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime
import uuid

from app.db.models import Media, UserMedia
from app.schemas.import_schemas import ImportSource


class NetflixCSVParser:
    """
    Parser for Netflix viewing history CSV files

    Expected CSV format:
    Title,Date
    "Breaking Bad: Season 1: \"Pilot\"","01/20/2024"
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_row(self, user_id: uuid.UUID, row: Dict[str, Any]) -> None:
        """
        Process a single CSV row

        Args:
            user_id: User ID
            row: CSV row dictionary

        Raises:
            ValueError: If row is invalid
        """
        # Extract title and date
        title = row.get('Title', '').strip()
        date_str = row.get('Date', '').strip()

        if not title:
            raise ValueError("Missing title")

        # Parse Netflix title format
        # Format: "Show Name: Season X: Episode Name" or "Movie Name"
        parsed_title = self._parse_netflix_title(title)

        # Parse date
        consumed_date = self._parse_date(date_str) if date_str else None

        # Search for media in database
        media = await self._find_or_create_media(
            title=parsed_title['main_title'],
            media_type=parsed_title['type'],
            metadata=parsed_title['metadata']
        )

        # Check if already imported
        existing = await self.db.execute(
            select(UserMedia).where(
                (UserMedia.user_id == user_id) &
                (UserMedia.media_id == media.id)
            )
        )

        if existing.scalar_one_or_none():
            # Update existing entry
            user_media = existing.scalar_one()
            user_media.consumed_at = consumed_date
            user_media.raw_import_data = {
                'original_title': title,
                'date': date_str,
                'updated_at': datetime.utcnow().isoformat()
            }
        else:
            # Create new entry
            user_media = UserMedia(
                user_id=user_id,
                media_id=media.id,
                platform='netflix',
                consumed_at=consumed_date,
                imported_from=ImportSource.NETFLIX_CSV.value,
                status='watched',
                raw_import_data={
                    'original_title': title,
                    'date': date_str
                }
            )
            self.db.add(user_media)

        await self.db.flush()

    def _parse_netflix_title(self, title: str) -> Dict[str, Any]:
        """
        Parse Netflix title format

        Args:
            title: Netflix title string

        Returns:
            Parsed title information
        """
        # Netflix format: "Show: Season X: Episode" or just "Movie"
        parts = title.split(':')

        if len(parts) >= 3:
            # TV series with season/episode
            main_title = parts[0].strip()
            season_info = parts[1].strip()
            episode_info = ':'.join(parts[2:]).strip()

            return {
                'main_title': main_title,
                'type': 'tv_series',
                'metadata': {
                    'season': season_info,
                    'episode': episode_info,
                    'full_title': title
                }
            }
        elif len(parts) == 2:
            # Might be "Show: Special" or "Movie: Part 1"
            main_title = parts[0].strip()
            subtitle = parts[1].strip()

            # Check if it's a season indicator
            if 'season' in subtitle.lower() or 'limited series' in subtitle.lower():
                return {
                    'main_title': main_title,
                    'type': 'tv_series',
                    'metadata': {
                        'season': subtitle,
                        'full_title': title
                    }
                }
            else:
                return {
                    'main_title': main_title,
                    'type': 'movie',
                    'metadata': {
                        'subtitle': subtitle,
                        'full_title': title
                    }
                }
        else:
            # Single title - likely a movie
            return {
                'main_title': title.strip(),
                'type': 'movie',
                'metadata': {
                    'full_title': title
                }
            }

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime

        Supports multiple formats:
        - MM/DD/YYYY
        - DD/MM/YYYY
        - YYYY-MM-DD

        Args:
            date_str: Date string

        Returns:
            Parsed datetime

        Raises:
            ValueError: If date format is invalid
        """
        # Remove quotes if present
        date_str = date_str.strip('"\'')

        # Try different formats
        formats = [
            '%m/%d/%Y',  # US format
            '%d/%m/%Y',  # European format
            '%Y-%m-%d',  # ISO format
            '%m-%d-%Y',
            '%d-%m-%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If no format works, raise error
        raise ValueError(f"Unable to parse date: {date_str}")

    async def _find_or_create_media(
        self,
        title: str,
        media_type: str,
        metadata: Dict[str, Any]
    ) -> Media:
        """
        Find existing media or create new entry

        Args:
            title: Media title
            media_type: Type of media
            metadata: Additional metadata

        Returns:
            Media object
        """
        # Try to find existing media by title (case-insensitive)
        result = await self.db.execute(
            select(Media).where(
                func.lower(Media.title) == title.lower()
            ).limit(1)
        )
        media = result.scalar_one_or_none()

        if media:
            # Update metadata if needed
            if media.metadata is None:
                media.metadata = {}

            # Merge Netflix-specific metadata
            if 'netflix_imports' not in media.metadata:
                media.metadata['netflix_imports'] = []

            media.metadata['netflix_imports'].append({
                'imported_at': datetime.utcnow().isoformat(),
                'metadata': metadata
            })

            # Update type if it was unknown
            if media.type in [None, 'unknown'] and media_type != 'unknown':
                media.type = media_type

            return media

        # Create new media entry
        media = Media(
            title=title,
            type=media_type,
            platform_ids={'netflix': True},
            metadata={
                'source': 'netflix_csv',
                'imported_at': datetime.utcnow().isoformat(),
                **metadata
            }
        )

        self.db.add(media)
        await self.db.flush()

        return media
