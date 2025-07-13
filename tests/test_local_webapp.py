#!/usr/bin/env python3
"""
Test script for evaluating locally hosted web applications with interactive features.

This script demonstrates how to use the web-eval-agent to test local web applications
with various interactive elements like forms, buttons, navigation, etc.
"""

import asyncio
import os
from webEvalAgent.src.tool_handlers import handle_web_evaluation

async def test_local_webapp_interactions():
    """
    Test web evaluation on a local web application with interactive features.
    
    This test demonstrates how to:
    1. Navigate to a local URL (e.g., http://localhost:3000)
    2. Interact with forms, buttons, and other UI elements
    3. Test specific user workflows
    4. Evaluate the user experience
    """
    
    # Set up the API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("   Please set your Gemini API key: export GEMINI_API_KEY='your_key_here'")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    print("🚀 Testing local web application interactions...")
    print("=" * 80)
    
    # Example test scenarios for different types of local applications
    test_scenarios = [
        {
            "name": "React Development Server Test",
            "url": "http://localhost:3000",
            "task": """
            Please test this React development application:
            
            1. Navigate to the homepage and describe what you see
            2. Look for any navigation menu or header elements
            3. Try to find and click on any buttons or links
            4. If there are forms, try filling them out with test data
            5. Test any interactive features like dropdowns, modals, or tabs
            6. Check for any error messages or console errors
            7. Evaluate the overall user experience and responsiveness
            
            Provide a detailed report of:
            - What features you found and tested
            - Any issues or bugs encountered
            - User experience assessment
            - Suggestions for improvements
            """
        },
        {
            "name": "Next.js Application Test",
            "url": "http://localhost:3000",
            "task": """
            Test this Next.js application focusing on:
            
            1. Page loading and navigation between routes
            2. Form submissions and data handling
            3. Any authentication features (login/signup)
            4. Search functionality if present
            5. Mobile responsiveness (resize browser window)
            6. Performance and loading times
            
            Please interact with all available features and provide feedback on:
            - Functionality completeness
            - User interface design
            - Performance issues
            - Accessibility considerations
            """
        },
        {
            "name": "Express.js Backend Test",
            "url": "http://localhost:8000",
            "task": """
            Test this Express.js web application:
            
            1. Check if the server is responding correctly
            2. Test any API endpoints that have web interfaces
            3. Try different routes and pages
            4. Test form submissions and data processing
            5. Check error handling (try invalid inputs)
            6. Evaluate the overall backend functionality
            
            Report on:
            - Server response times
            - Error handling quality
            - Data validation
            - User feedback mechanisms
            """
        },
        {
            "name": "Custom Local Application Test",
            "url": "http://localhost:8080",
            "task": """
            Comprehensively test this local web application:
            
            1. **Navigation Testing:**
               - Test all menu items and navigation links
               - Check breadcrumbs and back/forward functionality
               - Verify all pages load correctly
            
            2. **Form Testing:**
               - Fill out all forms with valid data
               - Test form validation with invalid data
               - Check required field validation
               - Test file uploads if present
            
            3. **Interactive Elements:**
               - Click all buttons and verify their actions
               - Test dropdowns, checkboxes, and radio buttons
               - Interact with any sliders, toggles, or custom controls
               - Test modal dialogs and popups
            
            4. **User Workflow Testing:**
               - Complete typical user journeys from start to finish
               - Test the most common use cases
               - Verify data persistence across pages
            
            5. **Error Handling:**
               - Try edge cases and invalid inputs
               - Check how the app handles network errors
               - Test browser back/refresh scenarios
            
            Provide a comprehensive evaluation including:
            - Feature completeness assessment
            - User experience quality rating
            - Performance observations
            - Bug reports with reproduction steps
            - Improvement recommendations
            """
        }
    ]
    
    # Let user choose which test to run
    print("Available test scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. {scenario['name']} - {scenario['url']}")
    
    print("\nTo run a specific test, modify the script or use the custom test below.")
    print("For this demo, we'll run a comprehensive local application test.\n")
    
    # Run the comprehensive test (you can modify the URL and task as needed)
    test_params = {
        "url": "http://localhost:3000",  # Change this to your local application URL
        "task": """
        Please thoroughly test this local web application:
        
        **NAVIGATION & LAYOUT:**
        1. Describe the overall layout and design
        2. Test all navigation elements (menus, links, buttons)
        3. Check if the layout is responsive
        
        **INTERACTIVE FEATURES:**
        1. Find and test all forms on the page
        2. Try clicking all buttons and interactive elements
        3. Test any search functionality
        4. Interact with dropdowns, modals, or dynamic content
        
        **USER EXPERIENCE:**
        1. Complete a typical user workflow from start to finish
        2. Test the most important features of the application
        3. Check for any error messages or broken functionality
        4. Evaluate loading times and performance
        
        **DETAILED REPORTING:**
        Please provide:
        - A summary of all features you found and tested
        - Any bugs or issues encountered with reproduction steps
        - User experience assessment (ease of use, design quality)
        - Performance observations
        - Specific recommendations for improvements
        - Overall rating of the application quality
        
        Be thorough and test everything you can interact with!
        """,
        "headless": False,  # Set to True for headless testing
        "tool_call_id": "local-webapp-test"
    }
    
    print(f"🌐 Testing local application: {test_params['url']}")
    print("📋 Running comprehensive interactive feature test...")
    print("🔍 This will test forms, buttons, navigation, and user workflows")
    print("=" * 80)
    
    try:
        # Run the web evaluation
        result = await handle_web_evaluation(
            test_params,
            ctx=None,
            api_key=api_key
        )
        
        print("✅ Local web application test completed!")
        print("=" * 80)
        print("📊 TEST RESULTS:")
        print("=" * 80)
        
        # Print the results
        if isinstance(result, list):
            for i, item in enumerate(result):
                if hasattr(item, 'text'):
                    print(f"📄 Result {i+1}:")
                    print(item.text)
                    print("-" * 60)
                else:
                    print(f"📄 Result {i+1}: {str(item)}")
                    print("-" * 60)
        else:
            print(f"📄 Complete Result:\n{str(result)}")
            
        print("=" * 80)
        print("🎉 Local web application testing completed!")
        print("\n💡 TIP: Check the 'Operative Control Center' dashboard for detailed logs and screenshots")
            
    except Exception as e:
        print(f"❌ Error during local web application test: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure your local web application is running")
        print("2. Verify the URL is correct and accessible")
        print("3. Check that GEMINI_API_KEY is set correctly")
        print("4. Ensure all dependencies are installed")

