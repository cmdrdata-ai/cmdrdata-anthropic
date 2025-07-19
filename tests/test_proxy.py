"""
Tests for TrackedProxy and Anthropic-specific tracking
"""

import time
from unittest.mock import Mock, PropertyMock, patch

import pytest

from cmdrdata_anthropic.proxy import (
    ANTHROPIC_TRACK_METHODS,
    TrackedProxy,
    track_messages_create,
)


class TestTrackedProxy:
    def test_proxy_forwards_attributes(self):
        """Test that proxy forwards attribute access to underlying client"""
        mock_client = Mock()
        mock_client.some_attr = "test_value"
        mock_tracker = Mock()

        proxy = TrackedProxy(mock_client, mock_tracker, {})

        assert proxy.some_attr == "test_value"

    def test_proxy_forwards_method_calls(self):
        """Test that proxy forwards method calls to underlying client"""
        mock_client = Mock()
        mock_client.some_method.return_value = "result"
        mock_tracker = Mock()

        proxy = TrackedProxy(mock_client, mock_tracker, {})

        result = proxy.some_method("arg1", kwarg="value")
        assert result == "result"
        mock_client.some_method.assert_called_once_with("arg1", kwarg="value")

    def test_proxy_wraps_tracked_methods(self):
        """Test that proxy wraps methods that should be tracked"""
        mock_client = Mock()
        mock_client.tracked_method.return_value = "result"
        mock_tracker = Mock()
        mock_track_func = Mock()

        track_methods = {"tracked_method": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        result = proxy.tracked_method("arg1", kwarg="value")

        # Verify original method was called
        mock_client.tracked_method.assert_called_once_with("arg1", kwarg="value")

        # Verify tracking function was called
        mock_track_func.assert_called_once()
        assert result == "result"

    def test_proxy_handles_nested_attributes(self):
        """Test that proxy handles nested attributes like client.messages.create"""
        mock_client = Mock()
        mock_messages = Mock()
        mock_messages.create.return_value = "result"
        mock_client.messages = mock_messages
        mock_tracker = Mock()
        mock_track_func = Mock()

        track_methods = {"messages.create": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        # Access nested attribute
        messages_proxy = proxy.messages
        assert messages_proxy is not None

        # Call the nested method
        result = messages_proxy.create("arg1", kwarg="value")

        # Verify original method was called
        mock_messages.create.assert_called_once_with("arg1", kwarg="value")

        # Verify tracking function was called
        mock_track_func.assert_called_once()
        assert result == "result"

    def test_proxy_customer_id_extraction(self):
        """Test that proxy extracts customer_id from kwargs"""
        mock_client = Mock()
        mock_client.tracked_method.return_value = "result"
        mock_tracker = Mock()
        mock_track_func = Mock()

        track_methods = {"tracked_method": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        result = proxy.tracked_method("arg1", customer_id="customer-123", kwarg="value")

        # Verify customer_id was removed from kwargs before calling original method
        mock_client.tracked_method.assert_called_once_with("arg1", kwarg="value")

        # Verify tracking function received customer_id
        mock_track_func.assert_called_once()
        call_kwargs = mock_track_func.call_args[1]
        assert call_kwargs["customer_id"] == "customer-123"

    def test_proxy_tracking_disabled(self):
        """Test that proxy respects track_usage=False"""
        mock_client = Mock()
        mock_client.tracked_method.return_value = "result"
        mock_tracker = Mock()
        mock_track_func = Mock()

        track_methods = {"tracked_method": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        result = proxy.tracked_method("arg1", track_usage=False, kwarg="value")

        # Verify original method was called
        mock_client.tracked_method.assert_called_once_with("arg1", kwarg="value")

        # Verify tracking function was NOT called
        mock_track_func.assert_not_called()

    def test_proxy_tracking_failure_resilience(self):
        """Test that proxy continues if tracking fails"""
        mock_client = Mock()
        mock_client.tracked_method.return_value = "result"
        mock_tracker = Mock()
        mock_track_func = Mock(side_effect=Exception("Tracking failed"))

        track_methods = {"tracked_method": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        # Should not raise exception
        result = proxy.tracked_method("arg1", kwarg="value")

        # Verify original method was called and result returned
        mock_client.tracked_method.assert_called_once_with("arg1", kwarg="value")
        assert result == "result"

    def test_proxy_tracks_api_error(self):
        """Test that the proxy tracks an error if the API call fails"""
        mock_client = Mock()
        # Simulate an API error from the client
        api_error = Exception("API call failed")
        api_error.status_code = 500
        mock_client.tracked_method.side_effect = api_error

        mock_tracker = Mock()
        mock_track_func = Mock()

        track_methods = {"tracked_method": mock_track_func}
        proxy = TrackedProxy(mock_client, mock_tracker, track_methods)

        # The proxy should re-raise the original exception
        with pytest.raises(Exception, match="API call failed"):
            proxy.tracked_method("arg1", kwarg="value")

        # Verify that the tracking function was still called with error details
        mock_track_func.assert_called_once()
        call_kwargs = mock_track_func.call_args[1]

        assert call_kwargs["result"] is None
        assert call_kwargs["error_occurred"] is True
        assert call_kwargs["error_type"] == "server_error"
        assert call_kwargs["error_code"] == "500"
        assert "API call failed" in call_kwargs["error_message"]
        assert call_kwargs["request_start_time"] is not None
        assert call_kwargs["request_end_time"] is not None

    def test_proxy_attribute_error(self):
        """Test that proxy raises AttributeError for non-existent attributes"""
        mock_client = Mock()
        del mock_client.nonexistent_attr  # Ensure it doesn't exist
        mock_tracker = Mock()

        proxy = TrackedProxy(mock_client, mock_tracker, {})

        with pytest.raises(AttributeError):
            _ = proxy.nonexistent_attr

    def test_proxy_dir(self):
        """Test that proxy __dir__ returns attributes from both proxy and client"""
        mock_client = Mock()
        mock_client.client_attr = "value"
        mock_tracker = Mock()

        proxy = TrackedProxy(mock_client, mock_tracker, {})

        dir_result = dir(proxy)
        assert "client_attr" in dir_result

    def test_proxy_repr(self):
        """Test proxy string representation"""
        mock_client = Mock()
        mock_tracker = Mock()

        proxy = TrackedProxy(mock_client, mock_tracker, {})

        repr_str = repr(proxy)
        assert "TrackedProxy" in repr_str


class TestAnthropicTrackingMethods:
    def test_track_messages_create_success(self, mock_anthropic_response):
        """Test successful tracking of messages.create"""
        mock_tracker = Mock()

        track_messages_create(
            result=mock_anthropic_response,
            customer_id="customer-123",
            tracker=mock_tracker,
            method_name="messages.create",
            args=(),
            kwargs={"model": "claude-sonnet-4-20250514"},
        )

        # Verify tracking was called
        mock_tracker.track_usage_background.assert_called_once()
        call_args = mock_tracker.track_usage_background.call_args[1]
        assert call_args["customer_id"] == "customer-123"
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["input_tokens"] == 10
        assert call_args["output_tokens"] == 20
        assert call_args["provider"] == "anthropic"
        assert call_args["metadata"]["response_id"] == "msg_123"
        assert call_args["metadata"]["type"] == "message"
        assert call_args["metadata"]["role"] == "assistant"
        assert call_args["metadata"]["stop_reason"] == "end_turn"
        assert call_args["metadata"]["stop_sequence"] is None

    def test_track_messages_create_no_customer_id(self, mock_anthropic_response):
        """Test tracking without customer ID"""
        mock_tracker = Mock()

        with patch(
            "cmdrdata_anthropic.proxy.get_effective_customer_id", return_value=None
        ):
            track_messages_create(
                result=mock_anthropic_response,
                customer_id=None,
                tracker=mock_tracker,
                method_name="messages.create",
                args=(),
                kwargs={},
            )

        # Verify tracking was called with customer_id=None (new behavior allows tracking without customer_id)
        mock_tracker.track_usage_background.assert_called_once()
        call_args = mock_tracker.track_usage_background.call_args[1]
        assert call_args["customer_id"] is None
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["input_tokens"] == 10
        assert call_args["output_tokens"] == 20
        assert call_args["provider"] == "anthropic"
        assert call_args["metadata"]["response_id"] == "msg_123"
        assert call_args["metadata"]["type"] == "message"
        assert call_args["metadata"]["role"] == "assistant"
        assert call_args["metadata"]["stop_reason"] == "end_turn"
        assert call_args["metadata"]["stop_sequence"] is None

    def test_track_messages_create_no_usage_info(self):
        """Test tracking with response that has no usage info"""
        mock_response = Mock()
        del mock_response.usage  # No usage attribute
        mock_tracker = Mock()

        track_messages_create(
            result=mock_response,
            customer_id="customer-123",
            tracker=mock_tracker,
            method_name="messages.create",
            args=(),
            kwargs={},
        )

        # Verify tracking was not called
        mock_tracker.track_usage_background.assert_not_called()

    def test_track_messages_create_extraction_failure(self):
        """Test graceful handling of data extraction failure"""
        mock_response = Mock()
        # Mock response where accessing usage raises an exception
        type(mock_response).usage = PropertyMock(side_effect=Exception("Access error"))
        mock_tracker = Mock()

        # Should not raise exception
        track_messages_create(
            result=mock_response,
            customer_id="customer-123",
            tracker=mock_tracker,
            method_name="messages.create",
            args=(),
            kwargs={},
        )

        # Verify tracking was not called due to error
        mock_tracker.track_usage_background.assert_not_called()

    def test_track_messages_create_with_error(self):
        """Test tracking of a failed messages.create call"""
        mock_tracker = Mock()
        start_time = time.time() - 1
        end_time = time.time()

        track_messages_create(
            result=None,  # No result on error
            customer_id="customer-123",
            tracker=mock_tracker,
            method_name="messages.create",
            args=(),
            kwargs={"model": "claude-sonnet-4-20250514"},
            # Error details
            error_occurred=True,
            error_type="authentication",
            error_code="401",
            error_message="Invalid API key",
            request_id="req_abc",
            request_start_time=start_time,
            request_end_time=end_time,
        )

        mock_tracker.track_usage_background.assert_called_once()
        call_kwargs = mock_tracker.track_usage_background.call_args[1]

        assert call_kwargs["customer_id"] == "customer-123"
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["input_tokens"] == 0  # No usage on error
        assert call_kwargs["output_tokens"] == 0
        assert call_kwargs["provider"] == "anthropic"
        assert call_kwargs["error_occurred"] is True
        assert call_kwargs["error_type"] == "authentication"
        assert call_kwargs["error_code"] == "401"
        assert call_kwargs["error_message"] == "Invalid API key"
        assert call_kwargs["request_id"] == "req_abc"
        assert call_kwargs["request_start_time"] == start_time
        assert call_kwargs["request_end_time"] == end_time

    def test_anthropic_track_methods_configuration(self):
        """Test that ANTHROPIC_TRACK_METHODS is configured correctly"""
        assert "messages.create" in ANTHROPIC_TRACK_METHODS
        assert ANTHROPIC_TRACK_METHODS["messages.create"] == track_messages_create


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    response = Mock()
    response.id = "msg_123"
    response.type = "message"
    response.role = "assistant"
    response.model = "claude-sonnet-4-20250514"
    response.stop_reason = "end_turn"
    response.stop_sequence = None
    response.content = [{"type": "text", "text": "Hello! How can I help?"}]

    # Mock usage information
    response.usage = Mock()
    response.usage.input_tokens = 10
    response.usage.output_tokens = 20

    return response
