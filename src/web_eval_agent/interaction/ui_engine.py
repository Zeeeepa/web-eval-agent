"""
Advanced UI Interaction Engine

Sophisticated UI interaction system with multiple detection strategies,
intelligent wait conditions, and robust error handling.
"""

import asyncio
import time
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from playwright.async_api import Page, ElementHandle, Locator
from browser_use import Agent

logger = logging.getLogger(__name__)


class InteractionStrategy(Enum):
    """Available interaction strategies."""
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"
    TEXT_CONTENT = "text_content"
    PLACEHOLDER = "placeholder"
    ARIA_LABEL = "aria_label"
    DATA_TESTID = "data_testid"
    VISUAL_RECOGNITION = "visual_recognition"
    BROWSER_USE_AI = "browser_use_ai"


class WaitCondition(Enum):
    """Wait conditions for element interactions."""
    VISIBLE = "visible"
    ATTACHED = "attached"
    DETACHED = "detached"
    STABLE = "stable"
    ENABLED = "enabled"
    EDITABLE = "editable"
    HIDDEN = "hidden"


@dataclass
class ElementSelector:
    """Element selector with multiple strategies."""
    strategy: InteractionStrategy
    value: str
    description: str
    confidence: float = 1.0
    timeout: int = 5000
    
    
@dataclass
class InteractionResult:
    """Result of an interaction attempt."""
    success: bool
    strategy_used: Optional[InteractionStrategy]
    element_found: bool
    action_completed: bool
    error_message: Optional[str]
    execution_time: float
    element_info: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None


