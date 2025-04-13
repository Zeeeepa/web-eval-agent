#!/usr/bin/env python3

import httpx
import yaml
from typing import Dict, List, Any

async def get_chat_completion(context: Dict[str, Any], api_key: str) -> List[Dict[str, Any]]:
    """Get chat completion from the LLM API for test generation.
    
    Args:
        context: Dictionary containing mermaid_diagram and existing_tests
        api_key: The API key for authentication
        
    Returns:
        List[Dict[str, Any]]: List of generated/reconciled test definitions
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
   - Specific URL
   - Detailed steps
   - Expected results

Return ONLY the YAML content for the tests, with no additional explanation or markdown formatting."""

        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://operative-backend.onrender.com/api/chat",
                headers={
                    "x-operative-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {"role": "system", "content": "You are a UI test generator that creates comprehensive test cases based on application structure. Output only valid YAML."},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            result = response.json()
            print(f"API Response: {result}")  # Debug log
            
            if "error" in result:
                raise Exception(result["error"])
            
            # The response should be YAML content in the message
            if "message" not in result:
                raise Exception("API response missing 'message' field")
                
            # Parse the YAML content from the message
            try:
                new_tests = yaml.safe_load(result["message"])
                if not isinstance(new_tests, list):
                    raise Exception("Generated tests must be a list")
                return new_tests
            except yaml.YAMLError as e:
                print(f"Error parsing generated YAML: {e}")
                print(f"Raw YAML content: {result['message']}")
                return context['existing_tests']
            
    except Exception as e:
        print(f"Error getting chat completion: {e}")
        # Return existing tests on error to avoid losing test coverage
        return context['existing_tests'] 