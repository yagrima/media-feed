"""
Unit tests for title parsing service.
"""

import pytest
from app.services.title_parser import TitleParser, title_parser


class TestTitleParser:
    """Test cases for TitleParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TitleParser()

    def test_parse_tv_series_with_season_and_episode(self):
        """Test parsing TV series with season and episode."""
        result = self.parser.parse("Breaking Bad: Season 5: Episode 1")
        assert result['base_title'] == "Breaking Bad"
        assert result['season_number'] == 5
        assert result['episode_number'] == 1
        assert result['is_tv_series'] is True

    def test_parse_tv_series_short_format(self):
        """Test parsing TV series with S01E01 format."""
        result = self.parser.parse("Stranger Things S03E02")
        assert result['base_title'] == "Stranger Things"
        assert result['season_number'] == 3
        assert result['episode_number'] == 2
        assert result['is_tv_series'] is True

    def test_parse_tv_series_season_only(self):
        """Test parsing TV series with only season information."""
        result = self.parser.parse("The Office: Season 2")
        assert result['base_title'] == "The Office"
        assert result['season_number'] == 2
        assert result['episode_number'] is None
        assert result['is_tv_series'] is True

    def test_parse_movie_title(self):
        """Test parsing movie title (no season/episode)."""
        result = self.parser.parse("Inception")
        assert result['base_title'] == "Inception"
        assert result['season_number'] is None
        assert result['episode_number'] is None
        assert result['is_tv_series'] is False

    def test_parse_movie_with_year(self):
        """Test parsing movie title with year."""
        result = self.parser.parse("The Dark Knight (2008)")
        assert result['base_title'] == "The Dark Knight (2008)"
        assert result['is_tv_series'] is False

    def test_parse_title_with_special_characters(self):
        """Test parsing title with special characters."""
        result = self.parser.parse("Marvel's Agents of S.H.I.E.L.D.: Season 1")
        assert result['base_title'] == "Marvel's Agents of S.H.I.E.L.D."
        assert result['season_number'] == 1

    def test_parse_empty_title(self):
        """Test parsing empty title."""
        result = self.parser.parse("")
        assert result['base_title'] == ""
        assert result['season_number'] is None
        assert result['is_tv_series'] is False

    def test_parse_none_title(self):
        """Test parsing None title."""
        result = self.parser.parse(None)
        assert result['base_title'] == ""

    def test_normalize_title_basic(self):
        """Test basic title normalization."""
        normalized = self.parser.normalize_title("The Walking Dead")
        assert normalized == "walking dead"

    def test_normalize_title_with_year(self):
        """Test normalization removes year."""
        normalized = self.parser.normalize_title("Inception (2010)")
        assert normalized == "inception"

    def test_normalize_title_with_special_chars(self):
        """Test normalization removes special characters."""
        normalized = self.parser.normalize_title("Marvel's Agents of S.H.I.E.L.D.")
        assert "shield" in normalized.lower()

    def test_normalize_title_articles(self):
        """Test normalization removes articles."""
        assert self.parser.normalize_title("The Matrix") == "matrix"
        assert self.parser.normalize_title("A Beautiful Mind") == "beautiful mind"
        assert self.parser.normalize_title("An Unexpected Journey") == "unexpected journey"

    def test_extract_year_valid(self):
        """Test year extraction from title."""
        year = self.parser.extract_year("Inception (2010)")
        assert year == 2010

    def test_extract_year_none(self):
        """Test year extraction when no year present."""
        year = self.parser.extract_year("Inception")
        assert year is None

    def test_extract_year_invalid(self):
        """Test year extraction with invalid year."""
        year = self.parser.extract_year("Ancient Rome (300)")
        assert year is None  # Year too old

    def test_is_sequel_candidate_matching_base(self):
        """Test sequel candidate detection with matching base titles."""
        is_candidate = self.parser.is_sequel_candidate(
            "Breaking Bad: Season 1",
            "Breaking Bad: Season 2"
        )
        assert is_candidate is True

    def test_is_sequel_candidate_different_titles(self):
        """Test sequel candidate detection with different titles."""
        is_candidate = self.parser.is_sequel_candidate(
            "Breaking Bad",
            "Better Call Saul"
        )
        assert is_candidate is False

    def test_is_sequel_candidate_with_articles(self):
        """Test sequel candidate detection ignoring articles."""
        is_candidate = self.parser.is_sequel_candidate(
            "The Walking Dead: Season 1",
            "Walking Dead: Season 2"
        )
        assert is_candidate is True

    def test_parse_various_season_formats(self):
        """Test parsing various season format styles."""
        test_cases = [
            ("Show Name: Season 3", 3),
            ("Show Name: S3", 3),
            ("Show Name Season 3", 3),
            ("Show Name S3E1", 3),
        ]
        for title, expected_season in test_cases:
            result = self.parser.parse(title)
            assert result['season_number'] == expected_season, f"Failed for: {title}"

    def test_parse_complex_netflix_format(self):
        """Test parsing complex Netflix format."""
        result = self.parser.parse("Ozark: Season 4: Part 2: Episode 7")
        assert result['base_title'] == "Ozark"
        assert result['season_number'] == 4
        assert result['is_tv_series'] is True

    def test_original_title_preserved(self):
        """Test that original title is preserved in result."""
        original = "Breaking Bad: Season 5: Episode 1"
        result = self.parser.parse(original)
        assert result['original_title'] == original


class TestTitleParserSingleton:
    """Test the singleton instance."""

    def test_singleton_instance_works(self):
        """Test that the singleton instance is usable."""
        result = title_parser.parse("Test Show: Season 1")
        assert result['season_number'] == 1
        assert result['base_title'] == "Test Show"
