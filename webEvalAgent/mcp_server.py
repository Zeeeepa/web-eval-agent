#!/usr/bin/env python3

import asyncio
import os
import argparse
import traceback
import uuid
from enum import Enum

# Set the API key to a fake key to avoid error in backend
os.environ["ANTHROPIC_API_KEY"] = 'not_a_real_key'
os.environ["ANONYMIZED_TELEMETRY"] = 'false'

# MCP imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

# Import our modules
from webEvalAgent.src.browser_manager import PlaywrightBrowserManager
# from webEvalAgent.src.browser_utils import cleanup_resources # Removed import
from webEvalAgent.src.api_utils import validate_api_key
from webEvalAgent.src.tool_handlers import handle_web_app_ux_evaluation
from webEvalAgent.src.auth_utils import open_login_browser

# Create the MCP server
mcp = FastMCP("Operative")

# Define the browser tools
class BrowserTools(str, Enum):
    WEB_APP_UX_EVALUATOR = "web_app_ux_evaluator"
    OPEN_LOGIN_BROWSER = "open_login_browser"

# Parse command line arguments (keeping the parser for potential future arguments)
parser = argparse.ArgumentParser(description='Run the MCP server with browser debugging capabilities')
args = parser.parse_args()

# Get API key from environment variable
api_key = os.environ.get('OPERATIVE_API_KEY')

# Validate the API key
if api_key:
    is_valid = asyncio.run(validate_api_key(api_key))
    if not is_valid:
        print("Error: Invalid API key. Please provide a valid OperativeAI API key in the OPERATIVE_API_KEY environment variable.")
else:
    print("Error: No API key provided. Please set the OPERATIVE_API_KEY environment variable.")

@mcp.tool(name=BrowserTools.WEB_APP_UX_EVALUATOR)
async def web_app_ux_evaluator(url: str, task: str, working_directory: str, ctx: Context) -> list[TextContent]:
    """Evaluate the user experience / interface of a web application.

    This tool allows the AI to assess the quality of user experience and interface design
    of a web application by performing specific tasks and analyzing the interaction flow.

    Before this tool is used, the web application should already be running locally in a separate terminal.

    Args:
        url: Required. The localhost URL of the web application to evaluate, including the port number. 
        task: Required. The specific UX/UI aspect to test (e.g., "test the checkout flow",
             "evaluate the navigation menu usability", "check form validation feedback")
             If no task is provided, the tool will high level evaluate the web application
        working_directory: Required. The root directory of the project

    Returns:
        list[TextContent]: A detailed evaluation of the web application's UX/UI, including
                         observations, issues found, and recommendations for improvement
                         Do not save this information to any file, but only return it to the agent
    """
    try:
        # Generate a new tool_call_id for this specific tool call
        tool_call_id = str(uuid.uuid4())
        print(f"Generated new tool_call_id for web_app_ux_evaluator: {tool_call_id}")
        return await handle_web_app_ux_evaluation(
            {"url": url, "task": task, "tool_call_id": tool_call_id},
            ctx,
            api_key
        )
    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error executing web_app_ux_evaluator: {str(e)}\n\nTraceback:\n{tb}"
        )]

@mcp.tool(name=BrowserTools.OPEN_LOGIN_BROWSER)
async def open_login_browser_tool(url: str, ctx: Context) -> list[TextContent]:
    """Open a browser window to allow the user to manually log in to a website.
    
    This tool opens a browser window with a persistent profile, allowing users to manually log in
    to websites like Google. The authentication state will be saved and reused in subsequent
    web app UX evaluation browser sessions.
    
    Args:
        url: Required. The URL of the login page to open (e.g., 'https://accounts.google.com')
        
    Returns:
        list[TextContent]: A message indicating the outcome of the login browser session
    """
    try:
        ctx.report_progress("Opening login browser...")
        success = await open_login_browser(url, timeout=60)
        
        if success:
            return [TextContent(
                type="text",
                text="Login browser session completed. Authentication state has been saved and will be used in subsequent browser sessions."
            )]
        else:
            return [TextContent(
                type="text",
                text="Failed to open login browser. Please check logs for details."
            )]
    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error executing open_login_browser: {str(e)}\n\nTraceback:\n{tb}"
        )]

if __name__ == "__main__":
    try:
        # Run the FastMCP server
        mcp.run(transport='stdio')
    finally:
        # Ensure resources are cleaned up
        # asyncio.run(cleanup_resources()) # Cleanup now handled in browser_utils
        pass # Keep finally block structure if needed later

def main():
     try:
         # Run the FastMCP server
         mcp.run(transport='stdio')
     finally:
         # Ensure resources are cleaned up
         # asyncio.run(cleanup_resources()) # Cleanup now handled in browser_utils
         pass # Keep finally block structure if needed later