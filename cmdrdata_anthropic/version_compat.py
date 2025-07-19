"""
Version compatibility and detection for cmdrdata-anthropic
"""

import sys
import warnings
from typing import Any, Dict, Optional, Tuple

try:
    from packaging import version
except ImportError:
    # Fallback version parsing
    class FakeVersion:
        def __init__(self, v: str) -> None:
            self.v = v

        def __lt__(self, other: "FakeVersion") -> bool:
            return self.v < other.v

        def __le__(self, other: "FakeVersion") -> bool:
            return self.v <= other.v

        def __gt__(self, other: "FakeVersion") -> bool:
            return self.v > other.v

        def __ge__(self, other: "FakeVersion") -> bool:
            return self.v >= other.v

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, FakeVersion):
                return NotImplemented
            return self.v == other.v

        def __str__(self) -> str:
            return self.v

    def parse(v: str) -> FakeVersion:
        return FakeVersion(v)

    version = type("Version", (), {"parse": parse})()


class VersionCompatibility:
    """Handles version detection and compatibility warnings for Anthropic"""

    # Supported Anthropic version ranges
    SUPPORTED_ANTHROPIC_VERSIONS = {
        "min": "0.21.0",
        "max": "1.0.0",  # Updated for latest versions
        "tested": [
            "0.21.0",
            "0.25.0",
            "0.28.0",
            "0.30.0",
            "0.32.0",
            "0.34.0",
            "0.35.0",
            "0.36.0",
            "0.37.0",
            "0.38.0",
        ],
        "latest_tested": "0.38.0",
    }

    def __init__(self) -> None:
        self.anthropic_version: Optional[str] = None
        self._check_anthropic_version()

    def _check_anthropic_version(self) -> None:
        """Check installed version of Anthropic SDK"""
        try:
            import anthropic

            self.anthropic_version = anthropic.__version__
            self._validate_anthropic_version()
        except ImportError:
            warnings.warn(
                "Anthropic SDK not found. Please install it: pip install anthropic>=0.21.0",
                UserWarning,
                stacklevel=3,
            )

    def _validate_anthropic_version(self) -> None:
        """Validate Anthropic version and show warnings if needed"""
        if not self.anthropic_version:
            return

        current = version.parse(self.anthropic_version)
        min_version = version.parse(self.SUPPORTED_ANTHROPIC_VERSIONS["min"])
        max_version = version.parse(self.SUPPORTED_ANTHROPIC_VERSIONS["max"])

        if current < min_version:
            warnings.warn(
                f"cmdrdata-anthropic: Anthropic SDK version {self.anthropic_version} is below minimum "
                f"supported version {self.SUPPORTED_ANTHROPIC_VERSIONS['min']}. "
                f"Please upgrade: pip install anthropic>={self.SUPPORTED_ANTHROPIC_VERSIONS['min']}",
                UserWarning,
                stacklevel=3,
            )
        elif current >= max_version:
            warnings.warn(
                f"cmdrdata-anthropic: Anthropic SDK version {self.anthropic_version} is newer than tested version. "
                f"cmdrdata-anthropic was tested up to version {self.SUPPORTED_ANTHROPIC_VERSIONS['latest_tested']}. "
                f"Functionality may be limited. Please check for cmdrdata-anthropic updates.",
                UserWarning,
                stacklevel=3,
            )
        # Only warn for significantly older untested versions, not newer ones
        elif (
            current < version.parse("0.30.0")
            and str(current) not in self.SUPPORTED_ANTHROPIC_VERSIONS["tested"]
        ):
            warnings.warn(
                f"cmdrdata-anthropic: Anthropic SDK version {self.anthropic_version} has not been fully tested. "
                f"Latest tested version: {self.SUPPORTED_ANTHROPIC_VERSIONS['latest_tested']}. "
                f"Consider upgrading for best compatibility.",
                UserWarning,
                stacklevel=3,
            )

    def is_anthropic_supported(self) -> bool:
        """Check if Anthropic version is supported"""
        if not self.anthropic_version:
            return False

        current = version.parse(self.anthropic_version)
        min_version = version.parse(self.SUPPORTED_ANTHROPIC_VERSIONS["min"])
        max_version = version.parse(self.SUPPORTED_ANTHROPIC_VERSIONS["max"])

        return bool(min_version <= current < max_version)

    def get_compatibility_info(self) -> Dict[str, Any]:
        """Get comprehensive compatibility information"""
        return {
            "anthropic": {
                "installed": self.anthropic_version,
                "supported": self.is_anthropic_supported(),
                "min_supported": self.SUPPORTED_ANTHROPIC_VERSIONS["min"],
                "max_supported": self.SUPPORTED_ANTHROPIC_VERSIONS["max"],
                "tested_versions": self.SUPPORTED_ANTHROPIC_VERSIONS["tested"],
            },
            "python": {
                "version": f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
                "supported": sys.version_info >= (3, 8),
            },
        }


# Global instance
_version_compat = VersionCompatibility()


def check_compatibility() -> bool:
    """
    Check if the current environment is compatible with cmdrdata-anthropic.

    Returns:
        True if compatible, False otherwise
    """
    return _version_compat.is_anthropic_supported()


def get_compatibility_info() -> Dict[str, Any]:
    """
    Get detailed compatibility information.

    Returns:
        Dictionary with compatibility details
    """
    return _version_compat.get_compatibility_info()
