#!/usr/bin/env python3
"""
Service Abstraction Layer for All Integrated Services
Provides unified interfaces and error handling for external services
"""

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import time
import json
from pathlib import Path

from .config_manager import get_config_manager, ServiceStatus

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class ServiceUnavailableError(ServiceError):
    """Service is temporarily unavailable"""
    pass

class ServiceAuthenticationError(ServiceError):
    """Authentication failed"""
    pass

class ServiceRateLimitError(ServiceError):
    """Rate limit exceeded"""
    pass

@dataclass
class ServiceResponse:
    """Standard response format for all services"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseService(ABC):
    """Abstract base class for all service integrations"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config_manager = get_config_manager()
        self.config = self.config_manager.get_service_config(service_name)
        self.logger = logging.getLogger(f"service.{service_name}")
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._cleanup_session()
        
    async def _initialize_session(self):
        """Initialize HTTP session"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
            
    async def _cleanup_session(self):
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> ServiceResponse:
        """Make HTTP request with retry logic and error handling"""
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts):
            try:
                if not self._session:
                    await self._initialize_session()
                
                async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()
                    
                    # Try to parse as JSON
                    try:
                        response_data = json.loads(response_data)
                    except json.JSONDecodeError:
                        pass
                    
                    if response.status == 200:
                        self.config_manager.update_service_status(self.service_name, ServiceStatus.HEALTHY)
                        return ServiceResponse(
                            success=True,
                            data=response_data,
                            status_code=response.status,
                            response_time=response_time
                        )
                    elif response.status == 401:
                        raise ServiceAuthenticationError(f"Authentication failed for {self.service_name}")
                    elif response.status == 429:
                        raise ServiceRateLimitError(f"Rate limit exceeded for {self.service_name}")
                    else:
                        return ServiceResponse(
                            success=False,
                            error=f"HTTP {response.status}: {response_data}",
                            status_code=response.status,
                            response_time=response_time
                        )
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    self.config_manager.update_service_status(self.service_name, ServiceStatus.UNAVAILABLE)
                    return ServiceResponse(
                        success=False,
                        error=f"Service unavailable after {self.config.retry_attempts} attempts: {str(e)}",
                        response_time=time.time() - start_time
                    )
        
        return ServiceResponse(success=False, error="Max retry attempts exceeded")
    
    @abstractmethod
    async def health_check(self) -> ServiceResponse:
        """Check if the service is healthy"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> ServiceResponse:
        """Authenticate with the service"""
        pass

class GitHubService(BaseService):
    """GitHub API service abstraction"""
    
    def __init__(self):
        super().__init__("github")
        self.github_config = self.config_manager.get_github_config()
        
    async def health_check(self) -> ServiceResponse:
        """Check GitHub API health"""
        headers = {
            "Authorization": f"token {self.github_config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        return await self._make_request(
            "GET",
            f"{self.github_config.api_url}/user",
            headers=headers
        )
    
    async def authenticate(self) -> ServiceResponse:
        """Authenticate with GitHub"""
        return await self.health_check()
    
    async def get_repository(self, owner: str, repo: str) -> ServiceResponse:
        """Get repository information"""
        headers = {
            "Authorization": f"token {self.github_config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        return await self._make_request(
            "GET",
            f"{self.github_config.api_url}/repos/{owner}/{repo}",
            headers=headers
        )
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> ServiceResponse:
        """Get pull request information"""
        headers = {
            "Authorization": f"token {self.github_config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        return await self._make_request(
            "GET",
            f"{self.github_config.api_url}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers
        )

class CloudflareService(BaseService):
    """Cloudflare API service abstraction"""
    
    def __init__(self):
        super().__init__("cloudflare")
        self.cloudflare_config = self.config_manager.get_cloudflare_config()
        
    async def health_check(self) -> ServiceResponse:
        """Check Cloudflare API health"""
        headers = {
            "Authorization": f"Bearer {self.cloudflare_config.api_key}",
            "Content-Type": "application/json"
        }
        
        return await self._make_request(
            "GET",
            f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_config.account_id}",
            headers=headers
        )
    
    async def authenticate(self) -> ServiceResponse:
        """Authenticate with Cloudflare"""
        return await self.health_check()
    
    async def deploy_worker(self, script_content: str) -> ServiceResponse:
        """Deploy worker script"""
        headers = {
            "Authorization": f"Bearer {self.cloudflare_config.api_key}",
            "Content-Type": "application/javascript"
        }
        
        return await self._make_request(
            "PUT",
            f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_config.account_id}/workers/scripts/{self.cloudflare_config.worker_name}",
            headers=headers,
            data=script_content
        )
    
    async def trigger_webhook(self, payload: Dict[str, Any]) -> ServiceResponse:
        """Trigger webhook endpoint"""
        headers = {"Content-Type": "application/json"}
        
        return await self._make_request(
            "POST",
            self.cloudflare_config.worker_url,
            headers=headers,
            data=payload
        )

