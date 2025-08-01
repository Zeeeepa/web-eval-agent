# 🚀 Comprehensive Integration System for Web-Eval-Agent

This integration extends the web-eval-agent with a comprehensive system that combines multiple specialized services for complete code analysis, UI validation, and intelligent workflow orchestration.

## 🎯 System Overview

The integrated system combines:

- 🌐 **Web-eval-agent** → Enhanced UI validation with full functionality testing
- ☁️ **Cloudflare** → PR notification system via webhook-gateway
- 🏗️ **Grainchain** → Local sandboxing for secure code execution
- 🤖 **Codegen API** → Intelligent code analysis and generation
- 🔍 **Graph-sitter + Serena** → Runtime error detection with LSP integration

## 🔄 Complete Workflow

```
PR Event → Cloudflare Webhook → Code Analysis (Graph-sitter + Serena) → 
Security Validation (Grainchain) → Sandbox Testing → UI Validation (Web-eval-agent) → 
Intelligent Analysis (Codegen) → Comprehensive Report → Notifications
```

## 📋 Prerequisites

### Required API Keys and Credentials

1. **GitHub Token**: Personal access token with repo permissions
2. **Gemini API Key**: From [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **Cloudflare Credentials**: API key and account ID
4. **Codegen API Token**: From your Codegen organization

### Required Dependencies

```bash
# Core dependencies
pip install grainchain graph-sitter aiohttp pydantic

# Optional dependencies for enhanced features
pip install graph-sitter[serena]  # For Serena LSP integration
```

## ⚙️ Configuration

### 1. Environment Setup

Copy the configuration template:
```bash
cp config/environment.template .env
```

Edit `.env` with your actual credentials:
```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=optional_webhook_secret

# Cloudflare Configuration  
CLOUDFLARE_API_KEY=your_cloudflare_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_WORKER_NAME=webhook-gateway
CLOUDFLARE_WORKER_URL=https://webhook-gateway.your-domain.workers.dev

# Codegen Configuration
CODEGEN_API_TOKEN=your_codegen_api_token
CODEGEN_ORG_ID=your_org_id

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
```

### 2. Cloudflare Worker Deployment

Deploy the webhook gateway:
```bash
cd cloudflare
wrangler deploy --env production
wrangler secret put GITHUB_WEBHOOK_SECRET --env production
```

### 3. GitHub Webhook Configuration

Set up webhook in your GitHub repository:
- **Payload URL**: `https://webhook-gateway.your-domain.workers.dev/webhook`
- **Content type**: `application/json`
- **Events**: Pull requests, Push, Issues
- **Secret**: Your webhook secret

## 🛠️ Usage

### Enhanced MCP Tools

The integration adds several new MCP tools:

#### 1. Comprehensive Analysis
```python
# Analyze repository with all integrated services
await handle_comprehensive_analysis(
    repository_path="/path/to/repo",
    analysis_type="full",  # "full", "code_only", "ui_only", "security_only"
    include_ui_validation=True,
    user_requirements="Focus on security and performance"
)
```

#### 2. Advanced Code Analysis
```python
# Code analysis with runtime error detection
await handle_code_analysis_with_runtime_errors(
    code_path="/path/to/code",
    languages=["python", "typescript"],
    include_serena=True  # Enable Serena LSP analysis
)
```

#### 3. Secure Code Execution
```python
# Execute code in secure sandbox
await handle_secure_code_execution(
    code="print('Hello, secure world!')",
    language="python",
    files={"config.json": '{"debug": true}'},
    security_level="high"  # "low", "medium", "high"
)
```

#### 4. Webhook Processing
```python
# Process GitHub webhook events
await handle_webhook_processing(
    webhook_payload=github_webhook_data,
    process_immediately=True
)
```

#### 5. Service Health Check
```python
# Check health of all integrated services
await handle_service_health_check()
```

### Original Web-Eval-Agent Tools

All original tools remain available:
- `web_eval_agent`: Automated UX evaluation
- `setup_browser_state`: Interactive browser setup

## 🏗️ Architecture

### Core Components

#### 1. Configuration Manager (`config_manager.py`)
- Centralized configuration for all services
- Secure credential management
- Service health monitoring
- Environment validation

#### 2. Service Abstractions (`service_abstractions.py`)
- Unified interfaces for all external services
- Error handling and retry mechanisms
- Health check capabilities
- Rate limiting and authentication

#### 3. Cloudflare Integration (`cloudflare/`)
- **webhook-gateway.js**: GitHub webhook processing worker
- **wrangler.toml**: Cloudflare Worker configuration
- Intelligent event routing and filtering
- Rate limiting and security validation

#### 4. Grainchain Integration (`grainchain_integration.py`)
- Local provider integration for secure code execution
- Security validation and code scanning
- Snapshot-based testing workflows
- Resource isolation and cleanup

#### 5. Graph-sitter Integration (`graph_sitter_integration.py`)
- Multi-language code parsing and analysis
- Serena LSP extension for runtime error detection
- SWE-bench feature integration
- Comprehensive error categorization

#### 6. Workflow Orchestrator (`workflow_orchestrator.py`)
- Event-driven architecture coordinating all services
- Intelligent workflow routing based on code characteristics
- Parallel processing with dependency management
- Comprehensive result aggregation and reporting

#### 7. Enhanced Tool Handlers (`enhanced_tool_handlers.py`)
- Extended MCP tool capabilities
- Integration with all services
- Comprehensive reporting and analytics
- User-friendly interfaces

### Data Flow

1. **Event Trigger**: GitHub webhook or direct API call
2. **Routing**: Cloudflare Worker processes and routes events
3. **Analysis**: Graph-sitter analyzes code structure and errors
4. **Security**: Grainchain validates code security
5. **Testing**: Sandbox execution and UI validation
6. **Intelligence**: Codegen provides AI-powered insights
7. **Reporting**: Comprehensive results aggregation
8. **Notification**: Results sent back to GitHub/user

## 🔍 Features

### Code Analysis
- **Multi-language Support**: Python, TypeScript, JavaScript, React
- **Runtime Error Detection**: Via Serena LSP integration
- **SWE-bench Metrics**: Standardized software engineering benchmarks
- **Dependency Analysis**: Comprehensive dependency tracking
- **Complexity Metrics**: Code complexity and maintainability scores

### Security
- **Code Security Scanning**: Pattern-based security validation
- **Sandbox Isolation**: Complete execution environment isolation
- **Network Restrictions**: Configurable network access controls
- **Resource Limits**: CPU, memory, and timeout constraints
- **Audit Trails**: Comprehensive execution logging

### UI Validation
- **Full Element Testing**: Comprehensive interactive element validation
- **Accessibility Compliance**: WCAG accessibility checking
- **Responsive Design**: Multi-device layout validation
- **Performance Analysis**: Page load and interaction timing
- **User Workflow Testing**: End-to-end user journey validation

### Workflow Management
- **Event-driven Architecture**: Intelligent event processing
- **Dependency Management**: Step dependency resolution
- **Parallel Processing**: Concurrent execution where possible
- **Error Recovery**: Graceful failure handling and recovery
- **Progress Tracking**: Real-time workflow status monitoring

## 📊 Monitoring and Analytics

### Health Monitoring
- Service availability checking
- Configuration validation
- Performance metrics tracking
- Error rate monitoring
- Resource usage analytics

### Reporting
- Comprehensive workflow reports
- Step-by-step execution details
- Performance benchmarks
- Security analysis results
- Recommendations and insights

## 🚨 Troubleshooting

### Common Issues

#### 1. Configuration Errors
```bash
# Check configuration validity
python -c "from webEvalAgent.src.config_manager import get_config_manager; print(get_config_manager().validate_configurations())"
```

#### 2. Service Health Issues
```bash
# Check all service health
python -c "import asyncio; from webEvalAgent.src.enhanced_tool_handlers import handle_service_health_check; print(asyncio.run(handle_service_health_check()))"
```

#### 3. Grainchain Not Available
If grainchain is not installed, the system will fall back to local execution:
```bash
pip install grainchain
```

#### 4. Graph-sitter Issues
For enhanced code analysis:
```bash
pip install graph-sitter graph-sitter[serena]
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔐 Security Considerations

- **API Key Management**: All credentials stored in environment variables
- **Webhook Validation**: GitHub webhook signature verification
- **Code Execution**: Sandboxed execution with resource limits
- **Network Isolation**: Configurable network access restrictions
- **Audit Logging**: Comprehensive execution and access logging

## 🚀 Deployment

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp config/environment.template .env
# Edit .env with your credentials

# Run health check
python -c "import asyncio; from webEvalAgent.src.enhanced_tool_handlers import handle_service_health_check; print(asyncio.run(handle_service_health_check()))"
```

### Production
1. Deploy Cloudflare Worker
2. Configure GitHub webhooks
3. Set up monitoring and alerting
4. Configure backup and recovery procedures

## 📈 Performance

### Expected Performance
- **Code Analysis**: 1-5 seconds for typical repositories
- **UI Validation**: 30-120 seconds depending on complexity
- **Sandbox Execution**: 5-30 seconds for typical code
- **Workflow Completion**: 2-10 minutes for comprehensive analysis

### Optimization
- Parallel execution where possible
- Intelligent caching of analysis results
- Resource pooling for sandbox operations
- Efficient webhook processing and routing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## 📄 License

This integration extends the existing web-eval-agent license terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review service health status
3. Check configuration validity
4. Open an issue with detailed logs and configuration (redacted)

---

Built with ❤️ for comprehensive code analysis and validation.
