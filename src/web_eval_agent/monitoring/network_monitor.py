"""
Network Monitor

Advanced network monitoring with request/response analysis, timing metrics,
and performance insights.
"""

import time
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetworkTiming:
    """Detailed network timing information."""
    dns_lookup: Optional[float] = None
    tcp_connect: Optional[float] = None
    tls_handshake: Optional[float] = None
    request_sent: Optional[float] = None
    waiting: Optional[float] = None
    content_download: Optional[float] = None
    total_time: Optional[float] = None


@dataclass
class NetworkRequest:
    """Comprehensive network request information."""
    url: str
    method: str
    headers: Dict[str, str]
    timestamp: float
    request_id: str
    resource_type: str
    initiator: Optional[Dict[str, Any]] = None
    post_data: Optional[str] = None
    
    # Response data
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    response_timestamp: Optional[float] = None
    
    # Timing and performance
    timing: Optional[NetworkTiming] = None
    size: Optional[int] = None
    compressed_size: Optional[int] = None
    
    # Analysis
    error: Optional[str] = None
    blocked_reason: Optional[str] = None
    cache_hit: bool = False
    from_service_worker: bool = False
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate request duration."""
        if self.response_timestamp and self.timestamp:
            return self.response_timestamp - self.timestamp
        return None
        
    @property
    def domain(self) -> str:
        """Extract domain from URL."""
        return urlparse(self.url).netloc
        
    @property
    def is_successful(self) -> bool:
        """Check if request was successful."""
        return self.response_status is not None and 200 <= self.response_status < 400
        
    @property
    def is_error(self) -> bool:
        """Check if request resulted in error."""
        return self.error is not None or (self.response_status is not None and self.response_status >= 400)


@dataclass
class NetworkAnalysis:
    """Network monitoring analysis results."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    blocked_requests: int
    cached_requests: int
    
    # Performance metrics
    average_response_time: float
    slowest_requests: List[Dict[str, Any]]
    fastest_requests: List[Dict[str, Any]]
    
    # Resource analysis
    resource_types: Dict[str, int]
    domains: Dict[str, int]
    status_codes: Dict[int, int]
    
    # Size analysis
    total_bytes_transferred: int
    total_bytes_compressed: int
    compression_ratio: float
    
    # Issues and recommendations
    issues: List[str]
    recommendations: List[str]
    performance_score: float


