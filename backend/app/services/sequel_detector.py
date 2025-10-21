"""
Sequel detection service for finding sequels, new seasons, and related media.

This service analyzes user media and detects potential sequels based on:
- Title matching (base title comparison)
- Season number progression
- Release dates
- External metadata (TMDB)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import Media, UserMedia
from app.services.title_parser import title_parser


class SequelMatch:
    """Represents a detected sequel match with confidence scoring."""

    def __init__(
        self,
        original_media: Media,
        sequel_media: Media,
        confidence: float,
        match_type: str,
        reason: str
    ):
        """
        Initialize sequel match.

        Args:
            original_media: The media the user has consumed
            sequel_media: The detected sequel
            confidence: Match confidence score (0.0-1.0)
            match_type: Type of match (season_increment, exact_title, fuzzy_match)
            reason: Human-readable explanation of the match
        """
        self.original_media = original_media
        self.sequel_media = sequel_media
        self.confidence = confidence
        self.match_type = match_type
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'original_media_id': str(self.original_media.id),
            'sequel_media_id': str(self.sequel_media.id),
            'confidence': self.confidence,
            'match_type': self.match_type,
            'reason': self.reason,
            'sequel_title': self.sequel_media.title,
            'sequel_platform': self.sequel_media.platform,
        }


class SequelDetector:
    """Detects sequels and related media for user's consumed content."""

    # Confidence thresholds
    EXACT_SEASON_INCREMENT_CONFIDENCE = 0.95  # Same show, next season
    EXACT_TITLE_MATCH_CONFIDENCE = 0.90       # Exact base title match
    FUZZY_MATCH_CONFIDENCE = 0.70             # Fuzzy/partial match
    MIN_CONFIDENCE_THRESHOLD = 0.60           # Minimum to report

    def __init__(self, db: Session):
        """
        Initialize sequel detector.

        Args:
            db: Database session
        """
        self.db = db
        self.parser = title_parser

    def find_sequels_for_user(self, user_id: str) -> List[SequelMatch]:
        """
        Find all potential sequels for a user's consumed media.

        Args:
            user_id: User ID to check

        Returns:
            List of sequel matches above confidence threshold
        """
        # Get user's media
        user_media = self.db.query(UserMedia).filter(
            UserMedia.user_id == user_id
        ).all()

        all_matches = []
        for um in user_media:
            media = um.media
            sequels = self.find_sequels_for_media(media, user_id)
            all_matches.extend(sequels)

        # Sort by confidence descending
        all_matches.sort(key=lambda x: x.confidence, reverse=True)

        return all_matches

    def find_sequels_for_media(
        self,
        media: Media,
        user_id: Optional[str] = None
    ) -> List[SequelMatch]:
        """
        Find potential sequels for a specific media item.

        Args:
            media: The media to find sequels for
            user_id: Optional user ID to exclude already consumed media

        Returns:
            List of sequel matches
        """
        matches = []

        # Parse the title to get base title and season info
        parsed = self.parser.parse(media.title)
        base_title = parsed['base_title']
        normalized_base = self.parser.normalize_title(base_title)

        # Query for potential sequel candidates
        candidates = self._find_candidates(media, normalized_base)

        for candidate in candidates:
            # Skip if user already has this media
            if user_id and self._user_has_media(user_id, candidate.id):
                continue

            # Skip self
            if candidate.id == media.id:
                continue

            # Analyze match
            match = self._analyze_match(media, candidate, parsed)
            if match and match.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                matches.append(match)

        return matches

    def _find_candidates(self, media: Media, normalized_base: str) -> List[Media]:
        """
        Find candidate media that might be sequels.

        Args:
            media: Original media
            normalized_base: Normalized base title

        Returns:
            List of candidate media items
        """
        # For now, search by similar titles in the same platform
        # In production, would use more sophisticated matching
        all_media = self.db.query(Media).filter(
            Media.type == media.type  # Same type (movie/tv_series)
        ).all()

        candidates = []
        for candidate in all_media:
            candidate_parsed = self.parser.parse(candidate.title)
            candidate_normalized = self.parser.normalize_title(candidate_parsed['base_title'])

            # Check if base titles match
            if candidate_normalized == normalized_base:
                candidates.append(candidate)

        return candidates

    def _analyze_match(
        self,
        original: Media,
        candidate: Media,
        original_parsed: Dict[str, Any]
    ) -> Optional[SequelMatch]:
        """
        Analyze if candidate is a sequel of original.

        Args:
            original: Original media
            candidate: Candidate sequel
            original_parsed: Parsed original title data

        Returns:
            SequelMatch if match found, None otherwise
        """
        candidate_parsed = self.parser.parse(candidate.title)

        # Check if both are TV series with season info
        if original_parsed['is_tv_series'] and candidate_parsed['is_tv_series']:
            orig_season = original_parsed['season_number']
            cand_season = candidate_parsed['season_number']

            if orig_season and cand_season and cand_season > orig_season:
                # This is a later season of the same show
                confidence = self.EXACT_SEASON_INCREMENT_CONFIDENCE
                match_type = 'season_increment'
                reason = f"Season {cand_season} follows Season {orig_season}"

                return SequelMatch(
                    original_media=original,
                    sequel_media=candidate,
                    confidence=confidence,
                    match_type=match_type,
                    reason=reason
                )

        # Check for exact base title match (movies or series without season info)
        orig_normalized = self.parser.normalize_title(original_parsed['base_title'])
        cand_normalized = self.parser.normalize_title(candidate_parsed['base_title'])

        if orig_normalized == cand_normalized:
            # Check release dates if available
            if self._is_released_after(original, candidate):
                confidence = self.EXACT_TITLE_MATCH_CONFIDENCE
                match_type = 'exact_title'
                reason = f"Same title, newer release"

                return SequelMatch(
                    original_media=original,
                    sequel_media=candidate,
                    confidence=confidence,
                    match_type=match_type,
                    reason=reason
                )

        return None

    def _is_released_after(self, original: Media, candidate: Media) -> bool:
        """
        Check if candidate was released after original.

        Args:
            original: Original media
            candidate: Candidate media

        Returns:
            True if candidate is newer
        """
        # For now, assume true if we can't determine
        # In production, would use TMDB release dates
        return True

    def _user_has_media(self, user_id: str, media_id: str) -> bool:
        """
        Check if user already has consumed this media.

        Args:
            user_id: User ID
            media_id: Media ID

        Returns:
            True if user has this media
        """
        exists = self.db.query(UserMedia).filter(
            and_(
                UserMedia.user_id == user_id,
                UserMedia.media_id == media_id
            )
        ).first()
        return exists is not None

    def get_sequel_summary(self, matches: List[SequelMatch]) -> Dict[str, Any]:
        """
        Generate summary statistics for sequel matches.

        Args:
            matches: List of sequel matches

        Returns:
            Summary dictionary
        """
        if not matches:
            return {
                'total_sequels': 0,
                'by_type': {},
                'by_platform': {},
                'high_confidence_count': 0,
            }

        by_type = {}
        by_platform = {}

        for match in matches:
            # Count by match type
            match_type = match.match_type
            by_type[match_type] = by_type.get(match_type, 0) + 1

            # Count by platform
            platform = match.sequel_media.platform
            by_platform[platform] = by_platform.get(platform, 0) + 1

        high_confidence = sum(
            1 for m in matches
            if m.confidence >= self.EXACT_TITLE_MATCH_CONFIDENCE
        )

        return {
            'total_sequels': len(matches),
            'by_type': by_type,
            'by_platform': by_platform,
            'high_confidence_count': high_confidence,
        }


def create_sequel_detector(db: Session) -> SequelDetector:
    """
    Factory function to create sequel detector.

    Args:
        db: Database session

    Returns:
        SequelDetector instance
    """
    return SequelDetector(db)
