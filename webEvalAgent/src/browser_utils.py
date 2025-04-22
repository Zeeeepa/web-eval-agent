#!/usr/bin/env python3

import asyncio
import io
import json
import logging
import uuid
import warnings
import os
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Tuple, List, Optional
from collections import deque

# Import log server function
from .log_server import send_log
# Import auth utils
from .auth_utils import get_auth_profile_dir

# Import Playwright types
from playwright.async_api import async_playwright, Error as PlaywrightError, Browser as PlaywrightBrowser, BrowserContext as PlaywrightBrowserContext, Page as PlaywrightPage

# Local imports (assuming browser_manager is potentially still used for singleton logic elsewhere, or can be removed if fully replaced)
# from browser_manager import PlaywrightBrowserManager # Commented out if not needed

# Browser-use imports
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext # Import BrowserContext

# Langchain/MCP imports
from langchain_anthropic import ChatAnthropic
from mcp.server.fastmcp import Context
from langchain.globals import set_verbose

# This prevents the browser window from stealing focus during execution.
async def _no_bring_to_front(self, *args, **kwargs):
    print("Skipping bring_to_front call.") # Optional: for debugging
    return None

PlaywrightPage.bring_to_front = _no_bring_to_front
# --- End Patch ---

# Global variable to store agent instance - might be less necessary if Agent is created per task run
agent_instance = None
# Global variable to store the original patched method if patching class-level
original_create_context: Optional[callable] = None

# Define the maximum number of logs/requests to keep
MAX_LOG_ENTRIES = 10

# --- URL Filtering for Network Requests ---
def should_log_network_request(url: str) -> bool:
    """Determine if a network request should be logged based on its URL.
    
    Args:
        url: The URL of the request
        
    Returns:
        bool: True if the request should be logged, False if it should be filtered out
    """
    # Filter out common static assets that aren't usually relevant
    # Add or remove patterns based on your specific needs
    
    # Skip node_modules requests (usually library code)
    if '/node_modules/' in url:
        return False
        
    # Skip common static file types
    extensions_to_filter = [
        '.js', '.css', '.woff', '.woff2', '.ttf', '.eot', '.svg', '.png', 
        '.jpg', '.jpeg', '.gif', '.ico', '.map'
    ]
    
    for ext in extensions_to_filter:
        if url.endswith(ext) or f"{ext}?" in url:  # Handle URLs with query params
            return False
    
    # Always log API endpoints (usually important)
    if '/api/' in url or '/graphql' in url:
        return True
        
    # Log navigation requests (page loads)
    if '?' not in url and '.' not in url.split('/')[-1]:
        return True
    
    # By default, log everything that wasn't filtered
    return True

# --- Log Storage (Global within this module using deque) ---
console_log_storage: deque = deque(maxlen=MAX_LOG_ENTRIES)
network_request_storage: deque = deque(maxlen=MAX_LOG_ENTRIES)

# --- Log Handlers (Use deque's append and send_log with type) ---
async def handle_console_message(message):
    try:
        text = message.text
        log_entry = { "type": message.type, "text": text, "location": message.location, "timestamp": asyncio.get_event_loop().time() }
        console_log_storage.append(log_entry)
        # Send to dashboard with type 'console'
        send_log(f"CONSOLE [{log_entry['type']}]: {log_entry['text']}", "🖥️", log_type='console')
    except Exception as e:
        # Send to dashboard with type 'status' or 'agent' for errors
        send_log(f"Error handling console message: {e}", "❌", log_type='status')

async def handle_request(request):
    try:
        if not should_log_network_request(request.url):
            return
            
        try: headers = await request.all_headers()
        except PlaywrightError as e: headers = {"error": f"Req Header Error: {e}"}
        except Exception as e: headers = {"error": f"Unexpected Req Header Error: {e}"}

        post_data = None
        try:
            if request.post_data:
                 post_data_buffer = await request.post_data_buffer()
                 if post_data_buffer:
                     try: post_data = post_data_buffer.decode('utf-8', errors='replace')
                     except Exception: post_data = repr(post_data_buffer)
                 else: post_data = ""
            else: post_data = None
        except PlaywrightError as e: post_data = f"Post Data Error: {e}"
        except Exception as e: post_data = f"Unexpected Post Data Error: {e}"

        request_entry = { "url": request.url, "method": request.method, "headers": headers, "postData": post_data, "timestamp": asyncio.get_event_loop().time(), "resourceType": request.resource_type, "is_navigation": request.is_navigation_request(), "id": id(request) }
        network_request_storage.append(request_entry)
        # Send to dashboard with type 'network'
        send_log(f"NET REQ [{request_entry['method']}]: {request_entry['url']}", "➡️", log_type='network')
    except Exception as e:
        url = request.url if request else 'Unknown URL'
        # Send error to dashboard with type 'status' or 'agent'
        send_log(f"Error handling request event for {url}: {e}", "❌", log_type='status')

