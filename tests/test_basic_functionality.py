"""
Basic integration tests for cmdrdata-anthropic
"""

from unittest.mock import Mock, patch

import pytest

from cmdrdata_anthropic import AsyncTrackedAnthropic, TrackedAnthropic
from cmdrdata_anthropic.context import customer_context
from tests.conftest import VALID_ANTHROPIC_KEY, VALID_CMDRDATA_KEY


class TestBasicFunctionality:
    def test_import_tracked_anthropic(self):
        """Test that TrackedAnthropic can be imported"""
        assert TrackedAnthropic is not None

    def test_import_async_tracked_anthropic(self):
        """Test that AsyncTrackedAnthropic can be imported"""
        assert AsyncTrackedAnthropic is not None

    def test_basic_client_creation(self):
        """Test basic client creation without errors"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)
            assert client is not None

    def test_basic_async_client_creation(self):
        """Test basic async client creation without errors"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = AsyncTrackedAnthropic(api_key=VALID_ANTHROPIC_KEY)
            assert client is not None

    def test_client_with_tracking_enabled(self):
        """Test client creation with tracking enabled"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = Mock()

            client = TrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            assert client._track_usage is True
            assert client._tracker is not None

    def test_customer_context_integration(self, mock_anthropic_response):
        """Test integration with customer context"""
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
                with customer_context("customer-123"):
                    result = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=100,
                        messages=[{"role": "user", "content": "Hello"}],
                    )

                # Verify tracking was called with context customer ID
                mock_track.assert_called_once()
                call_args = mock_track.call_args[1]
                assert call_args["customer_id"] == "customer-123"

    def test_version_info_available(self):
        """Test that version information is available"""
        from cmdrdata_anthropic import get_version

        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_compatibility_check_available(self):
        """Test that compatibility checking is available"""
        from cmdrdata_anthropic import check_compatibility, get_compatibility_info

        compat = check_compatibility()
        assert isinstance(compat, bool)

        info = get_compatibility_info()
        assert isinstance(info, dict)
        assert "anthropic" in info
        assert "python" in info

    def test_exceptions_available(self):
        """Test that exceptions are properly exported"""
        from cmdrdata_anthropic import (
            CMDRDataError,
            ConfigurationError,
            NetworkError,
            TrackingError,
            ValidationError,
        )

        # All should be classes
        assert isinstance(CMDRDataError, type)
        assert isinstance(ValidationError, type)
        assert isinstance(ConfigurationError, type)
        assert isinstance(NetworkError, type)
        assert isinstance(TrackingError, type)

    def test_context_functions_available(self):
        """Test that context management functions are available"""
        from cmdrdata_anthropic import (
            clear_customer_context,
            customer_context,
            get_customer_context,
            set_customer_context,
        )

        # Test basic context operations
        set_customer_context("test-customer")
        assert get_customer_context() == "test-customer"

        clear_customer_context()
        assert get_customer_context() is None

    @pytest.mark.asyncio
    async def test_async_basic_integration(self, mock_anthropic_response):
        """Test basic async integration"""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = Mock()
            mock_messages = Mock()
            mock_messages.create = Mock(return_value=mock_anthropic_response)
            mock_client.messages = mock_messages
            mock_anthropic.return_value = mock_client

            client = AsyncTrackedAnthropic(
                api_key=VALID_ANTHROPIC_KEY, cmdrdata_api_key=VALID_CMDRDATA_KEY
            )

            # Should be able to access messages
            messages = client.messages
            assert messages is not None


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
