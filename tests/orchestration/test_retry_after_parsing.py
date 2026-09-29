"""Tests for the parse_retry_after function."""

from datetime import datetime, timezone
import pytest
from orchestration.provider_adapters.base import ProviderAdapter


class TestParseRetryAfter:
    """Test the parse_retry_after function with various inputs."""

    def test_valid_integer_seconds(self):
        """Test parsing of valid integer seconds."""
        assert ProviderAdapter.parse_retry_after("30") == 30.0
        assert ProviderAdapter.parse_retry_after("0") == 0.0
        assert ProviderAdapter.parse_retry_after("3600") == 3600.0
        assert ProviderAdapter.parse_retry_after("1") == 1.0

    def test_integer_sign_rejected(self):
        """Test that signed integers are rejected (delay-seconds is 1*DIGIT, no sign)."""
        assert ProviderAdapter.parse_retry_after("+30") is None
        assert ProviderAdapter.parse_retry_after("-30") is None

    def test_invalid_float_rejected(self):
        """Test that floats are rejected."""
        assert ProviderAdapter.parse_retry_after("30.5") is None
        assert ProviderAdapter.parse_retry_after("0.1") is None
        assert ProviderAdapter.parse_retry_after("1.0") is None

    def test_invalid_scientific_notation_rejected(self):
        """Test that scientific notation is rejected."""
        assert ProviderAdapter.parse_retry_after("1e10") is None
        assert ProviderAdapter.parse_retry_after("1.5e2") is None
        assert ProviderAdapter.parse_retry_after("3e+5") is None
        assert ProviderAdapter.parse_retry_after("2E3") is None

    def test_invalid_underscore_rejected(self):
        """Test that underscores are rejected."""
        assert ProviderAdapter.parse_retry_after("1_000") is None
        assert ProviderAdapter.parse_retry_after("1_0") is None

    def test_invalid_characters_rejected(self):
        """Test that various invalid characters are rejected."""
        assert ProviderAdapter.parse_retry_after("abc") is None
        assert ProviderAdapter.parse_retry_after("30s") is None
        assert ProviderAdapter.parse_retry_after("") is None
        assert ProviderAdapter.parse_retry_after("   ") is None

    def test_huge_integer_overflow_rejected(self):
        """Test that huge integers are rejected to avoid overflow."""
        assert ProviderAdapter.parse_retry_after("999999999999999999999") is None  # Very large number
        assert ProviderAdapter.parse_retry_after("1000000000") is not None  # Just under our limit
        assert ProviderAdapter.parse_retry_after("1000000001") is not None  # Just under our limit

    def test_whitespace_handling(self):
        """Test handling of whitespace around valid integers."""
        assert ProviderAdapter.parse_retry_after(" 30 ") == 30.0
        assert ProviderAdapter.parse_retry_after("\t10\n") == 10.0

    def test_valid_http_date_parsing(self):
        """Test parsing of valid HTTP-date format."""
        # Create a fixed "now" time for testing
        now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        future_time = "Wed, 01 Jan 2023 13:00:30 GMT"  # 1 hour and 30 seconds ahead
        
        result = ProviderAdapter.parse_retry_after(future_time, now)
        assert result == pytest.approx(3630.0, abs=1.0)  # 1 hour + 30 seconds

    def test_past_http_date_parsing(self):
        """Test parsing of a past HTTP-date (should return 0, not negative)."""
        now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        past_time = "Wed, 01 Jan 2023 11:00:00 GMT"  # 1 hour in the past
        
        result = ProviderAdapter.parse_retry_after(past_time, now)
        assert result == 0.0  # Should be clamped to 0, not negative

    def test_valid_weekday_month_formats(self):
        """Test that valid weekday/month formats are accepted."""
        now = datetime(2023, 10, 15, 12, 0, 0, tzinfo=timezone.utc)  # A Sunday
        # Valid HTTP date format with weekday
        future_time = "Sun, 22 Oct 2023 12:00:00 GMT"  # 7 days ahead
        
        result = ProviderAdapter.parse_retry_after(future_time, now)
        assert result == pytest.approx(7 * 24 * 3600.0, abs=1.0)  # 7 days in seconds

    def test_malformed_dates_rejected(self):
        """Test that malformed dates are rejected."""
        assert ProviderAdapter.parse_retry_after("Definitely not a date") is None
        assert ProviderAdapter.parse_retry_after("2023-10-15T12:00:00") is None  # ISO format, not HTTP-date
        assert ProviderAdapter.parse_retry_after("15/10/2023 12:00:00") is None  # Wrong format

    def test_none_input(self):
        """Test handling of None input."""
        assert ProviderAdapter.parse_retry_after(None) is None

    def test_unicode_numeric_rejected(self):
        """Test that unicode numeric characters are rejected."""
        assert ProviderAdapter.parse_retry_after("３０") is None  # Full-width numbers (non-ASCII)
        # The sequence \u0033\u0030 is actually ASCII '3' and '0', so it should pass
        # Testing with actual non-ASCII digits like Arabic-indic digits
        assert ProviderAdapter.parse_retry_after("٣٠") is None  # Arabic-indic digits 3 and 0 (non-ASCII)

    def test_edge_cases(self):
        """Test edge cases."""
        # Maximum allowed value based on our limit
        assert ProviderAdapter.parse_retry_after("999999999") is not None
        # Values within our reasonable limit should pass
        assert ProviderAdapter.parse_retry_after("1000000000000000") is not None  # 10^14, under limit
        # Over our limit
        assert ProviderAdapter.parse_retry_after("1000000000000000000000") is None  # Much bigger, over limit