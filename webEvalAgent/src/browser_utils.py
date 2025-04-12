#!/usr/bin/env python3

import asyncio
import io
import json
import logging
import uuid
import warnings
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Tuple, List, Optional
from collections import deque

# Import Playwright types
from playwright.async_api import async_playwright, Error as PlaywrightError, Browser as PlaywrightBrowser, BrowserContext as PlaywrightBrowserContext

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

# Global variable to store agent instance - might be less necessary if Agent is created per task run
agent_instance = None
# Global variable to store the original patched method if patching class-level
original_create_context: Optional[callable] = None

# Define the maximum number of logs/requests to keep
MAX_LOG_ENTRIES = 10

# --- Log Storage (Global within this module using deque) ---
console_log_storage: deque = deque(maxlen=MAX_LOG_ENTRIES)
network_request_storage: deque = deque(maxlen=MAX_LOG_ENTRIES)

# --- Log Handlers (Use deque's append) ---
async def handle_console_message(message):
    try:
        text = message.text
        log_entry = { "type": message.type, "text": text, "location": message.location, "timestamp": asyncio.get_event_loop().time() }
        # Appending to deque automatically handles maxlen
        console_log_storage.append(log_entry)
        # print(f"-> CONSOLE LOG ({len(console_log_storage)}/{MAX_LOG_ENTRIES}): {log_entry['type']} - {log_entry['text'][:150]}") # Updated debug print
    except Exception as e:
        print(f"Error handling console message: {e} - Args: {message.args}")

async def handle_request(request):
    try:
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
        # Appending to deque automatically handles maxlen
        network_request_storage.append(request_entry)
        # print(f"-> NETWORK REQ ({len(network_request_storage)}/{MAX_LOG_ENTRIES}): {request_entry['method']} {request_entry['url']}") # Updated debug print
    except Exception as e:
        print(f"Error handling request event for {request.url if request else 'Unknown URL'}: {e}")

async def handle_response(response):
    req_id = id(response.request)
    url = response.url
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

        # Iterate through the deque (which contains dicts)
        # Note: Modifying items in a deque while iterating isn't ideal,
        # but finding the specific request dict should be okay here.
        # For very high traffic, a dict lookup might be better.
        for req in network_request_storage:
            if req.get("id") == req_id and "response_status" not in req:
                req["response_status"] = status
                req["response_headers"] = headers
                req["response_body_size"] = body_size
                req["response_timestamp"] = asyncio.get_event_loop().time()
                # print(f"-> NETWORK RESP ({len(network_request_storage)}/{MAX_LOG_ENTRIES}): {status} for {url}") # Updated debug print
                break
    except Exception as e:
        print(f"Error handling response event for {url}: {e}")


