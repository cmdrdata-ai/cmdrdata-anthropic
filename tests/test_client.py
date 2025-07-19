"""
Tests for TrackedAnthropic client
"""

from unittest.mock import Mock, patch

import pytest

from cmdrdata_anthropic import TrackedAnthropic
from cmdrdata_anthropic.exceptions import ConfigurationError, ValidationError
from tests.conftest import VALID_ANTHROPIC_KEY, VALID_CMDRDATA_KEY


class TestTrackedAnthropic:
    def test_client_initialization_success(self):
        """Test successful client initialization"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            assert client is not None
            assert client._track_usage is True
            assert client._tracker is not None

    def test_client_initialization_without_tracking(self):
        """Test client initialization without usage tracking"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            assert client is not None
            assert client._track_usage is False
            assert client._tracker is None

    def test_client_initialization_disabled_tracking(self):
        """Test client initialization with explicitly disabled tracking"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY,
                cmdrdata_api_key=VALID_CMDRDATA_KEY,
                track_usage=False,
            )

            assert client is not None
            assert client._track_usage is False

    def test_missing_anthropic_sdk(self):
        """Test error when Anthropic SDK is not installed"""
        with patch("builtins.__import__", side_effect=ImportError):
            with pytest.raises(ConfigurationError, match="Anthropic SDK not found"):
                TrackedAnthropic()

    def test_invalid_anthropic_api_key(self):
        """Test validation of invalid Anthropic API key"""
        with patch("anthropic.Anthropic"):
            with pytest.raises(ValidationError, match="Invalid Anthropic API key"):
                TrackedAnthropic(api_key="invalid-key")

    def test_invalid_cmdrdata_api_key(self):
        """Test validation of invalid cmdrdata API key"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            with pytest.raises(ValidationError, match="Invalid cmdrdata API key"):
                TrackedAnthropic(
                    api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key="invalid-key"
                )

    def test_anthropic_client_failure(self):
        """Test handling of Anthropic client initialization failure"""
        with patch("anthropic.Anthropic", side_effect=Exception("Client error")):
            with pytest.raises(
                ConfigurationError, match="Failed to initialize Anthropic client"
            ):
                TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

    def test_tracker_initialization_failure(self):
        """Test graceful handling of tracker initialization failure"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            with patch(
                "cmdrdata_anthropic.client.UsageTracker",
                side_effect=Exception("Tracker error"),
            ):
                client = TrackedAnthropic(
                    api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
                )

                # Should still create client but disable tracking
                assert client is not None
                assert client._track_usage is False

    def test_attribute_forwarding(self):
        """Test that client attributes are forwarded correctly"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.some_attribute = "test_value"
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            assert client.some_attribute == "test_value"

    def test_tracked_messages_access(self):
        """Test accessing messages attribute returns tracked proxy"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            # Should return a TrackedProxy for messages
            messages = client.messages
            assert messages is not None
            # The proxy should wrap the original messages object

    def test_get_usage_tracker(self):
        """Test getting the usage tracker instance"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            tracker = client.get_usage_tracker()
            assert tracker is not None

    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            stats = client.get_performance_stats()
            assert isinstance(stats, dict)

    def test_repr(self):
        """Test string representation of client"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            repr_str = repr(client)
            assert "TrackedAnthropic" in repr_str
            assert "enabled" in repr_str


class TestTrackedAnthropicMessagesCreate:
    def test_messages_create_with_tracking_success(self, mock_anthropic_response):
        """Test successful messages.create call with tracking"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create.return_value = mock_anthropic_response
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(client._tracker, "track_usage_background") as mock_track:
                result = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                )

                # Verify original API was called
                mock_messages.create.assert_called_once()

                # Verify tracking was called
                mock_track.assert_called_once()
                call_args = mock_track.call_args[1]
                assert call_args["customer_id"] is None  # No context set
                assert call_args["model"] == "claude-sonnet-4-20250514"
                assert call_args["input_tokens"] == 10
                assert call_args["output_tokens"] == 20
                assert call_args["provider"] == "anthropic"
                assert call_args["metadata"]["response_id"] == "msg_123"
                assert call_args["metadata"]["type"] == "message"
                assert call_args["metadata"]["role"] == "assistant"
                assert call_args["metadata"]["stop_reason"] == "end_turn"
                assert call_args["metadata"]["stop_sequence"] is None

                assert result == mock_anthropic_response

    def test_messages_create_without_tracking(self, mock_anthropic_response):
        """Test messages.create call without tracking enabled"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create.return_value = mock_anthropic_response
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            # Client without tracking
            client = TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            result = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Verify original API was called
            mock_messages.create.assert_called_once()
            assert result == mock_anthropic_response

    def test_messages_create_with_customer_context(self, mock_anthropic_response):
        """Test messages.create with customer context"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create.return_value = mock_anthropic_response
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(client._tracker, "track_usage_background") as mock_track:
                result = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                    customer_id="customer-123",
                )

                # Verify tracking was called with customer ID
                mock_track.assert_called_once()
                call_args = mock_track.call_args[1]
                assert call_args["customer_id"] == "customer-123"

    def test_messages_create_tracking_disabled(self, mock_anthropic_response):
        """Test messages.create with tracking explicitly disabled"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create.return_value = mock_anthropic_response
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(client._tracker, "track_usage_background") as mock_track:
                result = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                    track_usage=False,
                )

                # Verify tracking was not called
                mock_track.assert_not_called()

    def test_messages_create_tracking_failure(self, mock_anthropic_response):
        """Test that API call succeeds even if tracking fails"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create.return_value = mock_anthropic_response
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(
                client._tracker,
                "track_usage_background",
                side_effect=Exception("Tracking failed"),
            ):
                # Should not raise exception
                result = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                )

                assert result == mock_anthropic_response


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
