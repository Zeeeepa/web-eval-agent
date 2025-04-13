#!/usr/bin/env python3

import asyncio
import os
import argparse
import traceback
import uuid
import json
import subprocess
import threading
import sys
from enum import Enum
from pathlib import Path

# Set the API key to a fake key to avoid error in backend
os.environ["ANTHROPIC_API_KEY"] = 'not_a_real_key'
os.environ["ANONYMIZED_TELEMETRY"] = 'false'

# MCP imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

# Import our modules
from webEvalAgent.src.browser_manager import PlaywrightBrowserManager
from webEvalAgent.src.browser_utils import cleanup_resources
from webEvalAgent.src.api_utils import validate_api_key
from webEvalAgent.src.tool_handlers import handle_web_app_ux_evaluation
from webEvalAgent.src.cursorrules_utils import create_or_update_cursorrules
from webEvalAgent.src.yaml_utils import load_yaml_or_default, save_yaml
from webEvalAgent.src.chat_completion import get_chat_completion

# Create the MCP server
mcp = FastMCP("Operative")

# Define the browser tools
class BrowserTools(str, Enum):
    WEB_APP_UX_EVALUATOR = "web_app_ux_evaluator"
    WEB_UX_RUN_TESTS_PARALLEL = "web_ux_run_tests_parallel"
    GENERATE_UI_TESTS = "generate_ui_tests"

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

@mcp.tool(name=BrowserTools.GENERATE_UI_TESTS)
async def generate_ui_tests(mermaid_diagram: str, working_directory: str, ctx: Context) -> list[TextContent]:
    """Generate UI tests based on a mermaid diagram and reconcile with existing tests.

    Args:
        mermaid_diagram: The mermaid diagram representing the application structure
        working_directory: The root directory of the project containing uitests.yaml

    Returns:
        list[TextContent]: A summary of the generated/updated tests
    """
    try:
        # Load existing tests or get default template
        tests_file = os.path.join(working_directory, "uitests.yaml")
        existing_tests = load_yaml_or_default(tests_file)

        # Get new/reconciled tests from LLM
        new_tests = await get_chat_completion(
            context={
                "mermaid_diagram": mermaid_diagram,
                "existing_tests": existing_tests
            },
            api_key=api_key
        )

        # Save the updated tests
        save_yaml(tests_file, new_tests)

        # Generate summary of changes
        added = len(new_tests) - len(existing_tests)
        summary = f"""UI Test Generation Summary:
- Previous test count: {len(existing_tests)}
- New test count: {len(new_tests)}
- Tests {'added' if added >= 0 else 'removed'}: {abs(added)}

Updated tests have been saved to {tests_file}"""

        return [TextContent(
            type="text",
            text=summary
        )]

    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error generating UI tests: {str(e)}\n\nTraceback:\n{tb}"
        )]

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
        working_directory: Required. The root directory of the project to create/update the .cursorrules file

    Returns:
        list[TextContent]: A detailed evaluation of the web application's UX/UI, including
                         observations, issues found, and recommendations for improvement
    """
    try:
        # Create or update the .cursorrules file
        create_or_update_cursorrules(working_directory)
        
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

@mcp.tool(name=BrowserTools.WEB_UX_RUN_TESTS_PARALLEL)
async def web_ux_run_tests_parallel(ctx: Context) -> list[TextContent]:
    """Run all UX tests from uitests.yaml in parallel.

    This tool automatically runs multiple UX evaluation tests in parallel, reading test definitions 
    from uitests.yaml. Each test is executed as a separate browser task, and the results 
    are aggregated into a single report.

    Returns:
        list[TextContent]: A detailed evaluation report containing results for all tests.
    """
    browser_stream_process = None
    monitor_browser = None
    
    try:
        # Start the browser stream server
        print("Starting browser stream server...")
        browser_stream_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          "src", "browser_stream.py")
        
        # Start the server as a subprocess using uv
        browser_stream_process = subprocess.Popen(
            ["uv", "run", browser_stream_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server time to start
        await asyncio.sleep(2)
        print("Browser stream server started on http://localhost:8080")
        
        # Start Playwright and open a browser to view the stream
        print("Opening browser to monitor test progress...")
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        monitor_browser = await playwright.chromium.launch(headless=False)
        monitor_page = await monitor_browser.new_page()
        
        # Try to connect to the browser stream server
        try:
            await monitor_page.goto("http://localhost:8080", timeout=5000)
            print("Successfully connected to browser stream")
        except Exception as e:
            print(f"Warning: Could not connect to browser stream: {e}")
        
        # Load tests from the YAML file
        working_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tests_file = os.path.join(working_directory, "uitests.yaml")
        tests = load_yaml_or_default(tests_file)
            
        # Function to run a single test
        async def run_test(test):
            test_id = test.get('id')
            test_desc = test.get('description')
            test_url = test.get('url')
            
            # Create a task description
            task_description = f"[Test: {test_id}] url:{test_url} - {test_desc}\n\nSteps:\n" + "\n".join(
                f"- {step}" for step in test.get('steps', [])
            )
            task_description = task_description + "\n\n" + "\n\n DO NOT LEAVE THE SPECIFIED DOMAIN"
            
            # Generate unique tool call ID
            tool_call_id = str(uuid.uuid4())
            
            try:
                # Create a context for this test
                test_ctx = Context()
                
                # Run the test with visible browser
                result = await handle_web_app_ux_evaluation(
                    {"url": test_url, "task": task_description, "tool_call_id": tool_call_id},
                    test_ctx,
                    api_key,
                    headless=True  # Run with visible browser
                )
                
                return {
                    "test_id": test_id,
                    "description": test_desc,
                    "url": test_url,
                    "status": "success",
                    "result": result
                }
            except Exception as e:
                return {
                    "test_id": test_id,
                    "description": test_desc,
                    "url": test_url,
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
        
        # Print progress information
        print(f"Running {len(tests)} UX tests in parallel...")
        
        # Create tasks for all tests
        tasks = [run_test(test) for test in tests]
        
        # Run the tests concurrently
        results = await asyncio.gather(*tasks)
        
        # Process results
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]
        
        # Build summary report
        summary = f"""UX Test Results Summary:
