#!/usr/bin/env python3

import asyncio
import os
import json
from mcp.types import TextContent

# Import the MCP server functions directly
from webEvalAgent.mcp_server import web_eval_agent

class MockContext:
    """Mock context for testing"""
    pass

async def test_ssh_search_mcp():
    """Test SSH search using the MCP server directly"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    print("🚀 Testing SSH search via MCP server...")
    print("=" * 60)
    
    try:
        # Create mock context
        ctx = MockContext()
        
        # Call the web_eval_agent function directly
        result = await web_eval_agent(
            url="https://google.com",
            task="""Please go to Google and search for 'ssh'. Then provide me with a detailed list of all the search results you can see, including:

1. The title of each search result
2. The URL/domain of each result  
3. The description/snippet text
4. Any special result boxes (featured snippets, knowledge panels, etc.)

Please be thorough and list as many results as you can see on the first page.""",
            ctx=ctx,
            headless_browser=True
        )
        
        print("✅ MCP web evaluation completed!")
        print("=" * 60)
        print("📊 SSH SEARCH RESULTS:")
        print("=" * 60)
        
        # Print the results
        if isinstance(result, list):
            for i, item in enumerate(result):
                if isinstance(item, TextContent):
                    print(f"📄 Result {i+1}:")
                    print(item.text)
                    print("-" * 40)
                else:
                    print(f"📄 Result {i+1}: {str(item)}")
                    print("-" * 40)
        else:
            print(f"📄 Complete Result:\n{str(result)}")
            
        print("=" * 60)
        print("🎉 SSH search test via MCP completed!")
            
    except Exception as e:
        print(f"❌ Error during MCP test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ssh_search_mcp())

