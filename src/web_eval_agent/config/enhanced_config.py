"""
Enhanced Configuration Management

Comprehensive configuration system for the enhanced web evaluation agent
with environment-specific settings and validation.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Browser configuration settings."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000  # milliseconds
    slow_mo: int = 0  # milliseconds
    args: List[str] = field(default_factory=lambda: [
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security'
    ])
    ignore_https_errors: bool = True
    permissions: List[str] = field(default_factory=lambda: ['geolocation', 'notifications'])


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings."""
    console_monitoring: bool = True
    network_monitoring: bool = True
    performance_monitoring: bool = True
    interaction_monitoring: bool = True
    screenshot_on_failure: bool = True
    video_recording: bool = False
    trace_collection: bool = False
    detailed_logging: bool = True


@dataclass
class AgentConfig:
    """Agent execution configuration."""
    max_agents: int = 5
    default_agents: int = 3
    timeout_per_agent: int = 60  # seconds
    max_retries: int = 3
    retry_delay: int = 2  # seconds
    parallel_execution: bool = True
    use_vision: bool = True
    temperature: float = 0.1


@dataclass
class ReportingConfig:
    """Reporting configuration settings."""
    output_format: str = 'json'  # 'json', 'html', 'pdf', 'markdown'
    include_screenshots: bool = True
    include_console_logs: bool = True
    include_network_logs: bool = True
    include_performance_metrics: bool = True
    detailed_analysis: bool = True
    executive_summary: bool = True
    export_raw_data: bool = False
    report_directory: str = './reports'


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    api_key_validation: bool = True
    rate_limiting: bool = True
    max_requests_per_minute: int = 60
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    content_security_policy: bool = True
    sanitize_inputs: bool = True


@dataclass
class PerformanceConfig:
    """Performance optimization settings."""
    resource_caching: bool = True
    image_optimization: bool = True
    script_optimization: bool = True
    concurrent_requests: int = 10
    request_timeout: int = 30  # seconds
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80


