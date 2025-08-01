#!/usr/bin/env python3

import asyncio
import os
from webEvalAgent.src.tool_handlers import handle_web_evaluation

async def test_ssh_search_simple():
    """Simple test for SSH search on Google"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Simplified test parameters
    test_params = {
        "url": "https://google.com",
        "task": "Go to Google, search for 'ssh', and tell me what search results you see. List the first 5 search result titles and their descriptions.",
        "headless": True,  # Run in headless mode
        "tool_call_id": "ssh-search-simple"
    }
    
    print(f"🌐 Testing SSH search on Google")
    print("🚀 Starting evaluation...")
    
    try:
        # Run the web evaluation with timeout
        result = await asyncio.wait_for(
            handle_web_evaluation(test_params, ctx=None, api_key=api_key),
            timeout=120  # 2 minute timeout
        )
        
        print("✅ Web evaluation completed!")
        print("📊 RESULTS:")
        print("=" * 50)
        
        # Print results
        if isinstance(result, list):
            for i, item in enumerate(result):
                if hasattr(item, 'text'):
                    print(f"📄 Result {i+1}:")
                    print(item.text)
                    print("-" * 30)
        else:
            print(f"📄 Result: {str(result)}")
            
    except asyncio.TimeoutError:
        print("⏰ Test timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ssh_search_simple())

