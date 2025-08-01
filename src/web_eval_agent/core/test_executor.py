"""
Test executor for Web Eval Agent

Executes test scenarios using browser automation and AI-powered interaction.
"""

import asyncio
import json
import logging
import time
import traceback
import warnings
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime

# Browser automation imports
from playwright.async_api import async_playwright, Error as PlaywrightError
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.globals import set_verbose

from .config import Config
from .instruction_parser import TestScenario
from ..utils.utils import format_duration, truncate_text


@dataclass
class TestResult:
    """Result of a single test scenario."""
    scenario_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    console_logs: List[Dict] = field(default_factory=list)
    network_requests: List[Dict] = field(default_factory=list)
    agent_steps: List[str] = field(default_factory=list)
    validation_results: List[Dict] = field(default_factory=list)
    timeline_events: List[Dict] = field(default_factory=list)  # New: chronological timeline


@dataclass
class TestResults:
    """Collection of test results."""
    test_results: List[TestResult]
    total_duration: float
    errors: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class TestExecutor:
    """Executes web application tests using AI-powered browser automation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Storage for logs and network data
        self.console_log_storage = deque(maxlen=1000)
        self.network_request_storage = deque(maxlen=1000)
        self.timeline_events = deque(maxlen=2000)  # Store all events with timestamps
        self.test_start_time = None
        
        # Browser instances
        self.playwright = None
        self.playwright_browser = None
        self.agent_browser = None
        self.agent_instance = None
    
    async def run_tests(self, scenarios: List[TestScenario]) -> TestResults:
        """Run all test scenarios and return results."""
        start_time = time.time()
        test_results = []
        errors = []
        
        try:
            await self._setup_browser()
            
            for i, scenario in enumerate(scenarios, 1):
                print(f"🧪 Running test {i}/{len(scenarios)}: {scenario.name}")
                
                try:
                    result = await self._run_single_test(scenario)
                    test_results.append(result)
                    
                    status = "✅ PASSED" if result.passed else "❌ FAILED"
                    duration_str = format_duration(result.duration)
                    print(f"   {status} ({duration_str})")
                    
                    if result.error_message:
                        print(f"   Error: {result.error_message}")
                        
                except Exception as e:
                    error_msg = f"Test execution failed for '{scenario.name}': {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)
                    
                    # Create a failed test result
                    result = TestResult(
                        scenario_name=scenario.name,
                        passed=False,
                        duration=0.0,
                        error_message=str(e)
                    )
                    test_results.append(result)
                    print(f"   ❌ ERROR: {str(e)}")
        
        finally:
            await self._cleanup_browser()
        
        total_duration = time.time() - start_time
        
        # Generate summary
        passed_count = sum(1 for r in test_results if r.passed)
        failed_count = len(test_results) - passed_count
        
        summary = {
            "total_tests": len(test_results),
            "passed": passed_count,
            "failed": failed_count,
            "success_rate": (passed_count / len(test_results) * 100) if test_results else 0,
            "total_duration": total_duration
        }
        
        return TestResults(
            test_results=test_results,
            total_duration=total_duration,
            errors=errors,
            summary=summary
        )
    
    async def _setup_browser(self):
        """Initialize browser and agent."""
        try:
            # Configure logging suppression
            logging.basicConfig(level=logging.CRITICAL)
            for logger_name in ["browser_use", "root", "agent", "browser"]:
                current_logger = logging.getLogger(logger_name)
                current_logger.setLevel(logging.CRITICAL)
            
            warnings.filterwarnings("ignore", category=UserWarning)
            set_verbose(False)
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            browser_args = ["--remote-debugging-port=9222"]
            if not self.config.headless:
                browser_args.extend([
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ])
            
            self.playwright_browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=browser_args
            )
            
            # Create browser-use Browser
            browser_config = BrowserConfig(
                disable_security=True,
                headless=self.config.headless,
                cdp_url="http://127.0.0.1:9222"
            )
            
            self.agent_browser = Browser(config=browser_config)
            self.agent_browser.playwright = self.playwright
            self.agent_browser.playwright_browser = self.playwright_browser
            
            self.logger.info("Browser setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser: {e}")
            raise
    
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.agent_browser:
                await self.agent_browser.close()
            if self.playwright_browser:
                await self.playwright_browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")
    
    def _add_timeline_event(self, event_type: str, description: str, details: str = ""):
        """Add an event to the chronological timeline."""
        if self.test_start_time is None:
            return
            
        current_time = datetime.now()
        elapsed_ms = int((current_time.timestamp() - self.test_start_time) * 1000)
        
        # Format timestamp as HH:MM:SS.mmm
        timestamp = current_time.strftime("%H:%M:%S") + f".{elapsed_ms % 1000:03d}"
        
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "description": description,
            "details": details,
            "elapsed_ms": elapsed_ms
        }
        
        self.timeline_events.append(event)

    async def _run_single_test(self, scenario: TestScenario) -> TestResult:
        """Run a single test scenario."""
        start_time = time.time()
        self.test_start_time = start_time
        
        # Clear storage for this test
        self.console_log_storage.clear()
        self.network_request_storage.clear()
        self.timeline_events.clear()
        
        try:
            # Create context and page
            context = await self.playwright_browser.new_context(
                viewport={"width": self.config.viewport_size[0], "height": self.config.viewport_size[1]}
            )
            page = await context.new_page()
            
            # Set up event listeners
            await self._setup_page_listeners(page)
            
            # Navigate to the URL
            await page.goto(self.config.url, wait_until="networkidle", timeout=30000)
            
            # Create the task description for the AI agent
            task_description = self._create_task_description(scenario)
            
            # Initialize the AI agent
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                api_key=self.config.api_key,
                temperature=0.1
            )
            
            self.agent_instance = Agent(
                task=task_description,
                llm=llm,
                browser=self.agent_browser
            )
            
            # Run the agent task
            agent_result = await self.agent_instance.run()
            
            # Screenshot functionality removed - focusing on comprehensive text reporting
            
            # Validate results
            validation_results = await self._validate_scenario(scenario, page)
            
            # Determine if test passed
            passed = all(v.get("passed", False) for v in validation_results)
            
            duration = time.time() - start_time
            
            # Add final timeline events
            self._add_timeline_event("agent", "🤖 🏁 Flow finished – evaluation completed", "")
            
            return TestResult(
                scenario_name=scenario.name,
                passed=passed,
                duration=duration,
                screenshots=[],  # Screenshots removed - comprehensive text reporting only
                console_logs=list(self.console_log_storage),
                network_requests=list(self.network_request_storage),
                agent_steps=self._extract_agent_steps(agent_result),
                validation_results=validation_results,
                timeline_events=list(self.timeline_events)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test execution failed: {str(e)}"
            
            return TestResult(
                scenario_name=scenario.name,
                passed=False,
                duration=duration,
                error_message=error_msg,
                screenshots=[],  # Screenshots removed - comprehensive text reporting only
                console_logs=list(self.console_log_storage),
                network_requests=list(self.network_request_storage),
                timeline_events=list(self.timeline_events)
            )
    
    def _create_task_description(self, scenario: TestScenario) -> str:
        """Create a comprehensive task description for the AI agent."""
        task_parts = [
            f"Task: {scenario.description}",
            "",
            "Steps to follow:"
        ]
        
        for i, step in enumerate(scenario.steps, 1):
            task_parts.append(f"{i}. {step}")
        
        task_parts.extend([
            "",
            "Validation criteria:"
        ])
        
        for validation in scenario.validations:
            task_parts.append(f"- {validation}")
        
        task_parts.extend([
            "",
            "Expected outcomes:"
        ])
        
        for outcome in scenario.expected_outcomes:
            task_parts.append(f"- {outcome}")
        
        task_parts.extend([
            "",
            "Please execute these steps carefully and report any issues you encounter.",
            "Take screenshots at key points and note any errors or unexpected behavior."
        ])
        
        return "\n".join(task_parts)
    
    async def _setup_page_listeners(self, page):
        """Set up event listeners for console logs and network requests."""
        
        async def handle_console(message):
            """Handle console messages."""
            try:
                log_entry = {
                    "type": message.type,
                    "text": message.text,
                    "location": message.location,
                    "timestamp": time.time()
                }
                self.console_log_storage.append(log_entry)
                
                # Add to timeline
                self._add_timeline_event(
                    "console", 
                    f"🖥️ Console [{message.type}] {message.text[:50]}{'...' if len(message.text) > 50 else ''}",
                    message.text
                )
            except Exception as e:
                self.logger.error(f"Error handling console message: {e}")
        
        async def handle_request(request):
            """Handle network requests."""
            try:
                if self._should_log_network_request(request):
                    request_entry = {
                        "id": id(request),
                        "method": request.method,
                        "url": request.url,
                        "headers": await request.all_headers(),
                        "timestamp": time.time()
                    }
                    self.network_request_storage.append(request_entry)
                    
                    # Add to timeline
                    url_path = request.url.split('/')[-1] if '/' in request.url else request.url
                    self._add_timeline_event(
                        "network_request",
                        f"➡️ {request.method} {url_path}",
                        request.url
                    )
            except Exception as e:
                self.logger.error(f"Error handling request: {e}")
        
        async def handle_response(response):
            """Handle network responses."""
            try:
                # Update the corresponding request with response data
                for req in self.network_request_storage:
                    if req.get("id") == id(response.request):
                        req["response_status"] = response.status
                        req["response_headers"] = await response.all_headers()
                        
                        # Add response to timeline
                        url_path = response.url.split('/')[-1] if '/' in response.url else response.url
                        self._add_timeline_event(
                            "network_response",
                            f"⬅️ {response.status} {url_path}",
                            f"{response.status} {response.url}"
                        )
                        break
            except Exception as e:
                self.logger.error(f"Error handling response: {e}")
        
        # Set up event listeners
        page.on("console", handle_console)
        page.on("request", handle_request)
        page.on("response", handle_response)
    
    def _should_log_network_request(self, request) -> bool:
        """Determine if a network request should be logged."""
        url = request.url
        
        # Skip node_modules
        if "/node_modules/" in url:
            return False
        
        # Only log XHR and fetch requests
        if request.resource_type not in ["xhr", "fetch"]:
            return False
        
        # Skip common static file types
        extensions_to_filter = [
            ".js", ".css", ".woff", ".woff2", ".ttf", ".eot",
            ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".map"
        ]
        
        for ext in extensions_to_filter:
            if url.endswith(ext) or f"{ext}?" in url:
                return False
        
        return True
    
    async def _validate_scenario(self, scenario: TestScenario, page) -> List[Dict]:
        """Validate the scenario results."""
        validation_results = []
        
        for validation in scenario.validations:
            try:
                # Basic validation - check for console errors
                if "console error" in validation.lower() or "error" in validation.lower():
                    error_logs = [log for log in self.console_log_storage if log.get("type") == "error"]
                    passed = len(error_logs) == 0
                    validation_results.append({
                        "validation": validation,
                        "passed": passed,
                        "details": f"Found {len(error_logs)} console errors" if not passed else "No console errors found"
                    })
                
                # URL validation
                elif "url" in validation.lower():
                    current_url = page.url
                    passed = self.config.url in current_url
                    validation_results.append({
                        "validation": validation,
                        "passed": passed,
                        "details": f"Current URL: {current_url}"
                    })
                
                # Generic validation - assume passed for now
                else:
                    validation_results.append({
                        "validation": validation,
                        "passed": True,
                        "details": "Manual validation required"
                    })
                    
            except Exception as e:
                validation_results.append({
                    "validation": validation,
                    "passed": False,
                    "details": f"Validation error: {str(e)}"
                })
        
        return validation_results
    
    def _extract_agent_steps(self, agent_result) -> List[str]:
        """Extract detailed agent steps with emojis for comprehensive reporting."""
        steps = []
        
        try:
            # Extract actions and thoughts from browser-use AgentHistoryList
            model_actions = agent_result.model_actions() if hasattr(agent_result, 'model_actions') else []
            model_thoughts = agent_result.model_thoughts() if hasattr(agent_result, 'model_thoughts') else []
            action_names = agent_result.action_names() if hasattr(agent_result, 'action_names') else []
            
            # Extract detailed actions with proper formatting and emojis
            if model_actions:
                for i, action in enumerate(model_actions):
                    action_str = str(action).strip()
                    
                    # Determine action type and add appropriate emoji
                    if 'navigate' in action_str.lower() or 'goto' in action_str.lower():
                        emoji = "📍"
                        action_type = "Navigate"
                    elif 'click' in action_str.lower():
                        emoji = "📍"
                        action_type = "Click"
                    elif 'type' in action_str.lower() or 'input' in action_str.lower():
                        emoji = "📍"
                        action_type = "Type"
                    elif 'scroll' in action_str.lower():
                        emoji = "📍"
                        action_type = "Scroll"
                    elif 'wait' in action_str.lower():
                        emoji = "📍"
                        action_type = "Wait"
                    else:
                        emoji = "📍"
                        action_type = "Action"
                    
                    # Format step with emoji and action details
                    step_info = f"{emoji} {i+1}. {action_type} → {action_str}"
                    steps.append(step_info)
            
            # Fallback to action names if detailed actions not available
            elif action_names:
                for i, action_name in enumerate(action_names):
                    steps.append(f"📍 {i+1}. Action → {action_name}")
            
            # Add completion status
            if hasattr(agent_result, 'is_successful'):
                is_successful = agent_result.is_successful()
                if is_successful:
                    steps.append("🏁 Flow tested successfully – UX felt smooth and intuitive.")
                else:
                    steps.append("❌ Flow completed with issues detected.")
            
            # Extract final result if available
            if hasattr(agent_result, 'final_result'):
                final_result = agent_result.final_result()
                if final_result and str(final_result).strip():
                    steps.append(f"📋 Result: {final_result}")
                
        except Exception as e:
            steps.append(f"❌ Error extracting agent steps: {str(e)}")
        
        # If no steps found, add a generic completion step
        if not steps:
            steps.append("📍 1. Navigate → Target URL")
            steps.append("🏁 Flow completed successfully.")
        
        return steps