async def handle_response(response):
    req_id = id(response.request)
    url = response.url
    
    if not should_log_network_request(url):
        return
        
    try:
        try: headers = await response.all_headers()
        except PlaywrightError as e: headers = {"error": f"Resp Header Error: {e}"}
        except Exception as e: headers = {"error": f"Unexpected Resp Header Error: {e}"}
        status = response.status

        body_size = -1
        try:
            body_buffer = await response.body()
            body_size = len(body_buffer) if body_buffer else 0
        except PlaywrightError as e: print(f"Warning: Could not get response body size for {url}: {e}")
        except Exception as e: print(f"Warning: Unexpected error getting response body size for {url}: {e}")

        for req in network_request_storage:
            if req.get("id") == req_id and "response_status" not in req:
                req["response_status"] = status
                req["response_headers"] = headers
                req["response_body_size"] = body_size
                req["response_timestamp"] = asyncio.get_event_loop().time()
                # Send to dashboard with type 'network'
                send_log(f"NET RESP [{status}]: {url}", "⬅️", log_type='network')
                break
        else:
            # Send unmatched response to dashboard with type 'network'
             send_log(f"NET RESP* [{status}]: {url} (req not matched/updated)", "⬅️", log_type='network')
    except Exception as e:
        # Send error to dashboard with type 'status' or 'agent'
        send_log(f"Error handling response event for {url}: {e}", "❌", log_type='status')


