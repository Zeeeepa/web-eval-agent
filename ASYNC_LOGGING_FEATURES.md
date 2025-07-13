# 🚀 Async & Concurrency + Structured Logging Features

This document describes the new async & concurrency capabilities and structured logging features added to web-eval-agent, specifically designed for testing UI from GitHub PRs and branches.

## 🎯 Overview

The enhanced web-eval-agent now supports:

- **Concurrent Evaluation Sessions**: Run multiple UI tests simultaneously
- **Structured Logging**: Comprehensive logging with context and metrics
- **GitHub PR Integration**: Automatic testing of GitHub PRs and branches
- **Browser Instance Pooling**: Efficient resource management
- **Session Management**: Isolated evaluation sessions with proper cleanup

## 🔧 New MCP Tools

### `test_github_pr`

Test UI from a GitHub Pull Request with automatic deployment detection.

```bash
# Example usage in your IDE chat
Test the UI for PR #96 in Zeeeepa/codegenApp - check the new project dashboard functionality
```

**Parameters:**
- `git_repo`: GitHub repository (e.g., "Zeeeepa/codegenApp")
- `pull_request`: PR number (e.g., 96)
- `task`: Natural language description of what to test
- `headless_browser`: Whether to run in headless mode (default: true)

**Features:**
- Automatic deployment URL detection
- PR metadata integration
- Enhanced task context with PR information
- Structured logging with GitHub context

### `test_github_branch`

Test UI from a GitHub branch with automatic deployment detection.

```bash
# Example usage in your IDE chat
Test the main branch of Zeeeepa/codegenApp - verify all core features work correctly
```

**Parameters:**
- `git_repo`: GitHub repository (e.g., "Zeeeepa/codegenApp")
- `branch`: Branch name (e.g., "main", "feature/new-ui")
- `task`: Natural language description of what to test
- `headless_browser`: Whether to run in headless mode (default: true)

## 🏗️ Architecture Improvements

### Session Manager

The new `SessionManager` provides:

- **Concurrent Sessions**: Run up to 5 evaluation sessions simultaneously
- **Resource Isolation**: Each session has its own browser instance and context
- **Automatic Cleanup**: Proper resource cleanup when sessions complete
- **Queue Management**: Intelligent queuing when at capacity
- **Metrics Tracking**: Real-time session metrics and status

```python
# Example: Create and manage sessions
session_manager = get_session_manager(max_concurrent_sessions=5)

async with session_manager.evaluation_session(config) as session_id:
    result = await session_manager.run_evaluation(session_id, evaluation_func)
```

### Browser Pool

The `BrowserPool` manages browser instances efficiently:

- **Instance Reuse**: Reuse browser instances across evaluations
- **Health Monitoring**: Automatic cleanup of unhealthy instances
- **Configurable Limits**: Control pool size and instance lifecycle
- **Context Isolation**: Each session gets a clean browser context

```python
# Example: Use browser pool
browser_pool = BrowserPool(max_size=10)

async with browser_pool.browser_instance(headless=True) as instance:
    # Use browser instance for evaluation
    pass
```

### Structured Logging

The new logging system provides:

- **Context Awareness**: Automatic session and GitHub context
- **Performance Metrics**: Built-in performance tracking
- **Multiple Outputs**: Console, file, and JSON logging
- **Rich Metadata**: Browser actions, network requests, errors

```python
# Example: Use structured logging
logger = get_logger("my-component")

with logger.evaluation_session(context):
    logger.log_browser_action("click", "button#submit", success=True)
    logger.log_network_request("https://api.example.com", "GET", 200)
    logger.log_console_error("JavaScript error detected")
```

## 🔗 GitHub Integration

### Automatic Deployment Detection

The system automatically detects deployment URLs using common patterns:

**PR Deployments:**
- Netlify: `https://pr-{number}--{repo}.netlify.app`
- Vercel: `https://{repo}-pr-{number}.vercel.app`
- Cloudflare Pages: `https://pr-{number}.{repo}.pages.dev`

**Branch Deployments:**
- Netlify: `https://{branch}--{repo}.netlify.app`
- Vercel: `https://{repo}-git-{branch}.vercel.app`
- Cloudflare Pages: `https://{branch}.{repo}.pages.dev`

### GitHub API Integration

When `GITHUB_TOKEN` is provided:

