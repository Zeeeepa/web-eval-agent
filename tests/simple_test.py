#!/usr/bin/env python3

import asyncio
import os
from webEvalAgent.src.api_utils import validate_api_key

async def test_basic_functionality():
    """Test basic functionality of the migrated system"""
    
    # Test 1: API Key Validation
    print("🔍 Test 1: API Key Validation")
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return False
    
    print(f"🔑 Testing API key: {api_key[:10]}...")
    
    try:
        is_valid = await validate_api_key(api_key)
        if is_valid:
            print("✅ API key validation successful!")
        else:
            print("❌ API key validation failed")
            return False
    except Exception as e:
        print(f"❌ Error during API validation: {e}")
        return False
    
    # Test 2: Import Test
    print("\n🔍 Test 2: Module Import Test")
    try:
        from webEvalAgent.src.tool_handlers import handle_web_evaluation
        print("✅ Successfully imported handle_web_evaluation")
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ Successfully imported ChatGoogleGenerativeAI")
        
        # Test LLM initialization
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0.1,
        )
        print("✅ Successfully initialized Gemini LLM")
        
    except Exception as e:
        print(f"❌ Error during import test: {e}")
        return False
    
    # Test 3: Basic LLM Test
    print("\n🔍 Test 3: Basic LLM Test")
    try:
        response = llm.invoke("Hello! Can you respond with 'Gemini API is working'?")
        print(f"✅ LLM Response: {response.content}")
    except Exception as e:
        print(f"❌ Error during LLM test: {e}")
        return False
    
    print("\n🎉 All tests passed! The migration to Gemini API was successful!")
    print("🚀 The web-eval-agent is ready to use with Google Gemini API")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\n✅ Migration verification complete - all systems operational!")
    else:
        print("\n❌ Migration verification failed - please check the errors above")