- Total Tests: {len(tests)}
- Successful: {len(successful)}
- Failed: {len(failed)}

Browser Stream View: http://localhost:8080
"""
        
        # Add details for each test
        details = "\n\n## Test Details:\n\n"
        for result in results:
            if result["status"] == "success":
                # Extract the text content from the result
                result_text = "\n".join([content.text for content in result["result"] if hasattr(content, 'text')])
                details += f"### ✅ {result['test_id']}: {result['description']}\n"
                details += f"URL: {result['url']}\n\n"
                details += f"{result_text}\n\n"
            else:
                details += f"### ❌ {result['test_id']}: {result['description']}\n"
                details += f"URL: {result['url']}\n"
                details += f"Error: {result['error']}\n\n"
        
        # Combine summary and details
        report = summary + details
        
        return [TextContent(
            type="text",
            text=report
        )]
    
    except Exception as e:
        tb = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"Error executing web_ux_run_tests_parallel: {str(e)}\n\nTraceback:\n{tb}"
        )]
    finally:
        # Clean up resources
        if monitor_browser:
            try:
                await monitor_browser.close()
            except Exception as e:
                print(f"Error closing Playwright browser: {e}")
        
        if browser_stream_process:
            try:
                browser_stream_process.terminate()
                print("Browser stream server terminated")
            except Exception as e:
                print(f"Error terminating browser stream process: {e}")

if __name__ == "__main__":
    try:
        # Run the FastMCP server
        mcp.run(transport='stdio')
    finally:
        # Ensure resources are cleaned up
        asyncio.run(cleanup_resources())

def main():
     try:
         # Run the FastMCP server
         mcp.run(transport='stdio')
     finally:
         # Ensure resources are cleaned up
         asyncio.run(cleanup_resources())