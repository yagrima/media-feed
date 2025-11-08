"""
Netflix CSV Parser - Parse Netflix viewing history CSV
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, Any
from datetime import datetime
import uuid

from app.db.models import Media, UserMedia
from app.schemas.import_schemas import ImportSource
from app.services.tmdb_client import get_tmdb_client
import logging

logger = logging.getLogger(__name__)


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

        # Search for media in database (ONE per series)
        media = await self._find_or_create_media(
            title=parsed_title['main_title'],
            media_type=parsed_title['type'],
            metadata=parsed_title['metadata']
        )

        # Check if this specific episode already imported (for TV series)
        season_num = parsed_title.get('season_number')
        episode_num = parsed_title.get('episode_number')
        episode_title_str = parsed_title.get('episode_title')
        
        # Build query with episode-specific constraint
        query = select(UserMedia).where(
            (UserMedia.user_id == user_id) &
            (UserMedia.media_id == media.id)
        )
        
        # For TV series, use episode_title as unique identifier
        # (episode_number may be NULL for non-English titles)
        if parsed_title['type'] == 'tv_series' and episode_title_str:
            query = query.where(
                (UserMedia.season_number == season_num) &
                (UserMedia.episode_title == episode_title_str)
            )
        elif parsed_title['type'] == 'tv_series' and episode_num is not None:
            # Fallback: use episode_number if available
            query = query.where(
                (UserMedia.season_number == season_num) &
                (UserMedia.episode_number == episode_num)
            )
        
        existing = await self.db.execute(query)
        
        if existing.scalar_one_or_none():
            # Episode already imported, skip
            return
        
        # Create new UserMedia entry (one per episode)
        user_media = UserMedia(
            user_id=user_id,
            media_id=media.id,
            platform='netflix',
            consumed_at=consumed_date,
            imported_from=ImportSource.NETFLIX_CSV.value,
            status='watched',
            season_number=season_num,
            episode_number=episode_num,
            episode_title=parsed_title.get('episode_title'),
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
            # Create ONE Media per series, multiple UserMedia per episode
            base_title = parts[0].strip()  # "Arcane"
            season_info = parts[1].strip()  # "Staffel 2"
            episode_info = ':'.join(parts[2:]).strip()  # Episode name
            
            # Extract season and episode numbers
            season_number = self._extract_season_number(season_info)
            episode_number = self._extract_episode_number(episode_info)

            return {
                'main_title': base_title,  # Series name for ONE Media entry
                'type': 'tv_series',
                'season_number': season_number,
                'episode_number': episode_number,
                'episode_title': episode_info,  # Full episode name
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

    def _extract_season_number(self, season_str: str) -> int:
        """
        Extract season number from season string
        
        Examples:
            "Staffel 2" -> 2
            "Season 1" -> 1
            "Limited Series" -> None
        
        Args:
            season_str: Season string from Netflix
            
        Returns:
            Season number or None
        """
        import re
        
        # Try to find number after "Staffel" or "Season"
        match = re.search(r'(?:staffel|season)\s*(\d+)', season_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Try to find standalone number
        match = re.search(r'\d+', season_str)
        if match:
            return int(match.group(0))
        
        return None
    
    def _extract_episode_number(self, episode_str: str) -> int:
        """
        Extract episode number from episode string
        
        Examples:
            "Episode 1: Title" -> 1
            "Kapitel 5" -> 5
            "Part 3" -> 3
            "Just a title" -> None
        
        Args:
            episode_str: Episode string from Netflix
            
        Returns:
            Episode number or None
        """
        import re
        
        # Try to find number after common episode keywords
        match = re.search(r'(?:episode|kapitel|part|teil)\s*(\d+)', episode_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Try to find leading number (e.g., "5. Title")
        match = re.match(r'(\d+)[.:]\s*', episode_str)
        if match:
            return int(match.group(1))
        
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime

        Supports multiple formats:
        - MM/DD/YYYY (US format with 4-digit year)
        - M/D/YY (US format with 2-digit year)
        - DD/MM/YYYY (European format)
        - YYYY-MM-DD (ISO format)

        Args:
            date_str: Date string

        Returns:
            Parsed datetime

        Raises:
            ValueError: If date format is invalid
        """
        # Remove quotes if present
        date_str = date_str.strip('"\'')

        # Try different formats (2-digit year formats first for Netflix)
        formats = [
            '%m/%d/%y',  # US format with 2-digit year (e.g., 6/26/25)
            '%d/%m/%y',  # European format with 2-digit year
            '%m/%d/%Y',  # US format with 4-digit year
            '%d/%m/%Y',  # European format with 4-digit year
            '%Y-%m-%d',  # ISO format
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%m-%d-%y',
            '%d-%m-%y'
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
        
        For TV series: Creates ONE Media per series (base_title)
        For movies: Creates ONE Media per movie

        Args:
            title: Media title (series name or movie name)
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
            # Update metadata if needed - JSONB requires special handling
            current_metadata = media.media_metadata or {}
            
            # Merge Netflix-specific metadata
            if 'netflix_imports' not in current_metadata:
                current_metadata['netflix_imports'] = []

            current_metadata['netflix_imports'].append({
                'imported_at': datetime.utcnow().isoformat(),
                'metadata': metadata
            })
            
            # Set the metadata and flag as modified for SQLAlchemy
            media.media_metadata = current_metadata
            flag_modified(media, 'media_metadata')

            # Update type if it was unknown
            if media.type in [None, 'unknown'] and media_type != 'unknown':
                media.type = media_type

            return media

        # Create new media entry (ONE per series/movie)
        media = Media(
            title=title,  # Series name for TV, movie name for movies
            base_title=title if media_type == 'tv_series' else None,  # For consistency
            type=media_type,
            platform_ids={'netflix': True},
            media_metadata={
                'source': 'netflix_csv',
                'imported_at': datetime.utcnow().isoformat(),
                **metadata
            }
        )

        self.db.add(media)
        await self.db.flush()

        # Fetch episode counts from TMDB for new TV series
        if media_type == 'tv_series':
            await self._enrich_with_tmdb_data(media)

        return media

    async def _enrich_with_tmdb_data(self, media: Media) -> None:
        """
        Enrich media with TMDB episode counts
        
        Args:
            media: Media object to enrich
        """
        # Skip if already has episode data
        if media.total_episodes is not None:
            return
        
        try:
            tmdb_client = get_tmdb_client()
            episode_data = await tmdb_client.get_series_episode_count(media.title)
            
            if episode_data:
                media.total_seasons = episode_data['total_seasons']
                media.total_episodes = episode_data['total_episodes']
                media.tmdb_id = episode_data['tmdb_id']
                media.last_tmdb_update = datetime.utcnow()
                
                logger.info(
                    f"TMDB: Enriched '{media.title}' with {episode_data['total_episodes']} "
                    f"episodes across {episode_data['total_seasons']} seasons"
                )
            else:
                logger.info(f"TMDB: No episode data found for '{media.title}'")
                
        except Exception as e:
            # Don't fail the import if TMDB lookup fails
            logger.warning(f"TMDB: Failed to enrich '{media.title}': {e}")
