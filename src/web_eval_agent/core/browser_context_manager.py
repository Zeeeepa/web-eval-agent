"""
Enhanced Browser Context Manager

This module provides a comprehensive browser context manager that integrates
both browser-use agents and Playwright for advanced monitoring and control.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from browser_use import Agent, BrowserSession, BrowserProfile

logger = logging.getLogger(__name__)


@dataclass
class BrowserEvent:
    """Represents a browser event with timestamp and context."""
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    source: str  # 'console', 'network', 'performance', 'interaction'
    severity: str = 'info'  # 'error', 'warning', 'info', 'debug'


@dataclass
class NetworkRequest:
    """Detailed network request information."""
    url: str
    method: str
    headers: Dict[str, str]
    timestamp: float
    request_id: str
    resource_type: str
    response: Optional[Dict[str, Any]] = None
    timing: Optional[Dict[str, float]] = None
    error: Optional[str] = None


@dataclass
class ConsoleMessage:
    """Console message with categorization."""
    timestamp: float
    level: str  # 'error', 'warning', 'info', 'debug', 'log'
    text: str
    location: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    args: List[Any] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance metrics collection."""
    timestamp: float
    page_load_time: Optional[float] = None
    dom_content_loaded: Optional[float] = None
    first_paint: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    memory_usage: Optional[Dict[str, int]] = None
    resource_count: Optional[int] = None


