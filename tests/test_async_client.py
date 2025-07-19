"""
Tests for AsyncTrackedAnthropic client
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cmdrdata_anthropic import AsyncTrackedAnthropic
from cmdrdata_anthropic.exceptions import ConfigurationError, ValidationError
from tests.conftest import VALID_ANTHROPIC_KEY, VALID_CMDRDATA_KEY


class TestAsyncTrackedAnthropic:
    def test_async_client_initialization_success(self):
        """Test successful async client initialization"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            assert client is not None
            assert client._track_usage is True
            assert client._tracker is not None

    def test_async_client_initialization_without_tracking(self):
        """Test async client initialization without usage tracking"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            assert client is not None
            assert client._track_usage is False
            assert client._tracker is None

    def test_missing_anthropic_sdk(self):
        """Test error when Anthropic SDK is not installed"""
        with patch("builtins.__import__", side_effect=ImportError):
            with pytest.raises(ConfigurationError, match="Anthropic SDK not found"):
                AsyncTrackedAnthropic()

    def test_invalid_anthropic_api_key(self):
        """Test validation of invalid Anthropic API key"""
        with patch("anthropic.AsyncAnthropic"):
            with pytest.raises(ValidationError, match="Invalid Anthropic API key"):
                AsyncTrackedAnthropic(api_key="invalid-key")

    def test_invalid_cmdrdata_api_key(self):
        """Test validation of invalid cmdrdata API key"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            with pytest.raises(ValidationError, match="Invalid cmdrdata API key"):
                AsyncTrackedAnthropic(
                    api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key="invalid-key"
                )

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager functionality"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            async with client:
                pass

            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()

    def test_repr(self):
        """Test string representation of async client"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            repr_str = repr(client)
            assert "AsyncTrackedAnthropic" in repr_str
            assert "enabled" in repr_str

    def test_version_compatibility_warning(self):
        """Test version compatibility warning"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            with patch(
                "cmdrdata_anthropic.async_client.check_compatibility",
                return_value=False,
            ):
                with patch("cmdrdata_anthropic.async_client.logger") as mock_logger:
                    AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)
                    mock_logger.warning.assert_called_once()

    def test_client_initialization_failure(self):
        """Test failure during client initialization"""
        with patch("anthropic.AsyncAnthropic", side_effect=Exception("Init failed")):
            with pytest.raises(
                ConfigurationError, match="Failed to initialize AsyncAnthropic client"
            ):
                AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

    def test_tracker_initialization_failure(self):
        """Test failure during tracker initialization"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            with patch(
                "cmdrdata_anthropic.async_client.UsageTracker",
                side_effect=Exception("Tracker failed"),
            ):
                with patch("cmdrdata_anthropic.async_client.logger") as mock_logger:
                    client = AsyncTrackedAnthropic(
                        api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
                    )
                    assert client._track_usage is False
                    mock_logger.warning.assert_called_once()

    def test_getattr_attribute_error(self):
        """Test __getattr__ method with non-existent attribute"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            del mock_client.nonexistent_attr  # Ensure it doesn't exist
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            with pytest.raises(
                AttributeError, match="object has no attribute 'nonexistent_attr'"
            ):
                getattr(client, "nonexistent_attr")

    def test_setattr_original_client(self):
        """Test __setattr__ method for setting attributes on original client"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            # Set a non-private attribute - should be forwarded to original client
            client.custom_attr = "test_value"
            assert mock_client.custom_attr == "test_value"

    def test_dir_method(self):
        """Test __dir__ method returns combined attributes"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.__dir__ = Mock(return_value=["messages", "chat", "completions"])
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            attrs = dir(client)
            # Should include both proxy and original client attributes
            assert isinstance(attrs, list)
            # Check some expected attributes are present
            assert any("messages" in str(attr) for attr in attrs)


class TestAsyncTrackedAnthropicMessagesCreate:
    @pytest.mark.asyncio
    async def test_async_messages_create_with_tracking_success(
        self, mock_anthropic_response
    ):
        """Test successful async messages.create call with tracking"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = AsyncMock()
            mock_messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(
                client._tracker, "track_usage_async", new_callable=AsyncMock
            ) as mock_track:
                result = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                )

                # Verify original API was called
                mock_messages.create.assert_called_once()

                # Verify tracking was called
                mock_track.assert_called_once()
                call_args = mock_track.call_args[1]
                assert call_args["model"] == "claude-sonnet-4-20250514"
                assert call_args["input_tokens"] == 10
                assert call_args["output_tokens"] == 20
                assert call_args["provider"] == "anthropic"

                assert result == mock_anthropic_response

    @pytest.mark.asyncio
    async def test_async_messages_create_without_tracking(
        self, mock_anthropic_response
    ):
        """Test async messages.create call without tracking enabled"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = AsyncMock()
            mock_messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            # Client without tracking
            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)

            result = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Verify original API was called
            mock_messages.create.assert_called_once()
            assert result == mock_anthropic_response

    @pytest.mark.asyncio
    async def test_async_messages_create_with_customer_context(
        self, mock_anthropic_response
    ):
        """Test async messages.create with customer context"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = AsyncMock()
            mock_messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(
                client._tracker, "track_usage_async", new_callable=AsyncMock
            ) as mock_track:
                result = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                    customer_id="customer-123",
                )

                # Verify tracking was called with customer ID
                mock_track.assert_called_once()
                call_args = mock_track.call_args[1]
                assert call_args["customer_id"] == "customer-123"

    @pytest.mark.asyncio
    async def test_async_messages_create_tracking_disabled(
        self, mock_anthropic_response
    ):
        """Test async messages.create with tracking explicitly disabled"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = AsyncMock()
            mock_messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(
                client._tracker, "track_usage_async", new_callable=AsyncMock
            ) as mock_track:
                result = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                    track_usage=False,
                )

                # Verify tracking was not called
                mock_track.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_messages_create_tracking_failure(
        self, mock_anthropic_response
    ):
        """Test that async API call succeeds even if tracking fails"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = AsyncMock()
            mock_messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            with patch.object(
                client._tracker,
                "track_usage_async",
                new_callable=AsyncMock,
                side_effect=Exception("Tracking failed"),
            ):
                # Should not raise exception
                result = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}],
                )

                assert result == mock_anthropic_response

    @pytest.mark.asyncio
    async def test_track_messages_create_early_return(self):
        """Test _track_messages_create early return when tracking is disabled"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)
            client._track_usage = False
            client._tracker = None

            # This should return early without doing anything
            await client._track_messages_create(Mock())
            # If we get here without error, the early return worked


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