class NetworkMonitor:
    """
    Advanced network monitoring with comprehensive request/response analysis,
    performance metrics, and actionable insights.
    """
    
    def __init__(self):
        self.requests: List[NetworkRequest] = []
        self.pending_requests: Dict[str, NetworkRequest] = {}
        self.start_time = time.time()
        self.domains_seen: Set[str] = set()
        self.resource_types_seen: Set[str] = set()
        
    def add_request(self, request_data: Dict[str, Any]) -> str:
        """Add a new network request for monitoring."""
        request_id = request_data.get('request_id', str(time.time()))
        
        network_request = NetworkRequest(
            url=request_data['url'],
            method=request_data['method'],
            headers=request_data.get('headers', {}),
            timestamp=time.time(),
            request_id=request_id,
            resource_type=request_data.get('resource_type', 'other'),
            initiator=request_data.get('initiator'),
            post_data=request_data.get('post_data')
        )
        
        self.pending_requests[request_id] = network_request
        self.domains_seen.add(network_request.domain)
        self.resource_types_seen.add(network_request.resource_type)
        
        logger.debug(f"Added network request: {network_request.method} {network_request.url}")
        return request_id
        
    def add_response(self, request_id: str, response_data: Dict[str, Any]) -> None:
        """Add response data to an existing request."""
        if request_id not in self.pending_requests:
            logger.warning(f"Response received for unknown request: {request_id}")
            return
            
        request = self.pending_requests[request_id]
        
        # Update response data
        request.response_status = response_data.get('status')
        request.response_headers = response_data.get('headers', {})
        request.response_timestamp = time.time()
        request.size = response_data.get('size')
        request.compressed_size = response_data.get('compressed_size')
        
        # Check for cache hit
        cache_control = request.response_headers.get('cache-control', '').lower()
        request.cache_hit = 'from-cache' in response_data.get('from_cache', '') or \
                           response_data.get('from_disk_cache', False) or \
                           response_data.get('from_memory_cache', False)
                           
        # Check for service worker
        request.from_service_worker = response_data.get('from_service_worker', False)
        
        # Add timing data if available
        timing_data = response_data.get('timing', {})
        if timing_data:
            request.timing = NetworkTiming(
                dns_lookup=timing_data.get('dns_lookup'),
                tcp_connect=timing_data.get('tcp_connect'),
                tls_handshake=timing_data.get('tls_handshake'),
                request_sent=timing_data.get('request_sent'),
                waiting=timing_data.get('waiting'),
                content_download=timing_data.get('content_download'),
                total_time=timing_data.get('total_time')
            )
            
        # Move to completed requests
        self.requests.append(request)
        del self.pending_requests[request_id]
        
        logger.debug(f"Added response for request: {request.url} - Status: {request.response_status}")
        
    def add_request_failure(self, request_id: str, error: str, blocked_reason: Optional[str] = None) -> None:
        """Mark a request as failed."""
        if request_id not in self.pending_requests:
            logger.warning(f"Failure reported for unknown request: {request_id}")
            return
            
        request = self.pending_requests[request_id]
        request.error = error
        request.blocked_reason = blocked_reason
        
        # Move to completed requests
        self.requests.append(request)
        del self.pending_requests[request_id]
        
        logger.warning(f"Request failed: {request.url} - Error: {error}")
        
    def get_analysis(self) -> NetworkAnalysis:
        """Get comprehensive network analysis."""
        if not self.requests:
            return NetworkAnalysis(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                blocked_requests=0,
                cached_requests=0,
                average_response_time=0.0,
                slowest_requests=[],
                fastest_requests=[],
                resource_types={},
                domains={},
                status_codes={},
                total_bytes_transferred=0,
                total_bytes_compressed=0,
                compression_ratio=0.0,
                issues=[],
                recommendations=[],
                performance_score=0.0
            )
            
        # Basic counts
        total_requests = len(self.requests)
        successful_requests = len([r for r in self.requests if r.is_successful])
        failed_requests = len([r for r in self.requests if r.is_error])
        blocked_requests = len([r for r in self.requests if r.blocked_reason])
        cached_requests = len([r for r in self.requests if r.cache_hit])
        
        # Performance metrics
        response_times = [r.duration for r in self.requests if r.duration is not None]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Sort requests by response time for analysis
        timed_requests = [r for r in self.requests if r.duration is not None]
        timed_requests.sort(key=lambda x: x.duration, reverse=True)
        
        slowest_requests = [
            {
                'url': r.url,
                'method': r.method,
                'duration': r.duration,
                'status': r.response_status,
                'size': r.size
            }
            for r in timed_requests[:5]
        ]
        
        fastest_requests = [
            {
                'url': r.url,
                'method': r.method,
                'duration': r.duration,
                'status': r.response_status,
                'cache_hit': r.cache_hit
            }
            for r in timed_requests[-5:]
        ]
        
        # Resource type analysis
        resource_types = {}
        for request in self.requests:
            resource_type = request.resource_type
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            
        # Domain analysis
        domains = {}
        for request in self.requests:
            domain = request.domain
            domains[domain] = domains.get(domain, 0) + 1
            
        # Status code analysis
        status_codes = {}
        for request in self.requests:
            if request.response_status:
                status = request.response_status
                status_codes[status] = status_codes.get(status, 0) + 1
                
        # Size analysis
        total_bytes = sum(r.size for r in self.requests if r.size)
        total_compressed = sum(r.compressed_size for r in self.requests if r.compressed_size)
        compression_ratio = (1 - total_compressed / total_bytes) if total_bytes > 0 else 0.0
        
        # Generate issues and recommendations
        issues, recommendations = self._analyze_issues_and_recommendations(
            total_requests, failed_requests, average_response_time, 
            status_codes, domains, resource_types
        )
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(
            successful_requests / total_requests if total_requests > 0 else 0,
            average_response_time,
            cached_requests / total_requests if total_requests > 0 else 0
        )
        
        return NetworkAnalysis(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            blocked_requests=blocked_requests,
            cached_requests=cached_requests,
            average_response_time=average_response_time,
            slowest_requests=slowest_requests,
            fastest_requests=fastest_requests,
            resource_types=resource_types,
            domains=domains,
            status_codes=status_codes,
            total_bytes_transferred=total_bytes,
            total_bytes_compressed=total_compressed,
            compression_ratio=compression_ratio,
            issues=issues,
            recommendations=recommendations,
            performance_score=performance_score
        )
        
    def _analyze_issues_and_recommendations(
        self, 
        total_requests: int,
        failed_requests: int,
        avg_response_time: float,
        status_codes: Dict[int, int],
        domains: Dict[str, int],
        resource_types: Dict[str, int]
    ) -> tuple[List[str], List[str]]:
        """Analyze network data to identify issues and generate recommendations."""
        issues = []
        recommendations = []
        
        # High failure rate
        failure_rate = failed_requests / total_requests if total_requests > 0 else 0
        if failure_rate > 0.1:  # More than 10% failures
            issues.append(f"High network failure rate: {failure_rate:.1%} of requests failed")
            recommendations.append("🔧 Investigate network failures - check API endpoints and server status")
            
        # Slow response times
        if avg_response_time > 2000:  # More than 2 seconds
            issues.append(f"Slow average response time: {avg_response_time:.0f}ms")
            recommendations.append("⚡ Optimize API response times - consider caching, CDN, or server optimization")
        elif avg_response_time > 1000:  # More than 1 second
            recommendations.append("⏱️ Consider optimizing response times for better user experience")
            
        # HTTP error analysis
        error_4xx = sum(count for status, count in status_codes.items() if 400 <= status < 500)
        error_5xx = sum(count for status, count in status_codes.items() if status >= 500)
        
        if error_4xx > 0:
            issues.append(f"Client errors detected: {error_4xx} requests with 4xx status codes")
            recommendations.append("🔍 Review client-side requests - check URLs, parameters, and authentication")
            
        if error_5xx > 0:
            issues.append(f"Server errors detected: {error_5xx} requests with 5xx status codes")
            recommendations.append("🚨 Investigate server-side issues - check server logs and health")
            
        # Too many domains (potential performance impact)
        if len(domains) > 10:
            issues.append(f"High number of domains: {len(domains)} different domains contacted")
            recommendations.append("🌐 Consider reducing external dependencies to improve loading performance")
            
        # Large number of requests
        if total_requests > 100:
            recommendations.append("📊 High request volume detected - consider request bundling or optimization")
            
        # Resource type analysis
        if resource_types.get('image', 0) > 20:
            recommendations.append("🖼️ Many image requests detected - consider image optimization and lazy loading")
            
        if resource_types.get('script', 0) > 15:
            recommendations.append("📜 Many script requests detected - consider script bundling and minification")
            
        return issues, recommendations
        
    def _calculate_performance_score(self, success_rate: float, avg_response_time: float, cache_rate: float) -> float:
        """Calculate overall network performance score (0-100)."""
        # Success rate component (40% weight)
        success_score = success_rate * 40
        
        # Response time component (40% weight)
        # Good: <500ms, Acceptable: <1000ms, Poor: >2000ms
        if avg_response_time < 500:
            response_score = 40
        elif avg_response_time < 1000:
            response_score = 30
        elif avg_response_time < 2000:
            response_score = 20
        else:
            response_score = 10
            
        # Cache utilization component (20% weight)
        cache_score = cache_rate * 20
        
        return success_score + response_score + cache_score
        
    def get_domain_analysis(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed analysis per domain."""
        domain_stats = {}
        
        for request in self.requests:
            domain = request.domain
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'total_bytes': 0,
                    'response_times': [],
                    'resource_types': {},
                    'status_codes': {}
                }
                
            stats = domain_stats[domain]
            stats['total_requests'] += 1
            
            if request.is_successful:
                stats['successful_requests'] += 1
            elif request.is_error:
                stats['failed_requests'] += 1
                
            if request.size:
                stats['total_bytes'] += request.size
                
            if request.duration:
                stats['response_times'].append(request.duration)
                
            # Resource types for this domain
            resource_type = request.resource_type
            stats['resource_types'][resource_type] = stats['resource_types'].get(resource_type, 0) + 1
            
            # Status codes for this domain
            if request.response_status:
                status = request.response_status
                stats['status_codes'][status] = stats['status_codes'].get(status, 0) + 1
                
        # Calculate averages and additional metrics
        for domain, stats in domain_stats.items():
            if stats['response_times']:
                stats['average_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
            else:
                stats['average_response_time'] = 0
                stats['max_response_time'] = 0
                stats['min_response_time'] = 0
                
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests'] if stats['total_requests'] > 0 else 0
            
        return domain_stats
        
    def export_summary(self) -> Dict[str, Any]:
        """Export comprehensive network monitoring summary."""
        analysis = self.get_analysis()
        domain_analysis = self.get_domain_analysis()
        
        return {
            'monitoring_duration': time.time() - self.start_time,
            'analysis': analysis.__dict__,
            'domain_analysis': domain_analysis,
            'pending_requests': len(self.pending_requests),
            'timeline': [
                {
                    'timestamp': req.timestamp,
                    'url': req.url,
                    'method': req.method,
                    'status': req.response_status,
                    'duration': req.duration,
                    'size': req.size,
                    'error': req.error
                }
                for req in sorted(self.requests, key=lambda x: x.timestamp)[-20:]  # Last 20 requests
            ]
        }

