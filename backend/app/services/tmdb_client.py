"""
TMDB (The Movie Database) API client for metadata enrichment.

This service integrates with TMDB API to:
- Search for TV series and movies
- Get season information
- Enrich media with metadata (posters, descriptions, release dates)
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.config import settings
from app.core.cache import tmdb_cached
from app.core.rate_limiter import tmdb_rate_limit


logger = logging.getLogger(__name__)


class TMDBClient:
    """Client for interacting with TMDB API."""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TMDB client.

        Args:
            api_key: TMDB API key (defaults to settings.TMDB_API_KEY)
        """
        self.api_key = api_key or getattr(settings, 'TMDB_API_KEY', None)
        self.client = httpx.AsyncClient(timeout=10.0)

    @tmdb_rate_limit()
    @tmdb_cached(ttl_seconds=86400)  # 24 hour cache
    async def search_tv(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for TV series on TMDB.

        Args:
            query: TV series title to search
            year: Optional year filter

        Returns:
            List of TV series results
        """
        if not self.api_key:
            logger.warning("TMDB API key not configured, skipping search")
            return []

        try:
            params = {
                'api_key': self.api_key,
                'query': query,
                'page': 1,
            }
            if year:
                params['first_air_date_year'] = year

            response = await self.client.get(
                f"{self.BASE_URL}/search/tv",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error during TV search: {e}")
            return []

    @tmdb_rate_limit()
    @tmdb_cached(ttl_seconds=86400)
    async def search_movie(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for movies on TMDB.

        Args:
            query: Movie title to search
            year: Optional year filter

        Returns:
            List of movie results
        """
        if not self.api_key:
            logger.warning("TMDB API key not configured, skipping search")
            return []

        try:
            params = {
                'api_key': self.api_key,
                'query': query,
                'page': 1,
            }
            if year:
                params['year'] = year

            response = await self.client.get(
                f"{self.BASE_URL}/search/movie",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error during movie search: {e}")
            return []

    @tmdb_rate_limit()
    @tmdb_cached(ttl_seconds=604800)  # 7 day cache (episode counts don't change often)
    async def get_tv_details(self, tv_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a TV series.

        Args:
            tv_id: TMDB TV series ID

        Returns:
            TV series details or None if not found
        """
        if not self.api_key:
            return None

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/tv/{tv_id}",
                params={'api_key': self.api_key}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error getting TV details: {e}")
            return None

    async def get_season_details(
        self,
        tv_id: int,
        season_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific season.

        Args:
            tv_id: TMDB TV series ID
            season_number: Season number

        Returns:
            Season details including episodes, air dates, etc.
        """
        if not self.api_key:
            return None

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/tv/{tv_id}/season/{season_number}",
                params={'api_key': self.api_key}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error getting season details: {e}")
            return None

    async def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a movie.

        Args:
            movie_id: TMDB movie ID

        Returns:
            Movie details or None if not found
        """
        if not self.api_key:
            return None

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                params={'api_key': self.api_key}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error getting movie details: {e}")
            return None

    async def get_series_episode_count(self, series_name: str, year: Optional[int] = None) -> Optional[Dict[str, int]]:
        """
        Get total episode count for a TV series.

        Args:
            series_name: Name of the TV series
            year: Optional year for better matching

        Returns:
            Dictionary with 'total_seasons', 'total_episodes', 'tmdb_id' or None if not found
        """
        if not self.api_key:
            logger.warning("TMDB API key not configured, cannot fetch episode counts")
            return None

        try:
            # Search for the series
            results = await self.search_tv(series_name, year)
            if not results:
                logger.info(f"TMDB: No results found for '{series_name}'")
                return None

            # Get first (best) match
            best_match = results[0]
            tv_id = best_match.get('id')
            
            # Get detailed info
            details = await self.get_tv_details(tv_id)
            if not details:
                logger.warning(f"TMDB: Could not get details for TV ID {tv_id}")
                return None

            # Extract episode counts
            total_seasons = details.get('number_of_seasons', 0)
            total_episodes = details.get('number_of_episodes', 0)

            if total_episodes > 0:
                logger.info(f"TMDB: Found {total_episodes} episodes across {total_seasons} seasons for '{series_name}'")
                return {
                    'total_seasons': total_seasons,
                    'total_episodes': total_episodes,
                    'tmdb_id': tv_id
                }
            else:
                logger.warning(f"TMDB: No episode data for '{series_name}'")
                return None

        except Exception as e:
            logger.error(f"TMDB: Error fetching episode count for '{series_name}': {e}")
            return None

    async def find_best_match(
        self,
        title: str,
        media_type: str,
        year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching media on TMDB.

        Args:
            title: Media title to search
            media_type: Type of media ('tv_series' or 'movie')
            year: Optional year for better matching

        Returns:
            Best match result or None
        """
        if media_type == 'tv_series':
            results = await self.search_tv(title, year)
        else:
            results = await self.search_movie(title, year)

        if not results:
            return None

        # Return first result (TMDB orders by relevance)
        return results[0]

    async def enrich_media_metadata(
        self,
        title: str,
        media_type: str,
        season_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich media with metadata from TMDB.

        Args:
            title: Media title
            media_type: Type ('tv_series' or 'movie')
            season_number: Optional season number for TV series
            year: Optional release year

        Returns:
            Enriched metadata dictionary
        """
        metadata = {
            'tmdb_id': None,
            'imdb_id': None,
            'poster_url': None,
            'backdrop_url': None,
            'overview': None,
            'release_date': None,
            'genres': [],
            'rating': None,
        }

        # Find match
        match = await self.find_best_match(title, media_type, year)
        if not match:
            return metadata

        # Get detailed info
        if media_type == 'tv_series':
            tmdb_id = match.get('id')
            details = await self.get_tv_details(tmdb_id)

            if details:
                metadata['tmdb_id'] = tmdb_id
                metadata['imdb_id'] = details.get('external_ids', {}).get('imdb_id')
                metadata['overview'] = details.get('overview')
                metadata['release_date'] = details.get('first_air_date')
                metadata['genres'] = [g['name'] for g in details.get('genres', [])]
                metadata['rating'] = details.get('vote_average')

                # Poster and backdrop
                if details.get('poster_path'):
                    metadata['poster_url'] = f"{self.IMAGE_BASE_URL}{details['poster_path']}"
                if details.get('backdrop_path'):
                    metadata['backdrop_url'] = f"{self.IMAGE_BASE_URL}{details['backdrop_path']}"

                # Get season-specific info if provided
                if season_number and details.get('number_of_seasons', 0) >= season_number:
                    season_details = await self.get_season_details(tmdb_id, season_number)
                    if season_details:
                        metadata['season_air_date'] = season_details.get('air_date')
                        metadata['season_episode_count'] = season_details.get('episode_count')

        else:  # movie
            tmdb_id = match.get('id')
            details = await self.get_movie_details(tmdb_id)

            if details:
                metadata['tmdb_id'] = tmdb_id
                metadata['imdb_id'] = details.get('imdb_id')
                metadata['overview'] = details.get('overview')
                metadata['release_date'] = details.get('release_date')
                metadata['genres'] = [g['name'] for g in details.get('genres', [])]
                metadata['rating'] = details.get('vote_average')

                if details.get('poster_path'):
                    metadata['poster_url'] = f"{self.IMAGE_BASE_URL}{details['poster_path']}"
                if details.get('backdrop_path'):
                    metadata['backdrop_url'] = f"{self.IMAGE_BASE_URL}{details['backdrop_path']}"

        return metadata

    def get_poster_url(self, poster_path: str, size: str = 'w500') -> str:
        """
        Generate TMDB poster URL.

        Args:
            poster_path: TMDB poster path
            size: Image size (w92, w154, w185, w342, w500, w780, original)

        Returns:
            Full poster URL
        """
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_tmdb_client: Optional[TMDBClient] = None


def get_tmdb_client() -> TMDBClient:
    """
    Get or create TMDB client singleton.

    Returns:
        TMDBClient instance
    """
    global _tmdb_client
    if _tmdb_client is None:
        _tmdb_client = TMDBClient()
    return _tmdb_client
