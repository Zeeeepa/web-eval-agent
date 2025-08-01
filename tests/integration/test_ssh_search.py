#!/usr/bin/env python3

import asyncio
import os
from webEvalAgent.src.tool_handlers import handle_web_evaluation

async def test_ssh_search():
    """Test web agent searching for 'ssh' on Google and listing all results"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test parameters for SSH search
    test_params = {
        "url": "https://google.com",
        "task": """Go to Google.com and perform the following steps:
1. Navigate to the Google homepage
2. Find the search box
3. Type 'ssh' in the search box
4. Press Enter or click the search button to search
5. Wait for the search results to load
6. List ALL the search results you can see on the page, including:
   - The title of each result
   - The URL/link of each result
   - A brief description/snippet if available
7. Also note any special result boxes (like featured snippets, knowledge panels, etc.)
8. Provide a comprehensive list of everything you found

Please be thorough and list every search result visible on the page.""",
        "headless": False,  # Run with visible browser to see what's happening
        "tool_call_id": "ssh-search-test"
    }
    
    print(f"🌐 Testing SSH search on: {test_params['url']}")
    print(f"📋 Task: Search for 'ssh' and list all results")
    print("🚀 Starting web evaluation...")
    print("=" * 60)
    
    try:
        # Run the web evaluation
        result = await handle_web_evaluation(
            test_params,
            ctx=None,  # No context needed for this test
            api_key=api_key
        )
        
        print("✅ Web evaluation completed successfully!")
        print("=" * 60)
        print("📊 SEARCH RESULTS:")
        print("=" * 60)
        
        # Print the full results
        if isinstance(result, list) and len(result) > 0:
            for i, item in enumerate(result):
                if hasattr(item, 'text'):
                    print(f"Result {i+1}:")
                    print(item.text)
                    print("-" * 40)
                else:
                    print(f"Result {i+1}: {str(item)}")
                    print("-" * 40)
        else:
            print(f"📄 Complete Result:\n{str(result)}")
            
        print("=" * 60)
        print("🎉 SSH search test completed!")
            
    except Exception as e:
        print(f"❌ Error during web evaluation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ssh_search())

