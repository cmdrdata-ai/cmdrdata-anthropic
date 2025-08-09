"""
Async Tracked Anthropic client with automatic usage tracking
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

from .context import get_effective_customer_id

# Sentinel value to distinguish when customer_id is not provided
_MISSING = object()
from .exceptions import ConfigurationError, ValidationError
from .logging_config import get_logger
from .performance import PerformanceContext
from .security import APIKeyManager, InputSanitizer
from .tracker import UsageTracker
from .version_compat import check_compatibility

logger = get_logger(__name__)


class AsyncTrackedAnthropic:
    """
    Async drop-in replacement for AsyncAnthropic client with automatic usage tracking.

    This client maintains 100% API compatibility with the original AsyncAnthropic client
    while transparently tracking usage for customer billing and analytics.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cmdrdata_api_key: Optional[str] = None,
        cmdrdata_endpoint: str = "https://api.cmdrdata.ai/api/events",
        track_usage: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async tracked Anthropic client.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            cmdrdata_api_key: cmdrdata API key for usage tracking
            cmdrdata_endpoint: cmdrdata API endpoint URL
            track_usage: Whether to enable usage tracking
            **kwargs: Additional arguments passed to AsyncAnthropic client
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

        # Initialize the original AsyncAnthropic client
        try:
            self._original_client = anthropic.AsyncAnthropic(api_key=api_key, **kwargs)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize AsyncAnthropic client: {e}")

        # Set up usage tracking
        self._tracker = None
        self._track_usage = track_usage and cmdrdata_api_key is not None

        if self._track_usage and cmdrdata_api_key:
            try:
                self._tracker = UsageTracker(
                    api_key=cmdrdata_api_key,
                    endpoint=cmdrdata_endpoint,
                )
                logger.info("Usage tracking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize usage tracking: {e}")
                self._track_usage = False

        # Performance monitoring
        self._performance = PerformanceContext("async_client_init")

    async def _track_messages_create(
        self,
        result: Any,
        customer_id: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Track messages.create usage asynchronously"""
        if not self._track_usage or not self._tracker:
            return

        try:
            effective_customer_id = get_effective_customer_id(customer_id)

            # Note: We track usage even if customer_id is None for billing/analytics
            # The customer_id will be None in the tracking data which is acceptable

            if hasattr(result, "usage") and result.usage:
                await self._tracker.track_usage_async(
                    customer_id=effective_customer_id or "",  # Use empty string if None
                    model=getattr(result, "model", model or "unknown"),
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                    provider="anthropic",
                    metadata={
                        "response_id": getattr(result, "id", None),
                        "type": getattr(result, "type", None),
                        "role": getattr(result, "role", None),
                        "stop_reason": getattr(result, "stop_reason", None),
                        "stop_sequence": getattr(result, "stop_sequence", None),
                    },
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.warning(f"Failed to track usage for messages.create: {e}")

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically forward attribute access to the underlying client.
        """
        # Handle messages attribute specially to add tracking
        if name == "messages":
            return AsyncTrackedMessages(
                self._original_client.messages,
                self._track_messages_create if self._track_usage else None,
            )

        # For other attributes, just forward to the original client
        try:
            return getattr(self._original_client, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self._original_client).__name__}' object has no attribute '{name}'"
            )

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

    def __dir__(self) -> list[str]:
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

    async def __aenter__(self) -> "AsyncTrackedAnthropic":
        """Async context manager entry"""
        await self._original_client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        """Async context manager exit"""
        return await self._original_client.__aexit__(exc_type, exc_val, exc_tb)

    def __repr__(self) -> str:
        """Return a helpful representation"""
        tracking_status = "enabled" if self._track_usage else "disabled"
        return f"AsyncTrackedAnthropic(tracking={tracking_status})"


class AsyncTrackedMessages:
    """Wrapper for messages API with usage tracking"""

    def __init__(self, original_messages: Any, track_func: Optional[Any]) -> None:
        self._original_messages = original_messages
        self._track_func = track_func

    async def create(
        self,
        customer_id: Union[Optional[str], object] = _MISSING,
        track_usage: bool = True,
        **kwargs,
    ) -> Any:
        """Create a message with optional usage tracking"""
        # Call the original create method
        result = await self._original_messages.create(**kwargs)

        # Track usage if enabled
        if track_usage and self._track_func:
            # Only pass customer_id if it was explicitly provided
            track_kwargs = {
                "result": result,
                "model": kwargs.get("model"),
            }
            if customer_id is not _MISSING:
                track_kwargs["customer_id"] = customer_id
            await self._track_func(**track_kwargs)

        return result

    def __getattr__(self, name: str) -> Any:
        """Forward other method calls to the original messages object"""
        return getattr(self._original_messages, name)
