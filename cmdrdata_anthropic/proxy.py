"""
Dynamic proxy classes for transparent API forwarding with usage tracking
"""

import inspect
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Union

from .context import get_effective_customer_id
from .tracker import UsageTracker

logger = logging.getLogger(__name__)


class TrackedProxy:
    """
    Base proxy class that forwards all method calls to the underlying client
    while selectively adding usage tracking to specific methods.
    """

    def __init__(
        self,
        client: Any,
        tracker: UsageTracker,
        track_methods: Optional[Dict[str, Callable]] = None,
    ):
        """
        Initialize the proxy.

        Args:
            client: The underlying client (e.g., Anthropic client)
            tracker: Usage tracker instance
            track_methods: Dict mapping method names to tracking functions
        """
        # Store these with underscore prefixes to avoid conflicts
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_tracker", tracker)
        object.__setattr__(self, "_track_methods", track_methods or {})
        object.__setattr__(self, "_tracked_attributes", {})

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically forward attribute access to the underlying client.
        If the attribute is a method that should be tracked, wrap it.
        """
        # Check if we've already wrapped this attribute
        if name in self._tracked_attributes:
            return self._tracked_attributes[name]

        # Get the attribute from the underlying client
        try:
            attr = getattr(self._client, name)
        except AttributeError:
            # Don't cache non-existent attributes
            raise AttributeError(
                f"'{type(self._client).__name__}' object has no attribute '{name}'"
            )

        # If it's a callable and we have a tracker for it, wrap it
        if callable(attr) and name in self._track_methods:
            wrapped_attr = self._wrap_method(attr, name)
            self._tracked_attributes[name] = wrapped_attr
            return wrapped_attr

        # If it's another object that might need proxying, check if we should wrap it
        elif hasattr(attr, "__dict__") and not isinstance(
            attr, (str, int, float, bool, type(None))
        ):
            # This might be a sub-client (like client.messages)
            # Check if any of our track methods start with this attribute name
            sub_track_methods = {
                k[len(name) + 1 :]: v
                for k, v in self._track_methods.items()
                if k.startswith(f"{name}.")
            }

            if sub_track_methods:
                wrapped_attr = TrackedProxy(attr, self._tracker, sub_track_methods)
                self._tracked_attributes[name] = wrapped_attr
                return wrapped_attr

        # For everything else, just return the original attribute
        self._tracked_attributes[name] = attr
        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        """Forward attribute setting to the underlying client"""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._client, name, value)

    def __dir__(self):
        """Return attributes from both proxy and underlying client"""
        proxy_attrs = [
            attr for attr in object.__dir__(self) if not attr.startswith("_")
        ]
        client_attrs = dir(self._client)
        return sorted(set(proxy_attrs + client_attrs))

    def _wrap_method(self, method: Callable, method_name: str) -> Callable:
        """Wrap a method to add usage tracking and performance monitoring"""
        tracker_func = self._track_methods[method_name]

        def wrapped(*args, **kwargs):
            customer_id = kwargs.pop("customer_id", ...)
            track_usage = kwargs.pop("track_usage", True)
            custom_metadata = kwargs.pop("metadata", None)

            request_id = str(uuid.uuid4())
            start_time = time.time()
            error_occurred = False
            error_type = None
            error_code = None
            error_message = None

            try:
                result = method(*args, **kwargs)
                end_time = time.time()

                if track_usage:
                    try:
                        tracker_func(
                            result=result,
                            customer_id=customer_id,
                            tracker=self._tracker,
                            method_name=method_name,
                            args=args,
                            kwargs=kwargs,
                            custom_metadata=custom_metadata,
                            request_start_time=start_time,
                            request_end_time=end_time,
                            error_occurred=error_occurred,
                            error_type=error_type,
                            error_code=error_code,
                            error_message=error_message,
                            request_id=request_id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to track usage for {method_name}: {e}")

                return result

            except Exception as e:
                end_time = time.time()
                error_occurred = True
                error_message = str(e)

                if hasattr(e, "status_code"):
                    error_code = str(e.status_code)
                    if e.status_code == 429:
                        error_type = "rate_limit"
                    elif e.status_code == 401:
                        error_type = "authentication"
                    elif e.status_code >= 500:
                        error_type = "server_error"
                    else:
                        error_type = "invalid_request"
                else:
                    error_type = "sdk_error"

                if track_usage:
                    try:
                        tracker_func(
                            result=None,
                            customer_id=customer_id,
                            tracker=self._tracker,
                            method_name=method_name,
                            args=args,
                            kwargs=kwargs,
                            custom_metadata=custom_metadata,
                            request_start_time=start_time,
                            request_end_time=end_time,
                            error_occurred=error_occurred,
                            error_type=error_type,
                            error_code=error_code,
                            error_message=error_message,
                            request_id=request_id,
                        )
                    except Exception as track_error:
                        logger.warning(
                            f"Failed to track error for {method_name}: {track_error}"
                        )

                raise

        wrapped.__name__ = getattr(method, "__name__", method_name)
        wrapped.__doc__ = getattr(method, "__doc__", None)
        try:
            wrapped.__signature__ = inspect.signature(method)
        except (ValueError, TypeError):
            pass

        return wrapped

    def __repr__(self):
        """Return a helpful representation"""
        return f"TrackedProxy({repr(self._client)})"


def track_messages_create(
    result,
    customer_id,
    tracker,
    method_name,
    args,
    kwargs,
    custom_metadata=None,
    # Enhanced tracking parameters
    request_start_time=None,
    request_end_time=None,
    error_occurred=None,
    error_type=None,
    error_code=None,
    error_message=None,
    request_id=None,
):
    """Track Anthropic messages.create usage"""
    try:
        effective_customer_id = get_effective_customer_id(customer_id)

        input_tokens = 0
        output_tokens = 0
        model = kwargs.get("model", "unknown")

        if result and hasattr(result, "usage"):
            input_tokens = result.usage.input_tokens
            output_tokens = result.usage.output_tokens
            model = getattr(result, "model", model)
        elif not error_occurred:
            # No usage data available and no error, skip tracking
            return

        metadata = {
            "response_id": getattr(result, "id", None),
            "type": getattr(result, "type", None),
            "role": getattr(result, "role", None),
            "stop_reason": getattr(result, "stop_reason", None),
            "stop_sequence": getattr(result, "stop_sequence", None),
        }

        if custom_metadata:
            metadata.update(custom_metadata)

        tracker.track_usage_background(
            customer_id=effective_customer_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider="anthropic",
            metadata=metadata,
            request_start_time=request_start_time,
            request_end_time=request_end_time,
            error_occurred=error_occurred,
            error_type=error_type,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )

    except Exception as e:
        logger.warning(f"Failed to extract usage data from messages.create: {e}")


def track_messages_batch_create(
    result,
    customer_id,
    tracker,
    method_name,
    args,
    kwargs,
    custom_metadata=None,
    **tracking_params,
):
    """Track Anthropic messages batch creation"""
    try:
        effective_customer_id = get_effective_customer_id(customer_id)
        if not effective_customer_id:
            logger.warning("No customer_id provided for messages batch tracking")
            return

        metadata = {
            "batch_id": getattr(result, "id", None),
            "processing_status": getattr(result, "processing_status", None),
            "request_count": len(kwargs.get("requests", [])),
            "expires_at": getattr(result, "expires_at", None),
        }

        if custom_metadata:
            metadata.update(custom_metadata)

        # Batch creation doesn't provide token usage immediately
        # We track the batch creation event for analytics
        tracker.track_usage_background(
            customer_id=effective_customer_id,
            model="batch",  # Special identifier for batch operations
            input_tokens=0,  # Actual usage tracked when batch completes
            output_tokens=0,
            provider="anthropic",
            metadata=metadata,
            **tracking_params,
        )
    except Exception as e:
        logger.warning(f"Failed to track messages batch: {e}")


def track_completions_create(
    result,
    customer_id,
    tracker,
    method_name,
    args,
    kwargs,
    custom_metadata=None,
    **tracking_params,
):
    """Track Anthropic completions (legacy API)"""
    try:
        effective_customer_id = get_effective_customer_id(customer_id)
        if not effective_customer_id:
            logger.warning("No customer_id provided for completions tracking")
            return

        # Legacy completions API structure
        input_tokens = 0
        output_tokens = 0
        model = kwargs.get("model", "unknown")

        if result and hasattr(result, "usage"):
            input_tokens = getattr(result.usage, "input_tokens", 0)
            output_tokens = getattr(result.usage, "output_tokens", 0)
            model = getattr(result, "model", model)
        elif result and hasattr(result, "completion"):
            # Estimate tokens for legacy format (rough approximation)
            input_text = kwargs.get("prompt", "")
            output_text = getattr(result, "completion", "")
            input_tokens = len(input_text.split()) * 1.3  # Rough token estimate
            output_tokens = len(output_text.split()) * 1.3

        metadata = {
            "response_id": getattr(result, "id", None),
            "stop_reason": getattr(result, "stop_reason", None),
            "legacy_api": True,  # Mark as legacy API usage
        }

        if custom_metadata:
            metadata.update(custom_metadata)

        tracker.track_usage_background(
            customer_id=effective_customer_id,
            model=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            provider="anthropic",
            metadata=metadata,
            **tracking_params,
        )
    except Exception as e:
        logger.warning(f"Failed to track completions: {e}")


def track_token_count(
    result,
    customer_id,
    tracker,
    method_name,
    args,
    kwargs,
    custom_metadata=None,
    **tracking_params,
):
    """Track token counting operations (beta)"""
    try:
        effective_customer_id = get_effective_customer_id(customer_id)
        if not effective_customer_id:
            logger.warning("No customer_id provided for token count tracking")
            return

        token_count = getattr(result, "token_count", 0) if result else 0

        metadata = {
            "token_count": token_count,
            "operation": "count_tokens",
            "model": kwargs.get("model", "unknown"),
        }

        if custom_metadata:
            metadata.update(custom_metadata)

        # Token counting is typically free but worth tracking for analytics
        tracker.track_usage_background(
            customer_id=effective_customer_id,
            model=kwargs.get("model", "token-counter"),
            input_tokens=0,  # Count operations don't consume tokens
            output_tokens=0,
            provider="anthropic",
            metadata=metadata,
            **tracking_params,
        )
    except Exception as e:
        logger.warning(f"Failed to track token counting: {e}")


# Anthropic tracking configuration - All methods that consume tokens or should be tracked
ANTHROPIC_TRACK_METHODS = {
    # Primary Messages API
    "messages.create": track_messages_create,
    # Batch Processing (Beta)
    "messages.batches.create": track_messages_batch_create,
    # Legacy Completions API
    "completions.create": track_completions_create,
    # Beta Features - Token Counting
    "beta.messages.count_tokens": track_token_count,
}
