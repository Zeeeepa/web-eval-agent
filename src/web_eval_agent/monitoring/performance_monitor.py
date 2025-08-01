"""
Performance Monitor

Advanced performance monitoring with Core Web Vitals, resource timing,
and comprehensive performance analysis.
"""

import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PerformanceGrade(Enum):
    """Performance grade classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class CoreWebVitals:
    """Core Web Vitals metrics."""
    # Largest Contentful Paint (LCP)
    lcp: Optional[float] = None
    lcp_grade: Optional[PerformanceGrade] = None
    
    # First Input Delay (FID)
    fid: Optional[float] = None
    fid_grade: Optional[PerformanceGrade] = None
    
    # Cumulative Layout Shift (CLS)
    cls: Optional[float] = None
    cls_grade: Optional[PerformanceGrade] = None
    
    # First Contentful Paint (FCP)
    fcp: Optional[float] = None
    fcp_grade: Optional[PerformanceGrade] = None
    
    # Time to Interactive (TTI)
    tti: Optional[float] = None
    tti_grade: Optional[PerformanceGrade] = None
    
    # Total Blocking Time (TBT)
    tbt: Optional[float] = None
    tbt_grade: Optional[PerformanceGrade] = None


@dataclass
class ResourceTiming:
    """Resource loading timing information."""
    name: str
    entry_type: str
    start_time: float
    duration: float
    dns_lookup: Optional[float] = None
    tcp_connect: Optional[float] = None
    request_start: Optional[float] = None
    response_start: Optional[float] = None
    response_end: Optional[float] = None
    transfer_size: Optional[int] = None
    encoded_body_size: Optional[int] = None
    decoded_body_size: Optional[int] = None


@dataclass
class MemoryInfo:
    """Memory usage information."""
    used_js_heap_size: int
    total_js_heap_size: int
    js_heap_size_limit: int
    
    @property
    def memory_usage_percentage(self) -> float:
        """Calculate memory usage percentage."""
        return (self.used_js_heap_size / self.js_heap_size_limit) * 100 if self.js_heap_size_limit > 0 else 0


@dataclass
class PerformanceAnalysis:
    """Comprehensive performance analysis results."""
    core_web_vitals: CoreWebVitals
    overall_score: float
    overall_grade: PerformanceGrade
    
    # Timing metrics
    page_load_time: Optional[float]
    dom_content_loaded: Optional[float]
    first_paint: Optional[float]
    
    # Resource analysis
    total_resources: int
    total_transfer_size: int
    total_encoded_size: int
    compression_ratio: float
    
    # Memory analysis
    memory_info: Optional[MemoryInfo]
    memory_grade: Optional[PerformanceGrade]
    
    # Performance insights
    bottlenecks: List[str]
    recommendations: List[str]
    critical_issues: List[str]
    
    # Resource breakdown
    resource_breakdown: Dict[str, Dict[str, Any]]


class PerformanceMonitor:
    """
    Advanced performance monitoring with Core Web Vitals tracking,
    resource analysis, and actionable performance insights.
    """
    
    def __init__(self):
        self.measurements: List[Dict[str, Any]] = []
        self.resource_timings: List[ResourceTiming] = []
        self.memory_samples: List[MemoryInfo] = []
        self.start_time = time.time()
        self.navigation_start: Optional[float] = None
        
        # Performance thresholds (in milliseconds)
        self.thresholds = {
            'lcp': {'good': 2500, 'needs_improvement': 4000},
            'fid': {'good': 100, 'needs_improvement': 300},
            'cls': {'good': 0.1, 'needs_improvement': 0.25},
            'fcp': {'good': 1800, 'needs_improvement': 3000},
            'tti': {'good': 3800, 'needs_improvement': 7300},
            'tbt': {'good': 200, 'needs_improvement': 600}
        }
        
    def add_navigation_timing(self, timing_data: Dict[str, Any]) -> None:
        """Add navigation timing data."""
        self.navigation_start = timing_data.get('navigation_start', time.time())
        
        measurement = {
            'timestamp': time.time(),
            'type': 'navigation',
            'data': timing_data
        }
        
        self.measurements.append(measurement)
        logger.debug("Added navigation timing data")
        
    def add_paint_timing(self, paint_data: Dict[str, Any]) -> None:
        """Add paint timing data."""
        measurement = {
            'timestamp': time.time(),
            'type': 'paint',
            'data': paint_data
        }
        
        self.measurements.append(measurement)
        logger.debug(f"Added paint timing: {paint_data.get('name')}")
        
    def add_core_web_vital(self, metric_name: str, value: float, rating: Optional[str] = None) -> None:
        """Add Core Web Vital measurement."""
        measurement = {
            'timestamp': time.time(),
            'type': 'core_web_vital',
            'metric': metric_name,
            'value': value,
            'rating': rating
        }
        
        self.measurements.append(measurement)
        logger.info(f"Core Web Vital - {metric_name}: {value}ms (rating: {rating})")
        
    def add_resource_timing(self, resource_data: Dict[str, Any]) -> None:
        """Add resource timing data."""
        try:
            resource_timing = ResourceTiming(
                name=resource_data['name'],
                entry_type=resource_data.get('entry_type', 'resource'),
                start_time=resource_data['start_time'],
                duration=resource_data['duration'],
                dns_lookup=resource_data.get('domain_lookup_end', 0) - resource_data.get('domain_lookup_start', 0) if resource_data.get('domain_lookup_start') else None,
                tcp_connect=resource_data.get('connect_end', 0) - resource_data.get('connect_start', 0) if resource_data.get('connect_start') else None,
                request_start=resource_data.get('request_start'),
                response_start=resource_data.get('response_start'),
                response_end=resource_data.get('response_end'),
                transfer_size=resource_data.get('transfer_size'),
                encoded_body_size=resource_data.get('encoded_body_size'),
                decoded_body_size=resource_data.get('decoded_body_size')
            )
            
            self.resource_timings.append(resource_timing)
            logger.debug(f"Added resource timing: {resource_timing.name}")
            
        except KeyError as e:
            logger.warning(f"Invalid resource timing data, missing key: {e}")
            
    def add_memory_sample(self, memory_data: Dict[str, Any]) -> None:
        """Add memory usage sample."""
        try:
            memory_info = MemoryInfo(
                used_js_heap_size=memory_data['used_js_heap_size'],
                total_js_heap_size=memory_data['total_js_heap_size'],
                js_heap_size_limit=memory_data['js_heap_size_limit']
            )
            
            self.memory_samples.append(memory_info)
            logger.debug(f"Added memory sample: {memory_info.memory_usage_percentage:.1f}% usage")
            
        except KeyError as e:
            logger.warning(f"Invalid memory data, missing key: {e}")
            
    def add_layout_shift(self, shift_data: Dict[str, Any]) -> None:
        """Add layout shift measurement."""
        measurement = {
            'timestamp': time.time(),
            'type': 'layout_shift',
            'data': shift_data
        }
        
        self.measurements.append(measurement)
        logger.debug(f"Added layout shift: {shift_data.get('value', 0)}")
        
    def _grade_metric(self, metric: str, value: float) -> PerformanceGrade:
        """Grade a performance metric based on thresholds."""
        if metric not in self.thresholds:
            return PerformanceGrade.GOOD
            
        thresholds = self.thresholds[metric]
        
        if value <= thresholds['good']:
            return PerformanceGrade.EXCELLENT
        elif value <= thresholds['needs_improvement']:
            return PerformanceGrade.GOOD
        else:
            return PerformanceGrade.POOR
            
    def _extract_core_web_vitals(self) -> CoreWebVitals:
        """Extract Core Web Vitals from measurements."""
        cwv = CoreWebVitals()
        
        # Extract metrics from measurements
        for measurement in self.measurements:
            if measurement['type'] == 'core_web_vital':
                metric = measurement['metric'].lower()
                value = measurement['value']
                
                if metric == 'lcp':
                    cwv.lcp = value
                    cwv.lcp_grade = self._grade_metric('lcp', value)
                elif metric == 'fid':
                    cwv.fid = value
                    cwv.fid_grade = self._grade_metric('fid', value)
                elif metric == 'cls':
                    cwv.cls = value
                    cwv.cls_grade = self._grade_metric('cls', value)
                elif metric == 'fcp':
                    cwv.fcp = value
                    cwv.fcp_grade = self._grade_metric('fcp', value)
                elif metric == 'tti':
                    cwv.tti = value
                    cwv.tti_grade = self._grade_metric('tti', value)
                elif metric == 'tbt':
                    cwv.tbt = value
                    cwv.tbt_grade = self._grade_metric('tbt', value)
                    
        # Extract from paint timing if not available as CWV
        if cwv.fcp is None:
            for measurement in self.measurements:
                if measurement['type'] == 'paint' and measurement['data'].get('name') == 'first-contentful-paint':
                    cwv.fcp = measurement['data']['start_time']
                    cwv.fcp_grade = self._grade_metric('fcp', cwv.fcp)
                    break
                    
        return cwv
        
    def _analyze_resource_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Analyze resource loading breakdown by type."""
        breakdown = {}
        
        for resource in self.resource_timings:
            # Determine resource type from URL/name
            resource_type = self._classify_resource_type(resource.name)
            
            if resource_type not in breakdown:
                breakdown[resource_type] = {
                    'count': 0,
                    'total_duration': 0,
                    'total_size': 0,
                    'average_duration': 0,
                    'largest_resource': None,
                    'slowest_resource': None
                }
                
            stats = breakdown[resource_type]
            stats['count'] += 1
            stats['total_duration'] += resource.duration
            
            if resource.transfer_size:
                stats['total_size'] += resource.transfer_size
                
            # Track largest resource
            if resource.transfer_size and (not stats['largest_resource'] or 
                                         resource.transfer_size > stats['largest_resource']['size']):
                stats['largest_resource'] = {
                    'name': resource.name,
                    'size': resource.transfer_size,
                    'duration': resource.duration
                }
                
            # Track slowest resource
            if not stats['slowest_resource'] or resource.duration > stats['slowest_resource']['duration']:
                stats['slowest_resource'] = {
                    'name': resource.name,
                    'duration': resource.duration,
                    'size': resource.transfer_size or 0
                }
                
        # Calculate averages
        for resource_type, stats in breakdown.items():
            if stats['count'] > 0:
                stats['average_duration'] = stats['total_duration'] / stats['count']
                
        return breakdown
        
    def _classify_resource_type(self, url: str) -> str:
        """Classify resource type based on URL."""
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in ['.js', 'javascript']):
            return 'script'
        elif any(ext in url_lower for ext in ['.css', 'stylesheet']):
            return 'stylesheet'
        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            return 'image'
        elif any(ext in url_lower for ext in ['.woff', '.woff2', '.ttf', '.otf']):
            return 'font'
        elif 'api' in url_lower or 'ajax' in url_lower or url_lower.endswith('.json'):
            return 'api'
        else:
            return 'other'
            
    def _identify_bottlenecks(self, cwv: CoreWebVitals, resource_breakdown: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Core Web Vitals bottlenecks
        if cwv.lcp and cwv.lcp > 4000:
            bottlenecks.append(f"Poor Largest Contentful Paint ({cwv.lcp:.0f}ms) - main content loads too slowly")
            
        if cwv.fid and cwv.fid > 300:
            bottlenecks.append(f"Poor First Input Delay ({cwv.fid:.0f}ms) - page not responsive to user input")
            
        if cwv.cls and cwv.cls > 0.25:
            bottlenecks.append(f"Poor Cumulative Layout Shift ({cwv.cls:.3f}) - page layout is unstable")
            
        if cwv.fcp and cwv.fcp > 3000:
            bottlenecks.append(f"Slow First Contentful Paint ({cwv.fcp:.0f}ms) - initial content appears too late")
            
        # Resource-based bottlenecks
        if 'script' in resource_breakdown:
            script_stats = resource_breakdown['script']
            if script_stats['average_duration'] > 1000:
                bottlenecks.append(f"Slow JavaScript loading (avg {script_stats['average_duration']:.0f}ms)")
                
        if 'stylesheet' in resource_breakdown:
            css_stats = resource_breakdown['stylesheet']
            if css_stats['average_duration'] > 500:
                bottlenecks.append(f"Slow CSS loading (avg {css_stats['average_duration']:.0f}ms)")
                
        if 'image' in resource_breakdown:
            image_stats = resource_breakdown['image']
            if image_stats['total_size'] > 2000000:  # 2MB
                bottlenecks.append(f"Large image payload ({image_stats['total_size'] / 1024 / 1024:.1f}MB)")
                
        # Memory bottlenecks
        if self.memory_samples:
            latest_memory = self.memory_samples[-1]
            if latest_memory.memory_usage_percentage > 80:
                bottlenecks.append(f"High memory usage ({latest_memory.memory_usage_percentage:.1f}%)")
                
        return bottlenecks
        
    def _generate_recommendations(self, cwv: CoreWebVitals, resource_breakdown: Dict[str, Dict[str, Any]], bottlenecks: List[str]) -> List[str]:
        """Generate actionable performance recommendations."""
        recommendations = []
        
        # Core Web Vitals recommendations
        if cwv.lcp and cwv.lcp > 2500:
            recommendations.append("🎯 Optimize Largest Contentful Paint: compress images, use CDN, optimize server response time")
            
        if cwv.fid and cwv.fid > 100:
            recommendations.append("⚡ Improve First Input Delay: reduce JavaScript execution time, use web workers")
            
        if cwv.cls and cwv.cls > 0.1:
            recommendations.append("📐 Fix Cumulative Layout Shift: set image dimensions, avoid dynamic content insertion")
            
        if cwv.fcp and cwv.fcp > 1800:
            recommendations.append("🚀 Speed up First Contentful Paint: optimize critical rendering path, inline critical CSS")
            
        # Resource-specific recommendations
        if 'script' in resource_breakdown and resource_breakdown['script']['count'] > 10:
            recommendations.append("📦 Bundle JavaScript files to reduce HTTP requests")
            
        if 'stylesheet' in resource_breakdown and resource_breakdown['stylesheet']['count'] > 5:
            recommendations.append("🎨 Combine CSS files and remove unused styles")
            
        if 'image' in resource_breakdown:
            image_stats = resource_breakdown['image']
            if image_stats['total_size'] > 1000000:  # 1MB
                recommendations.append("🖼️ Optimize images: use WebP format, implement lazy loading, compress images")
                
        if 'font' in resource_breakdown:
            recommendations.append("🔤 Optimize font loading: use font-display: swap, preload critical fonts")
            
        # Memory recommendations
        if self.memory_samples:
            avg_memory = statistics.mean(sample.memory_usage_percentage for sample in self.memory_samples)
            if avg_memory > 60:
                recommendations.append("🧠 Optimize memory usage: remove memory leaks, optimize data structures")
                
        # General recommendations based on resource count
        total_resources = len(self.resource_timings)
        if total_resources > 100:
            recommendations.append("📊 Reduce resource count: implement resource bundling and lazy loading")
            
        return recommendations
        
    def _calculate_overall_score(self, cwv: CoreWebVitals) -> tuple[float, PerformanceGrade]:
        """Calculate overall performance score and grade."""
        scores = []
        
        # Core Web Vitals scoring (0-100 each)
        if cwv.lcp is not None:
            if cwv.lcp <= 2500:
                scores.append(100)
            elif cwv.lcp <= 4000:
                scores.append(75)
            else:
                scores.append(25)
                
        if cwv.fid is not None:
            if cwv.fid <= 100:
                scores.append(100)
            elif cwv.fid <= 300:
                scores.append(75)
            else:
                scores.append(25)
                
        if cwv.cls is not None:
            if cwv.cls <= 0.1:
                scores.append(100)
            elif cwv.cls <= 0.25:
                scores.append(75)
            else:
                scores.append(25)
                
        if cwv.fcp is not None:
            if cwv.fcp <= 1800:
                scores.append(100)
            elif cwv.fcp <= 3000:
                scores.append(75)
            else:
                scores.append(25)
                
        # Calculate average score
        overall_score = statistics.mean(scores) if scores else 50
        
        # Determine grade
        if overall_score >= 90:
            grade = PerformanceGrade.EXCELLENT
        elif overall_score >= 75:
            grade = PerformanceGrade.GOOD
        elif overall_score >= 50:
            grade = PerformanceGrade.NEEDS_IMPROVEMENT
        else:
            grade = PerformanceGrade.POOR
            
        return overall_score, grade
        
    def get_analysis(self) -> PerformanceAnalysis:
        """Get comprehensive performance analysis."""
        cwv = self._extract_core_web_vitals()
        resource_breakdown = self._analyze_resource_breakdown()
        bottlenecks = self._identify_bottlenecks(cwv, resource_breakdown)
        recommendations = self._generate_recommendations(cwv, resource_breakdown, bottlenecks)
        overall_score, overall_grade = self._calculate_overall_score(cwv)
        
        # Extract timing metrics
        page_load_time = None
        dom_content_loaded = None
        first_paint = None
        
        for measurement in self.measurements:
            if measurement['type'] == 'navigation':
                data = measurement['data']
                page_load_time = data.get('load_event_end', 0) - data.get('navigation_start', 0) if data.get('load_event_end') else None
                dom_content_loaded = data.get('dom_content_loaded_event_end', 0) - data.get('navigation_start', 0) if data.get('dom_content_loaded_event_end') else None
            elif measurement['type'] == 'paint' and measurement['data'].get('name') == 'first-paint':
                first_paint = measurement['data']['start_time']
                
        # Resource analysis
        total_resources = len(self.resource_timings)
        total_transfer_size = sum(r.transfer_size for r in self.resource_timings if r.transfer_size)
        total_encoded_size = sum(r.encoded_body_size for r in self.resource_timings if r.encoded_body_size)
        compression_ratio = (1 - total_encoded_size / total_transfer_size) if total_transfer_size > 0 else 0
        
        # Memory analysis
        memory_info = self.memory_samples[-1] if self.memory_samples else None
        memory_grade = None
        if memory_info:
            if memory_info.memory_usage_percentage < 50:
                memory_grade = PerformanceGrade.EXCELLENT
            elif memory_info.memory_usage_percentage < 70:
                memory_grade = PerformanceGrade.GOOD
            elif memory_info.memory_usage_percentage < 85:
                memory_grade = PerformanceGrade.NEEDS_IMPROVEMENT
            else:
                memory_grade = PerformanceGrade.POOR
                
        # Identify critical issues
        critical_issues = []
        if cwv.lcp and cwv.lcp > 4000:
            critical_issues.append("Critical: Largest Contentful Paint exceeds 4 seconds")
        if cwv.cls and cwv.cls > 0.25:
            critical_issues.append("Critical: Cumulative Layout Shift causes poor user experience")
        if memory_info and memory_info.memory_usage_percentage > 90:
            critical_issues.append("Critical: Memory usage near limit, risk of crashes")
            
        return PerformanceAnalysis(
            core_web_vitals=cwv,
            overall_score=overall_score,
            overall_grade=overall_grade,
            page_load_time=page_load_time,
            dom_content_loaded=dom_content_loaded,
            first_paint=first_paint,
            total_resources=total_resources,
            total_transfer_size=total_transfer_size,
            total_encoded_size=total_encoded_size,
            compression_ratio=compression_ratio,
            memory_info=memory_info,
            memory_grade=memory_grade,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            critical_issues=critical_issues,
            resource_breakdown=resource_breakdown
        )
        
    def export_summary(self) -> Dict[str, Any]:
        """Export comprehensive performance monitoring summary."""
        analysis = self.get_analysis()
        
        return {
            'monitoring_duration': time.time() - self.start_time,
            'analysis': {
                'overall_score': analysis.overall_score,
                'overall_grade': analysis.overall_grade.value,
                'core_web_vitals': {
                    'lcp': analysis.core_web_vitals.lcp,
                    'fid': analysis.core_web_vitals.fid,
                    'cls': analysis.core_web_vitals.cls,
                    'fcp': analysis.core_web_vitals.fcp,
                    'tti': analysis.core_web_vitals.tti,
                    'tbt': analysis.core_web_vitals.tbt
                },
                'timing_metrics': {
                    'page_load_time': analysis.page_load_time,
                    'dom_content_loaded': analysis.dom_content_loaded,
                    'first_paint': analysis.first_paint
                },
                'resource_analysis': {
                    'total_resources': analysis.total_resources,
                    'total_transfer_size': analysis.total_transfer_size,
                    'compression_ratio': analysis.compression_ratio
                },
                'memory_analysis': {
                    'current_usage': analysis.memory_info.memory_usage_percentage if analysis.memory_info else None,
                    'grade': analysis.memory_grade.value if analysis.memory_grade else None
                },
                'bottlenecks': analysis.bottlenecks,
                'recommendations': analysis.recommendations,
                'critical_issues': analysis.critical_issues
            },
            'resource_breakdown': analysis.resource_breakdown,
            'measurement_count': len(self.measurements),
            'resource_timing_count': len(self.resource_timings),
            'memory_samples_count': len(self.memory_samples)
        }