@dataclass
class EnhancedConfig:
    """Comprehensive configuration for enhanced web evaluation agent."""
    # Core settings
    api_key: str = ""
    environment: str = "development"  # 'development', 'staging', 'production'
    debug: bool = False
    log_level: str = "INFO"
    
    # Component configurations
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        self._load_environment_variables()
        self._validate_configuration()
        self._setup_logging()
        
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        # Core settings
        self.api_key = os.getenv('GEMINI_API_KEY', self.api_key)
        self.environment = os.getenv('WEB_EVAL_ENV', self.environment)
        self.debug = os.getenv('WEB_EVAL_DEBUG', str(self.debug)).lower() == 'true'
        self.log_level = os.getenv('WEB_EVAL_LOG_LEVEL', self.log_level)
        
        # Browser settings
        self.browser.headless = os.getenv('WEB_EVAL_HEADLESS', str(self.browser.headless)).lower() == 'true'
        self.browser.timeout = int(os.getenv('WEB_EVAL_TIMEOUT', str(self.browser.timeout)))
        
        # Agent settings
        self.agent.max_agents = int(os.getenv('WEB_EVAL_MAX_AGENTS', str(self.agent.max_agents)))
        self.agent.timeout_per_agent = int(os.getenv('WEB_EVAL_AGENT_TIMEOUT', str(self.agent.timeout_per_agent)))
        
        # Monitoring settings
        self.monitoring.console_monitoring = os.getenv('WEB_EVAL_CONSOLE_MONITORING', str(self.monitoring.console_monitoring)).lower() == 'true'
        self.monitoring.network_monitoring = os.getenv('WEB_EVAL_NETWORK_MONITORING', str(self.monitoring.network_monitoring)).lower() == 'true'
        self.monitoring.performance_monitoring = os.getenv('WEB_EVAL_PERFORMANCE_MONITORING', str(self.monitoring.performance_monitoring)).lower() == 'true'
        
        # Reporting settings
        self.reporting.output_format = os.getenv('WEB_EVAL_OUTPUT_FORMAT', self.reporting.output_format)
        self.reporting.report_directory = os.getenv('WEB_EVAL_REPORT_DIR', self.reporting.report_directory)
        
    def _validate_configuration(self) -> None:
        """Validate configuration settings."""
        errors = []
        
        # Validate API key
        if not self.api_key:
            errors.append("API key is required (set GEMINI_API_KEY environment variable)")
            
        # Validate environment
        if self.environment not in ['development', 'staging', 'production']:
            errors.append(f"Invalid environment: {self.environment}")
            
        # Validate browser settings
        if self.browser.timeout < 1000:
            errors.append("Browser timeout must be at least 1000ms")
            
        if self.browser.viewport_width < 320 or self.browser.viewport_height < 240:
            errors.append("Viewport dimensions must be at least 320x240")
            
        # Validate agent settings
        if self.agent.max_agents < 1 or self.agent.max_agents > 20:
            errors.append("Max agents must be between 1 and 20")
            
        if self.agent.timeout_per_agent < 10 or self.agent.timeout_per_agent > 300:
            errors.append("Agent timeout must be between 10 and 300 seconds")
            
        # Validate reporting settings
        if self.reporting.output_format not in ['json', 'html', 'pdf', 'markdown']:
            errors.append(f"Invalid output format: {self.reporting.output_format}")
            
        # Validate performance settings
        if self.performance.memory_limit_mb < 512:
            errors.append("Memory limit must be at least 512MB")
            
        if self.performance.cpu_limit_percent < 10 or self.performance.cpu_limit_percent > 100:
            errors.append("CPU limit must be between 10% and 100%")
            
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_message)
            
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set specific logger levels
        if self.debug:
            logging.getLogger('web_eval_agent').setLevel(logging.DEBUG)
        else:
            logging.getLogger('web_eval_agent').setLevel(log_level)
            
        # Suppress noisy third-party loggers in production
        if self.environment == 'production':
            logging.getLogger('playwright').setLevel(logging.WARNING)
            logging.getLogger('browser_use').setLevel(logging.WARNING)
            
    def get_browser_launch_args(self) -> List[str]:
        """Get browser launch arguments based on configuration."""
        args = self.browser.args.copy()
        
        if self.browser.headless:
            args.append('--headless=new')
            
        if self.environment == 'production':
            # Production-specific optimizations
            args.extend([
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ])
            
        return args
        
    def get_context_options(self) -> Dict[str, Any]:
        """Get browser context options."""
        return {
            'viewport': {
                'width': self.browser.viewport_width,
                'height': self.browser.viewport_height
            },
            'user_agent': self.browser.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'permissions': self.browser.permissions,
            'ignore_https_errors': self.browser.ignore_https_errors
        }
        
    def get_monitoring_settings(self) -> Dict[str, bool]:
        """Get monitoring settings as dictionary."""
        return {
            'console': self.monitoring.console_monitoring,
            'network': self.monitoring.network_monitoring,
            'performance': self.monitoring.performance_monitoring,
            'interaction': self.monitoring.interaction_monitoring,
            'screenshot_on_failure': self.monitoring.screenshot_on_failure,
            'video_recording': self.monitoring.video_recording,
            'trace_collection': self.monitoring.trace_collection,
            'detailed_logging': self.monitoring.detailed_logging
        }
        
    def get_agent_settings(self) -> Dict[str, Any]:
        """Get agent settings as dictionary."""
        return {
            'max_agents': self.agent.max_agents,
            'default_agents': self.agent.default_agents,
            'timeout': self.agent.timeout_per_agent,
            'max_retries': self.agent.max_retries,
            'retry_delay': self.agent.retry_delay,
            'parallel_execution': self.agent.parallel_execution,
            'use_vision': self.agent.use_vision,
            'temperature': self.agent.temperature
        }
        
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings as dictionary."""
        return {
            'api_key_validation': self.security.api_key_validation,
            'rate_limiting': self.security.rate_limiting,
            'max_requests_per_minute': self.security.max_requests_per_minute,
            'allowed_domains': self.security.allowed_domains,
            'blocked_domains': self.security.blocked_domains,
            'content_security_policy': self.security.content_security_policy,
            'sanitize_inputs': self.security.sanitize_inputs
        }
        
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'development'
        
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
        
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = asdict(self)
        # Remove sensitive information
        config_dict['api_key'] = '***REDACTED***' if self.api_key else ''
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
            
        logger.info(f"Configuration saved to {filepath}")
        
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'EnhancedConfig':
        """Load configuration from JSON file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
            
        # Remove redacted API key
        if config_dict.get('api_key') == '***REDACTED***':
            config_dict['api_key'] = ''
            
        # Reconstruct nested dataclasses
        browser_config = BrowserConfig(**config_dict.get('browser', {}))
        monitoring_config = MonitoringConfig(**config_dict.get('monitoring', {}))
        agent_config = AgentConfig(**config_dict.get('agent', {}))
        reporting_config = ReportingConfig(**config_dict.get('reporting', {}))
        security_config = SecurityConfig(**config_dict.get('security', {}))
        performance_config = PerformanceConfig(**config_dict.get('performance', {}))
        
        # Create main config
        config = cls(
            api_key=config_dict.get('api_key', ''),
            environment=config_dict.get('environment', 'development'),
            debug=config_dict.get('debug', False),
            log_level=config_dict.get('log_level', 'INFO'),
            browser=browser_config,
            monitoring=monitoring_config,
            agent=agent_config,
            reporting=reporting_config,
            security=security_config,
            performance=performance_config,
            custom_settings=config_dict.get('custom_settings', {})
        )
        
        logger.info(f"Configuration loaded from {filepath}")
        return config
        
    def create_profile(self, profile_name: str, overrides: Dict[str, Any]) -> 'EnhancedConfig':
        """Create a configuration profile with specific overrides."""
        config_dict = asdict(self)
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                # Handle nested keys like 'browser.headless'
                parts = key.split('.')
                current = config_dict
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config_dict[key] = value
                
        # Reconstruct config
        return self.__class__(**config_dict)
        
    def get_profile_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined configuration profiles."""
        return {
            'development': {
                'environment': 'development',
                'debug': True,
                'browser.headless': False,
                'monitoring.detailed_logging': True,
                'agent.max_agents': 2,
                'reporting.include_screenshots': True
            },
            'ci_testing': {
                'environment': 'staging',
                'debug': False,
                'browser.headless': True,
                'monitoring.video_recording': False,
                'agent.max_agents': 3,
                'agent.timeout_per_agent': 45,
                'reporting.output_format': 'json'
            },
            'production_monitoring': {
                'environment': 'production',
                'debug': False,
                'browser.headless': True,
                'monitoring.detailed_logging': False,
                'agent.max_agents': 5,
                'agent.timeout_per_agent': 30,
                'performance.memory_limit_mb': 1024,
                'reporting.executive_summary': True
            },
            'performance_testing': {
                'environment': 'staging',
                'monitoring.performance_monitoring': True,
                'monitoring.network_monitoring': True,
                'agent.max_agents': 1,
                'agent.timeout_per_agent': 120,
                'browser.slow_mo': 0,
                'reporting.include_performance_metrics': True
            },
            'accessibility_testing': {
                'environment': 'staging',
                'monitoring.interaction_monitoring': True,
                'agent.use_vision': True,
                'agent.max_agents': 2,
                'reporting.detailed_analysis': True,
                'custom_settings': {
                    'accessibility_focus': True,
                    'keyboard_navigation_testing': True
                }
            }
        }
        
    def apply_profile(self, profile_name: str) -> None:
        """Apply a predefined configuration profile."""
        presets = self.get_profile_presets()
        
        if profile_name not in presets:
            raise ValueError(f"Unknown profile: {profile_name}. Available profiles: {list(presets.keys())}")
            
        overrides = presets[profile_name]
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                # Handle nested keys
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
            else:
                setattr(self, key, value)
                
        logger.info(f"Applied configuration profile: {profile_name}")
        
    def validate_api_key(self) -> bool:
        """Validate the API key format."""
        if not self.api_key:
            return False
            
        # Basic validation for Google API key format
        if not self.api_key.startswith('AIza'):
            return False
            
        if len(self.api_key) < 35:
            return False
            
        return True
        
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging/debugging."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'api_key_configured': bool(self.api_key),
            'browser_headless': self.browser.headless,
            'max_agents': self.agent.max_agents,
            'monitoring_enabled': {
                'console': self.monitoring.console_monitoring,
                'network': self.monitoring.network_monitoring,
                'performance': self.monitoring.performance_monitoring,
                'interaction': self.monitoring.interaction_monitoring
            },
            'output_format': self.reporting.output_format
        }

