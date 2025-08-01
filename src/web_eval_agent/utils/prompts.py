#!/usr/bin/env python3

def get_web_evaluation_prompt(url: str, task: str) -> str:
    """
    Generate a prompt for web application evaluation.
    
    Args:
        url: The URL of the web application to evaluate
        task: The specific aspect to test
        
    Returns:
        str: The formatted evaluation prompt
    """
    return f"""VISIT: {url}
GOAL: {task}

Evaluate the UI/UX of the site. If you hit any critical errors (e.g., page fails to load, JS errors), stop and report the exact issue.

If a login page appears, first try clicking "Login" — saved credentials may work.
If login fields appear and no credentials are provided, do not guess. Stop and report that login is required. Suggest the user run setup_browser_state to log in and retry.

If no errors block progress, proceed and attempt the task. Try a couple times if needed before giving up — unless blocked by missing login access.
Make sure to click through the application from the base url, don't jump to other pages without naturally arriving there.

Report any UX issues (e.g., incorrect content, broken flows), or confirm everything worked smoothly.
Take note of any opportunities for improvement in the UI/UX, test and think about the application like a real user would.
"""
