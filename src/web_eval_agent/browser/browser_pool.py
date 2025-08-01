#!/usr/bin/env python3

"""
Browser instance pool for efficient resource management.
Provides browser instance pooling, lifecycle management, and cleanup.
"""

import asyncio
import uuid
import time
import weakref
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from browser_use.browser.browser import Browser as BrowserUseBrowser, BrowserConfig
from browser_use.browser.context import BrowserContext as BrowserUseContext

from .logging_config import get_logger, StructuredLogger


class InstanceStatus(Enum):
    """Browser instance status."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    INITIALIZING = "initializing"
    FAILED = "failed"
    CLEANUP = "cleanup"


@dataclass
class BrowserInstanceConfig:
    """Configuration for browser instances."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000
    slow_mo: int = 0
    devtools: bool = False
    
    def to_browser_config(self) -> BrowserConfig:
        """Convert to browser-use BrowserConfig."""
        return BrowserConfig(
            headless=self.headless,
            disable_security=True,  # For testing purposes
            chrome_instance_path=None,
            user_data_dir=None
        )


class BrowserInstance:
    """
    Represents a single browser instance with its context and page.
    """
    
    def __init__(self, instance_id: str, config: BrowserInstanceConfig):
        self.instance_id = instance_id
        self.config = config
        self.status = InstanceStatus.INITIALIZING
        self.created_at = time.time()
        self.last_used = time.time()
        self.use_count = 0
        
        # Browser components
        self.playwright_browser: Optional[Browser] = None
        self.browser_use_browser: Optional[BrowserUseBrowser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Cleanup tracking
        self._cleanup_callbacks: List[callable] = []
        self.logger = get_logger(f"browser-{instance_id}")
    
    async def initialize(self, playwright_instance):
        """Initialize the browser instance."""
        try:
            self.logger.info(f"Initializing browser instance {self.instance_id}")
            
            # Launch Playwright browser
            self.playwright_browser = await playwright_instance.chromium.launch(
                headless=self.config.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ],
                slow_mo=self.config.slow_mo,
                devtools=self.config.devtools
            )
            
            # Create browser context
            self.context = await self.playwright_browser.new_context(
                viewport={
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                },
                user_agent=self.config.user_agent,
                ignore_https_errors=True
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.config.timeout)
            
            # Create browser-use browser instance
            browser_config = self.config.to_browser_config()
            self.browser_use_browser = BrowserUseBrowser(
                config=browser_config,
                browser=self.playwright_browser
            )
            
            self.status = InstanceStatus.AVAILABLE
            self.logger.info(f"Browser instance {self.instance_id} initialized successfully")
            
        except Exception as e:
            self.status = InstanceStatus.FAILED
            self.logger.error(f"Failed to initialize browser instance {self.instance_id}", error=e)
            await self._cleanup()
            raise
    
    async def acquire(self) -> 'BrowserInstance':
        """Acquire this browser instance for use."""
        if self.status != InstanceStatus.AVAILABLE:
            raise RuntimeError(f"Browser instance {self.instance_id} is not available")
        
        self.status = InstanceStatus.IN_USE
        self.last_used = time.time()
        self.use_count += 1
        
        self.logger.debug(f"Browser instance {self.instance_id} acquired (use count: {self.use_count})")
        return self
    
    async def release(self):
        """Release this browser instance back to the pool."""
        if self.status != InstanceStatus.IN_USE:
            self.logger.warning(f"Attempting to release browser instance {self.instance_id} that is not in use")
            return
        
        try:
            # Reset browser state
            await self._reset_state()
            
            self.status = InstanceStatus.AVAILABLE
            self.last_used = time.time()
            
            self.logger.debug(f"Browser instance {self.instance_id} released")
            
        except Exception as e:
            self.logger.error(f"Error releasing browser instance {self.instance_id}", error=e)
            self.status = InstanceStatus.FAILED
    
    async def _reset_state(self):
        """Reset browser state for reuse."""
        if self.page:
            try:
                # Clear cookies and local storage
                await self.context.clear_cookies()
                await self.page.evaluate("localStorage.clear(); sessionStorage.clear();")
                
                # Navigate to blank page
                await self.page.goto("about:blank")
                
            except Exception as e:
                self.logger.warning(f"Error resetting browser state for {self.instance_id}", error=e)
    
    async def _cleanup(self):
        """Clean up browser resources."""
        self.status = InstanceStatus.CLEANUP
        self.logger.info(f"Cleaning up browser instance {self.instance_id}")
        
        try:
            # Run cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    await callback()
                except Exception as e:
                    self.logger.warning(f"Cleanup callback failed for {self.instance_id}", error=e)
            
            # Close page
            if self.page:
                await self.page.close()
                self.page = None
            
            # Close context
            if self.context:
                await self.context.close()
                self.context = None
            
            # Close browser
            if self.playwright_browser:
                await self.playwright_browser.close()
                self.playwright_browser = None
            
            self.browser_use_browser = None
            
        except Exception as e:
            self.logger.error(f"Error during cleanup of browser instance {self.instance_id}", error=e)
    
    def add_cleanup_callback(self, callback: callable):
        """Add a cleanup callback."""
        self._cleanup_callbacks.append(callback)
    
    def is_healthy(self) -> bool:
        """Check if the browser instance is healthy."""
        return (
            self.status in [InstanceStatus.AVAILABLE, InstanceStatus.IN_USE] and
            self.playwright_browser is not None and
            self.context is not None and
            self.page is not None
        )
    
    def get_age(self) -> float:
        """Get the age of this instance in seconds."""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """Get the idle time of this instance in seconds."""
        return time.time() - self.last_used


