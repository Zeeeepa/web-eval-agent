#!/usr/bin/env python3
"""
Test GEMINI API integration with browser-use
"""

import asyncio
import os
from browser_use import Agent, Browser, BrowserConfig

# Set the API key
GOOGLE_API_KEY = "AIzaSyBXmhlHudrD4zXiv-5fjxi1gGG-_kdtaZ0"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

async def test_gemini_integration():
    """Test GEMINI API integration with a simple web evaluation task"""
    
    print("🚀 Testing GEMINI API Integration with Browser-Use")
    print("=" * 60)
    
    try:
        # Import the ChatGoogleGenerativeAI LLM
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize the LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=GOOGLE_API_KEY
        )
        
        print("✅ GEMINI LLM initialized successfully")
        
        # Create browser config
        browser_config = BrowserConfig(
            headless=True,
            disable_security=True,
            chrome_instance_path=None,
            extra_chromium_args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
        )
        
        print("✅ Browser config configured")
        
        # Create browser
        browser = Browser(config=browser_config)
        
        print("✅ Browser created")
        
        # Define the test task
        task = """Visit https://example.com and perform a basic evaluation:
        
        1. Navigate to the homepage
        2. Check if the page loads successfully
        3. Verify the page title is present
        4. Look for any obvious errors or issues
        5. Provide a brief summary of your findings
        
        Focus on basic functionality and report any problems you encounter."""
        
        print("🔍 Starting web evaluation task...")
        print(f"📋 Task: {task[:100]}...")
        
        # Create and run the agent
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            use_vision=True
        )
        
        # Execute the task
        history = await agent.run()
        
        # Close browser
        await browser.close()
        
        # Get the result
        result = str(history.final_result()) if hasattr(history, 'final_result') else str(history)
        
        print("✅ Task completed successfully!")
        print("=" * 60)
        print("📊 EVALUATION RESULTS:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Save results to file
        with open("gemini_test_results.txt", "w") as f:
            f.write("GEMINI API Integration Test Results\n")
            f.write("=" * 40 + "\n")
            f.write(f"Task: {task}\n\n")
            f.write("Results:\n")
            f.write(result)
            f.write("\n\nTest completed successfully!")
        
        print("💾 Results saved to gemini_test_results.txt")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini_integration())
    if success:
        print("\n🎉 GEMINI API integration test completed successfully!")
    else:
        print("\n💥 GEMINI API integration test failed!")
