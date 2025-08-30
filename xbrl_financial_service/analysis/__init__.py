"""
Financial Analysis Module

Advanced financial analysis capabilities including funnel analysis,
trend analysis, and comprehensive metrics calculation.
"""

from .funnel_analyzer import FunnelAnalyzer
from .trend_analyzer import TrendAnalyzer
from .metrics_calculator import MetricsCalculator, MetricDefinition, MetricResult, TrendMetric

__all__ = [
    "FunnelAnalyzer",
    "TrendAnalyzer", 
    "MetricsCalculator",
    "MetricDefinition",
    "MetricResult",
    "TrendMetric"
]