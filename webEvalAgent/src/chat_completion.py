#!/usr/bin/env python3

import yaml
import uuid
import traceback
from typing import Dict, List, Any, Tuple, Union
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

def clean_yaml_content(content: str) -> str:
    """Clean YAML content by removing markdown code block syntax.
    
    Args:
        content: Raw content that may contain markdown code blocks
        
    Returns:
        str: Clean YAML content
    """
    # Remove opening code block if present
    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]
    
    # Remove closing code block if present
    if content.rstrip().endswith("```"):
        content = content[:content.rstrip().rfind("```")]
    
    return content.strip()

async def get_chat_completion(context: Dict[str, Any], api_key: str, tool_call_id: str = None) -> Tuple[Union[List[Dict[str, Any]], None], Union[str, None]]:
    """Get chat completion from the LLM API for test generation.
    
    Args:
        context: Dictionary containing mermaid_diagram and existing_tests
        api_key: The API key for authentication
        tool_call_id: Optional tool call ID for tracking
        
    Returns:
        Tuple containing:
        - List[Dict[str, Any]]: List of generated/reconciled test definitions or None on error
        - str: Error message with stack trace if an error occurred, None otherwise
    """
    try:
        # Convert existing tests to YAML for better prompt formatting
        existing_tests_yaml = yaml.safe_dump(context['existing_tests'], default_flow_style=False)
        
        # Construct the prompt
        prompt = f"""Given the following mermaid diagram representing the application structure:

{context['mermaid_diagram']}

And the existing UI tests in YAML format:

{existing_tests_yaml}

Generate a comprehensive set of UI tests that:
1. Cover all user flows shown in the mermaid diagram
2. Preserve existing test coverage where appropriate
3. Add new tests for any uncovered flows
4. Remove redundant tests
5. Ensure each test has:
   - A unique ID
   - Clear description
   - URL (use relative paths starting with /, e.g. "/" for home, "/dashboard" for dashboard)
   - Detailed steps
   - Expected results

IMPORTANT: All URLs in the tests must be relative paths starting with /. Do not use absolute URLs or domain names.

Return ONLY the YAML content for the tests, with no additional explanation or markdown formatting."""

        # Initialize the LLM client with proper parameters
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            base_url="https://operative-backend.onrender.com/v1beta/models/claude-3-5-sonnet-20240620",
            extra_headers={
                "x-operative-api-key": api_key,
                "x-operative-tool-call-id": tool_call_id or str(uuid.uuid4())
            },
            temperature=0,
            max_tokens=1000
        )
        
        # Create messages in the format expected by ChatAnthropic
        messages = [
            ("system", "You are a UI test generator that creates comprehensive test cases based on application structure. Output only valid YAML with relative URLs."),
            ("human", prompt)
        ]
        
        # Use the correct invoke format as per documentation
        response = await llm.ainvoke(messages)
        
        # Get content from the response and clean it
        yaml_content = clean_yaml_content(response.content)
        
        try:
            new_tests = yaml.safe_load(yaml_content)
            if new_tests is None:
                error_msg = "Generated YAML was empty or invalid"
                return context['existing_tests'], error_msg
            if not isinstance(new_tests, list):
                # If not a list, wrap it in a list
                new_tests = [new_tests]
                
            # Validate that all URLs are relative paths
            for test in new_tests:
                url = test.get('url', '')
                if not url.startswith('/'):
                    error_msg = f"Test {test.get('id', 'unknown')} has invalid URL '{url}'. All URLs must be relative paths starting with /"
                    return context['existing_tests'], error_msg
                    
            return new_tests, None
        except yaml.YAMLError as e:
            error_msg = f"Error parsing generated YAML:\n{str(e)}\n\nRaw YAML content:\n{yaml_content}\n\nStack trace:\n{traceback.format_exc()}"
            return context['existing_tests'], error_msg
            
    except Exception as e:
        error_msg = f"Error getting chat completion:\n{str(e)}\n\nStack trace:\n{traceback.format_exc()}"
        return context['existing_tests'], error_msg

def create_default_tests(mermaid_diagram: str) -> List[Dict[str, Any]]:
    """Create default test cases based on the mermaid diagram when API fails.
    
    Args:
        mermaid_diagram: The mermaid diagram string
        
    Returns:
        List[Dict[str, Any]]: List of default test definitions
    """
    # Extract node names from mermaid diagram
    nodes = []
    for line in mermaid_diagram.split('\n'):
        if '-->' in line:
            parts = line.split('-->')
            for part in parts:
                node = part.strip()
                if '[' in node and ']' in node:
                    node_name = node[node.find('[')+1:node.find(']')]
                    if node_name not in nodes:
                        nodes.append(node_name)
    
    # Create basic test for each major flow
    tests = []
    
    # Home page test
    tests.append({
        'id': 'home-page-test',
        'description': 'Verify home page loads and navigation works',
        'url': 'http://localhost:5173/',
        'steps': [
            'Navigate to the home page',
            'Verify the page title is correct',
            'Check if navigation menu is present'
        ]
    })
    
    # Navigation test if applicable
    if 'Navigation' in ' '.join(nodes):
        tests.append({
            'id': 'navigation-test',
            'description': 'Test navigation menu functionality',
            'url': 'http://localhost:5173/',
            'steps': [
                'Navigate to the home page',
                'Click on each navigation link',
                'Verify correct page loads for each link'
            ]
        })
    
    # Add more tests based on common flows in web apps
    tests.append({
        'id': 'responsive-layout-test',
        'description': 'Test responsive layout on different screen sizes',
        'url': 'http://localhost:5173/',
        'steps': [
            'Navigate to the home page',
            'Resize browser to mobile width',
            'Verify layout adjusts correctly',
            'Check if mobile menu works properly'
        ]
    })
    
    return tests 