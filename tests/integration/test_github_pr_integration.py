#!/usr/bin/env python3

"""
Test GitHub PR integration functionality.
Tests the new async & concurrency features with structured logging.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import webEvalAgent
sys.path.insert(0, str(Path(__file__).parent.parent))

from webEvalAgent.src.github_integration import GitHubIntegration, test_github_pr, test_github_branch
from webEvalAgent.src.session_manager import get_session_manager, SessionConfig
from webEvalAgent.src.logging_config import get_logger, create_session_context
from webEvalAgent.src.browser_pool import BrowserPool


async def test_github_pr_detection():
    """Test GitHub PR URL detection and metadata retrieval."""
    print("🔍 Testing GitHub PR detection...")
    
    # Initialize GitHub integration
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  No GITHUB_TOKEN found, skipping GitHub API tests")
        return
    
    integration = GitHubIntegration(github_token)
    
    try:
        # Test PR info retrieval
        pr_info = await integration.get_pr_info("Zeeeepa/codegenApp", 96)
        print(f"✅ PR Info retrieved: {pr_info.title}")
        print(f"   Branch: {pr_info.branch}")
        print(f"   Author: {pr_info.author}")
        print(f"   URL: {pr_info.url}")
        
        # Test deployment URL detection
        deployment_url = await integration.detect_deployment_url("Zeeeepa/codegenApp", pr_number=96)
        if deployment_url:
            print(f"✅ Deployment URL detected: {deployment_url}")
        else:
            print("⚠️  No deployment URL detected (this is expected for most repos)")
        
    except Exception as e:
        print(f"❌ Error testing GitHub PR detection: {e}")


async def test_session_manager():
    """Test the session manager with concurrent sessions."""
    print("\n🔄 Testing Session Manager...")
    
    session_manager = get_session_manager(max_concurrent_sessions=3)
    
    try:
        # Create multiple session configs
        configs = [
            SessionConfig(
                url="https://example.com",
                task=f"Test session {i}",
                github_repo="test/repo",
                github_pr=i,
                timeout=10
            )
            for i in range(1, 4)
        ]
        
        # Create sessions
        session_ids = []
        for config in configs:
            session_id = await session_manager.create_session(config)
            session_ids.append(session_id)
            print(f"✅ Created session: {session_id}")
        
        # Check session metrics
        metrics = await session_manager.get_session_metrics()
        print(f"📊 Session metrics: {metrics}")
        
        # Clean up sessions
        for session_id in session_ids:
            await session_manager.cancel_session(session_id)
            print(f"🧹 Cancelled session: {session_id}")
        
        print("✅ Session manager test completed")
        
    except Exception as e:
        print(f"❌ Error testing session manager: {e}")
    finally:
        await session_manager.shutdown()


async def test_browser_pool():
    """Test the browser pool functionality."""
    print("\n🌐 Testing Browser Pool...")
    
    browser_pool = BrowserPool(max_size=2)
    
    try:
        # Test acquiring browser instances
        instance1 = await browser_pool.acquire(headless=True, timeout=30)
        print(f"✅ Acquired browser instance: {instance1.instance_id}")
        
        instance2 = await browser_pool.acquire(headless=True, timeout=30)
        print(f"✅ Acquired browser instance: {instance2.instance_id}")
        
        # Check pool stats
        stats = await browser_pool.get_stats()
        print(f"📊 Browser pool stats: {stats}")
        
        # Release instances
        await browser_pool.release(instance1)
        await browser_pool.release(instance2)
        print("✅ Released browser instances")
        
        # Test context manager
        async with browser_pool.browser_instance(headless=True) as instance:
            print(f"✅ Context manager test with instance: {instance.instance_id}")
        
        print("✅ Browser pool test completed")
        
    except Exception as e:
        print(f"❌ Error testing browser pool: {e}")
    finally:
        await browser_pool.shutdown()


async def test_structured_logging():
    """Test structured logging functionality."""
    print("\n📝 Testing Structured Logging...")
    
    logger = get_logger("test-logger")
    
    # Create session context
    context = create_session_context(
        github_repo="Zeeeepa/codegenApp",
        github_pr=96,
        url="https://example.com",
        task="Test logging functionality"
    )
    
    # Test logging with context
    with logger.evaluation_session(context):
        logger.info("Starting evaluation test")
        logger.log_browser_action("click", "button#submit", success=True, duration=0.5)
        logger.log_network_request("https://api.example.com/data", "GET", 200, duration=0.3)
        logger.log_console_error("TypeError: Cannot read property 'foo' of undefined", 
                                source="app.js", line=42)
        logger.log_screenshot("/tmp/screenshot.png", step="after_login")
        logger.log_ai_response("Test the login form", "I will test the login form...", 
                              duration=2.1, model="gemini-pro")
        logger.info("Evaluation test completed")
    
    print("✅ Structured logging test completed")


async def test_full_github_pr_workflow():
    """Test the complete GitHub PR testing workflow."""
    print("\n🚀 Testing Full GitHub PR Workflow...")
    
    # Check for required environment variables
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("⚠️  No GEMINI_API_KEY found, skipping full workflow test")
        return
    
    try:
        # Test with a simple task that doesn't require actual deployment
        result = await test_github_pr(
            repo="Zeeeepa/codegenApp",
            pr_number=96,
            task="Navigate to the homepage and check if it loads properly",
            headless=True,
            timeout=60
        )
        
        print("✅ GitHub PR workflow test completed")
        print(f"📊 Result type: {type(result)}")
        
    except Exception as e:
        print(f"⚠️  GitHub PR workflow test failed (expected if no deployment): {e}")


async def main():
    """Run all tests."""
    print("🧪 Starting Web Eval Agent Enhanced Tests")
    print("=" * 50)
    
    # Run tests
    await test_structured_logging()
    await test_browser_pool()
    await test_session_manager()
    await test_github_pr_detection()
    await test_full_github_pr_workflow()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

