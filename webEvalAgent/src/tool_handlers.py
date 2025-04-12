#!/usr/bin/env python3

import io
import json
import traceback
import uuid
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, List, Any

from mcp.server.fastmcp import Context
from mcp.types import TextContent

# Import the manager directly
from webEvalAgent.src.browser_manager import PlaywrightBrowserManager
# Only import run_browser_task from browser_utils
from webEvalAgent.src.browser_utils import run_browser_task
# Import your prompt function
from webEvalAgent.src.prompts import get_ux_evaluation_prompt

# Function to get the singleton browser manager instance
def get_browser_manager() -> PlaywrightBrowserManager:
    """Get the singleton browser manager instance.
    
    This function provides a centralized way to access the singleton
    PlaywrightBrowserManager instance throughout the application.
    
    Returns:
        PlaywrightBrowserManager: The singleton browser manager instance
    """
    return PlaywrightBrowserManager.get_instance()

async def handle_web_app_ux_evaluation(arguments: Dict[str, Any], ctx: Context, api_key: str, headless: bool = False) -> list[TextContent]:
    """Handle web_app_ux_evaluator tool calls
    
    This function evaluates the user experience of a web application by using
    the browser-use agent to perform specific tasks and analyze the interaction flow.
    
    Args:
        arguments: The tool arguments containing 'url' and 'task'
        ctx: The MCP context for reporting progress
        api_key: The API key for authentication with the LLM service
        headless: Whether to run the browser in headless mode (default: False)
        
    Returns:
        list[TextContent]: The evaluation results, including console logs and network requests
    """
    # Validate required arguments
    if "url" not in arguments or "task" not in arguments:
        return [TextContent(
            type="text",
            text="Error: Both 'url' and 'task' parameters are required. Please provide a URL to evaluate and a specific UX/UI task to test."
        )]
    
    url = arguments["url"]
    task = arguments["task"]
    tool_call_id = arguments.get("tool_call_id", str(uuid.uuid4()))
    
    if not url or not isinstance(url, str):
        return [TextContent(
            type="text",
            text="Error: 'url' must be a non-empty string containing the web application URL to evaluate."
        )]
        
    if not task or not isinstance(task, str):
        return [TextContent(
            type="text",
            text="Error: 'task' must be a non-empty string describing the UX/UI aspect to test."
        )]
    
    # Get the singleton browser manager and initialize it
    browser_manager = get_browser_manager()
    if not browser_manager.is_initialized:
        await browser_manager.initialize()
        
    # Get the evaluation task prompt
    evaluation_task = get_ux_evaluation_prompt(url, task)
    
    # Run the browser task
    log_buffer = io.StringIO()
    with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
        result, console_logs, network_requests = await run_browser_task(
            evaluation_task, 
            "claude-3-7-sonnet-latest", 
            ctx, 
            tool_call_id=tool_call_id,
            api_key=api_key,
            headless=headless
        )
    
    # Get logs for debugging
    logs = log_buffer.getvalue()
    
    # Return the evaluation result
    return [TextContent(
        type="text",
        text=f"Web Application UX Evaluation Results:\n\n{result}\n\nDebug logs:\n{logs}\n\nConsole logs:\n{console_logs}\n\nNetwork requests:\n{network_requests}"
    )]