async def run_browser_task(task: str, model: str = "gemini-2.0-flash-001", ctx: Context = None, tool_call_id: str = None, api_key: str = None, headless: bool = False, step_callback = None) -> Tuple[str, str, str]:
    """
    Run a task using browser-use agent, capturing console and network logs.

    Args:
        task: The task to run.
        model: The model identifier (not directly used for LLM here, taken from ChatAnthropic).
        ctx: The MCP context for progress reporting.
        tool_call_id: The tool call ID for API headers.
        api_key: The API key for authentication.
        headless: Whether to run the browser in headless mode.
        step_callback: Optional callback function to be called after each step with (browser_state, agent_output, step_number).

    Returns:
        Tuple[str, str, str]: A tuple containing:
            - Agent's final result (stringified).
            - Console logs as a JSON string.
            - Network requests as a JSON string.
    """
    global agent_instance, console_log_storage, network_request_storage, original_create_context

    # --- Clear Logs for this Run ---
    # Deques are cleared like lists
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
        # --- Initialize Playwright Directly ---
        playwright = await async_playwright().start()
        playwright_browser = await playwright.chromium.launch(headless=headless)
        print("Playwright initialized directly.")

        # --- Create browser-use Browser ---
        browser_config = BrowserConfig(disable_security=True, headless=headless)
        agent_browser = Browser(config=browser_config)
        agent_browser.playwright = playwright
        agent_browser.playwright_browser = playwright_browser
        print("Assigned direct Playwright objects to agent_browser.")

        # --- Patch BrowserContext._create_context ---
        # Store original only if not already stored (first run)
        if original_create_context is None:
            original_create_context = BrowserContext._create_context
            local_original_create_context = original_create_context # Also store for finally block
        else:
            # Already patched, just ensure we have a reference for finally
            local_original_create_context = original_create_context


        async def patched_create_context(self: BrowserContext, browser_pw: PlaywrightBrowser) -> PlaywrightBrowserContext:
            # Use the globally stored original method
            if original_create_context is None:
                 raise RuntimeError("Original _create_context not stored correctly") # Should not happen

            # print("Patched BrowserContext._create_context called...") # Reduce noise
            raw_playwright_context: PlaywrightBrowserContext = await original_create_context(self, browser_pw)
            # print(f"Original _create_context created raw context: {raw_playwright_context}") # Reduce noise

            if raw_playwright_context:
                raw_playwright_context.on("console", handle_console_message)
                raw_playwright_context.on("request", handle_request)
                raw_playwright_context.on("response", handle_response)
                # print("Listeners attached to raw Playwright context.") # Reduce noise
            else:
                 print("!!! Warning: Original _create_context did not return a context.")

            return raw_playwright_context

        # Apply the patch (idempotent if already patched)
        BrowserContext._create_context = patched_create_context
        # print("Patched BrowserContext._create_context.") # Reduce noise

        # --- Check for browser stream server ---
        screenshot_client = None
        try:
            # Check if browser stream server is running at localhost:8080
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080", timeout=1.0)
                if response.status_code == 200:
                    screenshot_client = httpx.AsyncClient()
                    print("Browser stream server detected - will upload screenshots")
        except Exception:
            print("No browser stream server detected")

        # --- Ensure Tool Call ID ---
        if tool_call_id is None:
            tool_call_id = str(uuid.uuid4())
            print(f"Generated new tool_call_id in run_browser_task: {tool_call_id}")
            
        # Create a shorter ID for display
        agent_id = tool_call_id[:8] if tool_call_id else "unknown"

        # --- LLM Setup ---
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620",
            base_url="https://operative-backend.onrender.com/v1beta/models/claude-3-5-sonnet-20240620",
            extra_headers={
                "x-operative-api-key": api_key,
                "x-operative-tool-call-id": tool_call_id
            })

        # --- Agent Callback ---
        step_history = []
        
        # Create a combined callback that handles both step history and screenshots
        async def combined_callback(browser_state, agent_output, step_number):
            # Store step history
            step_history.append({
                "step": step_number,
                "url": browser_state.url,
                "output": agent_output
            })
            
            # Handle screenshots if server is available
            if screenshot_client and hasattr(browser_state, 'screenshot') and browser_state.screenshot:
                try:
                    # Send screenshot to browser stream server
                    await screenshot_client.post(
                        "http://localhost:8080/update_screenshot",
                        json={"agent_id": agent_id, "screenshot": browser_state.screenshot}
                    )
                    print(f"Sent screenshot for step {step_number}")
                except Exception as e:
                    print(f"Error sending screenshot: {e}")
            
            # Call the original step_callback if provided
            if step_callback:
                await step_callback(browser_state, agent_output, step_number)

        # --- Initialize and Run Agent ---
        agent = Agent(
            task=task,
            llm=llm,
            browser=agent_browser,
            register_new_step_callback=combined_callback
        )
        agent_instance = agent # Store globally if needed elsewhere

        if ctx:
            ctx.report_progress("Running browser task...")
            
        print(f"Agent starting task: {task}")
        agent_result = await agent.run(max_steps=30) # Agent returns AgentHistoryList
        
        if ctx:
            ctx.report_progress("Browser task completed")

        print("\n--- Agent Run Finished ---")
        for r in step_history:
            print(f"Step {r['step']}: {r['url']} - {r['output']}")

        # --- Final Log Summary ---
        print("\n--- Final Log Summary ---")
        # Convert deque to list before JSON serialization
        final_console_logs = list(console_log_storage)
        final_network_requests = list(network_request_storage)
        print(f"Total Console Logs Captured (max {MAX_LOG_ENTRIES}): {len(final_console_logs)}")
        print(f"Total Network Requests Captured (max {MAX_LOG_ENTRIES}): {len(final_network_requests)}")
        # Print samples from the lists
        if final_console_logs: print("\nSample Console Logs (Last 5):\n" + "\n".join([f"- {l.get('type','?').ljust(8)}: {l.get('text','?')[:150]}" for l in final_console_logs[-5:]]))
        if final_network_requests: print("\nSample Network Requests (Last 5):\n" + "\n".join([f"- {r.get('method','?').ljust(4)} {r.get('response_status','???')} {r.get('url','?')}" for r in final_network_requests[-5:]]))

        # --- Send final screenshot ---
        if screenshot_client:
            last_screenshot = None
            if agent_result and hasattr(agent_result, 'history') and agent_result.history:
                for item in reversed(agent_result.history.history):
                    if hasattr(item, 'state') and item.state and hasattr(item.state, 'screenshot'):
                        last_screenshot = item.state.screenshot
                        break
                        
            if last_screenshot:
                try:
                    await screenshot_client.post(
                        "http://localhost:8080/update_screenshot",
                        json={"agent_id": agent_id, "screenshot": last_screenshot}
                    )
                    print("Sent final screenshot")
                except Exception as e:
                    print(f"Error sending final screenshot: {e}")

        # --- Prepare Combined Results ---
        # Convert AgentHistoryList to a serializable format
        serialized_result = str(agent_result)
            
        # Ensure all objects in step_history are serializable
        serialized_step_history = []
        for step in step_history:
            serialized_step = {
                "step": step["step"],
                "url": step["url"],
                "output": str(step["output"]) if not isinstance(step["output"], (str, int, float, bool, type(None))) else step["output"]
            }
            serialized_step_history.append(serialized_step)
            
        combined_result = {
            "final_result": serialized_result,
            "step_history": serialized_step_history,
            "console_logs": final_console_logs,
            "network_requests": final_network_requests
        }

        # --- Return Results ---
        # Return both the final result and the step history along with logs
        return combined_result, json.dumps(combined_result, indent=2), json.dumps(final_network_requests, indent=2)

    except Exception as e:
        print(f"\n--- Error During Browser Task Execution ---")
        logging.error(f"Task '{task}' failed", exc_info=True)
        # Return error and any logs captured so far
        error_message = f"Error during task execution: {e}"
        # Convert deque objects to lists before JSON serialization
        return error_message, json.dumps(list(console_log_storage), indent=2), json.dumps(list(network_request_storage), indent=2)

    finally:
        # --- Cleanup ---
        print("\nCleaning up browser task resources...")
        # Restore original method only if we stored it in this run's scope
        # This avoids issues if multiple tasks run concurrently (though not recommended with this patching)
        if local_original_create_context:
             BrowserContext._create_context = local_original_create_context
             print("Restored original BrowserContext._create_context.")
             # Reset global only if we're sure no other task is running
             # For safety, might be better to always keep original_create_context stored globally once set.

        # Close browser-use Browser instance (might close underlying Playwright too)
        if agent_browser:
            try: await agent_browser.close()
            except Exception as e: print(f"Ignoring error during agent_browser.close(): {e}")

        # Ensure underlying Playwright resources are closed if agent_browser didn't
        if playwright_browser and playwright_browser.is_connected():
             await playwright_browser.close()
             print("Closed direct Playwright browser.")
        if playwright:
             await playwright.stop()
             print("Stopped Playwright.")
        print("Browser task cleanup complete.")


async def cleanup_resources() -> None:
    """
    Global cleanup function if needed, but run_browser_task should handle its own.
    If using a singleton manager elsewhere, this could call its close method.
    """
    print("Running global cleanup (if any specific actions needed)...")
    # Example if using singleton manager:
    # browser_manager = PlaywrightBrowserManager.get_instance()
    # if browser_manager.is_initialized:
    #     await browser_manager.close()
    #     print("Closed singleton browser manager.")
    pass
