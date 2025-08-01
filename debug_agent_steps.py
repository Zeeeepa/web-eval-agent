#!/usr/bin/env python3
"""
Debug script to test agent steps extraction
"""
import asyncio
import os
from browser_use import Agent, Browser
from langchain_google_genai import ChatGoogleGenerativeAI

async def test_agent_steps():
    """Test what the agent result actually contains"""
    
    # Set up the LLM
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBXmhlHudrD4zXiv-5fjxi1gGG-_kdtaZ0")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        api_key=api_key,
        temperature=0.1
    )
    
    # Create browser and agent with headless mode
    browser = Browser()
    
    agent = Agent(
        task="Navigate to http://localhost:5000 and check if the page loads successfully",
        llm=llm,
        browser=browser
    )
    
    try:
        print("🚀 Starting agent test...")
        
        # Run the agent with a short timeout
        result = await agent.run(max_steps=3)
        
        print(f"\n📊 AGENT RESULT ANALYSIS:")
        print(f"Type: {type(result)}")
        print(f"Attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
        
        # Check specific attributes
        if hasattr(result, 'model_actions'):
            print(f"\n🎯 model_actions: {result.model_actions}")
        
        if hasattr(result, 'action_names'):
            print(f"\n🎯 action_names: {result.action_names}")
            
        if hasattr(result, 'model_thoughts'):
            print(f"\n🎯 model_thoughts: {result.model_thoughts}")
            
        if hasattr(result, 'number_of_steps'):
            print(f"\n🎯 number_of_steps: {result.number_of_steps}")
            
        if hasattr(result, 'is_successful'):
            print(f"\n🎯 is_successful: {result.is_successful}")
            
        if hasattr(result, 'final_result'):
            print(f"\n🎯 final_result: {result.final_result}")
            
        # Test our extraction function
        from web_eval.test_executor import TestExecutor
        executor = TestExecutor(None)
        steps = executor._extract_agent_steps(result)
        
        print(f"\n✅ EXTRACTED STEPS ({len(steps)}):")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_agent_steps())
