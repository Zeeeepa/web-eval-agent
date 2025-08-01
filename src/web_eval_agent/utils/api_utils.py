#!/usr/bin/env python3

import google.generativeai as genai

async def validate_api_key(api_key: str) -> bool:
    """
    Validate the Google Gemini API key by making a test call.
    
    Args:
        api_key: The Gemini API key to validate
        
    Returns:
        bool: True if the API key is valid, False otherwise
    """
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # Try to list models as a validation test
        models = genai.list_models()
        # If we can list models, the API key is valid
        return True
    except Exception:
        return False