class BrowserPool:
    """
    Pool of browser instances for efficient resource management.
    """
    
    def __init__(self, max_size: int = 10, max_idle_time: int = 300, max_instance_age: int = 3600):
        self.max_size = max_size
        self.max_idle_time = max_idle_time  # 5 minutes
        self.max_instance_age = max_instance_age  # 1 hour
        
        self.available_instances: List[BrowserInstance] = []
        self.active_instances: Dict[str, BrowserInstance] = {}
        self.all_instances: Dict[str, BrowserInstance] = {}
        
        self.playwright_instance = None
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        self.logger = get_logger("browser-pool")
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
    
    async def _cleanup_worker(self):
        """Worker task that cleans up old and idle instances."""
        while not self._shutdown:
            try:
                await self._cleanup_old_instances()
                await asyncio.sleep(60)  # Run cleanup every minute
            except Exception as e:
                self.logger.error("Cleanup worker error", error=e)
                await asyncio.sleep(60)
    
    async def _cleanup_old_instances(self):
        """Clean up old and idle instances."""
        async with self._lock:
            current_time = time.time()
            instances_to_remove = []
            
            for instance in self.available_instances[:]:
                # Remove instances that are too old or idle
                if (instance.get_age() > self.max_instance_age or 
                    instance.get_idle_time() > self.max_idle_time or
                    not instance.is_healthy()):
                    
                    instances_to_remove.append(instance)
                    self.available_instances.remove(instance)
            
            # Clean up removed instances
            for instance in instances_to_remove:
                await self._destroy_instance(instance)
                self.logger.info(f"Cleaned up old/idle browser instance {instance.instance_id}")
    
    async def _ensure_playwright(self):
        """Ensure Playwright is initialized."""
        if self.playwright_instance is None:
            self.playwright_instance = await async_playwright().start()
    
    async def _create_instance(self, config: BrowserInstanceConfig) -> BrowserInstance:
        """Create a new browser instance."""
        await self._ensure_playwright()
        
        instance_id = str(uuid.uuid4())
        instance = BrowserInstance(instance_id, config)
        
        try:
            await instance.initialize(self.playwright_instance)
            self.all_instances[instance_id] = instance
            self.logger.info(f"Created new browser instance {instance_id}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create browser instance {instance_id}", error=e)
            raise
    
    async def _destroy_instance(self, instance: BrowserInstance):
        """Destroy a browser instance."""
        try:
            await instance._cleanup()
            self.all_instances.pop(instance.instance_id, None)
            self.logger.debug(f"Destroyed browser instance {instance.instance_id}")
        except Exception as e:
            self.logger.error(f"Error destroying browser instance {instance.instance_id}", error=e)
    
    async def acquire(self, headless: bool = True, timeout: int = 30) -> BrowserInstance:
        """Acquire a browser instance from the pool."""
        config = BrowserInstanceConfig(headless=headless)
        
        async with self._lock:
            # Try to find an available instance with matching config
            for instance in self.available_instances[:]:
                if (instance.config.headless == config.headless and 
                    instance.is_healthy()):
                    
                    self.available_instances.remove(instance)
                    await instance.acquire()
                    self.active_instances[instance.instance_id] = instance
                    
                    self.logger.debug(f"Acquired existing browser instance {instance.instance_id}")
                    return instance
            
            # Create new instance if pool not at capacity
            if len(self.all_instances) < self.max_size:
                instance = await self._create_instance(config)
                await instance.acquire()
                self.active_instances[instance.instance_id] = instance
                
                self.logger.info(f"Created and acquired new browser instance {instance.instance_id}")
                return instance
            
            # Pool is full, wait for an instance to become available
            self.logger.warning("Browser pool is full, waiting for available instance")
            
        # Wait for an instance to become available (with timeout)
        start_time = time.time()
        while time.time() - start_time < timeout:
            await asyncio.sleep(0.5)
            
            async with self._lock:
                if self.available_instances:
                    instance = self.available_instances.pop(0)
                    if instance.is_healthy():
                        await instance.acquire()
                        self.active_instances[instance.instance_id] = instance
                        return instance
                    else:
                        # Instance is unhealthy, destroy it
                        await self._destroy_instance(instance)
        
        raise TimeoutError(f"Failed to acquire browser instance within {timeout} seconds")
    
    async def release(self, instance: BrowserInstance):
        """Release a browser instance back to the pool."""
        async with self._lock:
            if instance.instance_id not in self.active_instances:
                self.logger.warning(f"Attempting to release unknown instance {instance.instance_id}")
                return
            
            # Remove from active instances
            self.active_instances.pop(instance.instance_id, None)
            
            try:
                await instance.release()
                
                # Add back to available instances if healthy
                if instance.is_healthy():
                    self.available_instances.append(instance)
                    self.logger.debug(f"Released browser instance {instance.instance_id} back to pool")
                else:
                    # Instance is unhealthy, destroy it
                    await self._destroy_instance(instance)
                    self.logger.info(f"Destroyed unhealthy browser instance {instance.instance_id}")
                    
            except Exception as e:
                self.logger.error(f"Error releasing browser instance {instance.instance_id}", error=e)
                await self._destroy_instance(instance)
    
    async def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        async with self._lock:
            return {
                "total_instances": len(self.all_instances),
                "available_instances": len(self.available_instances),
                "active_instances": len(self.active_instances),
                "max_size": self.max_size
            }
    
    @asynccontextmanager
    async def browser_instance(self, headless: bool = True, timeout: int = 30):
        """Context manager for acquiring and releasing browser instances."""
        instance = await self.acquire(headless=headless, timeout=timeout)
        try:
            yield instance
        finally:
            await self.release(instance)
    
    async def shutdown(self):
        """Shutdown the browser pool and clean up all resources."""
        self.logger.info("Shutting down browser pool")
        self._shutdown = True
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            # Destroy all instances
            all_instances = list(self.all_instances.values())
            for instance in all_instances:
                await self._destroy_instance(instance)
            
            self.available_instances.clear()
            self.active_instances.clear()
            self.all_instances.clear()
        
        # Close Playwright
        if self.playwright_instance:
            await self.playwright_instance.stop()
            self.playwright_instance = None
        
        self.logger.info("Browser pool shutdown complete")