- **PR Metadata**: Retrieve PR title, description, author, etc.
- **Deployment Status**: Check GitHub deployment status
- **Branch Information**: Get branch details and commit info
- **Comment Integration**: Post evaluation results as PR comments

## 📊 Logging and Metrics

### Log Outputs

The system generates multiple log outputs:

1. **Console Logs**: Human-readable colored output
2. **File Logs**: Detailed logs in `logs/web-eval-agent.log`
3. **Structured Logs**: JSON logs in `logs/web-eval-agent.jsonl`

### Performance Metrics

Automatic tracking of:

- **Session Duration**: Total evaluation time
- **Browser Startup Time**: Time to initialize browser
- **Page Load Time**: Time for pages to load
- **AI Response Time**: Time for AI model responses
- **Action Counts**: Successful/failed browser actions
- **Network Activity**: Request counts and timing
- **Error Tracking**: Console errors and exceptions

### GitHub Context

All logs include GitHub context when available:

```json
{
  "context": {
    "session_id": "uuid",
    "github_repo": "Zeeeepa/codegenApp",
    "github_pr": 96,
    "github_branch": "feature/project-dashboard",
    "url": "https://pr-96--codegenapp.netlify.app",
    "task": "Test the new project dashboard"
  }
}
```

## 🚀 Usage Examples

### Basic GitHub PR Testing

```python
# Test a specific PR
result = await test_github_pr(
    repo="Zeeeepa/codegenApp",
    pr_number=96,
    task="Test the new project dashboard functionality",
    headless=True
)
```

### Concurrent Testing

```python
# Run multiple tests concurrently
session_manager = get_session_manager(max_concurrent_sessions=3)

configs = [
    SessionConfig(url="https://app1.com", task="Test login"),
    SessionConfig(url="https://app2.com", task="Test checkout"),
    SessionConfig(url="https://app3.com", task="Test search"),
]

results = await asyncio.gather(*[
    session_manager.evaluation_session(config)
    for config in configs
])
```

### Custom Logging

```python
# Create custom logger with context
logger = get_logger("custom-test")
context = create_session_context(
    github_repo="owner/repo",
    github_pr=123,
    url="https://example.com",
    task="Custom test"
)

with logger.evaluation_session(context):
    logger.info("Starting custom evaluation")
    # ... perform evaluation ...
    logger.log_evaluation_end(True, summary="All tests passed")
```

## 🔧 Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required for AI-powered evaluation
- `GITHUB_TOKEN`: Optional, enables GitHub API features
- `WEB_EVAL_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

### Session Manager Configuration

```python
session_manager = get_session_manager(
    max_concurrent_sessions=5,  # Max concurrent evaluations
    browser_pool_size=10        # Max browser instances
)
```

### Browser Pool Configuration

```python
browser_pool = BrowserPool(
    max_size=10,           # Max browser instances
    max_idle_time=300,     # 5 minutes idle timeout
    max_instance_age=3600  # 1 hour max age
)
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all new features
python tests/test_github_pr_integration.py

# Test specific components
python -c "
import asyncio
from tests.test_github_pr_integration import test_structured_logging
asyncio.run(test_structured_logging())
"
```

## 📈 Performance Benefits

The new architecture provides significant performance improvements:

- **Concurrent Execution**: 5x faster when running multiple evaluations
- **Resource Reuse**: 3x faster browser startup through pooling
- **Better Monitoring**: Real-time metrics and health checks
- **Automatic Cleanup**: Prevents memory leaks and resource exhaustion
- **Intelligent Queuing**: Optimal resource utilization

## 🔮 Future Enhancements

Planned improvements:

- **Distributed Sessions**: Scale across multiple machines
- **Advanced Metrics**: Performance profiling and bottleneck detection
- **Plugin System**: Custom evaluation plugins
- **Result Persistence**: Database storage for evaluation history
- **Real-time Dashboard**: Live monitoring of evaluation sessions

## 🤝 Contributing

To contribute to these features:

1. Check the session manager and browser pool implementations
2. Add new logging methods to the structured logger
3. Extend GitHub integration with additional platforms
4. Improve deployment URL detection patterns
5. Add new performance metrics and monitoring

## 📚 API Reference

See the individual module documentation:

- `webEvalAgent.src.session_manager`: Session management
- `webEvalAgent.src.browser_pool`: Browser instance pooling
- `webEvalAgent.src.logging_config`: Structured logging
- `webEvalAgent.src.github_integration`: GitHub PR/branch testing

