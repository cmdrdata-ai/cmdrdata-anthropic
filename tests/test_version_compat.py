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

    def test_fake_version_class(self):
        """Test the FakeVersion fallback class when packaging is not available"""
        # Temporarily hide the packaging module
        import sys

        original_modules = sys.modules.copy()

        try:
            # Remove packaging from sys.modules to trigger ImportError
            if "packaging" in sys.modules:
                del sys.modules["packaging"]
            if "packaging.version" in sys.modules:
                del sys.modules["packaging.version"]

            # Reload the module to trigger the fallback
            import importlib

            import cmdrdata_anthropic.version_compat

            importlib.reload(cmdrdata_anthropic.version_compat)

            # Test FakeVersion functionality
            from cmdrdata_anthropic.version_compat import version

            v1 = version.parse("1.0.0")
            v2 = version.parse("2.0.0")
            v3 = version.parse("1.0.0")

            assert v1 < v2
            assert v1 <= v2
            assert v1 <= v3
            assert v2 > v1
            assert v2 >= v1
            assert v1 == v3
            assert v1 != v2
            assert str(v1) == "1.0.0"

            # Test NotImplemented for wrong type comparison
            assert (v1 == "1.0.0") is False

        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)
            importlib.reload(cmdrdata_anthropic.version_compat)

    def test_validate_version_none(self):
        """Test _validate_anthropic_version with None version"""
        compat = VersionCompatibility()
        compat.anthropic_version = None
        # Should return early without warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compat._validate_anthropic_version()
            assert len(w) == 0

    def test_older_untested_version_warning(self):
        """Test warning for older untested versions"""
        with patch("anthropic.__version__", "0.29.0"):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                compat = VersionCompatibility()
                # Check if warning was issued for untested version
                warning_found = any(
                    "has not been fully tested" in str(warning.message) for warning in w
                )
                assert warning_found
