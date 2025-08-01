#!/usr/bin/env python3

import asyncio
import os
import argparse
import traceback
import uuid
from enum import Enum
from webEvalAgent.src.utils import stop_log_server
from webEvalAgent.src.log_server import send_log

# Set the Google API key for Gemini
if 'GEMINI_API_KEY' in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ['GEMINI_API_KEY']
os.environ["ANONYMIZED_TELEMETRY"] = 'false'

# MCP imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

# Import our enhanced modules
from webEvalAgent.src.api_utils import validate_api_key
from webEvalAgent.src.tool_handlers import handle_web_evaluation, handle_setup_browser_state
from webEvalAgent.src.logging_config import get_logger, create_session_context
from webEvalAgent.src.session_manager import get_session_manager, SessionConfig
from webEvalAgent.src.github_integration import GitHubIntegration, test_github_pr, test_github_branch

# Initialize structured logging
logger = get_logger("mcp-server")

# Stop any existing log server to avoid conflicts
stop_log_server()

# Create the MCP server
mcp = FastMCP("Operative")

# Define the browser tools
class BrowserTools(str, Enum):
    WEB_EVAL_AGENT = "web_eval_agent"
    SETUP_BROWSER_STATE = "setup_browser_state"
    TEST_GITHUB_PR = "test_github_pr"  # New tool for testing GitHub PRs
    TEST_GITHUB_BRANCH = "test_github_branch"  # New tool for testing GitHub branches

# Parse command line arguments (keeping the parser for potential future arguments)
parser = argparse.ArgumentParser(description='Run the MCP server with browser debugging capabilities')
args = parser.parse_args()

# Get API key from environment variable
api_key = os.environ.get('GEMINI_API_KEY')

# Validate the API key
if api_key:
    is_valid = asyncio.run(validate_api_key(api_key))
    if not is_valid:
        print("Error: Invalid API key. Please provide a valid Google Gemini API key in the GEMINI_API_KEY environment variable.")
else:
    print("Error: No API key provided. Please set the GEMINI_API_KEY environment variable.")

@mcp.tool(name=BrowserTools.WEB_EVAL_AGENT)
async def web_eval_agent(url: str, task: str, ctx: Context, headless_browser: bool = False) -> list[TextContent]:
    """Evaluate the user experience / interface of a web application.

    This tool allows the AI to assess the quality of user experience and interface design
    of a web application by performing specific tasks and analyzing the interaction flow.

    Before this tool is used, the web application should already be running locally on a port.

    Args:
        url: Required. The localhost URL of the web application to evaluate, including the port number.
            Example: http://localhost:3000, http://localhost:8080, http://localhost:4200, http://localhost:5173, etc.
            Try to avoid using the path segments of the URL, and instead use the root URL.
        task: Required. The specific UX/UI aspect to test (e.g., "test the checkout flow",
             "evaluate the navigation menu usability", "check form validation feedback")
             Be as detailed as possible in your task description. It could be anywhere from 2 sentences to 2 paragraphs.
        headless_browser: Optional. Whether to hide the browser window popup during evaluation.
        If headless_browser is True, only the operative control center browser will show, and no popup browser will be shown.

    Returns:
        list[list[TextContent, ImageContent]]: A detailed evaluation of the web application's UX/UI, including
                         observations, issues found, and recommendations for improvement
                         and screenshots of the web application during the evaluation
    """
    headless = headless_browser
    is_valid = await validate_api_key(api_key)

    if not is_valid:
        error_message_str = "❌ Error: API Key validation failed when running the tool.\n"
        error_message_str += "   Reason: Invalid or expired Gemini API key.\n"
        error_message_str += "   👉 Please check your GEMINI_API_KEY at https://aistudio.google.com/app/apikey"
        return [TextContent(type="text", text=error_message_str)]
    try:
        # Generate a new tool_call_id for this specific tool call
        tool_call_id = str(uuid.uuid4())
        return await handle_web_evaluation(
            {"url": url, "task": task, "headless": headless, "tool_call_id": tool_call_id},
            ctx,
            api_key
        )
    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error executing web_eval_agent: {str(e)}\n\nTraceback:\n{tb}"
        )]

@mcp.tool(name=BrowserTools.SETUP_BROWSER_STATE)
async def setup_browser_state(url: str = None, ctx: Context = None) -> list[TextContent]:
    """Sets up and saves browser state for future use.

    This tool should only be called in one scenario:
    1. The user explicitly requests to set up browser state/authentication

    Launches a non-headless browser for user interaction, allows login/authentication,
    and saves the browser state (cookies, local storage, etc.) to a local file.

    Args:
        url: Optional URL to navigate to upon opening the browser.
        ctx: The MCP context (used for progress reporting, not directly here).

    Returns:
        list[TextContent]: Confirmation of state saving or error messages.
    """
    is_valid = await validate_api_key(api_key)

    if not is_valid:
        error_message_str = "❌ Error: API Key validation failed when running the tool.\n"
        error_message_str += "   Reason: Invalid or expired Gemini API key.\n"
        error_message_str += "   👉 Please check your GEMINI_API_KEY at https://aistudio.google.com/app/apikey"
        return [TextContent(type="text", text=error_message_str)]
    try:
        # Generate a new tool_call_id for this specific tool call
        tool_call_id = str(uuid.uuid4())
        send_log(f"Generated new tool_call_id for setup_browser_state: {tool_call_id}")
        return await handle_setup_browser_state(
            {"url": url, "tool_call_id": tool_call_id},
            ctx,
            api_key
        )
    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error executing setup_browser_state: {str(e)}\n\nTraceback:\n{tb}"
        )]

