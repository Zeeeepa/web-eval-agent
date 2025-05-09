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
    return f"""VISIT: {url} AND YOUR MAIN GOAL IS: {task}

Evaluate the UI / UX of the website. If you encounter any errors during your evaluation
(e.g., connection issues, page not loading, JavaScript errors), immediately stop the evaluation
and report back the specific error encountered.

If you encounter a login page and no login credentials are available, DO NOT attempt to login.
Instead, stop the evaluation and report that authentication is required. Suggest that the user
run the setup_browser_state tool again to properly authenticate and save the login state.

If there are no errors and you can proceed with the evaluation, check for any problems with the UX
including not showing the correct content, or not being able to complete the task.
Please list the problems if found, otherwise state your findings and evaluation of the UX/UI.
"""