async def test_specific_features():
    """
    Test specific interactive features on a local web application.
    
    This function demonstrates how to test particular UI components or workflows.
    """
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    # Example: Testing a specific feature like a contact form
    contact_form_test = {
        "url": "http://localhost:3000/contact",
        "task": """
        Test the contact form on this page:
        
        1. Fill out the contact form with these test details:
           - Name: "John Doe"
           - Email: "john.doe@example.com"
           - Subject: "Test Message"
           - Message: "This is a test message to verify the contact form functionality."
        
        2. Submit the form and observe what happens
        3. Check for confirmation messages or error handling
        4. Verify form validation (try submitting with missing fields)
        5. Test with invalid email format
        
        Report on:
        - Form usability and design
        - Validation effectiveness
        - Success/error message clarity
        - Overall user experience
        """
    }
    
    # Example: Testing e-commerce functionality
    ecommerce_test = {
        "url": "http://localhost:3000/shop",
        "task": """
        Test the e-commerce functionality:
        
        1. Browse product listings
        2. Click on product details
        3. Add items to cart
        4. Modify cart quantities
        5. Proceed to checkout
        6. Test the checkout process (use test data)
        
        Evaluate:
        - Product browsing experience
        - Cart functionality
        - Checkout process usability
        - Payment form design (don't submit real payment)
        """
    }
    
    print("🎯 Specific feature testing examples created.")
    print("Modify the test parameters above to match your application's features.")

if __name__ == "__main__":
    print("🧪 Web-Eval-Agent Local Application Testing")
    print("=" * 50)
    print("This script tests locally hosted web applications with interactive features.")
    print("Make sure your local application is running before starting the test.\n")
    
    # Run the main test
    asyncio.run(test_local_webapp_interactions())
    
    print("\n" + "=" * 50)
    print("For more specific feature testing, check the test_specific_features() function.")

