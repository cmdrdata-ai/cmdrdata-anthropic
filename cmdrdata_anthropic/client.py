"""
Tracked Anthropic client with automatic usage tracking
"""

import logging
from typing import Any, Dict, Optional

from .context import get_effective_customer_id
from .exceptions import ConfigurationError, ValidationError
from .logging_config import get_logger
from .performance import PerformanceContext
from .proxy import ANTHROPIC_TRACK_METHODS, TrackedProxy
from .security import APIKeyManager, InputSanitizer
from .tracker import UsageTracker
from .version_compat import check_compatibility

logger = get_logger(__name__)


class TrackedAnthropic:
    """
    Drop-in replacement for Anthropic client with automatic usage tracking.

    This client maintains 100% API compatibility with the original Anthropic client
    while transparently tracking usage for customer billing and analytics.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cmdrdata_api_key: Optional[str] = None,
        cmdrdata_endpoint: str = "https://api.cmdrdata.ai/api/events",
        track_usage: bool = True,
        **kwargs,
    ):
        """
        Initialize the tracked Anthropic client.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            cmdrdata_api_key: cmdrdata API key for usage tracking
            cmdrdata_endpoint: cmdrdata API endpoint URL
            track_usage: Whether to enable usage tracking
            **kwargs: Additional arguments passed to Anthropic client
        """
        # Check version compatibility
        if not check_compatibility():
            logger.warning(
                "Anthropic SDK version may not be fully supported. "
                "Please check compatibility warnings."
            )

        # Import Anthropic here to provide better error messages
        try:
            import anthropic
        except ImportError:
            raise ConfigurationError(
                "Anthropic SDK not found. Please install it: pip install anthropic>=0.21.0"
            )

        # Validate API keys if provided
        if api_key:
            try:
                APIKeyManager.validate_api_key(api_key, "anthropic")
            except Exception as e:
                raise ValidationError(f"Invalid Anthropic API key: {e}")

        if cmdrdata_api_key:
            try:
                APIKeyManager.validate_api_key(cmdrdata_api_key, "cmdrdata")
            except Exception as e:
                raise ValidationError(f"Invalid cmdrdata API key: {e}")

        # Initialize the original Anthropic client
        try:
            self._original_client = anthropic.Anthropic(api_key=api_key, **kwargs)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Anthropic client: {e}")

        # Set up usage tracking
        self._tracker = None
        self._track_usage = track_usage and cmdrdata_api_key is not None

        if self._track_usage:
            try:
                self._tracker = UsageTracker(
                    api_key=cmdrdata_api_key,
                    endpoint=cmdrdata_endpoint,
                )
                logger.info("Usage tracking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize usage tracking: {e}")
                self._track_usage = False

        # Initialize tracked attributes cache
        self._tracked_attributes = {}

        # Performance monitoring
        self._performance = PerformanceContext("client_init")

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically forward attribute access to the underlying client.
        If the attribute should be tracked, wrap it with the proxy.
        """
        # Check if we've already wrapped this attribute
        if name in self._tracked_attributes:
            return self._tracked_attributes[name]

        # Get the attribute from the original client
        try:
            attr = getattr(self._original_client, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self._original_client).__name__}' object has no attribute '{name}'"
            )

        # If tracking is enabled and this attribute should be tracked, wrap it
        if self._track_usage and self._tracker:
            # Check if this attribute or any sub-attributes should be tracked
            relevant_track_methods = {
                k: v
                for k, v in ANTHROPIC_TRACK_METHODS.items()
                if k == name or k.startswith(f"{name}.")
            }

            if relevant_track_methods:
                # Strip the prefix for sub-attributes (e.g., "messages.create" -> "create")
                sub_track_methods = {}
                for k, v in relevant_track_methods.items():
                    if k == name:
                        # Direct method match
                        sub_track_methods[k] = v
                    elif k.startswith(f"{name}."):
                        # Sub-attribute, strip the prefix
                        sub_key = k[len(name) + 1 :]
                        sub_track_methods[sub_key] = v

                wrapped_attr = TrackedProxy(attr, self._tracker, sub_track_methods)
                self._tracked_attributes[name] = wrapped_attr
                return wrapped_attr

        # For everything else, just return the original attribute
        self._tracked_attributes[name] = attr
        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        """Forward attribute setting to the underlying client"""
        if name.startswith("_") or name in [
            "api_key",
            "base_url",
            "timeout",
            "max_retries",
            "default_headers",
        ]:
            object.__setattr__(self, name, value)
        else:
            setattr(self._original_client, name, value)

    def __dir__(self):
        """Return attributes from both proxy and underlying client"""
        proxy_attrs = [
            attr for attr in object.__dir__(self) if not attr.startswith("_")
        ]
        client_attrs = dir(self._original_client)
        return sorted(set(proxy_attrs + client_attrs))

    def get_usage_tracker(self) -> Optional[UsageTracker]:
        """Get the usage tracker instance (for testing/debugging)"""
        return self._tracker

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance monitoring statistics"""
        from .performance import get_performance_stats

        return get_performance_stats()

    def __repr__(self):
        """Return a helpful representation"""
        tracking_status = "enabled" if self._track_usage else "disabled"
        return f"TrackedAnthropic(tracking={tracking_status})"
