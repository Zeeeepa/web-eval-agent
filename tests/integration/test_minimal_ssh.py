#!/usr/bin/env python3

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, '/tmp/Zeeeepa/web-eval-agent')

async def test_minimal_ssh_search():
    """Minimal test for SSH search functionality"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    print("🚀 Starting minimal SSH search test...")
    
    try:
        # Import and test the LLM directly first
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0.1,
        )
        
        print("✅ LLM initialized successfully")
        
        # Test basic LLM functionality
        response = llm.invoke("Hello! Please respond with 'SSH search test ready'")
        print(f"✅ LLM Response: {response.content}")
        
        # Now try a simple browser automation without the full framework
        from playwright.async_api import async_playwright
        
        print("🌐 Testing basic browser automation...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set a realistic user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print("✅ Browser launched")
            
            # Try DuckDuckGo instead of Google (less bot detection)
            await page.goto('https://duckduckgo.com', wait_until='networkidle')
            print("✅ Navigated to DuckDuckGo")
            
            # Find search box
            search_box = await page.query_selector('input[name="q"]')
            if search_box:
                print("✅ Found search box")
                
                await search_box.fill('ssh')
                print("✅ Typed 'ssh'")
                
                await search_box.press('Enter')
                print("✅ Pressed Enter")
                
                # Wait for results
                await page.wait_for_timeout(3000)
                
                # Get search results
                results = await page.query_selector_all('h3')
                print(f"✅ Found {len(results)} potential results")
                
                # Extract first few results
                search_results = []
                for i, result in enumerate(results[:5]):
                    try:
                        text = await result.inner_text()
                        # Get the parent link
                        link_element = await result.query_selector('xpath=ancestor::a')
                        link = await link_element.get_attribute('href') if link_element else 'No link'
                        search_results.append({
                            'title': text,
                            'link': link
                        })
                    except:
                        pass
                
                print("\n📊 SSH SEARCH RESULTS:")
                print("=" * 50)
                for i, result in enumerate(search_results):
                    print(f"{i+1}. {result['title']}")
                    print(f"   Link: {result['link']}")
                    print("-" * 30)
                
                # Now test with the LLM to analyze results
                if search_results:
                    results_text = "\n".join([f"{i+1}. {r['title']} - {r['link']}" for i, r in enumerate(search_results)])
                    
                    analysis_prompt = f"""I searched for 'ssh' on DuckDuckGo and found these results:

{results_text}

Please analyze these search results and tell me:
1. What types of SSH-related topics are covered?
2. Which results seem most relevant for someone learning about SSH?
3. Are there any official documentation or tutorial links?"""

                    analysis = llm.invoke(analysis_prompt)
                    print("\n🤖 AI ANALYSIS:")
                    print("=" * 50)
                    print(analysis.content)
                
            else:
                print("❌ Could not find search box")
            
            await browser.close()
            print("✅ Browser closed")
        
        print("\n🎉 Minimal SSH search test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_ssh_search())

