#!/usr/bin/env python3
"""
Centralized Configuration Manager for Integrated Services
Handles secure credential management and service configuration
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

@dataclass
class ServiceConfig:
    """Base configuration for all services"""
    name: str
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 300  # 5 minutes

@dataclass
class GitHubConfig(ServiceConfig):
    """GitHub service configuration"""
    token: str
    api_url: str = "https://api.github.com"
    webhook_secret: Optional[str] = None
    
@dataclass
class CloudflareConfig(ServiceConfig):
    """Cloudflare service configuration"""
    api_key: str
    account_id: str
    worker_name: str
    worker_url: str
    zone_id: Optional[str] = None

@dataclass
class GrainchainConfig(ServiceConfig):
    """Grainchain sandboxing configuration"""
    provider: str = "local"
    timeout: int = 600
    memory_limit: str = "2GB"
    cpu_limit: float = 2.0
    network_isolation: bool = True
    auto_cleanup: bool = True

@dataclass
class CodegenConfig(ServiceConfig):
    """Codegen API configuration"""
    api_token: str
    org_id: str
    base_url: str = "https://api.codegen.com"
    model: str = "claude-3-sonnet"

@dataclass
class GeminiConfig(ServiceConfig):
    """Google Gemini configuration"""
    api_key: str
    model: str = "gemini-pro"
    temperature: float = 0.1
    max_tokens: int = 4096

@dataclass
class GraphSitterConfig(ServiceConfig):
    """Graph-sitter and Serena configuration"""
    languages: List[str] = None
    serena_enabled: bool = True
    lsp_timeout: int = 30
    error_detection_level: str = "comprehensive"
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ["python", "typescript", "javascript", "react"]

class ConfigManager:
    """Centralized configuration manager for all integrated services"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self._services: Dict[str, Any] = {}
        self._service_status: Dict[str, ServiceStatus] = {}
        
        # Load configurations
        self._load_configurations()
        
    def _load_configurations(self):
        """Load all service configurations from environment and files"""
        try:
            # GitHub Configuration
            github_token = os.getenv("GITHUB_TOKEN", "github_pat_11BPJSHDQ0NtZCMz6IlJDQ_k9esx5zQWmzZ7kPfSP7hdoEVk04yyyNuuxlkN0bxBwlTAXQ5LXI")
            self._services["github"] = GitHubConfig(
                name="github",
                token=github_token,
                webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET")
            )
            
            # Cloudflare Configuration
            self._services["cloudflare"] = CloudflareConfig(
                name="cloudflare",
                api_key=os.getenv("CLOUDFLARE_API_KEY", "eae82cf159577a8838cc83612104c09c5a0d6"),
                account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", "2b2a1d3effa7f7fe4fe2a8c4e48681e3"),
                worker_name=os.getenv("CLOUDFLARE_WORKER_NAME", "webhook-gateway"),
                worker_url=os.getenv("CLOUDFLARE_WORKER_URL", "https://webhook-gateway.pixeliumperfecto.workers.dev")
            )
            
            # Grainchain Configuration
            self._services["grainchain"] = GrainchainConfig(
                name="grainchain",
                provider=os.getenv("GRAINCHAIN_PROVIDER", "local"),
                memory_limit=os.getenv("GRAINCHAIN_MEMORY_LIMIT", "2GB"),
                cpu_limit=float(os.getenv("GRAINCHAIN_CPU_LIMIT", "2.0")),
                network_isolation=os.getenv("GRAINCHAIN_NETWORK_ISOLATION", "true").lower() == "true"
            )
            
            # Codegen Configuration
            self._services["codegen"] = CodegenConfig(
                name="codegen",
                api_token=os.getenv("CODEGEN_API_TOKEN", "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"),
                org_id=os.getenv("CODEGEN_ORG_ID", "323")
            )
            
            # Gemini Configuration
            gemini_key = os.getenv("GEMINI_API_KEY", "AIzaSyBXmhlHudrD4zXiv-5fjxi1gGG-_kdtaZ0")
            self._services["gemini"] = GeminiConfig(
                name="gemini",
                api_key=gemini_key
            )
            
            # Graph-sitter Configuration
            self._services["graph_sitter"] = GraphSitterConfig(
                name="graph_sitter",
                languages=os.getenv("GRAPH_SITTER_LANGUAGES", "python,typescript,javascript,react").split(","),
                serena_enabled=os.getenv("SERENA_ENABLED", "true").lower() == "true"
            )
            
            logger.info("All service configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service"""
        return self._services.get(service_name)
    
    def get_github_config(self) -> GitHubConfig:
        """Get GitHub configuration"""
        return self._services["github"]
    
    def get_cloudflare_config(self) -> CloudflareConfig:
        """Get Cloudflare configuration"""
        return self._services["cloudflare"]
    
    def get_grainchain_config(self) -> GrainchainConfig:
        """Get Grainchain configuration"""
        return self._services["grainchain"]
    
    def get_codegen_config(self) -> CodegenConfig:
        """Get Codegen configuration"""
        return self._services["codegen"]
    
    def get_gemini_config(self) -> GeminiConfig:
        """Get Gemini configuration"""
        return self._services["gemini"]
    
    def get_graph_sitter_config(self) -> GraphSitterConfig:
        """Get Graph-sitter configuration"""
        return self._services["graph_sitter"]
    
    def validate_configurations(self) -> Dict[str, bool]:
        """Validate all service configurations"""
        validation_results = {}
        
        for service_name, config in self._services.items():
            try:
                if service_name == "github":
                    validation_results[service_name] = bool(config.token and len(config.token) > 20)
                elif service_name == "cloudflare":
                    validation_results[service_name] = bool(config.api_key and config.account_id and config.worker_url)
                elif service_name == "codegen":
                    validation_results[service_name] = bool(config.api_token and config.org_id)
                elif service_name == "gemini":
                    validation_results[service_name] = bool(config.api_key and len(config.api_key) > 20)
                else:
                    validation_results[service_name] = True
                    
            except Exception as e:
                logger.error(f"Validation failed for {service_name}: {e}")
                validation_results[service_name] = False
        
        return validation_results
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get current status of a service"""
        return self._service_status.get(service_name, ServiceStatus.UNKNOWN)
    
    def update_service_status(self, service_name: str, status: ServiceStatus):
        """Update service status"""
        self._service_status[service_name] = status
        logger.info(f"Service {service_name} status updated to {status.value}")
    
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services"""
        return self._service_status.copy()
    
    def export_config(self, file_path: Optional[str] = None) -> str:
        """Export configuration to file (excluding sensitive data)"""
        safe_config = {}
        
        for service_name, config in self._services.items():
            config_dict = asdict(config)
            # Remove sensitive fields
            sensitive_fields = ["token", "api_key", "api_token", "webhook_secret"]
            for field in sensitive_fields:
                if field in config_dict:
                    config_dict[field] = "***REDACTED***"
            safe_config[service_name] = config_dict
        
        if file_path:
            with open(file_path, 'w') as f:
                yaml.dump(safe_config, f, default_flow_style=False)
            return file_path
        else:
            return yaml.dump(safe_config, default_flow_style=False)
    
    def get_environment_template(self) -> str:
        """Generate environment variable template"""
        template = """# Integrated Services Configuration Template
# Copy this to your .env file and fill in the actual values

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=optional_webhook_secret

# Cloudflare Configuration  
CLOUDFLARE_API_KEY=your_cloudflare_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_WORKER_NAME=webhook-gateway
CLOUDFLARE_WORKER_URL=https://webhook-gateway.your-domain.workers.dev

# Grainchain Configuration
GRAINCHAIN_PROVIDER=local
GRAINCHAIN_MEMORY_LIMIT=2GB
GRAINCHAIN_CPU_LIMIT=2.0
GRAINCHAIN_NETWORK_ISOLATION=true

# Codegen Configuration
CODEGEN_API_TOKEN=your_codegen_api_token
CODEGEN_ORG_ID=your_org_id

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key

# Graph-sitter Configuration
GRAPH_SITTER_LANGUAGES=python,typescript,javascript,react
SERENA_ENABLED=true
"""
        return template

# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def initialize_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """Initialize the global configuration manager"""
    global _config_manager
    _config_manager = ConfigManager(config_dir)
    return _config_manager
