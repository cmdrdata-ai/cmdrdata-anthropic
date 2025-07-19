# cmdrdata-anthropic

[![CI](https://github.com/cmdrdata-ai/cmdrdata-anthropic/workflows/CI/badge.svg)](https://github.com/cmdrdata-ai/cmdrdata-anthropic/actions)
[![codecov](https://codecov.io/gh/cmdrdata-ai/cmdrdata-anthropic/branch/main/graph/badge.svg)](https://codecov.io/gh/cmdrdata-ai/cmdrdata-anthropic)
[![PyPI version](https://badge.fury.io/py/cmdrdata-anthropic.svg)](https://badge.fury.io/py/cmdrdata-anthropic)
[![Python Support](https://img.shields.io/pypi/pyversions/cmdrdata-anthropic.svg)](https://pypi.org/project/cmdrdata-anthropic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Transparent usage tracking for Anthropic Claude API calls**

cmdrdata-anthropic provides drop-in replacements for Anthropic's Python SDK clients that automatically track usage for customer billing and analytics without requiring any changes to your existing code.

## 🛡️ Production Ready

**Extremely robust and reliable** - Built for production environments with:

- **100% Test Coverage** - Comprehensive tests ensuring reliability
- **Non-blocking I/O** - Fire-and-forget tracking never slows your app
- **Zero Code Changes** - Drop-in replacement for existing Anthropic clients
- **Thread-safe** - Safe for concurrent applications
- **Error Resilient** - Your app continues even if tracking fails

## 🚀 Quick Start

### Installation

```bash
pip install cmdrdata-anthropic
```

### Basic Usage

```python
# Before
import anthropic
client = anthropic.Anthropic(api_key="your-anthropic-key")

# After - same API, automatic tracking!
import cmdrdata_anthropic
client = cmdrdata_anthropic.TrackedAnthropic(
    api_key="your-anthropic-key",
    cmdrdata_api_key="your-cmdrdata-key"
)

# Same API as regular Anthropic client
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

print(response.content)
# Usage automatically tracked to cmdrdata backend!
```

### Async Support

```python
import cmdrdata_anthropic

async def main():
    client = cmdrdata_anthropic.AsyncTrackedAnthropic(
        api_key="your-anthropic-key",
        cmdrdata_api_key="your-cmdrdata-key"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Hello!"}]
    )

    print(response.content)
    # Async usage tracking included!
```

## 🎯 Customer Context Management

### Automatic Customer Tracking

```python
from cmdrdata_anthropic.context import customer_context

# Set customer context for automatic tracking
with customer_context("customer-123"):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Help me code"}]
    )
    # Automatically tracked for customer-123!

# Or pass customer_id directly
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello"}],
    customer_id="customer-456"  # Direct customer ID
)
```

### Manual Context Management

```python
from cmdrdata_anthropic.context import set_customer_context, clear_customer_context

# Set context for current thread
set_customer_context("customer-789")

response = client.messages.create(...)  # Tracked for customer-789

# Clear context
clear_customer_context()
```

## ⚙️ Configuration

### Environment Variables

```bash
# Optional: Set via environment variables
export ANTHROPIC_API_KEY="your-anthropic-key"
export CMDRDATA_API_KEY="your-cmdrdata-key"
export CMDRDATA_ENDPOINT="https://api.cmdrdata.ai/events"  # Optional
```

```python
# Then use without passing keys
client = cmdrdata_anthropic.TrackedAnthropic()
```

### Custom Configuration

```python
client = cmdrdata_anthropic.TrackedAnthropic(
    api_key="your-anthropic-key",
    cmdrdata_api_key="your-cmdrdata-key",
    cmdrdata_endpoint="https://your-custom-endpoint.com/events",
    track_usage=True,  # Enable/disable tracking
    timeout=30,  # Custom timeout
    max_retries=3  # Custom retry logic
)
```

## 🔒 Security & Privacy

### Automatic Data Sanitization

- **API keys automatically redacted** from logs
- **Sensitive data sanitized** before transmission
- **Input validation** prevents injection attacks
- **Secure defaults** for all configuration

### What Gets Tracked

```python
# Tracked data (anonymized):
{
    "customer_id": "customer-123",
    "model": "claude-sonnet-4-20250514",
    "input_tokens": 25,
    "output_tokens": 150,
    "total_tokens": 175,
    "provider": "anthropic",
    "timestamp": "2025-01-15T10:30:00Z",
    "metadata": {
        "response_id": "msg_abc123",
        "type": "message",
        "stop_reason": "end_turn"
    }
}
```

**Note**: Message content is never tracked - only metadata and token counts.

## 📊 Monitoring & Performance

### Built-in Performance Monitoring

```python
# Get performance statistics
stats = client.get_performance_stats()
print(f"Average response time: {stats['api_calls']['avg']}ms")
print(f"Total API calls: {stats['api_calls']['count']}")
```

### Health Monitoring

```python
# Check tracking system health
tracker = client.get_usage_tracker()
health = tracker.get_health_status()
print(f"Tracking healthy: {health['healthy']}")
```

## 🛠️ Advanced Usage

### Disable Tracking for Specific Calls

```python
# Disable tracking for sensitive operations
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Private query"}],
    track_usage=False  # This call won't be tracked
)
```

### Error Handling

```python
from cmdrdata_anthropic.exceptions import CMDRDataError, TrackingError

try:
    client = cmdrdata_anthropic.TrackedAnthropic(
        api_key="invalid-key",
        cmdrdata_api_key="invalid-cmdrdata-key"
    )
except CMDRDataError as e:
    print(f"Configuration error: {e}")
    # Handle configuration issues
```

### Integration with Existing Error Handling

```python
# All original Anthropic exceptions work the same way
try:
    response = client.messages.create(...)
except anthropic.APIError as e:
    print(f"Anthropic API error: {e}")
    # Your existing error handling works unchanged
```

## 🔧 Development

### Requirements

- Python 3.8+
- anthropic>=0.21.0

### Installation for Development

```bash
git clone https://github.com/cmdrdata-ai/cmdrdata-anthropic.git
cd cmdrdata-anthropic
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cmdrdata_anthropic

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

### Code Quality

```bash
# Format code
black cmdrdata_anthropic/
isort cmdrdata_anthropic/

# Type checking
mypy cmdrdata_anthropic/

# Security scanning
safety check
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Format your code (`black . && isort .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://docs.cmdrdata.ai/anthropic](https://docs.cmdrdata.ai/anthropic)
- **Issues**: [GitHub Issues](https://github.com/cmdrdata-ai/cmdrdata-anthropic/issues)
- **Support**: [support@cmdrdata.ai](mailto:support@cmdrdata.ai)

## 🔗 Related Projects

- **[cmdrdata-openai](https://github.com/cmdrdata-ai/cmdrdata-openai)** - Usage tracking for OpenAI
- **[CMDR Data Platform](https://www.cmdrdata.ai)** - Complete LLM usage analytics

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and version history.

---

**Built with ❤️ by the CMDR Data team**

*Making AI usage tracking effortless and transparent.*