class CodegenService(BaseService):
    """Codegen API service abstraction"""
    
    def __init__(self):
        super().__init__("codegen")
        self.codegen_config = self.config_manager.get_codegen_config()
        
    async def health_check(self) -> ServiceResponse:
        """Check Codegen API health"""
        headers = {
            "Authorization": f"Bearer {self.codegen_config.api_token}",
            "Content-Type": "application/json"
        }
        
        return await self._make_request(
            "GET",
            f"{self.codegen_config.base_url}/health",
            headers=headers
        )
    
    async def authenticate(self) -> ServiceResponse:
        """Authenticate with Codegen API"""
        return await self.health_check()
    
    async def create_agent_run(self, prompt: str, repository: str = None) -> ServiceResponse:
        """Create a new agent run"""
        headers = {
            "Authorization": f"Bearer {self.codegen_config.api_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "organization_id": self.codegen_config.org_id,
            "model": self.codegen_config.model
        }
        
        if repository:
            data["repository"] = repository
        
        return await self._make_request(
            "POST",
            f"{self.codegen_config.base_url}/agents/runs",
            headers=headers,
            data=data
        )
    
    async def get_agent_run(self, run_id: str) -> ServiceResponse:
        """Get agent run status and results"""
        headers = {
            "Authorization": f"Bearer {self.codegen_config.api_token}",
            "Content-Type": "application/json"
        }
        
        return await self._make_request(
            "GET",
            f"{self.codegen_config.base_url}/agents/runs/{run_id}",
            headers=headers
        )

class ServiceManager:
    """Manager for all service abstractions"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger("service_manager")
        
    async def initialize_services(self) -> Dict[str, ServiceResponse]:
        """Initialize all services and check their health"""
        results = {}
        
        # Initialize GitHub service
        try:
            github_service = GitHubService()
            async with github_service:
                health_result = await github_service.health_check()
                results["github"] = health_result
                if health_result.success:
                    self.services["github"] = github_service
        except Exception as e:
            results["github"] = ServiceResponse(success=False, error=str(e))
        
        # Initialize Cloudflare service
        try:
            cloudflare_service = CloudflareService()
            async with cloudflare_service:
                health_result = await cloudflare_service.health_check()
                results["cloudflare"] = health_result
                if health_result.success:
                    self.services["cloudflare"] = cloudflare_service
        except Exception as e:
            results["cloudflare"] = ServiceResponse(success=False, error=str(e))
        
        # Initialize Codegen service
        try:
            codegen_service = CodegenService()
            async with codegen_service:
                health_result = await codegen_service.health_check()
                results["codegen"] = health_result
                if health_result.success:
                    self.services["codegen"] = codegen_service
        except Exception as e:
            results["codegen"] = ServiceResponse(success=False, error=str(e))
        
        self.logger.info(f"Initialized {len(self.services)} services successfully")
        return results
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get a service instance"""
        return self.services.get(service_name)
    
    async def health_check_all(self) -> Dict[str, ServiceResponse]:
        """Run health checks on all services"""
        results = {}
        
        for service_name, service in self.services.items():
            try:
                async with service:
                    results[service_name] = await service.health_check()
            except Exception as e:
                results[service_name] = ServiceResponse(success=False, error=str(e))
        
        return results
    
    async def cleanup(self):
        """Cleanup all services"""
        for service in self.services.values():
            try:
                await service._cleanup_session()
            except Exception as e:
                self.logger.error(f"Error cleaning up service: {e}")

# Global service manager instance
_service_manager: Optional[ServiceManager] = None

def get_service_manager() -> ServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager
