"""
Intelligent Agent Orchestration System
Coordinates multiple agents for optimal testing coverage and efficiency.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.coverage_analyzer import CoverageMap, InteractiveElement, UserFlow


class AgentStatus(Enum):
    """Status of an agent in the system."""
    IDLE = "idle"
    BUSY = "busy"
    COMPLETED = "completed"
    FAILED = "failed"
    INITIALIZING = "initializing"


class TaskPriority(Enum):
    """Priority levels for testing tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestTask:
    """Represents a testing task to be executed by an agent."""
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    elements: List[str]  # Element selectors
    expected_duration: float
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    assigned_agent: Optional[str] = None
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class AgentInfo:
    """Information about an agent in the system."""
    agent_id: str
    status: AgentStatus
    capabilities: List[str]
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    performance_score: float = 100.0
    last_activity: float = field(default_factory=time.time)
    resource_usage: Dict[str, float] = field(default_factory=dict)


class IntelligentAgentCoordinator:
    """
    Intelligent agent coordinator that optimally distributes testing tasks
    among multiple agents for maximum efficiency and coverage.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Agent management
        self.agents: Dict[str, AgentInfo] = {}
        self.task_queue: List[TestTask] = []
        self.completed_tasks: List[TestTask] = []
        self.failed_tasks: List[TestTask] = []
        
        # Coordination state
        self.is_running = False
        self.coordination_lock = threading.Lock()
        self.task_assignment_history: Dict[str, List[str]] = {}
        
        # Performance tracking
        self.performance_metrics: Dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_task_duration": 0.0,
            "agent_utilization": {},
            "task_distribution": {}
        }
        
    async def initialize_coordination(self, num_agents: int, coverage_map: CoverageMap) -> None:
        """
        Initialize the coordination system with agents and coverage analysis.
        
        Args:
            num_agents: Number of agents to coordinate
            coverage_map: Comprehensive coverage analysis results
        """
        self.logger.info(f"🤖 Initializing intelligent agent coordination with {num_agents} agents")
        
        try:
            # Initialize agents
            await self._initialize_agents(num_agents)
            
            # Generate optimized task distribution
            tasks = await self._generate_optimal_tasks(coverage_map)
            self.task_queue.extend(tasks)
            
            # Start coordination loop
            self.is_running = True
            
            self.logger.info(f"✅ Agent coordination initialized with {len(tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize coordination: {e}")
            raise
    
    async def _initialize_agents(self, num_agents: int) -> None:
        """Initialize the specified number of agents."""
        for i in range(num_agents):
            agent_id = f"agent_{i+1}"
            
            # Determine agent capabilities based on specialization
            capabilities = self._determine_agent_capabilities(i, num_agents)
            
            agent_info = AgentInfo(
                agent_id=agent_id,
                status=AgentStatus.IDLE,
                capabilities=capabilities,
                performance_score=100.0,
                resource_usage={"cpu": 0.0, "memory": 0.0, "network": 0.0}
            )
            
            self.agents[agent_id] = agent_info
            self.task_assignment_history[agent_id] = []
            
        self.logger.info(f"🎯 Initialized {len(self.agents)} specialized agents")
    
    def _determine_agent_capabilities(self, agent_index: int, total_agents: int) -> List[str]:
        """Determine specialized capabilities for each agent."""
        base_capabilities = ["navigation", "interaction", "validation"]
        
        # Assign specializations based on agent index
        specializations = {
            0: ["forms", "input_validation", "accessibility"],
            1: ["navigation", "links", "performance"],
            2: ["ui_components", "visual_testing", "responsive"],
            3: ["security", "error_handling", "edge_cases"],
            4: ["integration", "workflows", "end_to_end"]
        }
        
        agent_specialization = specializations.get(agent_index % 5, ["general"])
        return base_capabilities + agent_specialization
    
    async def _generate_optimal_tasks(self, coverage_map: CoverageMap) -> List[TestTask]:
        """Generate optimized testing tasks based on coverage analysis."""
        tasks = []
        task_counter = 0
        
        try:
            # Generate tasks for interactive elements
            element_tasks = await self._create_element_tasks(coverage_map.elements, task_counter)
            tasks.extend(element_tasks)
            task_counter += len(element_tasks)
            
            # Generate tasks for user flows
            flow_tasks = await self._create_flow_tasks(coverage_map.user_flows, task_counter)
            tasks.extend(flow_tasks)
            task_counter += len(flow_tasks)
            
            # Generate specialized tasks
            specialized_tasks = await self._create_specialized_tasks(coverage_map, task_counter)
            tasks.extend(specialized_tasks)
            
            # Optimize task order and dependencies
            optimized_tasks = await self._optimize_task_order(tasks)
            
            self.logger.info(f"📋 Generated {len(optimized_tasks)} optimized testing tasks")
            return optimized_tasks
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate tasks: {e}")
            return []
    
    async def _create_element_tasks(self, elements: List[InteractiveElement], start_id: int) -> List[TestTask]:
        """Create testing tasks for individual interactive elements."""
        tasks = []
        
        for i, element in enumerate(elements):
            # Determine task priority based on element importance
            priority = self._calculate_element_priority(element)
            
            # Estimate task duration based on element complexity
            duration = self._estimate_task_duration(element)
            
            task = TestTask(
                task_id=f"element_task_{start_id + i}",
                task_type="element_interaction",
                description=f"Test {element.element_type.value} element: {element.text_content[:50]}",
                priority=priority,
                elements=[element.selector],
                expected_duration=duration,
                dependencies=[]
            )
            
            tasks.append(task)
        
        return tasks
    
    async def _create_flow_tasks(self, user_flows: List[UserFlow], start_id: int) -> List[TestTask]:
        """Create testing tasks for user flows."""
        tasks = []
        
        for i, flow in enumerate(user_flows):
            # User flows are typically high priority
            priority = TaskPriority.HIGH if flow.business_value_score > 7.0 else TaskPriority.MEDIUM
            
            # Estimate duration based on flow complexity
            duration = flow.complexity_score * 10  # Base estimation
            
            task = TestTask(
                task_id=f"flow_task_{start_id + i}",
                task_type="user_flow",
                description=f"Execute user flow: {flow.name}",
                priority=priority,
                elements=flow.entry_points,
                expected_duration=duration,
                dependencies=[]
            )
            
            tasks.append(task)
        
        return tasks
    
    async def _create_specialized_tasks(self, coverage_map: CoverageMap, start_id: int) -> List[TestTask]:
        """Create specialized testing tasks."""
        tasks = []
        
        # Performance testing task
        if coverage_map.performance_metrics:
            tasks.append(TestTask(
                task_id=f"perf_task_{start_id}",
                task_type="performance_testing",
                description="Comprehensive performance analysis",
                priority=TaskPriority.HIGH,
                elements=[],
                expected_duration=30.0
            ))
        
        # Accessibility testing task
        if coverage_map.accessibility_tree:
            tasks.append(TestTask(
                task_id=f"a11y_task_{start_id + 1}",
                task_type="accessibility_testing",
                description="Comprehensive accessibility audit",
                priority=TaskPriority.HIGH,
                elements=[],
                expected_duration=25.0
            ))
        
        # Security testing task
        tasks.append(TestTask(
            task_id=f"security_task_{start_id + 2}",
            task_type="security_testing",
            description="Security vulnerability assessment",
            priority=TaskPriority.MEDIUM,
            elements=[],
            expected_duration=20.0
        ))
        
        return tasks
    
    def _calculate_element_priority(self, element: InteractiveElement) -> TaskPriority:
        """Calculate priority for an element based on its characteristics."""
        score = element.priority_score
        
        if score >= 9.0:
            return TaskPriority.CRITICAL
        elif score >= 7.0:
            return TaskPriority.HIGH
        elif score >= 5.0:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _estimate_task_duration(self, element: InteractiveElement) -> float:
        """Estimate task duration based on element complexity."""
        base_duration = 5.0  # Base 5 seconds
        
        # Adjust based on element type
        type_multipliers = {
            "form": 3.0,
            "input": 2.0,
            "button": 1.0,
            "link": 1.0,
            "dropdown": 2.5,
            "modal": 2.0
        }
        
        multiplier = type_multipliers.get(element.element_type.value, 1.0)
        return base_duration * multiplier
    
    async def _optimize_task_order(self, tasks: List[TestTask]) -> List[TestTask]:
        """Optimize task order for maximum efficiency."""
        # Sort by priority first, then by estimated duration
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        optimized_tasks = sorted(tasks, key=lambda t: (
            priority_order[t.priority],
            t.expected_duration
        ))
        
        return optimized_tasks
    
    async def coordinate_testing(self) -> Dict[str, Any]:
        """
        Main coordination loop that manages task distribution and execution.
        
        Returns:
            Dict containing coordination results and metrics
        """
        self.logger.info("🚀 Starting intelligent agent coordination")
        
        coordination_start = time.time()
        
        try:
            # Start coordination tasks
            coordination_tasks = [
                asyncio.create_task(self._task_distribution_loop()),
                asyncio.create_task(self._performance_monitoring_loop()),
                asyncio.create_task(self._health_check_loop())
            ]
            
            # Wait for all tasks to complete or timeout
            timeout = self.config.get('coordination_timeout', 300)  # 5 minutes default
            
            await asyncio.wait_for(
                asyncio.gather(*coordination_tasks, return_exceptions=True),
                timeout=timeout
            )
            
            coordination_time = time.time() - coordination_start
            
            # Generate final results
            results = await self._generate_coordination_results(coordination_time)
            
            self.logger.info(f"✅ Agent coordination completed in {coordination_time:.2f}s")
            return results
            
        except asyncio.TimeoutError:
            self.logger.warning("⏰ Coordination timeout reached")
            return await self._generate_coordination_results(time.time() - coordination_start)
            
        except Exception as e:
            self.logger.error(f"❌ Coordination failed: {e}")
            raise
        
        finally:
            self.is_running = False
    
    async def _task_distribution_loop(self) -> None:
        """Main task distribution loop."""
        while self.is_running and (self.task_queue or self._has_active_agents()):
            try:
                # Find available agents
                available_agents = [
                    agent_id for agent_id, agent in self.agents.items()
                    if agent.status == AgentStatus.IDLE
                ]
                
                if available_agents and self.task_queue:
                    # Assign tasks to available agents
                    await self._assign_optimal_tasks(available_agents)
                
                # Check for completed tasks
                await self._process_completed_tasks()
                
                # Brief pause to prevent busy waiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"❌ Error in task distribution loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _assign_optimal_tasks(self, available_agents: List[str]) -> None:
        """Assign optimal tasks to available agents."""
        with self.coordination_lock:
            for agent_id in available_agents:
                if not self.task_queue:
                    break
                
                agent = self.agents[agent_id]
                
                # Find the best task for this agent
                best_task = self._find_best_task_for_agent(agent)
                
                if best_task:
                    # Assign task to agent
                    self.task_queue.remove(best_task)
                    best_task.assigned_agent = agent_id
                    best_task.start_time = time.time()
                    
                    agent.status = AgentStatus.BUSY
                    agent.current_task = best_task.task_id
                    agent.last_activity = time.time()
                    
                    self.task_assignment_history[agent_id].append(best_task.task_id)
                    
                    self.logger.info(f"📋 Assigned task {best_task.task_id} to {agent_id}")
                    
                    # Start task execution (simulated)
                    asyncio.create_task(self._execute_task(agent_id, best_task))
    
    def _find_best_task_for_agent(self, agent: AgentInfo) -> Optional[TestTask]:
        """Find the best task for a specific agent based on capabilities and performance."""
        if not self.task_queue:
            return None
        
        # Score tasks based on agent capabilities and task requirements
        scored_tasks = []
        
        for task in self.task_queue:
            score = self._calculate_task_agent_score(task, agent)
            scored_tasks.append((score, task))
        
        # Sort by score (highest first) and return the best match
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return scored_tasks[0][1] if scored_tasks else None
    
    def _calculate_task_agent_score(self, task: TestTask, agent: AgentInfo) -> float:
        """Calculate compatibility score between a task and an agent."""
        base_score = 50.0
        
        # Priority bonus
        priority_bonus = {
            TaskPriority.CRITICAL: 20.0,
            TaskPriority.HIGH: 15.0,
            TaskPriority.MEDIUM: 10.0,
            TaskPriority.LOW: 5.0
        }
        base_score += priority_bonus[task.priority]
        
        # Capability matching
        task_type_capabilities = {
            "element_interaction": ["interaction", "navigation"],
            "user_flow": ["workflows", "integration"],
            "performance_testing": ["performance"],
            "accessibility_testing": ["accessibility"],
            "security_testing": ["security"]
        }
        
        required_capabilities = task_type_capabilities.get(task.task_type, [])
        capability_matches = sum(1 for cap in required_capabilities if cap in agent.capabilities)
        base_score += capability_matches * 10.0
        
        # Performance factor
        base_score *= (agent.performance_score / 100.0)
        
        return base_score
    
    async def _execute_task(self, agent_id: str, task: TestTask) -> None:
        """Execute a task (simulated execution for now)."""
        try:
            # Simulate task execution time
            await asyncio.sleep(min(task.expected_duration, 10.0))  # Cap at 10 seconds for simulation
            
            # Simulate task completion
            task.completion_time = time.time()
            task.result = {
                "status": "completed",
                "duration": task.completion_time - task.start_time,
                "findings": f"Task {task.task_id} completed successfully",
                "agent_id": agent_id
            }
            
            # Update agent status
            agent = self.agents[agent_id]
            agent.status = AgentStatus.COMPLETED
            agent.current_task = None
            agent.completed_tasks.append(task.task_id)
            agent.last_activity = time.time()
            
            # Move task to completed
            self.completed_tasks.append(task)
            
            self.logger.info(f"✅ Task {task.task_id} completed by {agent_id}")
            
        except Exception as e:
            # Handle task failure
            task.error_message = str(e)
            task.retry_count += 1
            
            agent = self.agents[agent_id]
            agent.status = AgentStatus.FAILED
            agent.current_task = None
            agent.failed_tasks.append(task.task_id)
            
            if task.retry_count < task.max_retries:
                # Retry the task
                self.task_queue.append(task)
                self.logger.warning(f"⚠️ Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                # Task failed permanently
                self.failed_tasks.append(task)
                self.logger.error(f"❌ Task {task.task_id} failed permanently: {e}")
    
    async def _process_completed_tasks(self) -> None:
        """Process completed tasks and update agent statuses."""
        for agent_id, agent in self.agents.items():
            if agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                # Reset agent to idle for next task
                agent.status = AgentStatus.IDLE
    
    def _has_active_agents(self) -> bool:
        """Check if there are any active agents."""
        return any(agent.status == AgentStatus.BUSY for agent in self.agents.values())
    
    async def _performance_monitoring_loop(self) -> None:
        """Monitor agent performance and system metrics."""
        while self.is_running:
            try:
                # Update performance metrics
                self._update_performance_metrics()
                
                # Adjust agent performance scores based on recent activity
                self._adjust_agent_performance_scores()
                
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error in performance monitoring: {e}")
                await asyncio.sleep(5.0)
    
    async def _health_check_loop(self) -> None:
        """Monitor agent health and handle failures."""
        while self.is_running:
            try:
                current_time = time.time()
                
                for agent_id, agent in self.agents.items():
                    # Check for stuck agents
                    if agent.status == AgentStatus.BUSY:
                        time_since_activity = current_time - agent.last_activity
                        if time_since_activity > 60.0:  # 1 minute timeout
                            self.logger.warning(f"⚠️ Agent {agent_id} appears stuck, resetting")
                            agent.status = AgentStatus.IDLE
                            agent.current_task = None
                            agent.performance_score *= 0.9  # Reduce performance score
                
                await asyncio.sleep(10.0)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error in health check: {e}")
                await asyncio.sleep(10.0)
    
    def _update_performance_metrics(self) -> None:
        """Update overall performance metrics."""
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks)
        
        self.performance_metrics.update({
            "total_tasks": total_tasks,
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "success_rate": len(self.completed_tasks) / max(total_tasks, 1) * 100,
            "agent_utilization": {
                agent_id: len(agent.completed_tasks) / max(total_tasks, 1) * 100
                for agent_id, agent in self.agents.items()
            }
        })
        
        # Calculate average task duration
        if self.completed_tasks:
            total_duration = sum(
                task.completion_time - task.start_time 
                for task in self.completed_tasks 
                if task.start_time and task.completion_time
            )
            self.performance_metrics["average_task_duration"] = total_duration / len(self.completed_tasks)
    
    def _adjust_agent_performance_scores(self) -> None:
        """Adjust agent performance scores based on recent performance."""
        for agent_id, agent in self.agents.items():
            # Calculate success rate for this agent
            total_agent_tasks = len(agent.completed_tasks) + len(agent.failed_tasks)
            if total_agent_tasks > 0:
                success_rate = len(agent.completed_tasks) / total_agent_tasks
                
                # Adjust performance score
                if success_rate > 0.9:
                    agent.performance_score = min(100.0, agent.performance_score + 1.0)
                elif success_rate < 0.7:
                    agent.performance_score = max(50.0, agent.performance_score - 2.0)
    
    async def _generate_coordination_results(self, coordination_time: float) -> Dict[str, Any]:
        """Generate comprehensive coordination results."""
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks) + len(self.task_queue)
        
        results = {
            "coordination_summary": {
                "total_coordination_time": coordination_time,
                "total_tasks_generated": total_tasks,
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks),
                "remaining_tasks": len(self.task_queue),
                "success_rate": len(self.completed_tasks) / max(total_tasks, 1) * 100
            },
            "agent_performance": {
                agent_id: {
                    "completed_tasks": len(agent.completed_tasks),
                    "failed_tasks": len(agent.failed_tasks),
                    "performance_score": agent.performance_score,
                    "capabilities": agent.capabilities,
                    "final_status": agent.status.value
                }
                for agent_id, agent in self.agents.items()
            },
            "task_breakdown": {
                "by_type": self._get_task_breakdown_by_type(),
                "by_priority": self._get_task_breakdown_by_priority(),
                "by_status": {
                    "completed": len(self.completed_tasks),
                    "failed": len(self.failed_tasks),
                    "pending": len(self.task_queue)
                }
            },
            "performance_metrics": self.performance_metrics,
            "recommendations": self._generate_recommendations()
        }
        
        return results
    
    def _get_task_breakdown_by_type(self) -> Dict[str, int]:
        """Get task breakdown by type."""
        all_tasks = self.completed_tasks + self.failed_tasks + self.task_queue
        breakdown = {}
        
        for task in all_tasks:
            task_type = task.task_type
            breakdown[task_type] = breakdown.get(task_type, 0) + 1
        
        return breakdown
    
    def _get_task_breakdown_by_priority(self) -> Dict[str, int]:
        """Get task breakdown by priority."""
        all_tasks = self.completed_tasks + self.failed_tasks + self.task_queue
        breakdown = {}
        
        for task in all_tasks:
            priority = task.priority.value
            breakdown[priority] = breakdown.get(priority, 0) + 1
        
        return breakdown
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on coordination results."""
        recommendations = []
        
        # Performance recommendations
        success_rate = self.performance_metrics.get("success_rate", 0)
        if success_rate < 80:
            recommendations.append("Consider increasing task timeout or reducing task complexity")
        
        # Agent utilization recommendations
        agent_utilization = self.performance_metrics.get("agent_utilization", {})
        if agent_utilization:
            max_utilization = max(agent_utilization.values())
            min_utilization = min(agent_utilization.values())
            
            if max_utilization - min_utilization > 30:
                recommendations.append("Consider rebalancing task distribution among agents")
        
        # Task failure recommendations
        if len(self.failed_tasks) > len(self.completed_tasks) * 0.2:
            recommendations.append("High task failure rate detected - review task complexity and agent capabilities")
        
        return recommendations
