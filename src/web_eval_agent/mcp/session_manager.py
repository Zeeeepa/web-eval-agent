#!/usr/bin/env python3

"""
Session manager for handling concurrent web evaluation sessions.
Provides session isolation, resource management, and GitHub PR integration.
"""

import asyncio
import uuid
import time
from typing import Dict, Optional, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import weakref
from concurrent.futures import ThreadPoolExecutor
import threading

from .logging_config import StructuredLogger, LogContext, create_session_context, get_logger
from .browser_pool import BrowserPool, BrowserInstance


class SessionStatus(Enum):
    """Session status enumeration."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SessionConfig:
    """Configuration for an evaluation session."""
    url: str
    task: str
    headless: bool = True
    timeout: int = 300  # 5 minutes default
    max_retries: int = 3
    github_repo: Optional[str] = None
    github_pr: Optional[int] = None
    github_branch: Optional[str] = None
    user_id: Optional[str] = None
    api_key: str = ""
    
    def to_log_context(self, session_id: str) -> LogContext:
        """Convert to logging context."""
        return LogContext(
            session_id=session_id,
            github_repo=self.github_repo,
            github_pr=self.github_pr,
            github_branch=self.github_branch,
            url=self.url,
            task=self.task,
            user_id=self.user_id
        )


@dataclass
class SessionResult:
    """Result of an evaluation session."""
    session_id: str
    status: SessionStatus
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    
    def finish(self, success: bool, result: Optional[Any] = None, error: Optional[str] = None):
        """Mark the session as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.result = result
        self.error = error
        self.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED


class EvaluationSession:
    """
    Represents a single web evaluation session with its own browser instance and context.
    """
    
    def __init__(self, session_id: str, config: SessionConfig, logger: StructuredLogger):
        self.session_id = session_id
        self.config = config
        self.logger = logger
        self.status = SessionStatus.PENDING
        self.browser_instance: Optional[BrowserInstance] = None
        self.task: Optional[asyncio.Task] = None
        self.result = SessionResult(session_id=session_id, status=SessionStatus.PENDING)
        self.cancel_event = asyncio.Event()
        self._lock = asyncio.Lock()
        
        # Set up logging context
        self.log_context = config.to_log_context(session_id)
        self.logger.set_context(self.log_context)
    
    async def initialize(self, browser_pool: BrowserPool):
        """Initialize the session with a browser instance."""
        async with self._lock:
            if self.status != SessionStatus.PENDING:
                raise RuntimeError(f"Session {self.session_id} is not in pending state")
            
            self.status = SessionStatus.INITIALIZING
            self.logger.info(f"Initializing session {self.session_id}")
            
            try:
                # Get browser instance from pool
                self.browser_instance = await browser_pool.acquire(
                    headless=self.config.headless,
                    timeout=30
                )
                self.logger.info(f"Browser instance acquired for session {self.session_id}")
                
                self.status = SessionStatus.RUNNING
                self.logger.info(f"Session {self.session_id} initialized successfully")
                
            except Exception as e:
                self.status = SessionStatus.FAILED
                self.result.finish(False, error=str(e))
                self.logger.error(f"Failed to initialize session {self.session_id}", error=e)
                raise
    
    async def run_evaluation(self, evaluation_func: Callable[[Any, SessionConfig], Awaitable[Any]]):
        """Run the evaluation function with this session's browser."""
        if self.status != SessionStatus.RUNNING:
            raise RuntimeError(f"Session {self.session_id} is not in running state")
        
        if not self.browser_instance:
            raise RuntimeError(f"Session {self.session_id} has no browser instance")
        
        try:
            self.logger.log_evaluation_start(self.config.url, self.config.task)
            
            # Run evaluation with timeout
            result = await asyncio.wait_for(
                evaluation_func(self.browser_instance, self.config),
                timeout=self.config.timeout
            )
            
            self.result.finish(True, result=result)
            self.logger.log_evaluation_end(True, summary="Evaluation completed successfully")
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Session {self.session_id} timed out after {self.config.timeout} seconds"
            self.result.finish(False, error=error_msg)
            self.logger.error(error_msg)
            raise
            
        except Exception as e:
            error_msg = f"Session {self.session_id} failed: {str(e)}"
            self.result.finish(False, error=error_msg)
            self.logger.error(error_msg, error=e)
            raise
    
    async def cleanup(self, browser_pool: BrowserPool):
        """Clean up session resources."""
        async with self._lock:
            self.logger.info(f"Cleaning up session {self.session_id}")
            
            # Cancel task if running
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            # Return browser instance to pool
            if self.browser_instance:
                await browser_pool.release(self.browser_instance)
                self.browser_instance = None
            
            # Update status if not already finished
            if self.status == SessionStatus.RUNNING:
                self.status = SessionStatus.CANCELLED
                self.result.status = SessionStatus.CANCELLED
            
            self.logger.info(f"Session {self.session_id} cleaned up")
    
    def cancel(self):
        """Cancel the session."""
        self.cancel_event.set()
        if self.task and not self.task.done():
            self.task.cancel()