class BrowserContextManager:
    """
    Enhanced browser context manager that provides comprehensive monitoring
    and control capabilities by integrating browser-use and Playwright.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_session = None
        
        # Event storage
        self.events: List[BrowserEvent] = []
        self.console_messages: List[ConsoleMessage] = []
        self.network_requests: List[NetworkRequest] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'console': [],
            'network': [],
            'performance': [],
            'error': [],
            'interaction': []
        }
        
        # State tracking
        self.is_initialized = False
        self.monitoring_active = False
        self.start_time = None
        
    async def initialize(self) -> None:
        """Initialize both Playwright and browser-use sessions."""
        if self.is_initialized:
            return
            
        logger.info("Initializing enhanced browser context manager...")
        
        try:
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Configure browser launch options
            browser_args = [
                '--disable-gpu',
                '--no-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--enable-automation',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            
            if self.config.get('headless', True):
                browser_args.append('--headless=new')
                
            # Launch browser with monitoring capabilities
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=browser_args,
                slow_mo=self.config.get('slow_mo', 0)
            )
            
            # Create context with enhanced permissions
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                permissions=['geolocation', 'notifications'],
                ignore_https_errors=True
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set up monitoring
            await self._setup_monitoring()
            
            # Initialize browser-use session
            await self._setup_browser_use_session()
            
            self.is_initialized = True
            self.start_time = time.time()
            
            logger.info("Browser context manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser context manager: {e}")
            await self.cleanup()
            raise
            
    async def _setup_monitoring(self) -> None:
        """Set up comprehensive browser monitoring."""
        if not self.page:
            return
            
        # Console monitoring
        self.page.on('console', self._handle_console_message)
        self.page.on('pageerror', self._handle_page_error)
        
        # Network monitoring
        self.page.on('request', self._handle_request)
        self.page.on('response', self._handle_response)
        self.page.on('requestfailed', self._handle_request_failed)
        
        # Performance monitoring
        await self.page.add_init_script("""
            // Inject performance monitoring script
            window.__webEvalAgent = {
                startTime: performance.now(),
                events: [],
                
                recordEvent: function(type, data) {
                    this.events.push({
                        timestamp: performance.now(),
                        type: type,
                        data: data
                    });
                }
            };
            
            // Monitor performance metrics
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.__webEvalAgent.recordEvent('performance', {
                        name: entry.name,
                        entryType: entry.entryType,
                        startTime: entry.startTime,
                        duration: entry.duration,
                        ...entry.toJSON()
                    });
                }
            }).observe({entryTypes: ['navigation', 'paint', 'largest-contentful-paint', 'layout-shift']});
        """)
        
        self.monitoring_active = True
        logger.info("Browser monitoring setup complete")
        
    async def _setup_browser_use_session(self) -> None:
        """Initialize browser-use session for AI-driven interactions."""
        try:
            # Create browser profile compatible with our Playwright setup
            browser_profile = BrowserProfile(
                headless=self.config.get('headless', True),
                disable_security=True,
                user_data_dir=None,
                args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage'],
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=8.0,
                wait_between_actions=0.5
            )
            
            # Create browser session
            self.browser_session = BrowserSession(
                browser_profile=browser_profile,
                headless=self.config.get('headless', True)
            )
            
            logger.info("Browser-use session initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize browser-use session: {e}")
            # Continue without browser-use if it fails
            
    async def navigate_to(self, url: str) -> Dict[str, Any]:
        """Navigate to URL with comprehensive monitoring."""
        if not self.is_initialized:
            await self.initialize()
            
        logger.info(f"Navigating to: {url}")
        
        # Record navigation start
        nav_start = time.time()
        self._record_event('navigation', {'action': 'start', 'url': url})
        
        try:
            # Navigate with Playwright for monitoring
            response = await self.page.goto(
                url, 
                wait_until='networkidle',
                timeout=self.config.get('navigation_timeout', 30000)
            )
            
            # Wait for page to stabilize
            await asyncio.sleep(1)
            
            # Collect initial performance metrics
            performance_data = await self._collect_performance_metrics()
            
            # Record navigation completion
            nav_duration = time.time() - nav_start
            self._record_event('navigation', {
                'action': 'complete',
                'url': url,
                'duration': nav_duration,
                'status': response.status if response else None
            })
            
            return {
                'success': True,
                'url': url,
                'status': response.status if response else None,
                'duration': nav_duration,
                'performance': performance_data
            }
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            self._record_event('navigation', {
                'action': 'failed',
                'url': url,
                'error': str(e),
                'duration': time.time() - nav_start
            })
            
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'duration': time.time() - nav_start
            }
            
    async def create_agent(self, task: str, llm) -> Optional[Agent]:
        """Create a browser-use agent with the current session."""
        if not self.browser_session:
            logger.warning("Browser-use session not available, cannot create agent")
            return None
            
        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser_session=self.browser_session,
                use_vision=True
            )
            
            logger.info(f"Created agent for task: {task[:60]}...")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
            
    async def _handle_console_message(self, message) -> None:
        """Handle console messages from the browser."""
        console_msg = ConsoleMessage(
            timestamp=time.time(),
            level=message.type,
            text=message.text,
            location=message.location,
            args=[str(arg) for arg in message.args]
        )
        
        self.console_messages.append(console_msg)
        
        # Determine severity
        severity = 'info'
        if message.type in ['error', 'assert']:
            severity = 'error'
        elif message.type == 'warning':
            severity = 'warning'
            
        self._record_event('console', {
            'level': message.type,
            'text': message.text,
            'location': message.location
        }, severity=severity)
        
        # Call registered handlers
        for handler in self.event_handlers.get('console', []):
            try:
                await handler(console_msg)
            except Exception as e:
                logger.error(f"Console handler error: {e}")
                
    async def _handle_page_error(self, error) -> None:
        """Handle JavaScript errors on the page."""
        error_msg = ConsoleMessage(
            timestamp=time.time(),
            level='error',
            text=str(error),
            stack_trace=getattr(error, 'stack', None)
        )
        
        self.console_messages.append(error_msg)
        
        self._record_event('error', {
            'type': 'javascript',
            'message': str(error),
            'stack': getattr(error, 'stack', None)
        }, severity='error')
        
    async def _handle_request(self, request) -> None:
        """Handle network requests."""
        network_req = NetworkRequest(
            url=request.url,
            method=request.method,
            headers=request.headers,
            timestamp=time.time(),
            request_id=str(id(request)),
            resource_type=request.resource_type
        )
        
        self.network_requests.append(network_req)
        
        self._record_event('network', {
            'type': 'request',
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type
        })
        
    async def _handle_response(self, response) -> None:
        """Handle network responses."""
        # Find corresponding request
        request_id = str(id(response.request))
        for req in self.network_requests:
            if req.request_id == request_id:
                req.response = {
                    'status': response.status,
                    'status_text': response.status_text,
                    'headers': response.headers,
                    'timestamp': time.time()
                }
                break
                
        self._record_event('network', {
            'type': 'response',
            'url': response.url,
            'status': response.status,
            'status_text': response.status_text
        })
        
    async def _handle_request_failed(self, request) -> None:
        """Handle failed network requests."""
        # Find corresponding request
        request_id = str(id(request))
        for req in self.network_requests:
            if req.request_id == request_id:
                req.error = "Request failed"
                break
                
        self._record_event('network', {
            'type': 'request_failed',
            'url': request.url,
            'method': request.method
        }, severity='error')
        
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # Get performance data from browser
            perf_data = await self.page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const paint = performance.getEntriesByType('paint');
                    const lcp = performance.getEntriesByType('largest-contentful-paint')[0];
                    const cls = performance.getEntriesByType('layout-shift');
                    
                    return {
                        pageLoadTime: navigation ? navigation.loadEventEnd - navigation.fetchStart : null,
                        domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.fetchStart : null,
                        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || null,
                        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null,
                        largestContentfulPaint: lcp ? lcp.startTime : null,
                        cumulativeLayoutShift: cls.reduce((sum, entry) => sum + entry.value, 0),
                        memoryUsage: performance.memory ? {
                            usedJSHeapSize: performance.memory.usedJSHeapSize,
                            totalJSHeapSize: performance.memory.totalJSHeapSize,
                            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                        } : null,
                        resourceCount: performance.getEntriesByType('resource').length
                    };
                }
            """)
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                page_load_time=perf_data.get('pageLoadTime'),
                dom_content_loaded=perf_data.get('domContentLoaded'),
                first_paint=perf_data.get('firstPaint'),
                first_contentful_paint=perf_data.get('firstContentfulPaint'),
                largest_contentful_paint=perf_data.get('largestContentfulPaint'),
                cumulative_layout_shift=perf_data.get('cumulativeLayoutShift'),
                memory_usage=perf_data.get('memoryUsage'),
                resource_count=perf_data.get('resourceCount')
            )
            
            self.performance_metrics.append(metrics)
            
            self._record_event('performance', {
                'page_load_time': metrics.page_load_time,
                'dom_content_loaded': metrics.dom_content_loaded,
                'first_contentful_paint': metrics.first_contentful_paint,
                'largest_contentful_paint': metrics.largest_contentful_paint,
                'cumulative_layout_shift': metrics.cumulative_layout_shift,
                'memory_usage': metrics.memory_usage,
                'resource_count': metrics.resource_count
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            return PerformanceMetrics(timestamp=time.time())
            
    def _record_event(self, event_type: str, data: Dict[str, Any], severity: str = 'info') -> None:
        """Record a browser event."""
        event = BrowserEvent(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=event_type,
            severity=severity
        )
        
        self.events.append(event)
        
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the browser session."""
        if not self.start_time:
            return {}
            
        session_duration = time.time() - self.start_time
        
        # Categorize console messages
        console_stats = {
            'total': len(self.console_messages),
            'errors': len([m for m in self.console_messages if m.level == 'error']),
            'warnings': len([m for m in self.console_messages if m.level == 'warning']),
            'info': len([m for m in self.console_messages if m.level in ['info', 'log']])
        }
        
        # Network statistics
        network_stats = {
            'total_requests': len(self.network_requests),
            'failed_requests': len([r for r in self.network_requests if r.error]),
            'status_codes': {}
        }
        
        for req in self.network_requests:
            if req.response:
                status = req.response['status']
                network_stats['status_codes'][status] = network_stats['status_codes'].get(status, 0) + 1
                
        # Performance summary
        latest_perf = self.performance_metrics[-1] if self.performance_metrics else None
        
        return {
            'session_duration': session_duration,
            'total_events': len(self.events),
            'console': console_stats,
            'network': network_stats,
            'performance': {
                'page_load_time': latest_perf.page_load_time if latest_perf else None,
                'first_contentful_paint': latest_perf.first_contentful_paint if latest_perf else None,
                'largest_contentful_paint': latest_perf.largest_contentful_paint if latest_perf else None,
                'cumulative_layout_shift': latest_perf.cumulative_layout_shift if latest_perf else None,
                'memory_usage': latest_perf.memory_usage if latest_perf else None
            },
            'monitoring_active': self.monitoring_active
        }
        
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        logger.info("Cleaning up browser context manager...")
        
        try:
            if self.browser_session:
                await self.browser_session.close()
                
            if self.page:
                await self.page.close()
                
            if self.context:
                await self.context.close()
                
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
        self.is_initialized = False
        self.monitoring_active = False
        
        logger.info("Browser context manager cleanup complete")

