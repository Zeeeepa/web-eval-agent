#!/usr/bin/env python3

import asyncio
import os

async def test_improved_ssh_search():
    """Improved SSH search test with better result extraction"""
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    print("🚀 Starting improved SSH search test...")
    
    try:
        from playwright.async_api import async_playwright
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0.1,
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set realistic headers
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print("✅ Browser launched")
            
            # Try DuckDuckGo
            await page.goto('https://duckduckgo.com', wait_until='networkidle')
            print("✅ Navigated to DuckDuckGo")
            
            # Find and use search box
            search_box = await page.query_selector('input[name="q"]')
            if search_box:
                await search_box.fill('ssh tutorial')
                await search_box.press('Enter')
                print("✅ Searched for 'ssh tutorial'")
                
                # Wait for results to load
                await page.wait_for_timeout(5000)
                
                # Try multiple selectors for search results
                result_selectors = [
                    '[data-testid="result"]',
                    '.result',
                    '.web-result',
                    'article',
                    '[data-layout="organic"]'
                ]
                
                search_results = []
                for selector in result_selectors:
                    results = await page.query_selector_all(selector)
                    if results:
                        print(f"✅ Found {len(results)} results with selector: {selector}")
                        
                        for i, result in enumerate(results[:5]):
                            try:
                                # Try to get title
                                title_element = await result.query_selector('h3, h2, .result__title, [data-testid="result-title-a"]')
                                title = await title_element.inner_text() if title_element else 'No title'
                                
                                # Try to get link
                                link_element = await result.query_selector('a, [data-testid="result-title-a"]')
                                link = await link_element.get_attribute('href') if link_element else 'No link'
                                
                                # Try to get description
                                desc_element = await result.query_selector('.result__snippet, [data-testid="result-snippet"], .snippet')
                                description = await desc_element.inner_text() if desc_element else 'No description'
                                
                                if title != 'No title':
                                    search_results.append({
                                        'title': title.strip(),
                                        'link': link,
                                        'description': description.strip()
                                    })
                            except Exception as e:
                                continue
                        
                        if search_results:
                            break
                
                if search_results:
                    print(f"\n📊 SSH SEARCH RESULTS ({len(search_results)} found):")
                    print("=" * 60)
                    
                    for i, result in enumerate(search_results):
                        print(f"{i+1}. {result['title']}")
                        print(f"   🔗 {result['link']}")
                        print(f"   📝 {result['description'][:100]}...")
                        print("-" * 40)
                    
                    # Get AI analysis
                    results_text = "\n".join([
                        f"{i+1}. Title: {r['title']}\n   URL: {r['link']}\n   Description: {r['description'][:200]}..."
                        for i, r in enumerate(search_results)
                    ])
                    
                    analysis_prompt = f"""I searched for 'ssh tutorial' and found these results:

{results_text}

Please provide a comprehensive analysis:
1. List each result with its title and what it covers
2. Identify which results are most useful for learning SSH
3. Categorize the types of resources (official docs, tutorials, tools, etc.)
4. Recommend the top 3 results for someone new to SSH"""

                    print("\n🤖 AI ANALYSIS OF SSH SEARCH RESULTS:")
                    print("=" * 60)
                    
                    analysis = llm.invoke(analysis_prompt)
                    print(analysis.content)
                    
                else:
                    print("❌ No search results found with any selector")
                    
                    # Debug: get page content
                    content = await page.content()
                    print(f"📄 Page content length: {len(content)} characters")
                    
                    # Let AI analyze the raw page
                    if len(content) > 0:
                        # Truncate content for analysis
                        truncated_content = content[:5000] + "..." if len(content) > 5000 else content
                        
                        debug_prompt = f"""I searched for 'ssh tutorial' on DuckDuckGo but couldn't extract results. Here's the page content:

{truncated_content}

Can you help me identify what search results are present on this page? Look for SSH-related links, titles, or content."""

                        debug_analysis = llm.invoke(debug_prompt)
                        print("\n🔍 AI DEBUG ANALYSIS:")
                        print("=" * 60)
                        print(debug_analysis.content)
            
            await browser.close()
            print("\n✅ Browser closed")
        
        print("🎉 Improved SSH search test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_ssh_search())