class SessionManager:
    """
    Manages multiple concurrent web evaluation sessions.
    Provides session isolation, resource pooling, and lifecycle management.
    """
    
    def __init__(self, max_concurrent_sessions: int = 5, browser_pool_size: int = 10):
        self.max_concurrent_sessions = max_concurrent_sessions
        self.browser_pool = BrowserPool(max_size=browser_pool_size)
        self.sessions: Dict[str, EvaluationSession] = {}
        self.active_sessions: Dict[str, EvaluationSession] = {}
        self.session_queue: asyncio.Queue = asyncio.Queue()
        self.logger = get_logger("session-manager")
        self._lock = asyncio.Lock()
        self._shutdown = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Start session worker
        self._start_worker()
    
    def _start_worker(self):
        """Start the session worker task."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._session_worker())
    
    async def _session_worker(self):
        """Worker task that processes queued sessions."""
        while not self._shutdown:
            try:
                # Wait for available slot
                while len(self.active_sessions) >= self.max_concurrent_sessions:
                    await asyncio.sleep(0.1)
                
                # Get next session from queue
                try:
                    session = await asyncio.wait_for(self.session_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Start session
                await self._start_session(session)
                
            except Exception as e:
                self.logger.error("Session worker error", error=e)
                await asyncio.sleep(1.0)
    
    async def _start_session(self, session: EvaluationSession):
        """Start a session execution."""
        try:
            async with self._lock:
                self.active_sessions[session.session_id] = session
            
            # Initialize session
            await session.initialize(self.browser_pool)
            
            self.logger.info(f"Session {session.session_id} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start session {session.session_id}", error=e)
            await self._cleanup_session(session.session_id)
    
    async def _cleanup_session(self, session_id: str):
        """Clean up a session and remove it from active sessions."""
        async with self._lock:
            session = self.active_sessions.pop(session_id, None)
            if session:
                await session.cleanup(self.browser_pool)
                self.logger.info(f"Session {session_id} removed from active sessions")
    
    async def create_session(self, config: SessionConfig) -> str:
        """Create a new evaluation session."""
        session_id = str(uuid.uuid4())
        
        # Create session logger with context
        session_logger = StructuredLogger(f"session-{session_id}")
        
        # Create session
        session = EvaluationSession(session_id, config, session_logger)
        
        async with self._lock:
            self.sessions[session_id] = session
        
        # Add to queue for processing
        await self.session_queue.put(session)
        
        self.logger.info(f"Session {session_id} created and queued", 
                        github_repo=config.github_repo,
                        github_pr=config.github_pr,
                        url=config.url)
        
        return session_id
    
    async def run_evaluation(self, session_id: str, 
                           evaluation_func: Callable[[Any, SessionConfig], Awaitable[Any]]) -> Any:
        """Run evaluation for a specific session."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Wait for session to be initialized
        while session.status == SessionStatus.PENDING:
            await asyncio.sleep(0.1)
        
        if session.status != SessionStatus.RUNNING:
            raise RuntimeError(f"Session {session_id} is not running (status: {session.status})")
        
        try:
            result = await session.run_evaluation(evaluation_func)
            return result
        finally:
            # Clean up session after evaluation
            await self._cleanup_session(session_id)
    
    async def get_session_status(self, session_id: str) -> Optional[SessionStatus]:
        """Get the status of a session."""
        session = self.sessions.get(session_id)
        return session.status if session else None
    
    async def get_session_result(self, session_id: str) -> Optional[SessionResult]:
        """Get the result of a session."""
        session = self.sessions.get(session_id)
        return session.result if session else None
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancel a session."""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.cancel()
        await self._cleanup_session(session_id)
        
        self.logger.info(f"Session {session_id} cancelled")
        return True
    
    async def list_active_sessions(self) -> List[str]:
        """List all active session IDs."""
        async with self._lock:
            return list(self.active_sessions.keys())
    
    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session manager metrics."""
        async with self._lock:
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": len(self.active_sessions),
                "queued_sessions": self.session_queue.qsize(),
                "max_concurrent": self.max_concurrent_sessions,
                "browser_pool_size": self.browser_pool.max_size,
                "browser_pool_active": len(self.browser_pool.active_instances),
                "browser_pool_available": len(self.browser_pool.available_instances)
            }
    
    @asynccontextmanager
    async def evaluation_session(self, config: SessionConfig):
        """Context manager for creating and managing an evaluation session."""
        session_id = await self.create_session(config)
        try:
            # Wait for session to be ready
            while True:
                status = await self.get_session_status(session_id)
                if status == SessionStatus.RUNNING:
                    break
                elif status in [SessionStatus.FAILED, SessionStatus.CANCELLED]:
                    raise RuntimeError(f"Session {session_id} failed to initialize")
                await asyncio.sleep(0.1)
            
            yield session_id
        finally:
            await self.cancel_session(session_id)
    
    async def shutdown(self):
        """Shutdown the session manager and clean up all resources."""
        self.logger.info("Shutting down session manager")
        self._shutdown = True
        
        # Cancel worker task
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active sessions
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.cancel_session(session_id)
        
        # Shutdown browser pool
        await self.browser_pool.shutdown()
        
        self.logger.info("Session manager shutdown complete")


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager(max_concurrent_sessions: int = 5, 
                       browser_pool_size: int = 10) -> SessionManager:
    """Get or create global session manager instance."""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager(
            max_concurrent_sessions=max_concurrent_sessions,
            browser_pool_size=browser_pool_size
        )
    return _global_session_manager


async def shutdown_session_manager():
    """Shutdown the global session manager."""
    global _global_session_manager
    if _global_session_manager:
        await _global_session_manager.shutdown()
        _global_session_manager = None

