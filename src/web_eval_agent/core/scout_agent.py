"""
Scout Agent for Web Eval Agent

Intelligent page scouting to discover interactive elements before testing.
"""

import asyncio
import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass

from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from .config import Config


@dataclass
class InteractiveElement:
    """Represents an interactive element found on the page."""
    element_type: str
    description: str
    location: str
    text_content: str
    selector: str = ""
    priority: int = 1  # 1=high, 2=medium, 3=low


class ScoutAgent:
    """Agent that scouts web pages to identify interactive elements."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=config.api_key
        )
    
    async def scout_page(self, url: str) -> List[str]:
        """Scout a page and return targeted test tasks for different elements."""
        try:
            # Create browser for scouting
            browser_config = BrowserConfig(
                headless=True,
                disable_security=True,
                chrome_instance_path=None,
                extra_chromium_args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
            )
            
            browser = Browser(config=browser_config)
            
            scout_task = f"""Visit {url} and identify ALL interactive elements on the page. 
            
            Do NOT click anything, just observe and catalog what's available. 
            
            List buttons, links, forms, input fields, menus, dropdowns, and any other clickable elements you can see. 
            
            For each element, note:
            - Element type (button, link, form, input, etc.)
            - Visible text or label
            - Location on page (header, main content, sidebar, footer)
            - Purpose or function
            
            Provide a comprehensive inventory of all interactive elements."""
            
            agent = Agent(
                task=scout_task,
                llm=self.llm,
                browser=browser,
                use_vision=True
            )
            
            history = await agent.run()
            await browser.close()
            
            scout_result = str(history.final_result()) if hasattr(history, 'final_result') else str(history)
            
            # Generate targeted test tasks
            test_tasks = await self._generate_test_tasks(url, scout_result)
            
            return test_tasks
            
        except Exception as e:
            print(f"⚠️ Scout agent failed: {e}")
            # Return fallback tasks
            return self._get_fallback_tasks(url)
    
    async def _generate_test_tasks(self, url: str, scout_result: str) -> List[str]:
        """Generate specific test tasks based on scout findings."""
        partition_prompt = f"""
Based on this scout report of interactive elements found on {url}:

{scout_result}

Create a list of specific testing tasks, each focusing on different elements. 
Each task should specify exactly which elements to test (by their text, location, or description). 
Aim for 6-8 distinct tasks that cover different elements without overlap.

Make each task very specific about which exact elements to test.

Format as JSON array: [
    "Test the [specific element description] - click on [exact button/link text or location]",
    "Test the [different specific element] - interact with [exact description]",
    ...
]

Focus on:
1. Navigation elements (header, menu, navigation links)
2. Main content interactions (buttons, links in content area)
3. Form elements (input fields, submit buttons, dropdowns)
4. Footer elements (footer links, contact info)
5. Interactive widgets (search, filters, toggles)
6. Media elements (images, videos, galleries)
"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=partition_prompt)])
            
            # Parse JSON response
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                element_tasks = json.loads(json_match.group())
                return element_tasks
            else:
                return self._get_fallback_tasks(url)
                
        except Exception as e:
            print(f"⚠️ Task generation failed: {e}")
            return self._get_fallback_tasks(url)
    
    def _get_fallback_tasks(self, url: str) -> List[str]:
        """Return fallback tasks if scouting fails."""
        return [
            f"Test navigation elements in the header area of {url}",
            f"Test main content links and buttons in {url}",
            f"Test footer links and elements in {url}",
            f"Test any form elements found in {url}",
            f"Test sidebar or secondary navigation in {url}",
            f"Test any remaining interactive elements in {url}"
        ]
    
    async def analyze_page_structure(self, url: str) -> Dict[str, Any]:
        """Analyze page structure and return detailed element information."""
        try:
            browser_config = BrowserConfig(
                headless=True,
                disable_security=True,
                chrome_instance_path=None,
                chrome_user_data_dir=None,
                additional_args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage'],
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=8.0,
                wait_between_actions=0.5
            )
            
            browser = Browser(config=browser_config)
            
            analysis_task = f"""Analyze the structure and interactive elements of {url}.
            
            Provide a detailed analysis including:
            1. Page layout structure (header, main, sidebar, footer)
            2. Navigation patterns and menu structure
            3. Interactive elements by category (forms, buttons, links, etc.)
            4. Content organization and hierarchy
            5. Any accessibility features or issues
            6. Performance observations (loading speed, responsiveness)
            
            Focus on elements that would be important for comprehensive testing."""
            
            agent = Agent(
                task=analysis_task,
                llm=self.llm,
                browser=browser,
                use_vision=True
            )
            
            history = await agent.run()
            await browser.close()
            
            analysis_result = str(history.final_result()) if hasattr(history, 'final_result') else str(history)
            
            return {
                "url": url,
                "structure_analysis": analysis_result,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                "url": url,
                "structure_analysis": f"Analysis failed: {e}",
                "timestamp": asyncio.get_event_loop().time(),
                "error": str(e)
            }