@mcp.tool(name=BrowserTools.TEST_GITHUB_PR)
async def test_github_pr(
    git_repo: str,
    pull_request: int,
    task: str,
    headless_browser: bool = True,
    ctx: Context = None
) -> list[TextContent]:
    """Test UI from a GitHub Pull Request.
    
    This tool automatically detects the deployment URL for a GitHub PR and runs
    comprehensive UI testing with the web evaluation agent.
    
    Args:
        git_repo: GitHub repository in format "owner/repo" (e.g., "Zeeeepa/codegenApp")
        pull_request: PR number to test (e.g., 96)
        task: Natural language description of what to test
        headless_browser: Whether to run browser in headless mode (default: True)
        ctx: The MCP context
    
    Returns:
        list[TextContent]: Detailed evaluation results including:
                         - PR context and metadata
                         - UI testing results and observations
                         - Performance metrics and screenshots
                         - Issues found and recommendations
    """
    is_valid = await validate_api_key(api_key)
    
    if not is_valid:
        error_message_str = "❌ Error: API Key validation failed when running the tool.\n"
        error_message_str += "   Reason: Invalid or expired Gemini API key.\n"
        error_message_str += "   👉 Please check your GEMINI_API_KEY at https://aistudio.google.com/app/apikey"
        return [TextContent(type="text", text=error_message_str)]
    
    try:
        # Create session context for GitHub PR testing
        session_context = create_session_context(
            github_repo=git_repo,
            github_pr=pull_request,
            task=task
        )
        
        logger.info(f"Starting GitHub PR test for {git_repo}#{pull_request}")
        logger.log_github_pr_context(git_repo, pull_request, "unknown")
        
        # Use GitHub integration to test the PR
        github_token = os.getenv('GITHUB_TOKEN')
        result = await test_github_pr(
            repo=git_repo,
            pr_number=pull_request,
            task=task,
            github_token=github_token,
            headless=headless_browser,
            api_key=api_key
        )
        
        # Format result for MCP response
        if isinstance(result, list) and result:
            return result
        else:
            return [TextContent(
                type="text",
                text=f"✅ GitHub PR #{pull_request} testing completed successfully!\n\n{str(result)}"
            )]
            
    except Exception as e:
        logger.error(f"Error testing GitHub PR {git_repo}#{pull_request}", error=e)
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"❌ Error testing GitHub PR {git_repo}#{pull_request}: {str(e)}\n\nTraceback:\n{tb}"
        )]

@mcp.tool(name=BrowserTools.TEST_GITHUB_BRANCH)
async def test_github_branch(
    git_repo: str,
    branch: str,
    task: str,
    headless_browser: bool = True,
    ctx: Context = None
) -> list[TextContent]:
    """Test UI from a GitHub branch.
    
    This tool automatically detects the deployment URL for a GitHub branch and runs
    comprehensive UI testing with the web evaluation agent.
    
    Args:
        git_repo: GitHub repository in format "owner/repo" (e.g., "Zeeeepa/codegenApp")
        branch: Branch name to test (e.g., "main", "feature/new-ui")
        task: Natural language description of what to test
        headless_browser: Whether to run browser in headless mode (default: True)
        ctx: The MCP context
    
    Returns:
        list[TextContent]: Detailed evaluation results including:
                         - Branch context and metadata
                         - UI testing results and observations
                         - Performance metrics and screenshots
                         - Issues found and recommendations
    """
    is_valid = await validate_api_key(api_key)
    
    if not is_valid:
        error_message_str = "❌ Error: API Key validation failed when running the tool.\n"
        error_message_str += "   Reason: Invalid or expired Gemini API key.\n"
        error_message_str += "   👉 Please check your GEMINI_API_KEY at https://aistudio.google.com/app/apikey"
        return [TextContent(type="text", text=error_message_str)]
    
    try:
        # Create session context for GitHub branch testing
        session_context = create_session_context(
            github_repo=git_repo,
            github_branch=branch,
            task=task
        )
        
        logger.info(f"Starting GitHub branch test for {git_repo}@{branch}")
        logger.log_github_pr_context(git_repo, None, branch)
        
        # Use GitHub integration to test the branch
        github_token = os.getenv('GITHUB_TOKEN')
        result = await test_github_branch(
            repo=git_repo,
            branch=branch,
            task=task,
            github_token=github_token,
            headless=headless_browser,
            api_key=api_key
        )
        
        # Format result for MCP response
        if isinstance(result, list) and result:
            return result
        else:
            return [TextContent(
                type="text",
                text=f"✅ GitHub branch '{branch}' testing completed successfully!\n\n{str(result)}"
            )]
            
    except Exception as e:
        logger.error(f"Error testing GitHub branch {git_repo}@{branch}", error=e)
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"❌ Error testing GitHub branch {git_repo}@{branch}: {str(e)}\n\nTraceback:\n{tb}"
        )]

def main():
     try:
         # Run the FastMCP server
         mcp.run(transport='stdio')
     finally:
         # Ensure resources are cleaned up when server terminates
         pass

# This entry point is used when running directly
if __name__ == "__main__":
    main()
