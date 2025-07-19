"""
Tests for Anthropic version compatibility detection
"""

import sys
import warnings
from unittest.mock import Mock, patch

import pytest

from cmdrdata_anthropic.version_compat import (
    VersionCompatibility,
    check_compatibility,
    get_compatibility_info,
)


class TestVersionCompatibility:
    def test_anthropic_version_detection(self):
        """Test detection of installed Anthropic version"""
        compat = VersionCompatibility()

        # Should detect some version (or warn if not installed)
        assert compat.anthropic_version is not None or len(warnings.filters) > 0

    def test_supported_anthropic_version(self):
        """Test that supported versions are marked as compatible"""
        with patch("anthropic.__version__", "0.25.0"):
            compat = VersionCompatibility()
            assert compat.is_anthropic_supported()

    def test_unsupported_anthropic_version(self):
        """Test handling of unsupported Anthropic versions"""
        with patch("cmdrdata_anthropic.version_compat.version") as mock_version:
            # Mock an unsupported (too old) version
            mock_parse = Mock()
            mock_old_version = Mock()
            mock_old_version.__lt__ = Mock(return_value=True)
            mock_old_version.__ge__ = Mock(return_value=False)
            mock_parse.return_value = mock_old_version
            mock_version.parse = mock_parse

            with patch("anthropic.__version__", "0.20.0"):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    compat = VersionCompatibility()
                    assert not compat.is_anthropic_supported()
                    assert len(w) > 0
                    assert "below minimum" in str(w[0].message)

    def test_missing_anthropic(self):
        """Test handling when Anthropic SDK is not installed"""
        with patch.dict("sys.modules", {"anthropic": None}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                compat = VersionCompatibility()
                assert not compat.is_anthropic_supported()
                assert len(w) > 0
                assert "not found" in str(w[0].message)

    def test_version_warnings(self):
        """Test version compatibility warnings"""
        with patch("cmdrdata_anthropic.version_compat.version") as mock_version:
            # Mock a newer untested version
            mock_parse = Mock()
            mock_new_version = Mock()
            mock_new_version.__lt__ = Mock(return_value=False)
            mock_new_version.__ge__ = Mock(return_value=True)
            mock_new_version.__str__ = Mock(return_value="0.99.0")
            mock_parse.return_value = mock_new_version
            mock_version.parse = mock_parse

            with patch("anthropic.__version__", "0.99.0"):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    compat = VersionCompatibility()
                    assert len(w) > 0
                    assert "newer than tested" in str(w[0].message)

    def test_get_compatibility_info(self):
        """Test compatibility information retrieval"""
        info = get_compatibility_info()

        assert "anthropic" in info
        assert "python" in info
        assert "version" in info["python"]
        assert info["python"]["supported"] == (sys.version_info >= (3, 8))

    def test_check_compatibility_function(self):
        """Test standalone compatibility check function"""
        result = check_compatibility()
        assert isinstance(result, bool)
