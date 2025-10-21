"""
Title parsing service for extracting base titles, seasons, and episodes from various formats.

This service handles Netflix and other platform title formats to normalize media information
for sequel detection and matching.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime


class TitleParser:
    """Parses media titles to extract structured information."""

    # Regex patterns for title parsing
    SEASON_PATTERNS = [
        r'[:\s]Season\s+(\d+)',  # ": Season 1"
        r'[:\s]S(\d+)',           # ": S1"
        r'\bSeason\s+(\d+)',      # "Season 1"
        r'\bS(\d+)E\d+',          # "S01E01"
    ]

    EPISODE_PATTERNS = [
        r'Episode\s+(\d+)',       # "Episode 1"
        r'E(\d+)',                # "E01"
        r'Ep\.?\s*(\d+)',         # "Ep. 1"
    ]

    # Common separators that indicate season/episode info
    SEPARATORS = [':', '—', '-', '–']

    def __init__(self):
        """Initialize the title parser."""
        self.season_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.SEASON_PATTERNS]
        self.episode_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.EPISODE_PATTERNS]

    def parse(self, title: str) -> Dict[str, Any]:
        """
        Parse a title string to extract base title, season, and episode information.

        Args:
            title: The title string to parse (e.g., "Breaking Bad: Season 5: Episode 1")

        Returns:
            Dictionary containing:
                - base_title: The show/movie name without season/episode info
                - season_number: The season number if found (None for movies)
                - episode_number: The episode number if found
                - is_tv_series: True if season/episode info detected
                - original_title: The original input title
        """
        if not title:
            return self._empty_result(title)

        result = {
            'base_title': title,
            'season_number': None,
            'episode_number': None,
            'is_tv_series': False,
            'original_title': title,
        }

        # Extract season number
        season_num = self._extract_season(title)
        if season_num:
            result['season_number'] = season_num
            result['is_tv_series'] = True

        # Extract episode number
        episode_num = self._extract_episode(title)
        if episode_num:
            result['episode_number'] = episode_num
            result['is_tv_series'] = True

        # Extract base title (remove season/episode information)
        base_title = self._extract_base_title(title, season_num, episode_num)
        result['base_title'] = base_title.strip()

        return result

    def _extract_season(self, title: str) -> Optional[int]:
        """Extract season number from title."""
        for regex in self.season_regex:
            match = regex.search(title)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_episode(self, title: str) -> Optional[int]:
        """Extract episode number from title."""
        for regex in self.episode_regex:
            match = regex.search(title)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_base_title(self, title: str, season_num: Optional[int], episode_num: Optional[int]) -> str:
        """
        Extract the base title by removing season/episode information.

        Handles formats like:
        - "Breaking Bad: Season 5: Episode 1" -> "Breaking Bad"
        - "Stranger Things: S2" -> "Stranger Things"
        - "The Office (US)" -> "The Office (US)"
        """
        base = title

        # Remove season information
        for pattern in self.SEASON_PATTERNS:
            base = re.sub(pattern + r'.*$', '', base, flags=re.IGNORECASE)

        # Remove episode information
        for pattern in self.EPISODE_PATTERNS:
            base = re.sub(pattern + r'.*$', '', base, flags=re.IGNORECASE)

        # Remove trailing separators
        for sep in self.SEPARATORS:
            if base.endswith(sep):
                base = base[:-len(sep)]

        # Clean up multiple spaces
        base = re.sub(r'\s+', ' ', base)

        return base.strip()

    def _empty_result(self, title: str) -> Dict[str, Any]:
        """Return an empty result structure."""
        return {
            'base_title': title or '',
            'season_number': None,
            'episode_number': None,
            'is_tv_series': False,
            'original_title': title or '',
        }

    def normalize_title(self, title: str) -> str:
        """
        Normalize a title for matching purposes.

        - Convert to lowercase
        - Remove special characters
        - Remove articles (the, a, an)
        - Remove year suffixes

        Args:
            title: The title to normalize

        Returns:
            Normalized title string
        """
        if not title:
            return ''

        normalized = title.lower()

        # Remove year in parentheses (e.g., "(2020)")
        normalized = re.sub(r'\s*\(\d{4}\)\s*', ' ', normalized)

        # Remove leading articles
        normalized = re.sub(r'^\s*(the|a|an)\s+', '', normalized)

        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def extract_year(self, title: str) -> Optional[int]:
        """
        Extract year from title if present.

        Args:
            title: Title that may contain year (e.g., "Inception (2010)")

        Returns:
            Year as integer or None
        """
        match = re.search(r'\((\d{4})\)', title)
        if match:
            try:
                year = int(match.group(1))
                # Validate year is reasonable
                if 1900 <= year <= datetime.now().year + 5:
                    return year
            except ValueError:
                pass
        return None

    def is_sequel_candidate(self, title1: str, title2: str) -> bool:
        """
        Quick check if two titles might be related (sequels, seasons, etc.).

        Args:
            title1: First title
            title2: Second title

        Returns:
            True if titles share a base name
        """
        parsed1 = self.parse(title1)
        parsed2 = self.parse(title2)

        norm1 = self.normalize_title(parsed1['base_title'])
        norm2 = self.normalize_title(parsed2['base_title'])

        # Check if normalized base titles match
        return norm1 == norm2 and len(norm1) > 0


# Create singleton instance
title_parser = TitleParser()
