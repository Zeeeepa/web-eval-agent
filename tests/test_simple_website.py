#!/usr/bin/env python3

import asyncio
import os
from webEvalAgent.src.tool_handlers import handle_web_evaluation

async def test_simple_website():
    """Test with a simpler website to verify the agent is working"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test with a simple website first
    test_params = {
        "url": "https://httpbin.org/html",
        "task": "Visit this webpage and tell me what you see. Describe the content, any headings, links, or other elements on the page.",
        "headless": True,
        "tool_call_id": "simple-test"
    }
    
    print(f"🌐 Testing simple website: {test_params['url']}")
    print("🚀 Starting evaluation...")
    
    try:
        # Run with a shorter timeout
        result = await asyncio.wait_for(
            handle_web_evaluation(test_params, ctx=None, api_key=api_key),
            timeout=60  # 1 minute timeout
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
        print("⏰ Test timed out after 1 minute")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_website())