async def run_browser_task(task: str, model: str = "gemini-2.0-flash-001", ctx: Context = None, tool_call_id: str = None, api_key: str = None) -> str:
    """
    Run a task using browser-use agent, sending logs to the dashboard.

    Args:
        task: The task to run.
        model: The model identifier (not directly used for LLM here, taken from ChatAnthropic).
        ctx: The MCP context for progress reporting.
        tool_call_id: The tool call ID for API headers.
        api_key: The API key for authentication.

    Returns:
        str: Agent's final result (stringified).
    """
    global agent_instance, console_log_storage, network_request_storage, original_create_context
    import traceback # Make sure traceback is imported for error logging

    # --- Clear Logs for this Run ---
    console_log_storage.clear()
    network_request_storage.clear()

    # Local Playwright variables for this run
    playwright = None
    playwright_browser = None
    agent_browser = None # browser-use Browser instance
    local_original_create_context = None # To store original method for this run's finally block

    # Configure logging suppression
    logging.basicConfig(level=logging.CRITICAL) # Set root logger level first
    # Then configure specific loggers
    for logger_name in ['browser_use', 'root', 'agent', 'browser']:
        # Get the logger for the current name and set its level
        current_logger = logging.getLogger(logger_name)
        current_logger.setLevel(logging.CRITICAL)

    warnings.filterwarnings("ignore", category=UserWarning)
    set_verbose(False)

    try:
        # --- Get auth profile directory ---
        auth_profile_dir = get_auth_profile_dir()
        use_auth_profile = os.path.exists(auth_profile_dir)
        
        if use_auth_profile:
            send_log(f"Using auth profile from: {auth_profile_dir}", "🔑", log_type='status')
        else:
            send_log("No auth profile found, browser will launch without saved session", "⚠️", log_type='status')

        # --- Initialize Playwright with auth profile if it exists ---
        playwright = await async_playwright().start()
        
        if use_auth_profile:
            # Launch with persistent context using the auth profile
            try:
                playwright_context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=auth_profile_dir,
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ]
                )
                playwright_browser = playwright_context.browser
                send_log("Playwright initialized with auth profile", "🎭", log_type='status')
            except Exception as e:
                send_log(f"Error launching with auth profile: {e}", "❌", log_type='status')
                # Fall back to regular browser
                playwright_browser = await playwright.chromium.launch(headless=False)
                send_log("Fallback: Playwright initialized without auth profile", "🎭", log_type='status')
        else:
            # Regular browser launch
            playwright_browser = await playwright.chromium.launch(headless=False)
            send_log("Playwright initialized for task.", "🎭", log_type='status')

        # --- Create browser-use Browser ---
        browser_config = BrowserConfig(disable_security=True, headless=False)
        agent_browser = Browser(config=browser_config)
        agent_browser.playwright = playwright
        agent_browser.playwright_browser = playwright_browser
        send_log("Linked Playwright to agent browser.", "🔗", log_type='status')

        # --- Patch BrowserContext._create_context ---
        # Store original only if not already stored (first run)
        if original_create_context is None:
            original_create_context = BrowserContext._create_context
            local_original_create_context = original_create_context # Also store for finally block
        else:
            # Already patched, just ensure we have a reference for finally
            local_original_create_context = original_create_context


        async def patched_create_context(self: BrowserContext, browser_pw: PlaywrightBrowser) -> PlaywrightBrowserContext:
            if original_create_context is None:
                 raise RuntimeError("Original _create_context not stored correctly")

            # print("Patched BrowserContext._create_context called...")
            raw_playwright_context: PlaywrightBrowserContext = await original_create_context(self, browser_pw)
            # print(f"Original _create_context created raw context: {raw_playwright_context}")
            send_log("BrowserContext patched, attaching log handlers...", "🔧", log_type='status') # Type: status

            if raw_playwright_context:
                raw_playwright_context.on("console", handle_console_message) # Handlers now send correct type
                raw_playwright_context.on("request", handle_request)         # Handlers now send correct type
                raw_playwright_context.on("response", handle_response)       # Handlers now send correct type
                # print("Listeners attached to raw Playwright context.")
                send_log("Log listeners attached.", "👂", log_type='status') # Type: status
            else:
                 send_log("Original _create_context did not return a context.", "⚠️", log_type='status') # Type: status

            return raw_playwright_context

        BrowserContext._create_context = patched_create_context
        # print("Patched BrowserContext._create_context.")

        # --- Ensure Tool Call ID ---
        if tool_call_id is None:
            tool_call_id = str(uuid.uuid4())
            send_log(f"Generated tool_call_id: {tool_call_id}", "🆔", log_type='status') # Type: status

        # --- LLM Setup ---
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620",
            base_url="https://operative-backend.onrender.com/v1beta/models/claude-3-5-sonnet-20240620",
            extra_headers={
                "x-operative-api-key": api_key,
                "x-operative-tool-call-id": tool_call_id
            })
        send_log(f"LLM ({llm.model}) configured.", "🤖", log_type='status') # Type: status

        # --- Agent Callback ---
        async def state_callback(browser_state, agent_output, step_number):
            # Send agent output with type 'agent'
            send_log(f"Step {step_number}", "📍", log_type='agent')
            send_log(f"URL: {browser_state.url}", "🔗", log_type='agent')
            # Ensure agent_output is a string before logging
            output_str = str(agent_output)
            send_log(f"Agent Output: {output_str}", "💬", log_type='agent')

        # --- Initialize and Run Agent ---
        agent = Agent(
            task=task,
            llm=llm,
            browser=agent_browser,
            register_new_step_callback=state_callback
        )
        agent_instance = agent

        send_log(f"Agent starting task: {task}", "🏃", log_type='agent') # Type: agent
        agent_result = await agent.run()
        send_log(f"Agent run finished.", "🏁", log_type='agent') # Type: agent

        # --- Prepare Combined Results ---
        # Convert AgentHistoryList to a serializable format (just stringify)
        serialized_result = str(agent_result)

        # Return only the agent result
        return serialized_result

    except Exception as e:
        error_message = f"Error in run_browser_task: {e}\n{traceback.format_exc()}"
        send_log(error_message, "❌", log_type='status') # Type: status
        return error_message
    finally:
        # --- Cleanup ---
        # Ensure patch is restored
        if local_original_create_context:
            BrowserContext._create_context = local_original_create_context
            send_log("Original BrowserContext restored.", "🔧", log_type='status') # Type: status

        # Close the browser created specifically for this task
        if agent_browser:
            await agent_browser.close()
            agent_browser = None
            send_log("Agent browser resources cleaned up.", "🧹", log_type='status') # Type: status
        # Close the playwright instance started for this task
        if playwright:
            await playwright.stop()
            playwright = None
            send_log("Playwright instance for task stopped.", "🧹", log_type='status') # Type: status

        # Clear the global instance if it was set
        agent_instance = None

# Note: Removed cleanup_resources() function as cleanup is now in finally block
# async def cleanup_resources() -> None:
#     ...
