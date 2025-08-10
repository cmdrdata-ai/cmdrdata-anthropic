# cmdrdata-anthropic

[![CI](https://github.com/cmdrdata-ai/cmdrdata-anthropic/workflows/CI/badge.svg)](https://github.com/cmdrdata-ai/cmdrdata-anthropic/actions)
[![codecov](https://codecov.io/gh/cmdrdata-ai/cmdrdata-anthropic/branch/main/graph/badge.svg)](https://codecov.io/gh/cmdrdata-ai/cmdrdata-anthropic)
[![PyPI version](https://badge.fury.io/py/cmdrdata-anthropic.svg)](https://badge.fury.io/py/cmdrdata-anthropic)
[![Python Support](https://img.shields.io/pypi/pyversions/cmdrdata-anthropic.svg)](https://pypi.org/project/cmdrdata-anthropic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The standard for AI customer intelligence - track every Claude call by customer, feature, or any dimension**

Join hundreds of companies making customer-level AI tracking the default. One line of code to add complete visibility into your AI operations. Free during beta.

## 📊 Complete AI Intelligence Layer

`cmdrdata-anthropic` is the missing analytics layer for your AI-powered application:

### **Track Everything That Matters**
- **Customer Intelligence** - Know exactly which customers use what features
- **Metadata Everything** - Tag usage by feature, experiment, team, region, or any dimension
- **Usage Patterns** - Understand how your AI is actually being used
- **Real-time Analytics** - Instant visibility into your AI operations

### **Built for Modern AI Apps**
- **One-line integration** - Drop-in replacement for Anthropic SDK
- **Zero latency overhead** - Async tracking never blocks your API calls
- **Unlimited custom fields** - Track any metadata that matters to your business
- **Privacy first** - Your data never touches our servers (optional self-hosting)

### **What You Can Track**
- **Token usage** by customer, feature, experiment, or any dimension
- **Model usage** patterns (Claude 3.5 Sonnet, Claude 3 Haiku, etc.)
- **Customer behavior** - Who uses what, when, and how much
- **Custom metadata** - Unlimited fields for your specific needs
- **Performance metrics** - Latency, errors, success rates by segment

## 🛡️ Production Ready

**Extremely robust and reliable** - Built for production environments with:

- **Resilient Tracking:** Claude calls succeed even if tracking fails.
- **Non-blocking I/O:** Fire-and-forget tracking never slows down your application.
- **Automatic Retries:** Failed tracking attempts are automatically retried with exponential backoff.
- **Thread-Safe Context:** Safely track usage across multi-threaded and async applications.
- **Enterprise Security:** API key sanitization and input validation.

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
    model="claude-3-5-sonnet-20241022",
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
        model="claude-3-5-sonnet-20241022",
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
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Help me code"}]
    )
    # Automatically tracked for customer-123!

# Or pass customer_id directly
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
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

### 💎 Advanced Analytics with Custom Metadata

Track arbitrary metadata with each API call to enable sophisticated analytics:

```python
# Example: AI writing assistant with feature tracking
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    messages=[{"role": "user", "content": "Write a blog post about AI..."}],
    customer_id="customer-123",
    # Custom metadata for analytics
    custom_metadata={
        "feature": "content_generation",
        "experiment_group": "claude_3_5_test",
        "content_type": "blog_post",
        "user_segment": "power_user",
        "session_id": "sess_abc123"
    }
)

# Example: Customer support automation with behavior tracking
response = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1000,
    messages=complex_support_conversation,
    customer_id="customer-456",
    custom_metadata={
        "use_case": "customer_support",
        "conversation_length": len(complex_support_conversation),
        "department": "technical_support",
        "interaction_type": "chat",
        "user_journey_stage": "resolution"
    }
)
```

**Intelligence Use Cases:**
- **Feature adoption**: Track which AI features customers actually use
- **A/B testing**: Compare model performance across experiment groups
- **User segmentation**: Understand usage patterns by customer segment
- **Journey analytics**: Track AI interactions throughout the customer journey
- **Performance optimization**: Identify which use cases need optimization
- **Product insights**: Data-driven decisions on feature development

## ⚙️ Configuration

### Environment Variables

```bash
# Optional: Set via environment variables
export ANTHROPIC_API_KEY="your-anthropic-key"
export CMDRDATA_API_KEY="your-cmdrdata-key"
export CMDRDATA_ENDPOINT="https://api.cmdrdata.ai/api/events"  # Optional
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
    cmdrdata_endpoint="https://your-custom-endpoint.com/api/events",
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
    model="claude-3-5-sonnet-20241022",
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

- Python 3.9+
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
- **Support**: [spot@cmdrdata.ai](mailto:spot@cmdrdata.ai)

## 🔗 Related Projects

- **[cmdrdata-openai](https://github.com/cmdrdata-ai/cmdrdata-openai)** - Usage tracking for OpenAI
- **[CMDR Data Platform](https://www.cmdrdata.ai)** - Complete LLM usage analytics

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and version history.

---

**Built with ❤️ by the CMDR Data team**

*Become the Google Analytics of your AI - understand everything, optimize everything.*