class UIInteractionEngine:
    """
    Advanced UI interaction engine with multiple detection strategies,
    intelligent wait conditions, and comprehensive error handling.
    """
    
    def __init__(self, page: Page, browser_use_agent: Optional[Agent] = None):
        self.page = page
        self.browser_use_agent = browser_use_agent
        self.interaction_history: List[Dict[str, Any]] = []
        self.element_cache: Dict[str, ElementHandle] = {}
        self.performance_metrics: Dict[str, List[float]] = {
            'element_detection': [],
            'interaction_execution': [],
            'wait_times': []
        }
        
    async def find_element(self, selectors: List[ElementSelector]) -> Tuple[Optional[ElementHandle], Optional[InteractionStrategy]]:
        """
        Find element using multiple strategies with fallback.
        
        Args:
            selectors: List of selectors to try in order
            
        Returns:
            Tuple of (element, strategy_used) or (None, None) if not found
        """
        start_time = time.time()
        
        for selector in sorted(selectors, key=lambda x: x.confidence, reverse=True):
            try:
                element = await self._find_element_by_strategy(selector)
                if element:
                    detection_time = time.time() - start_time
                    self.performance_metrics['element_detection'].append(detection_time)
                    
                    logger.info(f"Element found using {selector.strategy.value} in {detection_time:.2f}s")
                    return element, selector.strategy
                    
            except Exception as e:
                logger.debug(f"Strategy {selector.strategy.value} failed: {e}")
                continue
                
        logger.warning(f"Element not found after trying {len(selectors)} strategies")
        return None, None
        
    async def _find_element_by_strategy(self, selector: ElementSelector) -> Optional[ElementHandle]:
        """Find element using a specific strategy."""
        try:
            if selector.strategy == InteractionStrategy.CSS_SELECTOR:
                return await self.page.wait_for_selector(
                    selector.value, 
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.XPATH:
                return await self.page.wait_for_selector(
                    f"xpath={selector.value}",
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.TEXT_CONTENT:
                # Find by text content
                return await self.page.wait_for_selector(
                    f"text={selector.value}",
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.PLACEHOLDER:
                return await self.page.wait_for_selector(
                    f"[placeholder*='{selector.value}' i]",
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.ARIA_LABEL:
                return await self.page.wait_for_selector(
                    f"[aria-label*='{selector.value}' i]",
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.DATA_TESTID:
                return await self.page.wait_for_selector(
                    f"[data-testid='{selector.value}']",
                    timeout=selector.timeout,
                    state='visible'
                )
                
            elif selector.strategy == InteractionStrategy.VISUAL_RECOGNITION:
                # Placeholder for visual recognition - would integrate with computer vision
                logger.info("Visual recognition not yet implemented")
                return None
                
            elif selector.strategy == InteractionStrategy.BROWSER_USE_AI:
                # Use browser-use AI agent for element detection
                if self.browser_use_agent:
                    return await self._find_with_browser_use(selector.value)
                    
        except Exception as e:
            logger.debug(f"Strategy {selector.strategy.value} failed: {e}")
            return None
            
        return None
        
    async def _find_with_browser_use(self, description: str) -> Optional[ElementHandle]:
        """Use browser-use AI agent to find element."""
        if not self.browser_use_agent:
            return None
            
        try:
            # This would integrate with browser-use agent's element detection
            # For now, return None as placeholder
            logger.info(f"Browser-use AI search for: {description}")
            return None
            
        except Exception as e:
            logger.error(f"Browser-use AI detection failed: {e}")
            return None
            
    async def click_element(self, selectors: List[ElementSelector], **kwargs) -> InteractionResult:
        """
        Click an element with multiple fallback strategies.
        
        Args:
            selectors: List of selectors to try
            **kwargs: Additional click options
            
        Returns:
            InteractionResult with success status and details
        """
        start_time = time.time()
        
        # Find element
        element, strategy_used = await self.find_element(selectors)
        
        if not element:
            return InteractionResult(
                success=False,
                strategy_used=None,
                element_found=False,
                action_completed=False,
                error_message="Element not found with any strategy",
                execution_time=time.time() - start_time
            )
            
        try:
            # Wait for element to be actionable
            await self._wait_for_actionable(element)
            
            # Get element info before clicking
            element_info = await self._get_element_info(element)
            
            # Perform click
            await element.click(**kwargs)
            
            # Wait for potential navigation or changes
            await asyncio.sleep(0.5)
            
            execution_time = time.time() - start_time
            self.performance_metrics['interaction_execution'].append(execution_time)
            
            # Record interaction
            self._record_interaction('click', selectors, strategy_used, True, element_info)
            
            return InteractionResult(
                success=True,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=True,
                error_message=None,
                execution_time=execution_time,
                element_info=element_info
            )
            
        except Exception as e:
            error_msg = f"Click failed: {str(e)}"
            logger.error(error_msg)
            
            self._record_interaction('click', selectors, strategy_used, False, None, error_msg)
            
            return InteractionResult(
                success=False,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=False,
                error_message=error_msg,
                execution_time=time.time() - start_time
            )
            
    async def type_text(self, selectors: List[ElementSelector], text: str, **kwargs) -> InteractionResult:
        """
        Type text into an element with multiple fallback strategies.
        
        Args:
            selectors: List of selectors to try
            text: Text to type
            **kwargs: Additional typing options
            
        Returns:
            InteractionResult with success status and details
        """
        start_time = time.time()
        
        # Find element
        element, strategy_used = await self.find_element(selectors)
        
        if not element:
            return InteractionResult(
                success=False,
                strategy_used=None,
                element_found=False,
                action_completed=False,
                error_message="Element not found with any strategy",
                execution_time=time.time() - start_time
            )
            
        try:
            # Wait for element to be editable
            await self._wait_for_condition(element, WaitCondition.EDITABLE)
            
            # Get element info
            element_info = await self._get_element_info(element)
            
            # Clear existing text if needed
            if kwargs.get('clear', True):
                await element.clear()
                
            # Type text
            await element.type(text, **{k: v for k, v in kwargs.items() if k != 'clear'})
            
            execution_time = time.time() - start_time
            self.performance_metrics['interaction_execution'].append(execution_time)
            
            # Record interaction
            self._record_interaction('type', selectors, strategy_used, True, element_info, extra_data={'text': text})
            
            return InteractionResult(
                success=True,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=True,
                error_message=None,
                execution_time=execution_time,
                element_info=element_info
            )
            
        except Exception as e:
            error_msg = f"Type failed: {str(e)}"
            logger.error(error_msg)
            
            self._record_interaction('type', selectors, strategy_used, False, None, error_msg)
            
            return InteractionResult(
                success=False,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=False,
                error_message=error_msg,
                execution_time=time.time() - start_time
            )
            
    async def select_option(self, selectors: List[ElementSelector], option: Union[str, int], **kwargs) -> InteractionResult:
        """
        Select an option from a dropdown with multiple fallback strategies.
        
        Args:
            selectors: List of selectors to try
            option: Option to select (by text, value, or index)
            **kwargs: Additional selection options
            
        Returns:
            InteractionResult with success status and details
        """
        start_time = time.time()
        
        # Find element
        element, strategy_used = await self.find_element(selectors)
        
        if not element:
            return InteractionResult(
                success=False,
                strategy_used=None,
                element_found=False,
                action_completed=False,
                error_message="Element not found with any strategy",
                execution_time=time.time() - start_time
            )
            
        try:
            # Wait for element to be actionable
            await self._wait_for_actionable(element)
            
            # Get element info
            element_info = await self._get_element_info(element)
            
            # Select option based on type
            if isinstance(option, str):
                if option.startswith('value='):
                    await element.select_option(value=option[6:])
                elif option.startswith('label='):
                    await element.select_option(label=option[6:])
                else:
                    # Try by label first, then by value
                    try:
                        await element.select_option(label=option)
                    except:
                        await element.select_option(value=option)
            elif isinstance(option, int):
                await element.select_option(index=option)
            else:
                await element.select_option(option)
                
            execution_time = time.time() - start_time
            self.performance_metrics['interaction_execution'].append(execution_time)
            
            # Record interaction
            self._record_interaction('select', selectors, strategy_used, True, element_info, extra_data={'option': option})
            
            return InteractionResult(
                success=True,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=True,
                error_message=None,
                execution_time=execution_time,
                element_info=element_info
            )
            
        except Exception as e:
            error_msg = f"Select failed: {str(e)}"
            logger.error(error_msg)
            
            self._record_interaction('select', selectors, strategy_used, False, None, error_msg)
            
            return InteractionResult(
                success=False,
                strategy_used=strategy_used,
                element_found=True,
                action_completed=False,
                error_message=error_msg,
                execution_time=time.time() - start_time
            )
            
    async def wait_for_element(self, selectors: List[ElementSelector], condition: WaitCondition = WaitCondition.VISIBLE, timeout: int = 10000) -> InteractionResult:
        """
        Wait for an element to meet a specific condition.
        
        Args:
            selectors: List of selectors to try
            condition: Wait condition to check
            timeout: Maximum wait time in milliseconds
            
        Returns:
            InteractionResult with success status and details
        """
        start_time = time.time()
        
        for selector in sorted(selectors, key=lambda x: x.confidence, reverse=True):
            try:
                element = await self._wait_for_element_condition(selector, condition, timeout)
                if element:
                    wait_time = time.time() - start_time
                    self.performance_metrics['wait_times'].append(wait_time)
                    
                    element_info = await self._get_element_info(element)
                    
                    return InteractionResult(
                        success=True,
                        strategy_used=selector.strategy,
                        element_found=True,
                        action_completed=True,
                        error_message=None,
                        execution_time=wait_time,
                        element_info=element_info
                    )
                    
            except Exception as e:
                logger.debug(f"Wait condition failed for {selector.strategy.value}: {e}")
                continue
                
        return InteractionResult(
            success=False,
            strategy_used=None,
            element_found=False,
            action_completed=False,
            error_message=f"Element did not meet condition {condition.value} within {timeout}ms",
            execution_time=time.time() - start_time
        )
        
    async def _wait_for_element_condition(self, selector: ElementSelector, condition: WaitCondition, timeout: int) -> Optional[ElementHandle]:
        """Wait for element to meet specific condition."""
        state_map = {
            WaitCondition.VISIBLE: 'visible',
            WaitCondition.ATTACHED: 'attached',
            WaitCondition.DETACHED: 'detached',
            WaitCondition.HIDDEN: 'hidden'
        }
        
        if condition in state_map:
            if selector.strategy == InteractionStrategy.CSS_SELECTOR:
                return await self.page.wait_for_selector(
                    selector.value,
                    state=state_map[condition],
                    timeout=timeout
                )
            elif selector.strategy == InteractionStrategy.XPATH:
                return await self.page.wait_for_selector(
                    f"xpath={selector.value}",
                    state=state_map[condition],
                    timeout=timeout
                )
                
        # For other conditions, find element first then check condition
        element = await self._find_element_by_strategy(selector)
        if not element:
            return None
            
        if condition == WaitCondition.ENABLED:
            await element.wait_for_element_state('enabled', timeout=timeout)
        elif condition == WaitCondition.EDITABLE:
            await element.wait_for_element_state('editable', timeout=timeout)
        elif condition == WaitCondition.STABLE:
            await element.wait_for_element_state('stable', timeout=timeout)
            
        return element
        
    async def _wait_for_actionable(self, element: ElementHandle, timeout: int = 5000) -> None:
        """Wait for element to be actionable (visible, enabled, stable)."""
        await element.wait_for_element_state('visible', timeout=timeout)
        await element.wait_for_element_state('stable', timeout=timeout)
        
    async def _wait_for_condition(self, element: ElementHandle, condition: WaitCondition, timeout: int = 5000) -> None:
        """Wait for element to meet specific condition."""
        state_map = {
            WaitCondition.VISIBLE: 'visible',
            WaitCondition.ATTACHED: 'attached',
            WaitCondition.DETACHED: 'detached',
            WaitCondition.HIDDEN: 'hidden',
            WaitCondition.ENABLED: 'enabled',
            WaitCondition.EDITABLE: 'editable',
            WaitCondition.STABLE: 'stable'
        }
        
        if condition in state_map:
            await element.wait_for_element_state(state_map[condition], timeout=timeout)
            
    async def _get_element_info(self, element: ElementHandle) -> Dict[str, Any]:
        """Get comprehensive information about an element."""
        try:
            return await element.evaluate("""
                element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        textContent: element.textContent?.trim().substring(0, 100),
                        value: element.value,
                        placeholder: element.placeholder,
                        ariaLabel: element.getAttribute('aria-label'),
                        dataTestId: element.getAttribute('data-testid'),
                        visible: rect.width > 0 && rect.height > 0,
                        position: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        },
                        attributes: Array.from(element.attributes).reduce((acc, attr) => {
                            acc[attr.name] = attr.value;
                            return acc;
                        }, {})
                    };
                }
            """)
        except Exception as e:
            logger.warning(f"Failed to get element info: {e}")
            return {'error': str(e)}
            
    def _record_interaction(self, action: str, selectors: List[ElementSelector], strategy_used: Optional[InteractionStrategy], success: bool, element_info: Optional[Dict[str, Any]], error_message: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Record interaction for analysis and debugging."""
        interaction = {
            'timestamp': time.time(),
            'action': action,
            'selectors': [{'strategy': s.strategy.value, 'value': s.value, 'confidence': s.confidence} for s in selectors],
            'strategy_used': strategy_used.value if strategy_used else None,
            'success': success,
            'element_info': element_info,
            'error_message': error_message,
            'extra_data': extra_data or {}
        }
        
        self.interaction_history.append(interaction)
        
        # Log interaction
        if success:
            logger.info(f"✅ {action.upper()} successful using {strategy_used.value if strategy_used else 'unknown'}")
        else:
            logger.warning(f"❌ {action.upper()} failed: {error_message}")
            
    def generate_smart_selectors(self, description: str) -> List[ElementSelector]:
        """
        Generate smart selectors based on element description.
        
        Args:
            description: Natural language description of the element
            
        Returns:
            List of ElementSelector objects ordered by confidence
        """
        selectors = []
        desc_lower = description.lower()
        
        # Extract potential identifiers from description
        words = re.findall(r'\b\w+\b', desc_lower)
        
        # Button-specific selectors
        if any(word in desc_lower for word in ['button', 'click', 'submit', 'save', 'cancel']):
            # Try button with text content
            for word in words:
                if len(word) > 2:
                    selectors.append(ElementSelector(
                        strategy=InteractionStrategy.TEXT_CONTENT,
                        value=word,
                        description=f"Button with text '{word}'",
                        confidence=0.8
                    ))
                    
            # Try button tag with text
            selectors.append(ElementSelector(
                strategy=InteractionStrategy.CSS_SELECTOR,
                value="button",
                description="Any button element",
                confidence=0.6
            ))
            
        # Input field selectors
        if any(word in desc_lower for word in ['input', 'field', 'textbox', 'enter', 'type']):
            # Try by placeholder
            for word in words:
                if len(word) > 2:
                    selectors.append(ElementSelector(
                        strategy=InteractionStrategy.PLACEHOLDER,
                        value=word,
                        description=f"Input with placeholder containing '{word}'",
                        confidence=0.8
                    ))
                    
            # Try by aria-label
            for word in words:
                if len(word) > 2:
                    selectors.append(ElementSelector(
                        strategy=InteractionStrategy.ARIA_LABEL,
                        value=word,
                        description=f"Input with aria-label containing '{word}'",
                        confidence=0.7
                    ))
                    
        # Link selectors
        if any(word in desc_lower for word in ['link', 'navigate', 'go to']):
            for word in words:
                if len(word) > 2:
                    selectors.append(ElementSelector(
                        strategy=InteractionStrategy.TEXT_CONTENT,
                        value=word,
                        description=f"Link with text '{word}'",
                        confidence=0.8
                    ))
                    
        # Generic selectors based on common patterns
        for word in words:
            if len(word) > 3:
                # Try data-testid
                selectors.append(ElementSelector(
                    strategy=InteractionStrategy.DATA_TESTID,
                    value=word,
                    description=f"Element with data-testid '{word}'",
                    confidence=0.9
                ))
                
                # Try ID
                selectors.append(ElementSelector(
                    strategy=InteractionStrategy.CSS_SELECTOR,
                    value=f"#{word}",
                    description=f"Element with ID '{word}'",
                    confidence=0.8
                ))
                
                # Try class
                selectors.append(ElementSelector(
                    strategy=InteractionStrategy.CSS_SELECTOR,
                    value=f".{word}",
                    description=f"Element with class '{word}'",
                    confidence=0.6
                ))
                
        # Add browser-use AI as fallback
        selectors.append(ElementSelector(
            strategy=InteractionStrategy.BROWSER_USE_AI,
            value=description,
            description=f"AI-powered detection: {description}",
            confidence=0.5
        ))
        
        return sorted(selectors, key=lambda x: x.confidence, reverse=True)
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of UI interactions."""
        summary = {
            'total_interactions': len(self.interaction_history),
            'successful_interactions': len([i for i in self.interaction_history if i['success']]),
            'failed_interactions': len([i for i in self.interaction_history if not i['success']]),
            'success_rate': 0.0,
            'average_execution_time': 0.0,
            'strategy_usage': {},
            'common_failures': []
        }
        
        if self.interaction_history:
            summary['success_rate'] = summary['successful_interactions'] / summary['total_interactions']
            
            # Calculate average execution time
            if self.performance_metrics['interaction_execution']:
                summary['average_execution_time'] = sum(self.performance_metrics['interaction_execution']) / len(self.performance_metrics['interaction_execution'])
                
            # Strategy usage statistics
            for interaction in self.interaction_history:
                strategy = interaction.get('strategy_used')
                if strategy:
                    summary['strategy_usage'][strategy] = summary['strategy_usage'].get(strategy, 0) + 1
                    
            # Common failure patterns
            failures = [i for i in self.interaction_history if not i['success']]
            failure_messages = [f['error_message'] for f in failures if f.get('error_message')]
            summary['common_failures'] = list(set(failure_messages))[:5]  # Top 5 unique failures
            
        return summary
        
    def export_interaction_log(self) -> List[Dict[str, Any]]:
        """Export detailed interaction log for analysis."""
        return self.interaction_history.copy()

