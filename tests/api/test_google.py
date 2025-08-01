#!/usr/bin/env python3

import asyncio
import os
from webEvalAgent.src.tool_handlers import handle_web_evaluation

async def test_google_evaluation():
    """Test web evaluation on google.com"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test parameters
    test_params = {
        "url": "https://google.com",
        "task": "Evaluate the Google homepage for usability and design. Check if the search functionality works properly.",
        "headless": True,  # Run in headless mode for testing
        "tool_call_id": "test-123"
    }
    
    print(f"🌐 Testing web evaluation on: {test_params['url']}")
    print(f"📋 Task: {test_params['task']}")
    print("🚀 Starting evaluation...")
    
    try:
        # Run the web evaluation
        result = await handle_web_evaluation(
            test_params,
            ctx=None,  # No context needed for this test
            api_key=api_key
        )
        
        print("✅ Web evaluation completed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📝 Number of result items: {len(result) if isinstance(result, list) else 1}")
        
        # Print first few characters of the result
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if hasattr(first_result, 'text'):
                print(f"📄 First result preview: {first_result.text[:200]}...")
            else:
                print(f"📄 First result: {str(first_result)[:200]}...")
        else:
            print(f"📄 Result: {str(result)[:200]}...")
            
    except Exception as e:
        print(f"❌ Error during web evaluation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_google_evaluation())
